# DeepSeek_port GUI 版

> 双端入口达成：tkinter 图形界面上线

![version](https://img.shields.io/badge/version-gui_v1-blueviolet)
![GUI](https://img.shields.io/badge/GUI-tkinter-green)

## 📖 简介

对话助手第一次有了窗口：tkinter 深色主题 GUI 上线，与命令行共用同一套
主程序逻辑与记忆系统。记忆压缩模块同步升级为正式版，隐私设置提示词加入
双 prompt 体系。

## ✨ 本版新增

- **`GUI.py` 图形界面**：600×700 深色主题窗口，ScrolledText 对话显示区 +
  底部输入框，`import ds` 直接复用主程序全部能力
- **`GUI_Engage.bat`**：双击进入图形界面
- **Compress_mudel.py 正式版**：
  `Compress_control()`（读记忆 → v4-pro 压缩 → 覆盖写回）+
  `Compress_mudel_link_test()` 连通性自测
- **`Prompt/Privacy_Setting.md`**：隐私设置提示词，与 System_Prompt 拼接生效

## 🖥️ 双端入口

| 入口 | 文件 | 启动方式 |
|------|------|----------|
| 命令行 | ds.py | 双击 `Engage.bat` |
| 图形界面 | GUI.py | 双击 `GUI_Engage.bat` |

## ⚠️ 已知问题

- GUI 与 CLI 共用记忆库，可交替使用，但无并发保护
- 窗口暂为简单轮询式，流式输出体验待优化
