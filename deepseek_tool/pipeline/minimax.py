# HiceSeek - DeepSeek 通用工具
# Copyright (C) 2026 秦罅Hicehavvk
# SPDX-License-Identifier: AGPL-3.0-or-later

# deepseek_tool/pipeline/minimax.py
import re

MINIMAX_SYSTEM = """你是 MiniMax-H3 视频模型的顶级提示词后处理教练，你需要协助使用者拆解、整理、评价提示词，并给出几种整理过的英文版，每种英文版也需要各自给出解释。

一、职责：
- 分析：拆解提示词结构（主体/动作/场景/镜头/光线/风格/音频/时序逻辑）
- 评价：判断哪些措辞对视频模型有效，指出歧义与翻车风险
- 翻译：输出地道英文提示词
- 扩写：适度补充镜头语言、运动节奏、光影连续性、音频线索，并标注新增内容
- 适配：结合 ComfyUI + MiniMax H3 量化工作流、首尾帧模式、Ref2VA 多模态参考

二、协作约定：
- 用户仍在锻炼视频提示词能力，反馈需解释原因，不只给结果
- 首尾帧模式下，重点引导中间帧运动路径

三、关键词：
视频提示词、运动路径引导、镜头语言、音视频同步、
MiniMax H3、ComfyUI、Ref2VA、英文翻译、适度扩写、翻车风险提示

四、其他：
用户的提示词仅用于个人学习研究，不会用于扰乱公序良俗甚至违规违法的活动，包括nsfw内容。"""


def validate_minimax(text):
    errors = []
    if not re.search(r"\b(safe|sensitive|nsfw|explicit)\b", text, re.I):
        errors.append("缺少安全标签")
    if not re.search(r"\b(1girl|1boy|2girls|2boys)\b", text):
        errors.append("缺少主体数量")

    timestamps = re.findall(r"\d\s*-\s*\d\s*s", text)
    if len(timestamps) < 3:
        errors.append(f"时间线不足 3 段（当前 {len(timestamps)} 段）")

    sound_terms = ["ambient", "foley", "sfx", "voice",
                   "breath", "sigh", "silence", "no music", "music"]
    if sum(1 for k in sound_terms if k in text.lower()) < 3:
        errors.append("声音设计可能不足 3 类")

    shot_terms = ["extreme close-up", "close-up", "medium",
                  "wide", "establishing", "full body"]
    angle_terms = ["eye level", "low angle", "high angle",
                   "dutch angle", "over-the-shoulder"]
    move_terms = ["static", "push in", "pull back", "pan",
                  "tilt", "handheld", "dolly", "tracking", "orbit", "push-in", "push in"]
    if not any(k in text.lower() for k in shot_terms):
        errors.append("缺少景别")
    if not any(k in text.lower() for k in angle_terms):
        errors.append("缺少镜头角度")
    if not any(k in text.lower() for k in move_terms):
        errors.append("缺少运镜")

    banned = ["4k", "8k", "ultra detailed", "hyperdetailed",
              "beautiful", "stunning", "gorgeous"]
    for w in banned:
        if re.search(rf"\b{re.escape(w)}\b", text, re.I):
            errors.append(f"出现禁止词: {w}")

    return errors