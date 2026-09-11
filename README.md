# DeepSeek_port v2.0

> 新一代架构：记忆与提示词分家，历史结构化，全链路自检

![version](https://img.shields.io/badge/version-v2.0-blue)
![status](https://img.shields.io/badge/状态-当前版本-brightgreen)

## 📖 简介

按 8 月预研的结论完成大重构：记忆（Memories/）与提示词（Prompt/）目录分离，
对话历史改为 JSON 结构化存储，启动即执行文件完整性自检，SQL 落库接入主流程。

## 🏗️ 架构

| 模块 | 职责 |
|------|------|
| `ds.py` | 主程序：`file_detect()` 自检 → `U_Input()` 输入/上传 → `Core()` 对话 → `control()` 中控 |
| `Compress_mudel.py` | 记忆压缩（≥1.5MB 触发，v4-pro 提取要点后覆盖写回） |
| `Py_SQL.py` | `SQL_Instruction()` 对话记录落库 |
| `GUI.py` | tkinter 图形界面（复用同一套逻辑） |
| `Prompt/` | System_Prompt.md + Privacy_Setting.md 双提示词 |
| `Memories/` | AI_Memories.md 长期记忆 + Chat_History.json 结构化流水 |

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
        └─ 是 ──► Compress_control()：v4-pro 提取要点 → 覆盖写回
```

## 💬 输入与文件能力

| 指令 | 作用 |
|------|------|
| 直接输入文字 | 对话（自动携带全部记忆与时间戳） |
| `Code_Send:` | 上传文件：文本类（多编码尝试）/ 二进制类（base64）/ Office（docx 抽文本、xlsx 转表格） |
| `exit()` | 退出程序 |

限额：单文件 ≤ 5MB，单次输入总量 ≤ 1.5MB（超出以 Send_oversize 拦截）。

## 🚀 快速开始

```bash
pip install openai openpyxl pandas python-docx python-dotenv mysql-connector-python
# .env 配置 DEEPSEEK_API_KEY 后：
python ds.py      # 命令行
python GUI.py     # 图形界面
```

## 📌 与 1.5.x 的差异

- 记忆（Memories/）与提示词（Prompt/）目录分离，Menorise 退役
- 对话历史改为 JSON 结构化存储（role / content / 时间）
- 新增 `file_detect()` 启动自检，四类文件缺失即告警补建
- GUI 与 CLI 复用同一套主程序逻辑

## ⚠️ 已知问题

- `Memory_Scale_detect()` 中存在临时路径补丁（代码内已标注"后期修复"）
