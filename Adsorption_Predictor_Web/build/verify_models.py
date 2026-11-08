# -*- coding: utf-8 -*-
"""模型完整性校验：确认 models/ 里的副本与原项目模型逐位一致。

主题
    交付物把模型复制进了项目，必须证明复制没有损坏、也没有张冠李戴。
    只看"文件大小对得上"是不够的，要断言预测值一致。

任务
    对注册表中的每个模型：
      1. 用 backend 的特征层构造 200 行真实特征
      2. 分别用 models/ 的副本与原项目的模型预测
      3. 断言两者数值完全一致
    另外校验每个模型的输入维数与登记的特征集一致。

结构
    ① 常量区   ：源项目路径、抽样量、容差
    ② 供料     ：从数据集随机抽行并构造两套特征集
    ③ 比对     ：副本 vs 原件逐样本比对
    ④ 出口 main：汇总，任一不一致即非零退出

调用树
    main
    ├── sample_inputs        （准备：随机抽取真实记录转成表单输入）
    ├── compare_model        （核心：副本与原件预测比对）
    └── report               （输出）

数据流
    Dataset.csv → 表单输入 → features.build_row → 预测（副本/原件）→ 断言
"""

import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(BUILD_DIR)
sys.path.insert(0, WEB_DIR)

from backend import dataset_meta                  # noqa: E402
from backend import features                      # noqa: E402
from backend import model_registry as registry    # noqa: E402
from backend import paths                         # noqa: E402

# ============================================================================
# ① 常量区
# ============================================================================

# 原项目路径由同目录的 source_project.py 统一解析：
# 环境变量 SOURCE_PROJECT → 本项目同级目录 → 用户桌面
from source_project import find_source_project                 # noqa: E402
SOURCE_PROJECT, SOURCE_LABEL = find_source_project()

# 副本 → 原件 的相对路径
ORIGINALS = {
    "xgb_amount": (r"results\result2\xgboost_model_adsorption_amount.joblib",
                   r"results\result2\scaler_adsorption_amount.joblib"),
    "catboost_amount": (r"results\lightgbm_catboost\catboost_model_adsorption_amount.joblib",
                        None),
    "xgb_capacity": (r"results\Adsorption_capacity\xgboost_model_adsorption_capacity.joblib",
                     r"results\Adsorption_capacity\scaler_adsorption_capacity.joblib"),
    "xgb_capacity_wgan": (r"WGanBoost_Xgboost\xgboost_model_adsorption_capacity.joblib",
                          r"WGanBoost_Xgboost\scaler_adsorption_capacity.joblib"),
}

N_SAMPLES = 200
TOLERANCE = 1e-9
SEED = 20260101


# ============================================================================
# ② 供料
# ============================================================================

def sample_inputs(df, count, seed=SEED):
    """从数据集随机抽行，转成表单输入（含污染物与全部基础字段）。"""
    rng = np.random.default_rng(seed)
    rows = df.iloc[rng.choice(len(df), size=min(count, len(df)), replace=False)]

    inputs_list = []
    for _, row in rows.iterrows():
        item = {"Pollutant": str(row["Pollutant"])}
        for field in registry.BASE_NUMERIC_FIELDS:
            item[field] = float(row[field])
        inputs_list.append(item)
    return inputs_list


# ============================================================================
# ③ 比对
# ============================================================================

def compare_model(spec, inputs_list):
    """比对副本与原件的预测值，返回 (最大偏差, 样本数, 错误信息或 None)。"""
    original_model_path, original_scaler_path = ORIGINALS[spec["key"]]

    copy_model = joblib.load(paths.model_path(spec["modelFile"]))
    copy_scaler = joblib.load(paths.model_path(spec["scalerFile"])) if spec["scalerFile"] else None

    orig_model = joblib.load(os.path.join(SOURCE_PROJECT, original_model_path))
    orig_scaler = (joblib.load(os.path.join(SOURCE_PROJECT, original_scaler_path))
                   if original_scaler_path else None)

    worst = 0.0
    for inputs in inputs_list:
        row, _ = features.build_row(spec, inputs, dataset_meta.field_limits())

        expected_dim = len(registry.FEATURE_SETS[spec["featureSet"]]["columns"])
        if row.shape[1] != expected_dim:
            return None, 0, ("特征维数不符：构造出 %d 列，登记为 %d 列"
                             % (row.shape[1], expected_dim))

        def _predict(model, scaler):
            payload = scaler.transform(row) if scaler is not None else row
            return float(np.asarray(model.predict(payload)).ravel()[0])

        diff = abs(_predict(copy_model, copy_scaler) - _predict(orig_model, orig_scaler))
        worst = max(worst, diff)

    return worst, len(inputs_list), None


# ============================================================================
# ④ 出口 main
# ============================================================================

def report(rows, failures):
    print("\n" + "=" * 74)
    print("%-20s %-10s %-12s %s" % ("模型", "抽样数", "最大偏差", "结论"))
    print("-" * 74)
    for item in rows:
        print("%-20s %-10s %-12s %s"
              % (item["key"], item["n"], "%.3g" % item["worst"],
                 "一致" if item["worst"] <= TOLERANCE else "不一致"))

    if failures:
        print("\n校验未通过：")
        for text in failures:
            print("  ✗ %s" % text)
        return 1
    print("\n全部模型副本与原件预测一致，复制无损。")
    return 0


def main():
    df = pd.read_csv(paths.DATASET_CSV)
    print("数据集: %d 行 × %d 列（%s）" % (df.shape[0], df.shape[1], paths.DATASET_CSV))
    print("原项目: %s" % SOURCE_PROJECT)

    inputs_list = sample_inputs(df, N_SAMPLES)
    print("抽取 %d 条真实记录用于比对\n" % len(inputs_list))

    rows, failures = [], []
    for spec in registry.MODELS:
        key = spec["key"]
        print("[%s] %s" % (key, spec["label"]))
        try:
            worst, n, error = compare_model(spec, inputs_list)
        except Exception as exc:  # noqa: BLE001 - 记录失败但继续校验其余模型
            failures.append("%s 校验异常：%s: %s" % (key, type(exc).__name__, exc))
            print("    ✗ %s: %s" % (type(exc).__name__, exc))
            continue

        if error:
            failures.append("%s %s" % (key, error))
            print("    ✗ %s" % error)
            continue

        if worst > TOLERANCE:
            failures.append("%s 副本与原件预测不一致，最大偏差 %.3g" % (key, worst))
        print("    %d 条比对，最大偏差 %.3g" % (n, worst))
        rows.append({"key": key, "n": n, "worst": worst})

    return report(rows, failures)


if __name__ == "__main__":
    sys.exit(main())
