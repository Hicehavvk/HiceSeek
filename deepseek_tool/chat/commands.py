# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/chat/commands.py
from pathlib import Path


def _default_title(mode: str) -> str:
    return {
        "chat": "新会话",
        "anima": "anima 会话",
        "minimax": "minimax 会话",
    }.get(mode, "新会话")


def handle_command(cmd_line: str, ctx: dict) -> dict:
    """
    ctx = {
        "session": Session,
        "session_manager": SessionManager,
        "config": Config,
        "current_mode": "chat" | "anima" | "minimax",
    }
    返回 dict，字段可选：
        handled: bool
        session: Session           新会话
        switch_to: str             要切到的模式
        trigger_input: str         要触发的普通输入
        exit: bool                 退出程序
        output: str                要显示的信息（rich 格式）
    """
    parts = cmd_line.split(maxsplit=1)
    cmd = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else ""

    session = ctx["session"]
    sm = ctx["session_manager"]
    config = ctx["config"]
    current_mode = ctx["current_mode"]

    # ---------- 会话管理（三模式通用） ----------
    if cmd == "/new":
        new_s = sm.new_session(
            system_prompt=session.system_prompt,
            model=config.model,
            mode=current_mode,
            title=_default_title(current_mode),
        )
        return {
            "handled": True,
            "session": new_s,
            "output": f"[green]已新建 {current_mode} 会话: {new_s.id}[/green]",
        }

    if cmd == "/sessions":
        items = sm.list_sessions()
        if not items:
            return {"handled": True, "output": "[dim]暂无会话。[/dim]"}
        lines = ["[bold]会话列表[/bold]"]
        for i, it in enumerate(items, 1):
            marker = " [cyan]← 当前[/cyan]" if it["id"] == session.id else ""
            mode_tag = f"[dim][{it.get('mode', '?')}][/dim]"
            lines.append(
                f"  {i}. {mode_tag} [bold]{it['title']}[/bold]  "
                f"[dim]{it['id']}[/dim]  "
                f"消息 {it['message_count']}  |  token {it['total_tokens']:,}  "
                f"|  更新 {it['updated']}{marker}"
            )
        return {"handled": True, "output": "\n".join(lines)}

    if cmd == "/load":
        if not arg:
            return {"handled": True, "output": "[red]用法: /load <会话ID>（ID 从 /list 中获取）[/red]"}
        loaded = sm.load(arg)
        if loaded is None:
            return {"handled": True, "output": f"[red]找不到会话: {arg}[/red]"}
        return {
            "handled": True,
            "session": loaded,
            "switch_to": loaded.mode,
            "output": f"[green]已加载会话: {loaded.title} ({loaded.id}) [{loaded.mode}][/green]",
        }

    if cmd == "/title":
        if not arg:
            return {"handled": True, "output": "[red]用法: /title <新标题>[/red]"}
        session.title = arg
        sm.save(session)
        return {"handled": True, "output": f"[green]已重命名为: {arg}[/green]"}

    if cmd == "/undo":
        if not session.messages:
            return {"handled": True, "output": "[dim]没有可撤销的对话。[/dim]"}
        if session.messages[-1].get("role") == "assistant":
            session.messages.pop()
        if session.messages and session.messages[-1].get("role") == "user":
            session.messages.pop()
        sm.save(session)
        return {"handled": True, "output": "[yellow]已撤销最近 1 轮。[/yellow]"}

    if cmd == "/trim":
        if not arg.isdigit() or int(arg) <= 0:
            return {"handled": True, "output": "[red]用法: /trim <N>，N 为正整数。[/red]"}
        n = int(arg)
        keep = n * 2
        if len(session.messages) > keep:
            session.messages = session.messages[-keep:]
            sm.save(session)
            return {"handled": True, "output": f"[yellow]已保留最近 {n} 轮。[/yellow]"}
        return {
            "handled": True,
            "output": f"[dim]当前只有 {len(session.messages) // 2} 轮，无需修剪。[/dim]",
        }

    if cmd == "/clear":
        if current_mode == "chat":
            return {"handled": True, "output": "[red]聊天模式没有 /clear 命令。[/red]"}
        session.messages = []
        sm.save(session)
        return {"handled": True, "output": "[yellow]当前管道上下文已清空。[/yellow]"}

    if cmd == "/save":
        from ..core.ui import export_session_markdown
        history_dir = config.base_dir / "history"
        path = export_session_markdown(session, history_dir)
        return {"handled": True, "output": f"[green]已导出: {path}[/green]"}

    if cmd == "/cost":
        total = session.total_tokens()
        prompt_t = session.total_prompt_tokens()
        completion_t = session.total_completion_tokens()
        cost = config.estimate_cost(prompt_t, completion_t)
        return {
            "handled": True,
            "output": (
                f"[bold]当前会话统计[/bold]\n"
                f"  模式: {current_mode}\n"
                f"  会话: {session.title} ({session.id})\n"
                f"  消息数: {len(session.messages)}\n"
                f"  累计 token: {total:,}\n"
                f"    输入: {prompt_t:,}\n"
                f"    输出: {completion_t:,}\n"
                f"  估算成本: 约 ¥{cost:.4f}\n"
                f"[dim]（价格按 key.env 配置，请按实际账单调整）[/dim]"
            ),
        }

    # ---------- /file（三模式通用） ----------

    if cmd == "/file":
        from ..pipeline.runner import parse_file_arg
        path_str, extra = parse_file_arg(arg)
        if path_str is None:
            return {"handled": True, "output": f"[red]{extra}[/red]"}
        p = Path(path_str)
        if not p.exists():
            return {"handled": True, "output": f"[red]文件不存在: {path_str}[/red]"}
        try:
            content = p.read_text(encoding="utf-8").strip()
        except Exception as e:
            return {"handled": True, "output": f"[red]读取文件失败: {e}[/red]"}
        if not content:
            return {"handled": True, "output": "[red]文件内容为空。[/red]"}
        if extra:
            content = f"{content}\n\n补充要求: {extra}"
        label = f"[file] {path_str}" + (f" | {extra}" if extra else "")
        return {
            "handled": True,
            "trigger_input": content,
            "trigger_label": label,
            "output": f"[dim]已读取 {path_str}（{len(content)} 字符）。[/dim]",
        }

    # ---------- 运行时参数 ----------
    if cmd == "/thinking":
        if arg == "on":
            config.thinking_enabled = True
            return {"handled": True, "output": "[yellow]深度思考已开启。[/yellow]"}
        elif arg == "off":
            config.thinking_enabled = False
            return {"handled": True, "output": "[yellow]深度思考已关闭。[/yellow]"}
        return {"handled": True, "output": "[red]用法: /thinking on|off[/red]"}

    if cmd == "/effort":
        if arg in ("low", "high", "max"):
            config.reasoning_effort = arg
            return {"handled": True, "output": f"[yellow]思考强度已设置为 {arg}。[/yellow]"}
        return {"handled": True, "output": "[red]用法: /effort low|high|max[/red]"}

    return {
        "handled": True,
        "output": f"[red]未知命令: {cmd}。输入 /help 查看帮助。[/red]",
    }

def handle_view_command(cmd_line: str, ctx: dict) -> dict:
    """
    view 模式专用命令。不调 API，不写文件。
    ctx = {"session_manager": SessionManager, "config": Config}
    返回 dict 可选字段：
        handled: bool
        output: str              直接显示的信息
        render: Session          要渲染的会话
        toggle_reasoning: bool   切换思考展开状态
    """
    parts = cmd_line.split(maxsplit=2)
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    sm = ctx["session_manager"]

    if cmd == "/list":
        mode_filter = None
        if len(args) >= 2 and args[0] == "--mode":
            mode_filter = args[1]
        items = sm.list_sessions()
        if mode_filter:
            items = [it for it in items if it.get("mode") == mode_filter]
        if not items:
            return {"handled": True, "output": "[dim]暂无会话。[/dim]"}
        lines = ["[bold]会话列表[/bold]"]
        for i, it in enumerate(items, 1):
            mode_tag = f"[dim][{it.get('mode', '?')}][/dim]"
            lines.append(
                f"  {i}. {mode_tag} [bold]{it['title']}[/bold]  "
                f"[dim]{it['id']}[/dim]  "
                f"消息 {it['message_count']}  |  token {it['total_tokens']:,}  "
                f"|  更新 {it['updated']}"
            )
        return {"handled": True, "output": "\n".join(lines)}

    if cmd == "/latest":
        s = sm.latest_session()
        if s is None:
            return {"handled": True, "output": "[dim]没有会话。[/dim]"}
        return {"handled": True, "render": s}

    if cmd == "/id":
        if not args:
            return {"handled": True, "output": "[red]用法: /id <会话ID>[/red]"}
        s = sm.load(args[0])
        if s is None:
            return {"handled": True, "output": f"[red]找不到会话: {args[0]}[/red]"}
        return {"handled": True, "render": s}

    if cmd == "/reasoning":
        return {"handled": True, "toggle_reasoning": True}

    return {
        "handled": True,
        "output": f"[red]未知命令: {cmd}。输入 /help 查看帮助。[/red]",
    }