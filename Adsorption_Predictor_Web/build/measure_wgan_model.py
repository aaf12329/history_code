# -*- coding: utf-8 -*-
"""同口径复算 WGAN-GP 增强 XGBoost 模型的测试集指标。

主题
    该模型训练脚本只把指标打印到控制台，没有落盘，而网页需要如实标注精度。
    本脚本按源脚本的同一套随机种子与划分方式复现，重新算出测试集 R² / RMSE。

任务
    复现 WGanBoost_Xgboost/Gan_Boost_Xgb.py 的 run_complete_analysis 前 6 步：
      1. 固定 np.random.seed(42)，抽出 3 条验证集
      2. 原始数据 + WGAN 生成数据混合，构造 19 维 S11 特征集
      3. train_test_split(test_size=0.2, random_state=42)
      4. StandardScaler 拟合训练集
      5. 用保存的模型预测测试集
      6. 计算 R² / RMSE / MAE

结构
    ① 常量区   ：路径、特征顺序、目标列
    ② 特征工程 ：add_element_ratios / prepare_dataset（与源脚本逐行对齐）
    ③ 复现校验 ：对比复现的 scaler 与保存的 scaler，确认划分复现成功
    ④ 出口 main：算指标并写 wgan_metrics.json

调用树
    main
    ├── prepare_dataset            （准备：混合数据 + 19 维特征）
    ├── verify_reproduction        （校验：scaler 是否与保存的一致）
    └── write_metrics              （输出）

数据流
    Dataset.csv + generated_data_wgan_gp_new.csv
        → 混合 (2943, 19) → train_test_split → 标准化 → model.predict → R²/RMSE
"""

import json
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ============================================================================
# ① 常量区
# ============================================================================

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(BUILD_DIR)
# 原项目路径由同目录的 source_project.py 统一解析：
# 环境变量 SOURCE_PROJECT → 本项目同级目录 → 用户桌面
from source_project import find_source_project                 # noqa: E402
SOURCE_PROJECT, SOURCE_LABEL = find_source_project()
DATASET_CSV = os.path.join(SOURCE_PROJECT, "Dataset.csv")
GENERATED_PATHS = [
    os.path.join(SOURCE_PROJECT, "WGAN", "generated_data_wgan_gp.csv"),
    os.path.join(SOURCE_PROJECT, "WGAN", "generated_data_wgan_gp_new.csv"),
]
OUT_JSON = os.path.join(BUILD_DIR, "wgan_metrics.json")

TARGET = "Adsorption capacity"
FEATURE_ORDER = ["SBET", "VTotal", "Dp", "H/C", "N/C", "O+N/C", "O/C",
                 "Initial concentration", "Dosage", "Temperature", "Initial pH",
                 "E", "S", "A", "B", "V", "Kow", "pKa1", "MW"]
EXCLUDE_COLUMNS = ["Number", "Reference", "Adsorption amount", "Adsorption capacity",
                   "pKa3", "pKa2"]

MODEL_PATH = os.path.join(WEB_DIR, "models", "xgb_capacity_wgan.joblib")
SCALER_PATH = os.path.join(WEB_DIR, "models", "scaler_capacity_wgan.joblib")


# ============================================================================
# ② 特征工程（与源脚本逐行对齐）
# ============================================================================

def add_element_ratios(df):
    """用元素比值替换原始 C/H/O/N，并去掉污染物列。"""
    df = df.copy()
    df["H/C"] = df["H"] / df["C"]
    df["N/C"] = df["N"] / df["C"]
    df["O/C"] = df["O"] / df["C"]
    df["O+N/C"] = (df["O"] + df["N"]) / df["C"]
    drop_cols = [c for c in ["C", "H", "O", "N", "Pollutant"] if c in df.columns]
    drop_cols += [c for c in df.columns if c.startswith("Pollutant_")]
    return df.drop(columns=drop_cols)


def prepare_dataset(file_path, generated_path, target_variable=TARGET):
    """原始数据 + WGAN 生成数据混合，构造 S11 特征集。

    注意：np.random.seed(42) 必须在调用本函数前设置，且这是第一次消耗随机数，
    否则抽出的 3 条验证集会不同，后续划分也随之改变。
    """
    real_df = pd.read_csv(file_path)
    real_df["Number"] = range(1, len(real_df) + 1)

    if target_variable not in real_df.columns:
        raise ValueError("目标列不存在: %s" % target_variable)

    random_numbers = np.random.choice(real_df["Number"].dropna().unique(), size=3)
    validation_set = real_df[real_df["Number"].isin(random_numbers)]
    real_df = real_df[~real_df["Number"].isin(random_numbers)]

    real_feat = add_element_ratios(real_df)
    X_real = real_feat.drop(columns=EXCLUDE_COLUMNS)
    y_real = real_feat[target_variable]

    gen_df = pd.read_csv(generated_path)
    gen_feat = add_element_ratios(gen_df)
    X_gen = gen_feat.drop(columns=[c for c in EXCLUDE_COLUMNS if c in gen_feat.columns])
    y_gen = gen_feat[target_variable]

    X = pd.concat([X_real, X_gen], ignore_index=True)[FEATURE_ORDER]
    y = pd.concat([y_real, y_gen], ignore_index=True)

    print("混合数据集: 原始 %d 行 + WGAN 生成 %d 行 = %d 行, 特征 %d 个"
          % (len(X_real), len(X_gen), len(X), X.shape[1]))
    print("被抽为验证集（不参与训练）的行号: %s" % sorted(random_numbers.tolist()))
    return X, y, validation_set


# ============================================================================
# ③ 复现校验
# ============================================================================

def verify_reproduction(scaler_reproduced, scaler_saved):
    """对比复现的标准化器与保存的标准化器，确认数据划分复现成功。"""
    mean_diff = np.abs(np.asarray(scaler_reproduced.mean_) - np.asarray(scaler_saved.mean_)).max()
    scale_diff = np.abs(np.asarray(scaler_reproduced.scale_) - np.asarray(scaler_saved.scale_)).max()
    print("\n复现校验（越大说明划分复现越不可靠）:")
    print("  均值最大差 = %.3g" % mean_diff)
    print("  标准差最大差 = %.3g" % scale_diff)
    return float(max(mean_diff, scale_diff))


# ============================================================================
# ④ 出口 main
# ============================================================================

def write_metrics(payload, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return path


def main():
    generated_path = None
    for candidate in GENERATED_PATHS:
        if os.path.exists(candidate) and TARGET in pd.read_csv(candidate, nrows=0).columns:
            generated_path = candidate
            break
    if generated_path is None:
        print("未找到 WGAN 生成数据，无法复算")
        return 1
    print("使用生成数据:", generated_path)

    # 与源脚本一致：模块级随机种子，随后第一次消耗随机数就是验证集抽样
    np.random.seed(42)
    X, y, _ = prepare_dataset(DATASET_CSV, generated_path, TARGET)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    scaler_reproduced = StandardScaler()
    X_train_scaled = scaler_reproduced.fit_transform(X_train)
    X_test_scaled = scaler_reproduced.transform(X_test)

    scaler_saved = joblib.load(SCALER_PATH)
    worst = verify_reproduction(scaler_reproduced, scaler_saved)

    model = joblib.load(MODEL_PATH)
    y_pred = model.predict(X_test_scaled)

    metrics = {
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
        "source": "build/measure_wgan_model.py（同口径复算，随机种子 42）",
        "nTrain": int(len(X_train)),
        "nTest": int(len(X_test)),
        "nFeatures": int(X.shape[1]),
        "reproductionMaxScalerDiff": worst,
    }

    print("\n=== 复算结果（测试集 %d 条）===" % len(y_test))
    print("R²   = %.4f" % metrics["r2"])
    print("RMSE = %.2f" % metrics["rmse"])
    print("MAE  = %.2f" % metrics["mae"])
    if worst > 1e-6:
        print("⚠ 复现的标准化器与保存值存在差异（%.3g），指标仅供参考" % worst)
    else:
        print("✓ 划分复现一致，指标可信")

    write_metrics({"capacity_wgan_xgb": metrics}, OUT_JSON)
    print("\n已写", OUT_JSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
