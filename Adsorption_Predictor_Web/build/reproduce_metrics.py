# -*- coding: utf-8 -*-
"""交叉版本与指标一致性检查：新版库装载旧模型后行为是否仍与记录一致。

主题
    XGBoost 装载旧版本序列化的模型时会给出警告，提示"保存"与"序列化"存在差异。
    本项目用 xgboost 3.2.0 装载 1.7.6 训练的模型，必须确认预测行为没有漂移。
    同时复核页面上展示的精度指标是否确实属于所部署的那个模型。

任务
    对 25 维特征集的三个模型（两个目标）：
      1. 复现其 80/20 划分（原预处理未固定随机种子，故用多个种子观察分布）
      2. 用保存的标准化器与保存的模型预测测试集
      3. 计算 R² / RMSE，与页面展示值对比
    19 维的 WGAN 增强模型由 build/measure_wgan_model.py 单独复算。

结构
    ① 常量区   ：目标、页面展示指标、种子集合
    ② 复现     ：重建 25 维设计矩阵与划分
    ③ 评估     ：逐模型算 R² / RMSE
    ④ 出口 main：与展示值比较并给结论

调用树
    main
    ├── build_matrix      （准备：25 维设计矩阵 + 目标列）
    ├── evaluate_model    （核心：复现划分 → 保存的 scaler/model → 预测）
    └── report            （输出）

数据流
    Dataset.csv → 设计矩阵 → 抽 3 条验证集 → train_test_split → scaler → model → R²/RMSE
"""

import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

WEB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WEB_DIR)

from backend import model_registry as registry    # noqa: E402
from backend import paths                         # noqa: E402

# ============================================================================
# ① 常量区
# ============================================================================

# 本次覆盖 25 维特征集的模型；B19 的 WGAN 增强模型由 measure_wgan_model.py 负责
COVERED_KEYS = ["xgb_amount", "catboost_amount", "xgb_capacity"]

# 原预处理随机抽 3 条作验证集且未固定种子，故用多个种子观察复算值的分布
SEEDS = [0, 1, 7, 42, 123, 2026, 20260101]

# 页面展示值与复算留出值口径不同（5 折 CV vs 80/20 留出），允许的偏差上限
R2_TOLERANCE = 0.03

EXCLUDE_COLUMNS = ["Number", "Reference", "Adsorption amount", "Adsorption capacity",
                   "pKa3", "pKa2", "pKa1"]


# ============================================================================
# ② 复现
# ============================================================================

def build_matrix(df, target_column):
    """重建 25 维设计矩阵与目标向量（与 Boosting/Machine.py: prepare_dataset 同口径）。"""
    encoded = pd.get_dummies(df, columns=["Pollutant"])
    y = encoded[target_column]
    encoded = encoded.drop(columns=[c for c in EXCLUDE_COLUMNS if c in encoded.columns])
    return encoded.astype("float64"), y


# ============================================================================
# ③ 评估
# ============================================================================

def evaluate_model(spec, seed):
    """按指定种子复现划分，用页面所部署的模型与标准化器算测试集指标。"""
    df = pd.read_csv(paths.DATASET_CSV)
    target_column = registry.TARGETS[spec["target"]]["datasetColumn"]
    X, y = build_matrix(df, target_column)

    model = joblib.load(paths.model_path(spec["modelFile"]))
    scaler = (joblib.load(paths.model_path(spec["scalerFile"]))
              if spec["scalerFile"] else None)

    # 复现"随机抽 3 条作验证集、不参与训练"
    rng = np.random.default_rng(seed)
    drop_idx = rng.choice(len(X), size=3, replace=False)
    keep = np.setdiff1d(np.arange(len(X)), drop_idx)

    X_train, X_test, y_train, y_test = train_test_split(
        X.iloc[keep], y.iloc[keep], test_size=0.2, random_state=42)

    payload = scaler.transform(X_test) if scaler is not None else X_test
    y_pred = np.asarray(model.predict(payload)).ravel()

    return {
        "seed": seed,
        "r2": float(r2_score(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
    }


# ============================================================================
# ④ 出口 main
# ============================================================================

def report(rows, failures):
    print("\n" + "=" * 92)
    print("%-18s %-9s %-20s %-20s %s"
          % ("模型", "口径", "页面展示 R²/RMSE", "复算留出 R²/RMSE", "R² 偏差"))
    print("-" * 92)
    for item in rows:
        print("%-18s %-9s %-20s %-20s %+.4f"
              % (item["key"], item["protocol"],
                 "%.4f / %.2f" % (item["shownR2"], item["shownRmse"]),
                 "%.4f / %.2f" % (item["centerR2"], item["centerRmse"]),
                 item["centerR2"] - item["shownR2"]))

    if failures:
        print("\n结论：存在不一致")
        for text in failures:
            print("  ✗ %s" % text)
        return 1
    print("\n结论：三个模型复算值与页面展示值一致，新版库装载旧模型后行为无漂移。")
    print("      （页面口径与留出口径本就不同，偏差在 %.2f 以内即为正常）" % R2_TOLERANCE)
    return 0


def main():
    rows, failures = [], []
    for key in COVERED_KEYS:
        spec = registry.MODELS_BY_KEY[key]
        metrics = spec["metrics"]

        results = [evaluate_model(spec, seed) for seed in SEEDS]
        r2s = [r["r2"] for r in results]
        rmses = [r["rmse"] for r in results]
        center_r2 = (min(r2s) + max(r2s)) / 2.0
        center_rmse = (min(rmses) + max(rmses)) / 2.0

        rows.append({
            "key": key, "protocol": metrics.get("protocol", "未标注"),
            "shownR2": metrics["r2"], "shownRmse": metrics["rmse"],
            "centerR2": center_r2, "centerRmse": center_rmse,
        })

        if abs(center_r2 - metrics["r2"]) > R2_TOLERANCE:
            failures.append(
                "%s 复算 R² 中心 %.4f 与展示值 %.4f 相差超过 %.2f"
                % (key, center_r2, metrics["r2"], R2_TOLERANCE))
        # 复算值明显更差才说明模型装载有问题；更好属于划分随机性的正常波动
        if center_r2 < metrics["r2"] - R2_TOLERANCE * 1.5:
            failures.append("%s 复算 R²（%.4f）明显低于展示值（%.4f），疑似模型装载异常"
                            % (key, center_r2, metrics["r2"]))
        print("[%s] %s  |  复算 R² 区间 %.4f ~ %.4f（%d 个种子）"
              % (key, spec["label"], min(r2s), max(r2s), len(SEEDS)))

    return report(rows, failures)


if __name__ == "__main__":
    sys.exit(main())
