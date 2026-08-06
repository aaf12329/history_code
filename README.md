# DeepSeek_port QQ 机器人版（v1.5-QQBot）

> v1.5 的平台特化分支：把对话助手搬上 QQ

![version](https://img.shields.io/badge/version-v1.5--qqbot-blue)
![platform](https://img.shields.io/badge/platform-QQ-12B7F5)
![status](https://img.shields.io/badge/状态-已归档-lightgrey)

## 📖 简介

在 v1.5 记忆架构之上做的平台特化：接入 QQ 机器人框架 **qg-botsdk**，
把"命令行循环"改造成"消息回调驱动"，让同一个记忆系统在 QQ 里继续工作。

## 📌 与 v1.5 的差异

| 项目 | v1.5 | QQBot 版 |
|------|------|----------|
| 输入 | 命令行 `input()` | QQ 消息回调 |
| 输出 | 终端流式打印 | 返回完整字符串，由框架回发 |
| 上下文 | 记忆库 + 输入拼接 | 相同（记忆作为前缀整体载入） |
| 启动 | 直接运行脚本 | `EngageQQBot.bat` 一键启动 |
| 新增 | — | `detect()` 开机自检记忆/prompt 齐全性 |

## 🚀 快速开始

```bash
pip install qg-botsdk        # 另需 v1.0 的基础依赖
# 配置机器人 bot_id / bot_secret（沙箱模式）
python ds_QQBot.py           # 或双击 EngageQQBot.bat
```

## 📦 配套文件

- `EngageQQBot.bat`：机器人一键启动脚本
- `ChatQQ.py`：最小连通性测试脚本（收到任何消息回复"收到"）
- 记忆与提示词文件与 v1.5 通用（Menorise/）

## ⚠️ 已知问题

- prompt 文件读取无错误校验（作者备注：那俩文件最好别乱动）
- 记忆全量前缀载入，高频群聊场景 token 消耗偏大
