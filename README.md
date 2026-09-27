# DeepSeek_port

> 基于 DeepSeek API 的桌面级 AI 对话助手 —— 带长期记忆与自动记忆压缩，支持命令行 / 图形界面双入口，并探索 SQL 记忆存储与 QQ 机器人接入。

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![DeepSeek API](https://img.shields.io/badge/LLM-DeepSeek_API-4D6BFE)
![GUI](https://img.shields.io/badge/GUI-tkinter-green)
![Status](https://img.shields.io/badge/状态-持续开发中-orange)

---

## 📖 项目简介

DeepSeek_port 是一个从零开始迭代的个人 AI 对话助手项目。它解决的核心问题是：**让 DeepSeek 拥有可长期累积、可自动"瘦身"的记忆**。

对话内容以纯文本形式持续写入本地记忆库，整份记忆作为上下文参与每一轮对话；当记忆库体积超过阈值时，自动调用模型将记忆压缩提取要点，实现"越用越聪明"而不是"越用越贵"。项目自 2026 年 7 月的雏形脚本起步，经历了 8 个版本的演进（见 [版本历史](#-版本历史)），旧版本全部存档于 `废案及历史版本/` 并录入 git 历史。

## ✨ 功能特性

**对话核心**
- 基于 OpenAI SDK 调用 DeepSeek API，流式输出，支持思考模式
- 双提示词体系：`System_Prompt.md`（系统提示词）+ `Privacy_Setting.md`（隐私设置）拼接生效
- 启动即执行文件完整性自检，缺失的记忆/提示词文件自动补建

**长期记忆系统**
- `AI_Memories.md` 累积式记忆库，每轮对话的用户输入与 AI 回复自动写入
- `Chat_History.json` 结构化对话流水（user / assistant 分条记录）
- 记忆库 ≥ 1.5MB 自动触发压缩：调用 `deepseek-v4-pro` 提取要点后覆盖写回

**文件能力（`Code_Send:` 指令）**
- 文本类文件：多编码自动尝试（utf-8 / gbk / gb2312 / latin-1）
- 二进制文件：自动转 base64 附带发送
- Office 文档：docx 抽取段落文本、xlsx 转表格数据
- 双重保险：单文件 ≤ 5MB，单次输入总量 ≤ 1.5MB，超出自动拦截

**多端入口**
- 命令行版：`ds.py`
- 图形界面版：`GUI.py`（tkinter 深色主题窗口）

**实验方向**
- SQL 记忆存储（MySQL）：每轮对话同步落库
- QQ 机器人接入：已有特化版本存档

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 一个 DeepSeek API Key（[platform.deepseek.com](https://platform.deepseek.com) 申请）

### 安装步骤

```bash
# 1. 获取项目
git clone <仓库地址>
cd DeepSeek_port

# 2. （可选）创建虚拟环境
python -m venv venv
venv\Scripts\activate        # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key：在项目根目录创建 .env 文件，写入一行：
#    DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 启动

| 方式 | 操作 |
|------|------|
| 命令行 | 双击 `Engage.bat`，或 `python ds.py` |
| 图形界面 | 双击 `GUI_Engage.bat`，或 `python GUI.py` |

## 💬 使用说明

### 命令行指令

| 指令 | 作用 |
|------|------|
| 直接输入文字 | 与 AI 对话（自动携带全部记忆与时间戳） |
| `Code_Send:` | 进入文件上传流程，按提示输入文件路径 |
| `exit()` | 正常退出程序 |

### 支持上传的文件类型

| 类型 | 扩展名 | 处理方式 |
|------|--------|----------|
| 文本 | .txt .md .csv .py .html .xml .log .yaml .json | 直接读取（多编码尝试） |
| 二进制 | .jpg .png .gif .mp4 .mp3 .pdf .zip .exe | 转 base64 编码 |
| Office | .docx .xlsx | 抽取文本 / 转表格字符串 |

## 🧠 记忆系统工作原理

```
用户输入 ──► 记忆库(AI_Memories.md) + 用户输入 ──► 双提示词(System+Privacy)
                                                        │
        ┌───────────────────────────────────────────────┘
        ▼
   DeepSeek API（deepseek-v4-flash，流式输出）
        │
        ▼
   AI 回复 ──┬──► AI_Memories.md   （长期记忆，累积写入）
             ├──► Chat_History.json（结构化对话流水）
             └──► SQL 数据库       （实验性落库）

   每轮结束检测：AI_Memories.md ≥ 1.5MB ?
        └─ 是 ──► Compress_control()：deepseek-v4-pro 提取要点 → 覆盖写回
```

## 🏗️ 项目结构

```
DeepSeek_port/
├── ds.py                    # 主程序：文件自检 / 记忆读写 / 输入逻辑 / 核心对话 / 中控
├── GUI.py                   # tkinter 图形界面（深色主题）
├── Compress_mudel.py        # 记忆压缩模块（v4-pro 提取要点，覆盖写回）
├── Model_SQL.py             # DeepSeek 调用封装（SQL 实验用）
├── Py_SQL.py                # SQL 记忆指令接口（SQL_Instruction）
├── SQL_Link.py              # MySQL 连接（mysql-connector）
├── Crawler_test.py          # 爬虫测试脚本
├── Data_test.py             # 数据处理测试脚本
├── Engage.bat               # 命令行版启动脚本
├── GUI_Engage.bat           # GUI 版启动脚本
├── requirements.txt         # Python 依赖清单
├── .env                     # DEEPSEEK_API_KEY（已被 gitignore，不入库）
│
├── Prompt/                  # 提示词目录
│   ├── System_Prompt.md     #   系统提示词
│   └── Privacy_Setting.md   #   隐私设置提示词（与系统提示词拼接生效）
│
├── Memories/                # 记忆数据目录
│   ├── AI_Memories.md       #   长期记忆库（累积写入，超限自动压缩）
│   ├── Chat_History.json    #   结构化对话记录
│   └── history/             #   旧版记忆快照存档
│
└── 废案及历史版本/            # 全部旧版本存档（git 历史中均有对应提交）
    ├── En(重构前port).py     #   v0.1 最早雏形
    ├── ds(重构后1.0).py      #   v1.0
    ├── ds(1.5版本).py        #   v1.5
    ├── ds(1.5.1).py          #   v1.5.1
    ├── ds_QQBot.py           #   QQ 机器人特化版
    └── Menorise/             #   旧记忆系统数据（Memory_Library / test_Memory）
```

## 📜 版本历史

所有旧版本均可通过 git 标签或 `废案及历史版本/` 目录查阅，每个里程碑提交附有该版本专属的 README。

| 版本 | 日期 | 主要变化 | 存档位置 |
|------|------|----------|----------|
| v0.1 | 2026-07-27 | 最早雏形：单文件命令行对话，json 历史续聊 | `En(重构前port).py` |
| v1.0 | 2026-08-05 | 函数化重构；Memory.md 累积记忆；三类文件上传 | `ds(重构后1.0).py` |
| v1.5 | 2026-08-06 | Menorise 记忆目录；双 prompt；记忆压缩上线 | `ds(1.5版本).py` |
| v1.5-qqbot | 2026-08-06 | QQ 机器人特化版（qg-botsdk） | `ds_QQBot.py` |
| v1.5.1 | 2026-08-14 | 记忆库更名；venv_light 虚拟环境一键启动 | `ds(1.5.1).py` |
| GUI 版 | 2026-08-27 | tkinter 图形界面；压缩模块正式版 | `GUI.py` |
| SQL 实验 | 2026-08-28 | MySQL 记忆存储探索启动 | `Model_SQL.py` 等 |
| **v2.0（当前）** | 2026-09-11 | Memories/Prompt 目录架构；JSON 结构化历史；启动自检 | `ds.py` |

## 🗺️ 路线图

- [ ] 修复记忆路径的临时补丁，统一路径管理（代码内已标注）
- [ ] SQL 记忆存储由实验转正，支持按时间/相关度检索
- [ ] 记忆检索优化：按相关度取段替代全量载入，降低 token 消耗
- [ ] 重启 QQ 机器人接入（基于存档的 v1.5-qqbot）

## ❓ 常见问题

**提示未找到 DEEPSEEK_API_KEY**
项目根目录缺少 `.env` 文件或未写入 Key，参照 [快速开始](#-快速开始) 第 4 步配置。

**提示"调用错误，请检查网络"**
检查网络连接与 API Key 是否有效；Key 欠费或错误时同样会触发此提示。

**输入被拦截（Send_oversize）**
单次输入总量超过 1.5MB 或单个文件超过 5MB，请拆分内容后再发送。

**GUI 启动后无内容**
请在项目根目录运行 `python GUI.py`，程序按相对路径定位记忆与提示词文件。

## 📚 参考

- [hello-agents](https://github.com/datawhalechina/hello-agents) —— 记忆压缩思路的参考来源

## 📄 许可

个人学习项目，仅供学习交流使用。
