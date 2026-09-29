# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/pipeline/runner.py
import shlex

from .anima import ANIMA_SYSTEM, validate_anima, split_anima_blocks
from .minimax import MINIMAX_SYSTEM, validate_minimax
from .reverse import REVERSE_ANIMA_SYSTEM, REVERSE_MINIMAX_SYSTEM

PIPELINES = {
    "anima": {
        "system": ANIMA_SYSTEM,
        "validate": validate_anima,
        "blocks": split_anima_blocks,
        "label": "anima-2.9B",
    },
    "minimax": {
        "system": MINIMAX_SYSTEM,
        "validate": validate_minimax,
        "blocks": None,
        "label": "MiniMax-H3",
    },
    "reverse": {
        "system": REVERSE_ANIMA_SYSTEM,
        "validate": None,
        "blocks": None,
        "label": "reverse",
    },
}


def parse_file_arg(arg: str):
    """
    解析 /file 的参数。返回 (path_str, extra) 或 (None, error_msg)。
    选项 C：引号优先，无引号按第一个空格切分。路径尾部空格 rstrip。
    """
    arg = arg.strip()
    if not arg:
        return None, "用法: /file <路径> [补充要求]"

    if arg[0] in ('"', "'"):
        try:
            tokens = shlex.split(arg)
        except ValueError as e:
            return None, f"命令解析失败: {e}"
        if not tokens:
            return None, "用法: /file <路径> [补充要求]"
        path_str = tokens[0].rstrip()
        extra = " ".join(tokens[1:]).strip() if len(tokens) > 1 else ""
    else:
        idx = arg.find(" ")
        if idx == -1:
            path_str = arg.rstrip()
            extra = ""
        else:
            path_str = arg[:idx].rstrip()
            extra = arg[idx + 1:].strip()

    if not path_str:
        return None, "用法: /file <路径> [补充要求]"
    return path_str, extra