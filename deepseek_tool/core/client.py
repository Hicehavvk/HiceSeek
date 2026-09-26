# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/core/client.py
from openai import OpenAI
from .config import Config


class DeepSeekClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=60,
            max_retries=2,
        )

    def _build_extra_body(self) -> dict:
        return {
            "thinking": {
                "type": "enabled" if self.config.thinking_enabled else "disabled"
            }
        }

    def chat(self, messages: list[dict]):
        """非流式调用。返回 ({content, usage}, error)。"""
        try:
            resp = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                stream=False,
                temperature=self.config.temperature,
                max_tokens=self.config.get_max_tokens(),
                reasoning_effort=(
                    self.config.reasoning_effort
                    if self.config.thinking_enabled else None
                ),
                extra_body=self._build_extra_body(),
            )
        except Exception as e:
            return None, f"[API 请求失败] {e}"

        content = resp.choices[0].message.content or ""
        usage = {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        }
        return {"content": content, "usage": usage}, None

    def stream_chat(self, messages: list[dict], on_delta):
        """流式调用。返回 ({content, reasoning, usage}, error)。"""
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                stream=True,
                temperature=self.config.temperature,
                max_tokens=self.config.get_max_tokens(),
                reasoning_effort=(
                    self.config.reasoning_effort
                    if self.config.thinking_enabled else None
                ),
                extra_body=self._build_extra_body(),
                stream_options={"include_usage": True},
            )
        except Exception as e:
            return None, f"[API 请求失败] {e}"

        reasoning = ""
        content = ""
        usage = None

        try:
            for chunk in stream:
                if chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning += delta.reasoning_content
                    on_delta("reasoning", delta.reasoning_content)
                if delta.content:
                    content += delta.content
                    on_delta("content", delta.content)
        except Exception as e:
            return {"content": content, "reasoning": reasoning, "usage": usage}, f"[流中断] {e}"

        return {"content": content, "reasoning": reasoning, "usage": usage}, None