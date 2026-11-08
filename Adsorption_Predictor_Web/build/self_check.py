# -*- coding: utf-8 -*-
"""交付前最终自检：语法、范围一致性、模型完整性、接口数值。

主题
    提交前把该断言的状态一次性断言清楚，避免只凭"能启动"就交付。

任务
    1. 全部 Python 文件可被 ast 解析
    2. 后端计算的输入范围与 /api/meta 下发到前端的一致
    3. models/ 副本与原项目模型预测一致
    4. 接口预测值与直连模型一致
    5. 关键交付文件齐备

结构
    ① 常量区   项目根、必需文件清单
    ② 静态检查 语法 + 文件齐备 + 范围一致性
    ③ 动态检查 模型完整性 + 接口（调用同目录脚本）
    ④ 出口 main 汇总，任一失败即非零退出

调用树
    main
    ├── check_syntax
    ├── check_required_files
    ├── check_limits_consistency
    ├── run_script                （调用 verify_models.py / test_api.py）
    └── report
"""

import ast
import json
import os
import subprocess
import sys
import urllib.request

# ============================================================================
# ① 常量区
# ============================================================================

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(BUILD_DIR)
sys.path.insert(0, WEB_DIR)

PYTHON = sys.executable
BASE_URL = "http://127.0.0.1:8765"

REQUIRED_FILES = [
    "app.py", "start.bat", "requirements.txt", "README.md", ".gitignore",
    "deploy.bat", "deploy.py", "deploy.json",
    "backend/__init__.py", "backend/paths.py", "backend/model_registry.py",
    "backend/features.py", "backend/model_store.py", "backend/dataset_meta.py",
    "frontend/index.html", "frontend/style.css", "frontend/app.js",
    "frontend/field_meta.json", "frontend/samples.json",
    "models/xgb_amount.joblib", "models/scaler_amount.joblib",
    "models/catboost_amount.joblib", "models/xgb_capacity.joblib",
    "models/scaler_capacity.joblib", "models/xgb_capacity_wgan.joblib",
    "models/scaler_capacity_wgan.joblib", "models/Dataset.csv",
    "build/source_project.py", "build/make_field_meta.py", "build/make_samples.py",
    "build/make_architecture_figure.py",
    "docs/figures/图1_架构与调用关系.png", "docs/figures/图2_一次预测的数据流.png",
    "docs/figures/图3_项目完整结构.png",
    "docs/figures/图4_原理与实现对应.png",
    "build/measure_wgan_model.py", "build/verify_models.py",
    "build/reproduce_metrics.py", "build/test_api.py", "build/self_check.py",
]


# ============================================================================
# ② 静态检查
# ============================================================================

# 扫描项目自身源码时要跳过的目录：虚拟环境里有七千多个第三方 .py，
# 既慢又可能不是 UTF-8（实测某包的测试夹具就不是），必须排除。
SKIP_DIRS = {".venv", "venv", "env", ".git", "__pycache__", "node_modules",
             ".idea", ".vscode", ".pytest_cache", "dist", "build_lib"}


def check_syntax(failures):
    print("\n[1] Python 语法检查")
    count = 0
    for root, dirs, files in os.walk(WEB_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, WEB_DIR)
            try:
                # 用 utf-8-sig 读取：若文件带 UTF-8 BOM，Python 导入时能接受，
                # 但 ast.parse 会把 BOM 当成非法字符，这里对齐导入器的行为。
                with open(path, "r", encoding="utf-8-sig") as fh:
                    ast.parse(fh.read())
                count += 1
            except SyntaxError as exc:
                failures.append("语法错误 %s: %s" % (rel, exc))
                print("  ✗ %s  %s" % (rel, exc))
            except (UnicodeDecodeError, OSError) as exc:
                failures.append("无法读取 %s: %s" % (rel, exc))
                print("  ✗ %s  %s" % (rel, exc))
    print("  ✓ %d 个项目 Python 文件全部可解析（已跳过虚拟环境等目录）" % count)


def check_required_files(failures):
    print("\n[2] 交付文件齐备性")
    missing = [rel for rel in REQUIRED_FILES
               if not os.path.exists(os.path.join(WEB_DIR, rel.replace("/", os.sep)))]
    if missing:
        failures.extend("缺少文件 %s" % m for m in missing)
        for m in missing:
            print("  ✗ 缺少 %s" % m)
    else:
        print("  ✓ %d 个关键文件全部存在" % len(REQUIRED_FILES))


def check_limits_consistency(failures):
    print("\n[3] 输入范围一致性（后端 ↔ 前端）")
    from backend import dataset_meta
    from backend import model_registry as registry

    limits = dataset_meta.field_limits()
    try:
        with urllib.request.urlopen(BASE_URL + "/api/meta", timeout=30) as response:
            meta = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - 服务未启动时明确报告
        failures.append("无法访问 /api/meta：%s" % exc)
        print("  ✗ 无法访问服务：%s" % exc)
        return

    bad = []
    for field in registry.BASE_NUMERIC_FIELDS:
        low = meta["fields"][field].get("acceptLow")
        high = meta["fields"][field].get("acceptHigh")
        if low is None or abs(low - limits[field][0]) > 1e-9 or \
                abs(high - limits[field][1]) > 1e-9:
            bad.append(field)
    if bad:
        failures.append("范围与前端不一致：%s" % bad)
        print("  ✗ 不一致字段：%s" % bad)
    else:
        print("  ✓ %d 个字段的接受范围与 /api/meta 下发值一致"
              % len(registry.BASE_NUMERIC_FIELDS))

    # 顺带确认没有字段被收紧到拒绝真实数据
    data = dataset_meta.load_field_meta()["fields"]
    too_tight = [f for f in registry.BASE_NUMERIC_FIELDS
                 if data[f]["min"] < limits[f][0] or data[f]["max"] > limits[f][1]]
    if too_tight:
        failures.append("范围过紧，会拒绝真实数据：%s" % too_tight)
        print("  ✗ 会拒绝真实数据的字段：%s" % too_tight)
    else:
        print("  ✓ 全部真实数据都落在接受范围内")


# ============================================================================
# ③ 动态检查
# ============================================================================

def call_script(rel_path, capture_patterns, failures, label):
    print("\n%s" % label)
    proc = subprocess.run([PYTHON, os.path.join(BUILD_DIR, rel_path)],
                          cwd=WEB_DIR, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    output = (proc.stdout or "") + (proc.stderr or "")
    # 同一行可能命中多个关键词，去重后再打印
    matched = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped and any(p in stripped for p in capture_patterns):
            if stripped not in matched:
                matched.append(stripped)
    for line in matched:
        print("  " + line)
    if proc.returncode != 0:
        failures.append("%s 未通过（退出码 %d）" % (rel_path, proc.returncode))
        print("  ✗ 退出码 %d" % proc.returncode)
    else:
        print("  ✓ 通过")


# ============================================================================
# ④ 出口 main
# ============================================================================

def check_deploy_script(failures):
    """用 --dry-run 检查部署脚本可运行：能读配置、能定位解释器、命令拼得对。

    不真正创建环境——那要几分钟且占约 400 MB，不适合放进自检。
    """
    print("\n[7] 一键部署脚本（演练模式）")
    proc = subprocess.run([PYTHON, os.path.join(WEB_DIR, "deploy.py"), "--dry-run"],
                          cwd=WEB_DIR, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        failures.append("deploy.py --dry-run 未通过（退出码 %d）" % proc.returncode)
        print("  ✗ 退出码 %d" % proc.returncode)
        for line in output.splitlines()[-8:]:
            print("    " + line)
        return
    for line in output.splitlines():
        if "定位基础解释器" in line or "使用 " in line and "Python" in line:
            print("  " + line.strip())
    ok = "演练完成" in output
    print("  %s deploy.py 可正常读取 deploy.json 并生成安装步骤" % ("✓" if ok else "✗"))
    if not ok:
        failures.append("deploy.py --dry-run 未输出预期的演练结果")


def report(failures):
    print("\n" + "=" * 70)
    if failures:
        print("自检未通过，%d 项问题：" % len(failures))
        for item in failures:
            print("  ✗ %s" % item)
        return 1
    print("全部自检通过，可以交付。")
    return 0


def main():
    print("=" * 70)
    print("交付前最终自检")
    print("项目根目录：%s" % WEB_DIR)
    print("=" * 70)

    failures = []

    check_syntax(failures)
    check_required_files(failures)
    check_limits_consistency(failures)
    call_script("verify_models.py", ["一致", "无损", "✗"], failures,
                "[4] 模型副本完整性（对比原项目）")
    call_script("reproduce_metrics.py", ["结论", "偏差", "✗"], failures,
                "[5] 指标一致性与跨版本行为")
    call_script("test_api.py", ["最大偏差", "全部测试通过", "✗"], failures,
                "[6] 接口端到端数值校验")
    check_deploy_script(failures)

    return report(failures)


if __name__ == "__main__":
    sys.exit(main())
