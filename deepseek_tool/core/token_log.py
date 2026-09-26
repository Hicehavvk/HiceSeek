# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/core/token_log.py
import json
from datetime import datetime
from pathlib import Path

def log_token_call(token_log_file: Path, model: str, usage: dict):
    if not usage:
        return
    entry = {
        "ts": datetime.now().isoformat(),
        "model": model,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }
    token_log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def summarize_token_log(token_log_file: Path, days: int = 7):
    if not token_log_file.exists():
        return {}
    cutoff = datetime.now().timestamp() - days * 86400
    summary = {}
    with open(token_log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["ts"]).timestamp()
            except Exception:
                continue
            if ts < cutoff:
                continue
            date = entry["ts"][:10]
            if date not in summary:
                summary[date] = {"calls": 0, "tokens": 0}
            summary[date]["calls"] += 1
            summary[date]["tokens"] += entry.get("total_tokens", 0)
    return summary