# HiceSeek

面向 DeepSeek API 的命令行聊天工具，附带 anima / minimax 提示词后处理管道，以及一个只读会话浏览器。


# 一、简介

HiceSeek 是我（秦罅 - Hicehavvk）自用的 DeepSeek CLI，目标是把日常聊天、提示词后处理、历史会话查看整合到一个工具里。目前项目的完成度及成熟度较低，主要出于网上备份及旧版本回溯的需求在github上分享。


# 二、功能

## 1. 大模块

- **chat 模式**：通用聊天，内置鲸鱼娘角色，具有身份边界约束（技术问题如实回答）。
- **anima 模式**：把简短描述转成 anima-2.9B 的英文提示词，带加权、取景、光影校验。
- **minimax 模式**：协助拆解、评价、翻译 MiniMax-H3 视频提示词。
- **view 模式**：只读浏览历史会话，支持按模式过滤、查看思考内容。


## 2. 小模块

- 流式输出，思考内容与正文分色显示
- 深度思考开关、reasoning effort 切换
- 多会话管理：新建、加载、重命名、撤销、修剪、导出
- 会话持久化到 JSONL，坏文件不影响其他会话
- token 日志与成本估算
- anima / minimax 提示词校验（密度、加权、取景、光影、禁止词）
- view 模式只读浏览历史会话
- 启动参数与批处理入口


# 三、安装、依赖、配置

项目运行需要 Python 3.10+。

```bash
pip install -r requirements.txt
```

项目依赖 DeepSeek 官方 API 开放平台的付费key，请在完成相关申请及充值后，备份好文件“key.env.example”，并把“.example”后缀去掉，将key填入文件内的“DEEPSEEK_API_KEY=”后面。

“key.env.example”硬编码并调用了项目发布时的Deepseek 官方 API token价格、用于统计消费情况，如果看重预算控制，请在部署项目后按当下的实际价格调整。


# 四、使用说明

## 1. 模式

| 模式 | 启动方式 | 用途 |
|---|---|---|
| chat | `python run.py` | 通用聊天 |
| anima | `python run.py --mode anima` | anima 提示词后处理 |
| minimax | `python run.py --mode minimax` | MiniMax 提示词后处理 |
| view | `python run.py --mode view` | 浏览历史会话 |

Windows 下也可以直接双击对应的 .bat：chat.bat / anima.bat / minimax.bat / view.bat 进入以上模式。


## 2. 常用命令

项目启动/运行时可以通过“/help”查询命令。

非 view 模式：

| 命令 | 说明 |
|---|---|
| `/chat` `/anima` `/minimax` `/view` | 切换模式 |
| `/new` `/sessions` `/load <ID>` `/title <标题>` | 会话管理 |
| `/undo` `/trim <N>` `/save` `/cost` | 会话操作 |
| `/thinking on\|off` `/effort low\|high\|max` | 运行时参数 |
| `/help` `/exit` | 帮助与退出 |
| `/clear` | 清除上下文，管道模式专用[1] |

[1:对话时建议使用“/new”等命令进行会话管理。]

view 模式：

| 命令 | 说明 |
|---|---|
| `/list` `/list --mode <m>` | 列出会话 |
| `/latest` `/id <ID>` | 查看会话 |
| `/reasoning` | 切换思考展开 |

再次提醒：项目启动时可以通过“/help”查询完整命令。


# 五、其他

## 1.  项目主结构

```text
HiceSeek/
├── deepseek_tool/
│   ├── core/         # 配置、API 客户端、会话、token 日志、UI
│   ├── chat/         # 主循环与命令处理（含 view 模式）
│   ├── pipeline/     # anima / minimax 提示词管道
│   └── sessions/     # 对话记录，项目部署并开始使用后自动生成
├── document/         # 设计档案与迭代报告
├── run.py            # 启动入口
├── chat.bat          # 进入 chat 模式
├── anima.bat         # 进入 anima 管道
├── minimax.bat       # 进入 minimax 管道
├── view.bat          # 进入 view 模式
├── thinking.bat      # 启动时开启深度思考
├── key.env.example   # 配置模板
├── requirements.tx  # 依赖
├── token_log.jsonl  # token本地使用记录，项目部署并开始使用后自动生成
└── readme.md
```

## 2. 设计文档

- `document/20260924设计档案.md`：早期的立项文档
- `document/20260925迭代报告.md`：内部迭代记录
- `document/20260924其他对话节选.md`：嘉豪个人纪录

以上文档均在项目分享到 GitHub 前整理。


## 3. 许可

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)。

这意味着：你可以自由使用、修改、分发本项目，但如果你修改后通过网络提供服务，必须向用户提供修改后的源代码。

完整许可文本见LICENSE。


## 4. 免责声明

本项目代码通过 DeepSeek 网页端对话构建（甚至该 readme 文档也是以 DeepSeek 生成的案例删改的），本人没有开发/编程能力，目前本人自用时没有明显bug，但出于显而易见的能力边界问题、恕不保证代码稳定性。

anima / minimax 管道目前的 system prompt 涉及 NSFW 提示词后处理，相关内容及校验规则仅用于个人学习研究，不用于扰乱公序良俗或违规违法的活动。