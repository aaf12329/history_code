# DeepSeek_port 1.5.x 收官版（8 月 24 日）

> 1.5 系列最后一版：检测函数规范化，旧记忆系统功成身退

![version](https://img.shields.io/badge/version-1.5.x_final-blue)
![status](https://img.shields.io/badge/状态-过渡快照-lightgrey)

## 📖 简介

1.5 系列的收官迭代：整理文件检测与记忆规模检测函数，并将服役一个月的
旧记忆系统 **Menorise 整体存档**，为 v2.0 的 Memories/ + Prompt/ 新架构腾位。

## ✨ 本版改动

- 自检与阈值检测函数规范化：
  `memory_existence_file_detect()` / `Memory_Scale_detect()` / `control()`
- Menorise 记忆系统（Memory_Library / Original_Memory、test_Memory 测试数据、
  20MB 记忆全量备份）整体移入 `废案及历史版本/`
- 记忆规模自动压缩逻辑保留，等待接入新架构

## 🧭 定位

此版本是项目从"**单文件 + Menorise 目录**"向"**目录化架构**"过渡的快照，
功能与 v1.5.1 基本一致，代码整洁度提升。
