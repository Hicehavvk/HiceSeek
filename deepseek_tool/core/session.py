# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/core/session.py
import json
import random
import string
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _gen_id() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{ts}_{suffix}"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Session:
    id: str
    title: str
    mode: str
    model: str
    system_prompt: str
    messages: list
    created: str
    updated: str

    def to_meta(self) -> dict:
        return {
            "type": "meta",
            "id": self.id,
            "title": self.title,
            "mode": self.mode,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "created": self.created,
            "updated": self.updated,
        }

    def total_tokens(self) -> int:
        return sum(m.get("tokens", 0) for m in self.messages)

    def total_prompt_tokens(self) -> int:
        return sum(m.get("prompt_tokens", 0) for m in self.messages)

    def total_completion_tokens(self) -> int:
        return sum(m.get("completion_tokens", 0) for m in self.messages)

    def touch(self):
        self.updated = _now()


class SessionManager:
    def __init__(self, sessions_dir: Path):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.jsonl"

    def new_session(self, system_prompt: str, model: str,
                    mode: str = "chat", title: str = "新会话") -> Session:
        now = _now()
        session = Session(
            id=_gen_id(),
            title=title,
            mode=mode,
            model=model,
            system_prompt=system_prompt,
            messages=[],
            created=now,
            updated=now,
        )
        self.save(session)
        return session

    def save(self, session: Session) -> None:
        session.touch()
        path = self._path(session.id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(session.to_meta(), ensure_ascii=False) + "\n")
            for msg in session.messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def load(self, session_id: str) -> Session | None:
        path = self._path(session_id)
        if not path.exists():
            return None
        meta = None
        messages = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") == "meta":
                    meta = obj
                else:
                    messages.append(obj)
        if not meta:
            return None
        return Session(
            id=meta["id"],
            title=meta.get("title", "未命名"),
            mode=meta.get("mode", "chat"),
            model=meta.get("model", "deepseek-flash"),
            system_prompt=meta.get("system_prompt", ""),
            messages=messages,
            created=meta.get("created", ""),
            updated=meta.get("updated", ""),
        )

    def list_sessions(self) -> list[dict]:
        items = []
        for path in self.sessions_dir.glob("*.jsonl"):
            try:
                meta = None
                msg_count = 0
                total_tokens = 0
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        if obj.get("type") == "meta":
                            meta = obj
                        else:
                            msg_count += 1
                            total_tokens += obj.get("tokens", 0)
                if not meta:
                    continue
                items.append({
                    "id": meta["id"],
                    "title": meta.get("title", "未命名"),
                    "created": meta.get("created", ""),
                    "updated": meta.get("updated", ""),
                    "mode": meta.get("mode", "chat"),
                    "model": meta.get("model", ""),
                    "message_count": msg_count,
                    "total_tokens": total_tokens,
                })
            except Exception:
                continue
        items.sort(key=lambda x: x["updated"], reverse=True)
        return items

    def latest_session(self) -> Session | None:
        items = self.list_sessions()
        if not items:
            return None
        return self.load(items[0]["id"])

    def latest_by_mode(self, mode: str) -> Session | None:
        """返回指定 mode 的最新会话，没有则 None。"""
        items = self.list_sessions()
        for it in items:
            if it.get("mode") == mode:
                return self.load(it["id"])
        return None

    def rename(self, session_id: str, title: str) -> bool:
        session = self.load(session_id)
        if session is None:
            return False
        session.title = title
        self.save(session)
        return True

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False