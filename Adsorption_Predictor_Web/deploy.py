# -*- coding: utf-8 -*-
"""一键部署脚本：在项目根目录创建虚拟环境并安装依赖。

主题
    环境部署。让拿到本项目的人（或换一台机器）不必手动敲 conda / pip 命令，
    双击 deploy.bat 即可得到一套可直接运行 start.bat 的独立环境。

任务
    读 deploy.json → 用系统里的 Python 创建 .venv → 安装依赖 → 验证可导入。
    全程只用标准库，因此在本项目依赖尚未安装时就能运行。

结构
    ① 配置读取   读 deploy.json，套用命令行覆盖
    ② 环境准备   定位基础解释器、创建或复用虚拟环境
    ③ 依赖安装   按锁定版本 / requirements / 回退列表三选一安装
    ④ 验证       逐个 import 校验，并确认本项目后端模块可导入
    ⑤ 入口 main  串起以上步骤，汇总结果与后续操作

调用树
    main
    ├── load_config            （读 deploy.json + 命令行覆盖）
    ├── select_base_python     （搜索并挑选与锁定版本兼容的解释器）
    ├── ensure_venv            （创建或复用 .venv）
    ├── install_dependencies   （pip 安装；锁定版本→不锁版本→换源 的降级链）
    │   └── run_command        （执行子命令并实时透传输出）
    ├── verify_imports         （逐个 import 校验）
    ├── check_backend          （验证本项目后端模块可导入）
    └── report                 （输出后续操作指引）

数据流
    deploy.json → 配置字典
        → 基础解释器 → .venv/Scripts/python.exe
        → pip install（锁定版本 / -r requirements.txt / 包名列表）
        → import 验证 → 部署完成，可运行 start.bat

依赖
    仅标准库（subprocess / venv / json / argparse）。
    需要能联网访问 pip 源；需要磁盘约 900 MB 存放虚拟环境。

用法
    python deploy.py                  # 按 deploy.json 部署
    python deploy.py --dry-run        # 只打印将要执行的命令，不做改动
    python deploy.py --no-pin         # 忽略锁定版本，按 requirements 装
    python deploy.py --recreate       # 已存在环境也删除重建
    python deploy.py --venv-dir .venv-test
    python deploy.py --index-url https://pypi.org/simple
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

# ============================================================================
# ① 配置读取
# ============================================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = "deploy.json"
OFFICIAL_INDEX = "https://pypi.org/simple"

# 低于此版本的解释器无法运行本项目（scikit-learn 1.7 与 pandas 2.x 的要求）
MIN_PYTHON = (3, 9)

# 锁定版本是在这一档 Python 上验证过的；更新的版本未必有对应的预编译 wheel，
# 此时部署脚本会自动降级为"不锁版本"，本常量只用于提前给出提示。
PINNED_TESTED_UPTO = (3, 12)


class DeployError(RuntimeError):
    """部署过程中的可预期错误；消息面向使用者，直接打印。"""


def load_config(path, overrides):
    """读取 deploy.json 并套用命令行覆盖，返回规整后的配置字典。"""
    if not os.path.exists(path):
        raise DeployError("找不到配置文件：%s" % path)

    with open(path, "r", encoding="utf-8-sig") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise DeployError("配置文件不是合法 JSON（%s）：%s" % (path, exc)) from exc

    config = {
        "venvDir": raw.get("venvDir", ".venv"),
        "pythonExe": raw.get("pythonExe", ""),
        "requirementsFile": raw.get("requirementsFile", "requirements.txt"),
        "pinnedVersions": raw.get("pinnedVersions") or {},
        "fallbackPackages": raw.get("fallbackPackages") or [],
        "pipIndexUrl": raw.get("pipIndexUrl", ""),
        "pipExtraIndexUrl": raw.get("pipExtraIndexUrl", ""),
        "upgradePip": bool(raw.get("upgradePip", True)),
        "verifyImports": raw.get("verifyImports") or [],
        "checkBackend": bool(raw.get("checkBackend", True)),
        "venvArgs": raw.get("venvArgs") or [],
    }

    # 命令行覆盖优先
    if overrides.get("venv_dir"):
        config["venvDir"] = overrides["venv_dir"]
    if overrides.get("index_url") is not None:
        config["pipIndexUrl"] = overrides["index_url"]
    if overrides.get("python_exe"):
        config["pythonExe"] = overrides["python_exe"]

    # 相对路径一律相对项目根目录解析
    if not os.path.isabs(config["venvDir"]):
        config["venvDir"] = os.path.join(PROJECT_ROOT, config["venvDir"])
    return config


# ============================================================================
# ② 环境准备
# ============================================================================

def venv_python(config):
    """返回虚拟环境内解释器的路径（Windows 与 POSIX 目录不同）。"""
    if os.name == "nt":
        return os.path.join(config["venvDir"], "Scripts", "python.exe")
    return os.path.join(config["venvDir"], "bin", "python")


def probe_python(executable):
    """探测一个解释器的版本，返回版本文本；不可用则返回 None。"""
    candidate = shutil.which(executable) or executable
    if not os.path.exists(candidate):
        return None
    try:
        result = subprocess.run(
            [candidate, "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text or any(ch not in "0123456789." for ch in text):
        return None
    return text


def _parse_py_launcher():
    """解析 `py -0p` 的输出，得到本机所有已注册 Python 的路径与版本。

    输出形如：
         -V:3.14 *        C:\\python\\python.exe
         -V:3.10          C:\\python_310\\python.exe
    """
    found = []
    try:
        result = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return found
    if result.returncode != 0:
        return found
    for line in result.stdout.splitlines():
        match = re.match(r"\s*-V:(\d+\.\d+)\s+\*?\s*(.+?)\s*$", line)
        if match:
            found.append((match.group(2), match.group(1)))
    return found


def discover_candidates():
    """按优先级列出候选解释器，返回 [(标签, 可执行文件)]。

    优先级依据本项目实际情况：
      1. 运行本脚本的解释器、环境变量 PYTHON —— 用户意图最明确
      2. conda 环境 tf —— 本项目一直在这个环境上开发与验证
      3. py 启动器注册的其它版本，从高到低 —— 便于凑到兼容的版本区间
      4. PATH 上的 python —— 最后的兜底
    """
    candidates = []

    def add(label, executable):
        if executable and all(executable != item[1] for item in candidates):
            candidates.append((label, executable))

    add("运行本脚本的解释器", sys.executable)
    add("环境变量 PYTHON", os.environ.get("PYTHON"))

    # 只列与本项目相关且可移植的候选：conda 环境 tf 是本项目一直使用的开发环境。
    # 不写死其它机器的绝对路径——需要时用 deploy.json 的 pythonExe 指定。
    home = os.path.expanduser("~")
    for path in (os.path.join(home, ".conda", "envs", "tf", "python.exe"),
                 os.path.join(home, ".conda", "envs", "tf", "bin", "python")):
        if os.path.exists(path):
            add("conda 环境 tf", path)

    for path, version in sorted(_parse_py_launcher(),
                                key=lambda item: tuple(int(x) for x in item[1].split(".")),
                                reverse=True):
        add("py 启动器注册的 Python %s" % version, path)

    add("PATH 上的 python", shutil.which("python"))
    return candidates


def select_base_python(config):
    """挑选用于创建虚拟环境的解释器。

    选择规则（锁定版本能复现是首要目标）：
      · 显式配置了 pythonExe 就用它，只看版本下限；
      · 否则在候选里优先找"版本 <= 锁定版本验证上限"的解释器，
        因为更新的 Python 未必有锁定版本的预编译 wheel；
      · 都不满足时退回第一个版本达标的候选，并标记为降级，由调用方提示。
    返回 (路径, 版本文本, 来源说明, 是否降级)
    """
    explicit = config["pythonExe"]
    if explicit:
        text = probe_python(explicit)
        if text is None:
            raise DeployError("deploy.json 指定的 pythonExe 不可用：%s" % explicit)
        if tuple(int(x) for x in text.split(".")[:2]) < MIN_PYTHON:
            raise DeployError("pythonExe 版本过低：%s，本项目需要 %d.%d 及以上。"
                              % (text, MIN_PYTHON[0], MIN_PYTHON[1]))
        return shutil.which(explicit) or explicit, text, "deploy.json 指定", False

    use_pins = bool(config["pinnedVersions"])
    fallback = None
    probed = []

    for label, executable in discover_candidates():
        text = probe_python(executable)
        if text is None:
            continue
        version = tuple(int(x) for x in text.split(".")[:2])
        if version < MIN_PYTHON:
            probed.append((label, text, "版本过低"))
            continue
        if not use_pins or version <= PINNED_TESTED_UPTO:
            return executable, text, label, False
        probed.append((label, text, "高于锁定版本验证上限"))
        if fallback is None:
            fallback = (executable, text, label)

    if fallback is not None:
        return fallback[0], fallback[1], fallback[2], True

    detail = "\n".join("    %s -> Python %s（%s）" % item for item in probed) \
        or "    未发现任何 Python 解释器"
    raise DeployError(
        "没有找到版本合适的 Python 解释器（需要 %d.%d 及以上）。已检查：\n%s\n"
        "  请安装 Python 3.10 ~ 3.12，或在 deploy.json 的 pythonExe 里"
        "填写本机 python.exe 的完整路径。" % (MIN_PYTHON[0], MIN_PYTHON[1], detail))


def ensure_venv(base_python, config, recreate, dry_run):
    """创建虚拟环境；已存在且完好则复用。"""
    target = venv_python(config)

    if os.path.exists(config["venvDir"]) and not recreate:
        if os.path.exists(target):
            print("  已存在虚拟环境，复用：%s" % config["venvDir"])
            return False
        print("  目录 %s 已存在但不是有效环境，将重建。" % config["venvDir"])
        recreate = True

    if recreate and os.path.exists(config["venvDir"]):
        if dry_run:
            print("  [dry-run] 将删除 %s" % config["venvDir"])
        else:
            print("  删除旧的虚拟环境：%s" % config["venvDir"])
            shutil.rmtree(config["venvDir"], ignore_errors=True)

    command = [base_python, "-m", "venv", config["venvDir"]] + list(config["venvArgs"])
    run_command(command, dry_run=dry_run, what="创建虚拟环境")

    if not dry_run and not os.path.exists(target):
        raise DeployError("虚拟环境创建后仍找不到解释器：%s" % target)
    return True


# ============================================================================
# ③ 依赖安装
# ============================================================================

def run_command(command, dry_run=False, what="", cwd=None, quiet=False):
    """执行命令并实时透传输出（不捕获，便于看到 pip 进度）。"""
    printable = " ".join(('"%s"' % c) if " " in str(c) else str(c) for c in command)
    if what:
        print("  $ %s" % printable)
    if dry_run:
        print("  [dry-run] 跳过执行")
        return 0
    result = subprocess.run(command, cwd=cwd or PROJECT_ROOT)
    return result.returncode


def build_install_strategies(config, pin_override):
    """给出按优先级排列的安装策略，每一步都说明"为什么换下一种"。

    之所以做成降级链：锁定版本能复现验证过的组合，但精确版本未必有新版
    Python 的预编译 wheel（例如用 Python 3.12 以上时 numpy 2.2.6 可能装不上）。
    此时退而安装较新的可用版本，比直接失败更有用，但要如实告知用户。
    """
    requirements = os.path.join(PROJECT_ROOT, config["requirementsFile"])
    if os.path.exists(requirements):
        unpinned = ["-r", requirements]
        unpinned_label = "按 %s 安装（不锁版本）" % config["requirementsFile"]
    elif config["fallbackPackages"]:
        unpinned = list(config["fallbackPackages"])
        unpinned_label = "按 deploy.json 的回退包列表安装（不锁版本）"
    else:
        unpinned, unpinned_label = None, None

    use_pins = bool(config["pinnedVersions"]) and pin_override is not False
    strategies = []

    if use_pins:
        pinned = ["%s==%s" % (name, version)
                  for name, version in config["pinnedVersions"].items()]
        strategies.append((pinned, config["pipIndexUrl"],
                           "使用 deploy.json 锁定版本（可复现验证过的组合）"))
    if unpinned is not None:
        strategies.append((unpinned, config["pipIndexUrl"], unpinned_label))
    if config["pipIndexUrl"] and config["pipIndexUrl"].rstrip("/") != OFFICIAL_INDEX:
        args = unpinned if unpinned is not None else strategies[-1][0]
        label = unpinned_label if unpinned is not None else "改用官方源安装（不锁版本）"
        strategies.append((args, OFFICIAL_INDEX, label))

    if not strategies:
        raise DeployError("没有可安装的内容：pinnedVersions 为空、%s 不存在、"
                          "fallbackPackages 也为空。" % config["requirementsFile"])
    return strategies


def pip_command(config, index_url, extra_args):
    """拼出一条 pip 安装命令，附带指定的源。"""
    command = [venv_python(config), "-m", "pip", "install",
               "--disable-pip-version-check"]
    if index_url:
        command += ["--index-url", index_url]
    if config["pipExtraIndexUrl"]:
        command += ["--extra-index-url", config["pipExtraIndexUrl"]]
    return command + list(extra_args)


def install_dependencies(config, dry_run, pin_override=None):
    """按降级链依次尝试安装，遇到可行的第一种即停，并如实报告用了哪一种。"""
    if config["upgradePip"]:
        run_command(pip_command(config, config["pipIndexUrl"], ["--upgrade", "pip"]),
                    dry_run=dry_run, what="升级 pip")

    strategies = build_install_strategies(config, pin_override)
    last_code = None

    for index, (args, index_url, label) in enumerate(strategies):
        if index > 0:
            print("\n  ⚠ 上一种方式未成功，改用下一种：")
        print("  安装内容：%s" % label)
        if index_url and index_url != config["pipIndexUrl"]:
            print("  使用源　：%s" % index_url)

        code = run_command(pip_command(config, index_url, args),
                           dry_run=dry_run, what="安装依赖")
        if code == 0 or dry_run:
            if index > 0:
                print("  ✓ 已用「%s」完成安装。" % label)
                print("    注意：本次没能锁定版本，与第七节记录的版本组合可能有细微差异。")
            return
        last_code = code

    raise DeployError(
        "依赖安装失败（最后退出码 %s）。可依次排查：\n"
        "  1) 网络是否可访问 pip 源；可在 deploy.json 里换一个 pipIndexUrl\n"
        "  2) 磁盘剩余空间是否足够（虚拟环境约需 900 MB，"
        "其中 xgboost 与 catboost 各约 100 MB）\n"
        "  3) 若锁定版本装不上，多半是该 Python 版本没有对应 wheel：\n"
        "     把 deploy.json 的 pinnedVersions 置为 {} 再试，"
        "或改用 Python 3.10 ~ 3.12\n"
        "  4) 查看上方 pip 的报错原文，通常会指明是哪个包失败" % last_code)


# ============================================================================
# ④ 验证
# ============================================================================

def verify_imports(config, modules, dry_run):
    """在虚拟环境里逐个 import，任一失败即抛出。"""
    if not modules:
        return
    if dry_run:
        print("  [dry-run] 将验证导入：%s" % "、".join(modules))
        return

    script = ("import importlib, sys\n"
              "failed = []\n"
              "for name in %r:\n"
              "    try:\n"
              "        importlib.import_module(name)\n"
              "        print('    ok   ' + name)\n"
              "    except Exception as exc:\n"
              "        failed.append((name, exc))\n"
              "        print('    FAIL ' + name + ' -> ' + repr(exc))\n"
              "sys.exit(1 if failed else 0)\n" % (modules,))
    code = run_command([venv_python(config), "-c", script], what="验证依赖可导入")
    if code != 0:
        raise DeployError("有依赖无法导入，部署未完成。请查看上方 FAIL 行的具体报错。")


def check_backend(config, dry_run):
    """验证本项目后端模块可导入——能发现"依赖齐全但代码或模型缺失"的情况。"""
    if dry_run:
        print("  将导入 backend 各模块，并确认 models/ 齐备")
        return

    modules = ["backend.paths", "backend.model_registry", "backend.features",
               "backend.model_store", "backend.dataset_meta"]
    run_command([venv_python(config), "-c",
                 "import %s; print('    后端模块导入正常')" % ", ".join(modules)],
                what="导入 backend 模块")

    # 顺带确认模型文件在位，缺文件属于部署不完整
    missing = []
    model_dir = os.path.join(PROJECT_ROOT, "models")
    if not os.path.isdir(model_dir):
        missing.append("models/ 目录")
    else:
        for name in ["xgb_amount.joblib", "catboost_amount.joblib",
                     "xgb_capacity.joblib", "xgb_capacity_wgan.joblib",
                     "Dataset.csv"]:
            if not os.path.exists(os.path.join(model_dir, name)):
                missing.append("models/" + name)
    if missing:
        raise DeployError("模型文件缺失：%s\n"
                          "  请确认 models/ 目录随项目一起复制过来了。" % "、".join(missing))
    print("    模型文件齐备（models/）")


# ============================================================================
# ⑤ 入口 main
# ============================================================================

def human_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return "%.1f %s" % (num_bytes, unit)
        num_bytes /= 1024.0


def directory_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def report(config, base_python, version_text, source, created, elapsed, dry_run):
    print("\n" + "=" * 70)
    if dry_run:
        print("演练完成：以上是将会执行的步骤，未做任何改动。")
        print("去掉 --dry-run 即真正执行。")
        return 0

    target = venv_python(config)
    size = directory_size(config["venvDir"]) if os.path.isdir(config["venvDir"]) else 0

    print("部署完成，耗时 %.1f 秒" % elapsed)
    print("-" * 70)
    print("  基础解释器 : %s (Python %s)" % (base_python, version_text))
    print("  挑选来源   : %s" % source)
    print("  虚拟环境   : %s%s" % (config["venvDir"], "（本次新建）" if created else "（复用已有）"))
    print("  环境解释器 : %s" % target)
    print("  占用空间   : %s" % human_size(size))
    print("-" * 70)
    print("接下来：双击 start.bat 启动服务。")
    print("start.bat 会优先使用本环境的解释器，无需手动激活。")
    return 0


def main(argv=None):
    # 中文输出在 Windows 控制台需要显式指定编码，否则可能乱码
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="一键部署：创建虚拟环境并安装依赖")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="配置文件路径（默认 deploy.json）")
    parser.add_argument("--venv-dir", help="覆盖虚拟环境目录")
    parser.add_argument("--index-url", help="覆盖 pip 源；传空字符串则用官方源")
    parser.add_argument("--python-exe", help="覆盖用于创建环境的解释器")
    parser.add_argument("--no-pin", action="store_true",
                        help="忽略 deploy.json 的锁定版本，直接按 requirements 安装")
    parser.add_argument("--recreate", action="store_true", help="已存在环境也删除重建")
    parser.add_argument("--dry-run", action="store_true", help="只打印将执行的命令，不做改动")
    args = parser.parse_args(argv)

    started = time.time()
    config_path = args.config if os.path.isabs(args.config) \
        else os.path.join(PROJECT_ROOT, args.config)

    print("=" * 70)
    print("生物炭吸附性能预测器 · 一键部署")
    print("=" * 70)
    print("项目根目录：%s" % PROJECT_ROOT)
    print("配置文件　：%s" % config_path)
    if args.dry_run:
        print("模式　　　：演练（不会修改任何文件）")
    print()

    try:
        config = load_config(config_path, {
            "venv_dir": args.venv_dir,
            "index_url": args.index_url,
            "python_exe": args.python_exe,
        })

        print("[1/4] 挑选基础解释器")
        base_python, version_text, source, degraded = select_base_python(config)
        print("  使用 %s (Python %s)" % (base_python, version_text))
        print("  来源：%s" % source)
        if degraded:
            print("  提示：该版本高于锁定版本的验证上限（Python %d.%d）。"
                  % (PINNED_TESTED_UPTO[0], PINNED_TESTED_UPTO[1]))
            print("        若某些包没有对应 wheel，脚本会自动改为不锁版本安装，并明确告知。")
            print("        想避免降级，可安装 Python 3.10 ~ 3.12，"
                  "或在 deploy.json 的 pythonExe 里指定。")

        print("\n[2/4] 准备虚拟环境")
        created = ensure_venv(base_python, config, args.recreate, args.dry_run)

        print("\n[3/4] 安装依赖")
        install_dependencies(config, args.dry_run,
                             pin_override=False if args.no_pin else None)

        print("\n[4/4] 验证安装结果")
        verify_imports(config, config["verifyImports"], args.dry_run)

        if config["checkBackend"]:
            check_backend(config, args.dry_run)
        else:
            print("  已跳过后端验证（deploy.json 的 checkBackend 为 false）")

        return report(config, base_python, version_text, source, created,
                      time.time() - started, args.dry_run)

    except DeployError as exc:
        print("\n" + "=" * 70)
        print("部署未完成：")
        print("  %s" % exc)
        return 1
    except KeyboardInterrupt:
        print("\n已中断。已创建的环境保留在 %s，可重新运行本脚本继续。"
              % os.path.join(PROJECT_ROOT, ".venv"))
        return 130


if __name__ == "__main__":
    sys.exit(main())
