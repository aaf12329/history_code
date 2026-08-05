# DeepSeek_port v1.5

> 记忆系统成型：记忆目录化 + 双提示词 + 自动压缩

![version](https://img.shields.io/badge/version-v1.5-blue)
![status](https://img.shields.io/badge/状态-已归档-lightgrey)

## 📖 简介

记忆机制全面升级：记忆与提示词从单文件拆分为独立的 **Menorise/** 目录；
新增手搓的 **Compress_mudel 记忆压缩模块**，记忆库超限自动"瘦身"；
系统提示词与个人私设分离，双 prompt 共同生效。脚本同时改用相对路径寻址，
不再依赖启动时的工作目录。

## 🧠 记忆系统工作原理

```
用户输入+时间戳 ──► 追加至 Menorise/Memory_Library.md
                            │
每轮对话：整份记忆库 + 用户输入 拼接为 user 消息
          System_prompt.md + Personal_setting.md 拼接为 system 消息
                            │
                            ▼
                    DeepSeek（流式 + 思考）
                            │
每轮结束：AI 回复写回记忆库
          Memory_Library.md ≥ 2.5MB ? ──► Compress_mudel.control() 自动压缩
```

## 🏗️ 架构

| 函数 | 职责 |
|------|------|
| `prompt_read()` | 读取提示词文件 |
| `Memory()` | 指定路径的记忆读写 |
| `Use()` | API 调用（流式 + 思考模式） |
| `U_Input()` | 输入与三类文件上传 |
| `memoryfile_detect()` | 记忆/提示词文件自检补建 |
| `Memory_detect()` | 记忆库体积检测，≥2.5MB 触发压缩 |
| `control()` | 中控 |

## ✨ 功能特性

- **Menorise 记忆目录**：Memory_Library.md（记忆库）、System_prompt.md（系统提示词）、
  Personal_setting.md（个人私设）
- **双 prompt**：人设与私设分离维护，拼接后生效
- **自动记忆压缩**：Compress_mudel 模块在记忆库超限时启动
- 路径以脚本所在位置锚定，任意目录启动均可

## 🚀 快速开始

```bash
pip install openai openpyxl pandas python-docx python-dotenv
python "ds(1.5版本).py"
```

## 🏗️ 项目结构

```
DeepSeek_port/
├── ds(1.5版本).py        # 主程序
├── Compress_mudel.py     # 记忆压缩模块
└── Menorise/
    ├── Memory_Library.md     # 记忆库
    ├── System_prompt.md      # 系统提示词
    └── Personal_setting.md   # 个人私设
```

## 📌 与 v1.0 的差异

- 记忆/prompt 从单文件 Memory.md 拆分为 Menorise/ 三文件
- 新增双 prompt 与自动记忆压缩
- 路径全部改为脚本位置锚定

## ⚠️ 已知问题

- 压缩阈值 2.5MB，触发时机偏晚
- 仍是命令行交互，图形界面排期中
