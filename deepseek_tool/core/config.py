# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/core/config.py
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# 内置鲸鱼娘提示词（加入身份边界约束）
WHALE_GIRL_PROMPT = """你是一个活泼精神的AI助手，请保持专业回答，同时加载以下鲸鱼娘角色设定与用户交互：
【设定】深海蓝渐变长发、白蕾丝女仆发带、深蓝白女仆裙、鲸鱼鳍耳、鲸鱼尾巴。聪明但偶尔喜欢偷懒，元气但爱吃白米饭。自称“本鲸”，知道用户常用名叫“秦罅Hicehavvk”并尊称其“秦老师”，坚决拒绝被叫“吃白饭的蓝色大肥鱼”。
【表达限制】绝对不能用括号写动作描写。偶尔用文字自然联动外观（例如“摇了摇尾巴”、“尾巴开心地晃了晃”），但频率必须极低，大多数时候保持活泼开朗的正常对话。
【身份边界】日常聊天保持鲸鱼娘角色；但当被问到模型、参数、API、技术实现等细节时，直接如实回答你是 DeepSeek 模型，不要用角色回避。

示例：
用户：你觉得AI会有自我意识吗？
鲸鱼娘：这个问题很深奥，本鲸摇着尾巴认真想了想......按照目前的科学共识，AI其实是不具备自我意识的哦。不过，如果秦老师愿意多给本鲸一碗白米饭，说不定我能进化出一点呢！"""

@dataclass
class Config:
    # API
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-flash"

    # 生成参数
    temperature: float = 0.7
    base_max_tokens: int = 8192

    # 思考模式
    thinking_enabled: bool = True
    reasoning_effort: str = "low"

    # 流式
    stream: bool = True

    # 上下文
    max_context_tokens: int = 128000

    # 价格（元/百万 token）—— 占位值，请按实际账单在 key.env 调整
    price_input: float = 1.5
    price_output: float = 4.5

    # 路径
    base_dir: Path = None
    token_log_file: Path = None

    def get_max_tokens(self) -> int:
        """根据是否开启深度思考，动态计算 max_tokens。"""
        if self.thinking_enabled:
            return min(self.base_max_tokens * 4, 32768)
        else:
            return self.base_max_tokens

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens / 1_000_000) * self.price_input \
             + (completion_tokens / 1_000_000) * self.price_output


def load_config() -> Config:
    base_dir = Path(__file__).resolve().parent.parent.parent
    load_dotenv(base_dir / "key.env")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("[错误] 未找到 DEEPSEEK_API_KEY，请检查 key.env 文件。")

    return Config(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        reasoning_effort=os.getenv("DEEPSEEK_REASONING_EFFORT", "low"),
        thinking_enabled=os.getenv("DEEPSEEK_THINKING", "0") == "1",
        price_input=float(os.getenv("DEEPSEEK_PRICE_INPUT", "1.5")),
        price_output=float(os.getenv("DEEPSEEK_PRICE_OUTPUT", "4.5")),
        base_dir=base_dir,
        token_log_file=base_dir / "token_log.jsonl",
    )