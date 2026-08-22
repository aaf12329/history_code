# DeepSeek_port —— v2.0 重构预研（base_deepseek）

> 为下一代大重构打底：把 API 调用抽成公共基础层

![version](https://img.shields.io/badge/阶段-重构预研-yellow)

## 📖 简介

1.5.x 系列功能持续叠加，主脚本已接近 250 行，记忆、输入、调用、压缩全部挤在
一个文件里。本阶段开始为 v2.0 大重构做预研：验证"**调用与业务分离**"的方向。

## 📦 本阶段内容

- `base_deepseek.py`：最小可用的 DeepSeek 调用基础层——
  deepseek-v4-pro、非流式、thinking enabled + high reasoning，
  作为后续所有版本共用的调用范式参考
- 主对话程序仍为 1.5.x 版本，行为不变

## 🎯 预研结论

SDK 参数组合验证通过。v2.0 将按此思路把"API 调用 / 输入解析 / 记忆读写 /
中控调度"拆成独立模块。
