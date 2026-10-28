# history_code · 历史代码归档

按项目保存学习代码、实验和阶段快照。每个项目放在自己的文件夹中，原有源码、说明及资源保留；归档不代表项目已重新运行或具备生产可用性。

## 项目入口

| 独立目录 | 内容 | 阅读入口 |
| --- | --- | --- |
| `DeepSeek_port/` | 原仓库中的 DeepSeek 桌面对话、记忆压缩、GUI、SQL 与 QQ 机器人实验，包含早期废案 | [原项目说明](DeepSeek_port/README.md) |
| `demo_django1/` | Django 网站与图片、视频、摄像头目标检测旧项目 | [归档说明](demo_django1/README.md) |
| `industry-evidence-platform/` | 产业信息研究平台：采集、证据处理、建模、网页与 CLI，含此前归并的设计和研究资料 | [原项目说明](industry-evidence-platform/README.md) |
| `Scratch_lesson/` | Scratch 画笔伪 3D 光线投射工程、原理讲解和配套图片 | [原项目说明](Scratch_lesson/README.md) |

```text
history_code/
├── README.md
├── AGENTS.md
├── 归并记录_20261028.md
├── 归并清单_20261028.json
├── DeepSeek_port/
├── demo_django1/
├── industry-evidence-platform/
└── Scratch_lesson/
```

## 使用方式

先进入具体项目文件夹，再查看它自己的 README。不同项目的依赖、入口和历史环境各自独立，不在归档根目录建立一套混用环境。

例如，旧 DeepSeek 项目的当前工作目录应为 `DeepSeek_port/`；Django 项目的 `manage.py` 位于 `demo_django1/`。这只是目录定位说明，本次没有启动程序、安装依赖、连接数据库或调用模型服务。

旧 README 中的“当前版本”“持续开发”和当时的机器路径，是对应快照的历史描述；当前归档状态以本页和[归并记录](归并记录_20261028.md)为准。

## 历史与维护

- 本仓库原有提交历史保留。旧 DeepSeek 文件从根目录移动到 `DeepSeek_port/`，没有改写其内容。
- `4385a5f` 在 2026-10-03 收录了 `demo_django1.zip`，当时没有同步 README；本次补记，并纳入本地已有的解压目录。原压缩包仍可通过该提交追溯。
- 产业研究平台来自 [industry-evidence-platform](https://github.com/aaf12329/industry-evidence-platform) 的 `be3397c`，Scratch 项目来自 [Scratch_lesson](https://github.com/aaf12329/Scratch_lesson) 的 `7d99e7d`。使用不压缩历史的 Git subtree 导入，来源提交仍在本仓库历史中，不是嵌套仓库或子模块。
- 本机两个来源桌面目录保留；归档目录内的版本独立维护，修改其中一份不会自动同步另一份。源文件核对结果见[归并清单](归并清单_20261028.json)。
- 新归档按项目增加独立目录，同步本表和来源记录；不要把不同项目的源码平铺混在一起。
- `.env`、虚拟环境、依赖缓存、IDE 配置和 Python 字节码不作为新增归档内容。已有历史资源继续保留，不在本次整理中擅自清理。
- 本轮只做目录整理与文件完整性核验，没有重新运行任何项目，旧测试记录不等于本轮验收。

*整理日期：2026-10-28。*
