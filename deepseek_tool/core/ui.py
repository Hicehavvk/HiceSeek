# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/core/ui.py
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.markdown import Markdown

console = Console()


def role_labels(mode: str):
    """返回 (用户标签, 助手标签)。"""
    return {
        "chat": ("秦老师", "鲸鱼娘"),
        "anima": ("秦老师", "anima-2.9B"),
        "minimax": ("秦老师", "MiniMax-H3"),
        "view": ("秦老师", "会话"),
    }.get(mode, ("用户", "助手"))


def print_banner(config):
    console.print(Panel.fit(
        "[bold cyan]DeepSeek 通用工具[/bold cyan]\n"
        f"模型: {config.model}\n"
        f"深度思考: [yellow]{'开启' if config.thinking_enabled else '关闭'}[/yellow] | "
        f"Effort: [yellow]{config.reasoning_effort}[/yellow]",
        title="启动",
    ))


CHAT_HELP = """[bold]聊天模式命令[/bold]

  [cyan]/chat[/cyan]                 切换到聊天模式
  [cyan]/anima[/cyan]                切换到 anima 管道
  [cyan]/minimax[/cyan]              切换到 minimax 管道
  [cyan]/view[/cyan]                 切换到 view 模式
  [cyan]/new[/cyan]                  新建会话
  [cyan]/sessions[/cyan]             列出所有会话
  [cyan]/sessions --mode <m>[/cyan]  按模式过滤
  [cyan]/load <ID>[/cyan]            加载指定会话
  [cyan]/title <标题>[/cyan]         重命名当前会话
  [cyan]/undo[/cyan]                 撤销最近 1 轮
  [cyan]/trim <N>[/cyan]             只保留最近 N 轮
  [cyan]/save[/cyan]                 导出当前会话为 markdown
  [cyan]/cost[/cyan]                 查看当前会话 token 与成本
  [cyan]/file <路径>[/cyan]          从文件读取内容作为输入
  [cyan]/thinking on|off[/cyan]      切换深度思考
  [cyan]/effort low|high|max[/cyan]  设置思考强度
  [cyan]/help[/cyan]                 显示本帮助
  [cyan]/exit[/cyan]                 退出程序"""

PIPE_HELP_TMPL = """[bold]{label} 管道命令[/bold]

  [magenta]/chat[/magenta]                 切换到聊天模式
  [magenta]/anima[/magenta]                切换到 anima 管道
  [magenta]/minimax[/magenta]              切换到 minimax 管道
  [magenta]/view[/magenta]                 切换到 view 模式
  [magenta]/new[/magenta]                  新建会话
  [magenta]/sessions[/magenta]             列出所有会话
  [magenta]/load <ID>[/magenta]            加载指定会话
  [magenta]/title <标题>[/magenta]         重命名当前会话
  [magenta]/undo[/magenta]                 撤销最近 1 轮
  [magenta]/trim <N>[/magenta]             只保留最近 N 轮
  [magenta]/clear[/magenta]                清空当前管道上下文
  [magenta]/save[/magenta]                 导出当前会话为 markdown
  [magenta]/cost[/magenta]                 查看当前会话 token 与成本
  [magenta]/file <路径>[/magenta]          从文件读取内容作为输入
  [magenta]/thinking on|off[/magenta]      切换深度思考
  [magenta]/effort low|high|max[/magenta]  设置思考强度
  [magenta]/help[/magenta]                 显示本帮助
  [magenta]/exit[/magenta]                 退出程序"""

VIEW_HELP = """[bold]View 模式命令[/bold]

  [yellow]/list[/yellow]                列出所有会话
  [yellow]/list --mode <m>[/yellow]     按模式过滤（chat/anima/minimax）
  [yellow]/latest[/yellow]              查看最近更新的会话
  [yellow]/id <ID>[/yellow]             查看指定会话
  [yellow]/reasoning[/yellow]           切换展开/折叠思考内容
  [yellow]/chat[/yellow]                切换到聊天模式
  [yellow]/anima[/yellow]               切换到 anima 管道
  [yellow]/minimax[/yellow]             切换到 minimax 管道
  [yellow]/help[/yellow]                显示本帮助
  [yellow]/exit[/yellow]                退出程序"""

VIEW_HINT = ("[dim]命令: /list 列表 | /latest 最近 | /id <ID> 查看 | "
             "/reasoning 切换思考 | /chat /anima /minimax 切换 | "
             "/help 帮助 | /exit 退出[/dim]")


def print_help_for_mode(mode: str):
    if mode == "chat":
        console.print(Panel(CHAT_HELP, title="帮助", border_style="cyan"))
    elif mode == "view":
        console.print(Panel(VIEW_HELP, title="帮助", border_style="yellow"))
    else:
        label = {"anima": "anima-2.9B", "minimax": "MiniMax-H3"}.get(mode, mode)
        console.print(Panel(
            PIPE_HELP_TMPL.format(label=label),
            title="帮助",
            border_style="magenta",
        ))


def print_view_hint():
    console.print(VIEW_HINT)


def print_recent_token_summary(token_log_file: Path):
    from .token_log import summarize_token_log
    summary = summarize_token_log(token_log_file)
    if not summary:
        console.print("[dim]近期无 token 消耗记录。[/dim]")
        return
    console.print("[bold]近期消耗 (最近 7 天): [/bold]")
    for date in sorted(summary.keys(), reverse=True):
        s = summary[date]
        console.print(f"  {date}  {s['calls']} 次调用  共 {s['tokens']:,} token")


def stream_callback(event_type: str, text: str):
    if event_type == "reasoning":
        console.print(text, end="", style="dim italic")
    elif event_type == "content":
        console.print(text, end="")


def export_session_markdown(session, history_dir: Path) -> Path:
    from datetime import datetime
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = history_dir / f"session_{session.id}_{ts}.md"

    user_label, assistant_label = role_labels(session.mode)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {session.title}\n\n")
        f.write(f"- 会话ID: `{session.id}`\n")
        f.write(f"- 模式: `{session.mode}`\n")
        f.write(f"- 模型: `{session.model}`\n")
        f.write(f"- 创建: {session.created}\n")
        f.write(f"- 更新: {session.updated}\n\n---\n\n")
        for msg in session.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                f.write(f"**{user_label}**: {content}\n\n")
            elif role == "assistant":
                f.write(f"**{assistant_label}**:\n\n{content}\n\n---\n\n")
    return path


def render_session(session, show_reasoning: bool = False):
    """只读渲染一个 Session。"""
    total_tokens = session.total_tokens()
    lines = [
        f"[bold]{session.title}[/bold]",
        f"ID: [dim]{session.id}[/dim]",
        f"模式: [cyan]{session.mode}[/cyan]  |  模型: [cyan]{session.model}[/cyan]",
        f"创建: {session.created}  |  更新: {session.updated}",
        f"消息: {len(session.messages)} 条  |  累计 token: {total_tokens:,}",
    ]
    console.print(Panel("\n".join(lines), title="会话", border_style="cyan"))

    if session.system_prompt:
        console.print(Panel(
            session.system_prompt,
            title="System Prompt",
            border_style="dim",
        ))

    user_label, assistant_label = role_labels(session.mode)
    for msg in session.messages:
        _render_message(msg, user_label, assistant_label, show_reasoning)


def _render_message(msg: dict, user_label: str, assistant_label: str,
                    show_reasoning: bool):
    role = msg.get("role", "unknown")
    content = msg.get("content", "")
    ts = msg.get("ts", "")

    if role == "user":
        label, style = user_label, "bold green"
    elif role == "assistant":
        label, style = assistant_label, "bold magenta"
    else:
        label, style = role, "bold white"

    header = f"[{style}]{label}[/{style}]"
    if ts:
        header += f"  [dim]{ts}[/dim]"
    console.print(header)

    if role == "assistant" and msg.get("reasoning"):
        if show_reasoning:
            console.print("[dim italic]— 思考 —[/dim italic]")
            console.print(msg["reasoning"], style="dim italic")
            console.print()
        else:
            console.print("[dim](有思考内容，/reasoning 展开)[/dim]")

    if content:
        console.print(Markdown(content))
    console.print(Rule(style="dim"))