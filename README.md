# DeepSeek_port v0.1

> 项目最早雏形：单文件命令行 DeepSeek 对话脚本

![version](https://img.shields.io/badge/version-v0.1-blue)
![status](https://img.shields.io/badge/状态-已归档-lightgrey)

## 📖 简介

一个约 200 行的单文件脚本，解决"能聊起来"的问题：通过 OpenAI SDK 兼容接口调用
DeepSeek（deepseek-v4-flash），在终端进行多轮对话，逐字流式输出，并把对话历史
持久化到本地，重启程序可以接着上次聊。

## ✨ 功能特性

- 命令行多轮对话，流式逐字输出
- 对话历史持久化至 `chat_history.json`，重启自动加载续聊（文件损坏时自动新建对话）
- `Code_Send:` 指令：输入后追加文件路径，即可把本地文本文件内容随消息发给 AI
- 每条消息自动附加当前时间，让 AI 感知时间语境
- 退出指令 `exit` / `quit` / `q` / `退出`，退出前自动保存历史

## ⚙️ 配置

参数集中在脚本头部 `CONFIG` 字典，可直接修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `model` | deepseek-v4-flash | 对话模型 |
| `system_prompt` | "你是我最好的助手和朋友……" | AI 人设 |
| `history_file` | chat_history.json | 历史存档路径 |
| `exit_commands` | exit/quit/q/退出 | 退出指令 |

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install openai python-dotenv

# 2. 项目根目录创建 .env，写入：
#    DEEPSEEK_API_KEY="sk-xxxxxxxx"

# 3. 启动
python "En(重构前port).py"
```

## 💬 使用说明

| 指令 | 作用 |
|------|------|
| 直接输入文字 | 与 AI 对话（自动带时间戳） |
| `Code_Send:` | 追加读取本地文本文件发送 |
| `exit` / `quit` / `q` / `退出` | 保存历史并退出 |

## ⚠️ 已知不足（下版改进方向）

- 文件上传仅支持纯文本，二进制与 Office 文档无法读取
- 历史即上下文，没有独立的记忆沉淀机制，聊得越久请求体越大
- 网络异常直接报错退出，无重试
