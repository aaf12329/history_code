# DeepSeek_port v1.0（重构版）

> 首次系统性重构：从"能聊"到"有结构"

![version](https://img.shields.io/badge/version-v1.0-blue)
![status](https://img.shields.io/badge/状态-已归档-lightgrey)

## 📖 简介

对 v0.1 雏形完成第一次完整重构：单文件按职责拆分为清晰的函数结构，并把对话历史
机制升级为**累积式 Markdown 记忆库**——AI 不再只是"翻聊天记录"，而是每轮都带着
全部记忆回答。

## 🏗️ 架构

| 函数 | 职责 |
|------|------|
| `Use()` | API 调用与参数控制（流式输出 + 思考模式 + high reasoning） |
| `U_Input()` | 用户输入与文件上传解析 |
| `Memory()` | 记忆库读写（Memory.md 追加 / 全量读取） |
| `memoryfile_detect()` | 启动自检，记忆文件缺失自动创建 |
| `control()` | 中控：输入 → 带记忆调用 → 回复写回记忆 |

## ✨ 功能特性

- **累积式记忆**：所有对话（带时间戳）追加进 `Memory.md`，每轮整份读出作为
  system 提示词——AI 始终"带着全部记忆"回答
- **三类文件上传**（`Code_Send:` 指令）：
  - 文本类：.txt .md .csv .py .html .xml .log .yaml .json
  - 二进制类：图片/音视频等，自动转 base64 附带发送
  - Office 文档：docx 抽取段落文本、xlsx 转表格数据
- 模型 deepseek-v4-flash，开启思考模式

## 🚀 快速开始

```bash
pip install openai openpyxl pandas python-docx python-dotenv
# .env 配置同 v0.1
python "ds(重构后1.0).py"
```

## 💬 使用说明

| 指令 | 作用 |
|------|------|
| 直接输入文字 | 对话（自动带时间戳并写入记忆） |
| `Code_Send:` | 上传本地文件（按提示输入路径） |
| `exit()` | 退出程序 |

## 📌 与 v0.1 的差异

- 历史机制由 json 整体读写改为 **Markdown 记忆库累积追加**
- 新增二进制 / Office 文件支持
- 代码函数化重构，退出指令统一为 `exit()`

## ⚠️ 已知问题

- 记忆直接当系统提示词使用，没有独立的人设 prompt（v1.5 引入双 prompt）
- 记忆无上限，长对话会持续膨胀（压缩机制将在 v1.5 引入）
