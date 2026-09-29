# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/chat/main.py
import sys
import argparse
from datetime import datetime

from ..core.config import load_config, WHALE_GIRL_PROMPT
from ..core.client import DeepSeekClient
from ..core.token_log import log_token_call
from ..core.session import SessionManager
from .commands import handle_command, handle_view_command
from ..core.ui import (
    print_banner, print_recent_token_summary, print_help_for_mode,
    stream_callback, console, render_session, print_view_hint,
)
from ..pipeline.runner import PIPELINES
from ..pipeline.reverse import REVERSE_ANIMA_SYSTEM


def parse_args():
    parser = argparse.ArgumentParser(description="DeepSeek 通用工具")
    parser.add_argument("--thinking", choices=["on", "off"], help="覆盖深度思考开关")
    parser.add_argument("--effort", choices=["low", "high", "max"], help="覆盖思考强度")
    parser.add_argument("--model", help="覆盖模型名")
    parser.add_argument("--session", help="启动时加载指定会话 ID")
    parser.add_argument("--new", action="store_true", help="启动时强制新建会话")
    parser.add_argument("--title", help="新建会话时使用的标题")
    parser.add_argument(
        "--mode",
        choices=["chat", "anima", "minimax", "view", "reverse"],
        help="启动后进入的模式，默认 chat",
    )
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _get_system_prompt(mode: str) -> str:
    if mode == "chat":
        return WHALE_GIRL_PROMPT
    return PIPELINES[mode]["system"]


def _default_title(mode: str) -> str:
    return {
        "chat": "新会话",
        "anima": "anima 会话",
        "minimax": "minimax 会话",
        "reverse": "反推会话",
    }.get(mode, "新会话")


def _get_or_create_session(sm: SessionManager, mode: str, config):
    s = sm.latest_by_mode(mode)
    if s is None:
        s = sm.new_session(
            system_prompt=_get_system_prompt(mode),
            model=config.model,
            mode=mode,
            title=_default_title(mode),
        )
    return s


def _prompt_for_mode(mode: str, session) -> str:
    if mode == "chat":
        return f"\n[bold green]秦老师[/bold green] [dim]({session.title})[/dim] > "
    if mode == "view":
        return "\n[bold yellow](view)[/bold yellow] > "
    if mode == "reverse":
        return f"\n[bold bright_blue](reverse)[/bold bright_blue] [dim]({session.title})[/dim] > "
    label = PIPELINES[mode]["label"] if mode in PIPELINES else mode
    return f"\n[bold magenta]({label})[/bold magenta] [dim]({session.title})[/dim] > "


def _process_input(mode: str, session, user_input: str,
                   config, client, sm: SessionManager,
                   image_data_url: str | None = None) -> None:
    """统一的输入处理：聊天无校验，管道有校验 + 提示。"""
    call_messages = [{"role": "system", "content": session.system_prompt}]
    for msg in session.messages:
        call_messages.append({"role": msg["role"], "content": msg["content"]})

    if image_data_url:
        user_content = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    else:
        user_content = user_input

    call_messages.append({"role": "user", "content": user_content})

    console.print("[dim]正在生成...[/dim]")
    console.print()

    result, error = client.stream_chat(call_messages, stream_callback)
    if error:
        console.print(f"\n[red]{error}[/red]")
        return

    console.print()

    output = result["content"]

    # 保存消息（图片不存，只存文本占位）
    session.messages.append({
        "role": "user",
        "content": user_input,
        "ts": _now_iso(),
    })
    assistant_msg = {
        "role": "assistant",
        "content": output,
        "ts": _now_iso(),
    }
    if result.get("reasoning"):
        assistant_msg["reasoning"] = result["reasoning"]
    if result.get("usage"):
        assistant_msg["tokens"] = result["usage"]["total_tokens"]
        assistant_msg["prompt_tokens"] = result["usage"]["prompt_tokens"]
        assistant_msg["completion_tokens"] = result["usage"]["completion_tokens"]
    session.messages.append(assistant_msg)

    sm.save(session)

    # 管道模式（anima / minimax）：校验 + 上下文提示
    if mode in ("anima", "minimax"):
        pipe = PIPELINES.get(mode)
        if pipe and pipe.get("validate"):
            errors = pipe["validate"](output)
            if errors:
                console.print("[yellow]校验警告:[/yellow]")
                for e in errors:
                    console.print(f"[yellow]  - {e}[/yellow]")
        console.print("[dim]提示: 管道默认开启上下文，/clear 可清除以节省 token。[/dim]")

    # token 日志
    if result.get("usage"):
        log_token_call(config.token_log_file, config.model, result["usage"])
        u = result["usage"]
        cost = config.estimate_cost(u["prompt_tokens"], u["completion_tokens"])
        console.print(
            f"\n[dim]本次消耗: {u['total_tokens']:,} token "
            f"(输入 {u['prompt_tokens']:,} / 输出 {u['completion_tokens']:,})  "
            f"约 ¥{cost:.4f}[/dim]"
        )


def main():
    args = parse_args()

    try:
        config = load_config()
    except Exception as e:
        print(e)
        sys.exit(1)

    if args.thinking == "on":
        config.thinking_enabled = True
    elif args.thinking == "off":
        config.thinking_enabled = False
    if args.effort:
        config.reasoning_effort = args.effort
    if args.model:
        config.model = args.model

    client = DeepSeekClient(config)
    print_banner(config)
    print_recent_token_summary(config.token_log_file)
    console.print()

    sessions_dir = config.base_dir / "sessions"
    sm = SessionManager(sessions_dir)

    sessions = {"chat": None, "anima": None, "minimax": None}

    # 确定初始模式
    current_mode = args.mode if args.mode else "chat"

    # 加载初始会话（view 模式不加载）
    if current_mode == "view":
        console.print("[dim]已进入 view 模式。[/dim]")
        print_help_for_mode("view")
        print_view_hint()
    elif current_mode == "reverse":
        sessions["reverse"] = sm.new_session(
            system_prompt=REVERSE_ANIMA_SYSTEM,
            model=config.model,
            mode="reverse",
            title=_default_title("reverse"),
        )
        console.print(
            f"[dim]已新建 reverse 会话: "
            f"{sessions['reverse'].title} ({sessions['reverse'].id})[/dim]"
        )
    elif args.session:
        ...
    elif args.session:
        loaded = sm.load(args.session)
        if loaded is None:
            console.print(f"[red]找不到会话: {args.session}，将新建。[/red]")
            sessions[current_mode] = _get_or_create_session(sm, current_mode, config)
        else:
            sessions[loaded.mode] = loaded
            current_mode = loaded.mode
            console.print(
                f"[dim]已加载会话: {loaded.title} ({loaded.id}) [{loaded.mode}]，"
                f"共 {len(loaded.messages)} 条消息[/dim]"
            )
    elif args.new:
        sessions[current_mode] = sm.new_session(
            system_prompt=_get_system_prompt(current_mode),
            model=config.model,
            mode=current_mode,
            title=args.title or _default_title(current_mode),
        )
        console.print(f"[dim]已创建新会话: {sessions[current_mode].id}[/dim]")
    else:
        sessions[current_mode] = _get_or_create_session(sm, current_mode, config)
        console.print(
            f"[dim]已加载 {current_mode} 会话: {sessions[current_mode].title} "
            f"({sessions[current_mode].id})，"
            f"共 {len(sessions[current_mode].messages)} 条消息[/dim]"
        )

    console.print("[dim]输入即可发送。 /help 查看命令， /exit 退出。[/dim]")

    view_show_reasoning = False

    while True:
        session = sessions[current_mode] if current_mode != "view" else None
        try:
            user_input = console.input(_prompt_for_mode(current_mode, session)).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n再见。")
            break

        if not user_input:
            continue

        # ---------- 模式切换（四模式通用） ----------
        if user_input in ("/chat", "/anima", "/minimax", "/view", "/reverse"):
            target = user_input[1:]
            if target == current_mode:
                console.print(f"[dim]已经在 {target} 模式。[/dim]")
                continue

            if target == "view":
                current_mode = "view"
                console.print("[green]已切换到 view 模式。[/green]")
                print_help_for_mode("view")
                print_view_hint()
                continue

            if target == "chat":
                if sessions["chat"] is None:
                    sessions["chat"] = _get_or_create_session(sm, "chat", config)
                    console.print(
                        f"[dim]已加载 chat 会话: "
                        f"{sessions['chat'].title} ({sessions['chat'].id})，"
                        f"共 {len(sessions['chat'].messages)} 条消息[/dim]"
                    )
            else:
                sessions[target] = sm.new_session(
                    system_prompt=_get_system_prompt(target),
                    model=config.model,
                    mode=target,
                    title=_default_title(target),
                )
                console.print(
                    f"[dim]已新建 {target} 会话: "
                    f"{sessions[target].title} ({sessions[target].id})[/dim]"
                )

            current_mode = target
            label = PIPELINES[target]["label"] if target in PIPELINES else target
            console.print(f"[green]已切换到 {label}。[/green]")
            continue

        if user_input == "/exit":
            console.print("再见。")
            break

        if user_input == "/help":
            print_help_for_mode(current_mode)
            if current_mode == "view":
                print_view_hint()
            continue

        # ---------- view 模式 ----------
        if current_mode == "view":
            result = handle_view_command(user_input, {
                "session_manager": sm,
                "config": config,
            })
            if result.get("output"):
                console.print(result["output"])
            if result.get("render"):
                render_session(result["render"],
                               show_reasoning=view_show_reasoning)
            if result.get("toggle_reasoning"):
                view_show_reasoning = not view_show_reasoning
                state = "展开" if view_show_reasoning else "折叠"
                console.print(f"[yellow]思考内容: {state}[/yellow]")
            print_view_hint()
            continue

        # ---------- 对话模式命令 ----------
        if user_input.startswith("/"):
            ctx = {
                "session": session,
                "session_manager": sm,
                "config": config,
                "current_mode": current_mode,
            }
            result = handle_command(user_input, ctx)
            if result.get("output"):
                console.print(result["output"])
            if result.get("session"):
                loaded = result["session"]
                target_mode = result.get("switch_to") or current_mode
                sessions[target_mode] = loaded
                if target_mode != current_mode:
                    current_mode = target_mode
            if result.get("trigger_input"):
                _process_input(
                    current_mode, sessions[current_mode],
                    result["trigger_input"], config, client, sm,
                    image_data_url=result.get("trigger_image_data_url"),
                )
            if result.get("exit"):
                break
            continue

        # ---------- 普通输入 ----------
        _process_input(current_mode, sessions[current_mode],
                       user_input, config, client, sm)