# DeepSeek_port v1.5.1

> 工程化小步：虚拟环境 + 一键启动

![version](https://img.shields.io/badge/version-v1.5.1-blue)
![status](https://img.shields.io/badge/状态-已归档-lightgrey)

## 📖 简介

功能性改动不大的一版，重点在**可分发**：配套 venv_light 虚拟环境，依赖一次装好，
换机器、打包、分发免配置；启动脚本矩阵成型，双击即可运行。

## ✨ 本版改进

- 记忆库更名为 `Menorise/Original_Memory.md`（替代 Memory_Library.md）
- `venv_light/` 虚拟环境随项目走，实现"一次性打包、一键启动"
- 启动脚本矩阵：`Engage.bat`（CLI）、`Engage1.bat`、`GUI_Engage.bat`（GUI 预留）

## 🚀 快速开始

```bash
# 方式一：双击 Engage.bat
# 方式二：激活 venv_light 后运行
python "ds(1.5.1).py"
```

## 📌 与 v1.5 的差异

| 项目 | v1.5 | v1.5.1 |
|------|------|--------|
| 记忆库 | Menorise/Memory_Library.md | Menorise/Original_Memory.md |
| 运行环境 | 需手动配依赖 | venv_light 一键启动 |
| 启动方式 | python 直启 | Engage 脚本矩阵 |

## ⚠️ 已知问题（作者备注）

- "路径文件架构有点乱，在下一个版本会修复"
- 记忆与提示词仍集中在 Menorise/，与代码耦合较深
