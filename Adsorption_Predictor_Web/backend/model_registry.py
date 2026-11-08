# -*- coding: utf-8 -*-
"""模型注册表：全项目唯一的模型清单与特征集定义（纯常量，无逻辑）。

职责
    登记「有哪些模型、各自什么特征集、要不要标准化、精度多少、数据从哪来」。
    任何模块想知道模型信息都读这里，不在别处写第二份。

被谁调用
    backend.features, backend.predictor, app
调用谁
    无

字段说明（每个模型条目）
    key          : 前端与接口使用的唯一标识
    label        : 页面上显示的名字
    family       : 模型族（用于界面分组）
    target       : "amount" 或 "capacity"，对应 targets
    featureSet   : "A25" 或 "B19"，对应 featureSets
    modelFile    : models/ 下的模型文件名
    scalerFile   : models/ 下的标准化器文件名；None 表示该模型吃原始特征
    metrics      : 精度指标，source 注明出处，页面原样展示以便追溯
    note         : 训练口径说明（可选）
"""

# --- 特征集定义 -------------------------------------------------------------

FEATURE_SETS = {
    "A25": {
        "label": "25 维主特征集",
        "short": "25 维",
        "note": "论文主模型特征集：C/H/O/N 原始质量分数 + 污染物 7 个哑变量",
        "columns": [
            "SBET", "VTotal", "Dp", "C", "O", "H", "N", "Dosage",
            "Initial concentration", "Temperature", "Initial pH", "MW",
            "E", "S", "A", "B", "V", "Kow",
            "Pollutant_Sulfadiazine", "Pollutant_Sulfamerazine",
            "Pollutant_Sulfamethazine", "Pollutant_Sulfamethoxazole",
            "Pollutant_Sulfapyridine", "Pollutant_Sulfathiazole",
            "Pollutant_Sulfonamide",
        ],
    },
    "B19": {
        "label": "19 维 S11 特征集",
        "short": "19 维",
        "note": "论文 Fig.S11 特征集：用元素比值 H/C、N/C、O/C、O+N/C 取代原始 C/H/O/N，保留 pKa1，不含污染物哑变量",
        "columns": [
            "SBET", "VTotal", "Dp", "H/C", "N/C", "O+N/C", "O/C",
            "Initial concentration", "Dosage", "Temperature", "Initial pH",
            "E", "S", "A", "B", "V", "Kow", "pKa1", "MW",
        ],
    },
}

# --- 目标变量 ---------------------------------------------------------------

TARGETS = {
    "amount": {
        "label": "吸附量 Adsorption amount",
        "unit": "mg/g",
        "desc": "单位质量吸附剂吸附的污染物质量",
        "datasetColumn": "Adsorption amount",
    },
    "capacity": {
        "label": "吸附容量 Adsorption capacity",
        "unit": "mg/g",
        "desc": "吸附剂对污染物的饱和吸附容量",
        "datasetColumn": "Adsorption capacity",
    },
}

# --- 污染物类别（用于独热编码）----------------------------------------------

POLLUTANTS = [
    "Sulfadiazine", "Sulfamerazine", "Sulfamethazine", "Sulfamethoxazole",
    "Sulfapyridine", "Sulfathiazole", "Sulfonamide",
]

# --- 基础输入字段（用户填写的原始量，两种特征集都由这些推出）----------------

BASE_NUMERIC_FIELDS = [
    "SBET", "VTotal", "Dp", "C", "H", "O", "N",
    "Dosage", "Initial concentration", "Temperature", "Initial pH",
    "MW", "Kow", "pKa1", "E", "S", "A", "B", "V",
]

MOLECULAR_DESCRIPTORS = ["MW", "Kow", "pKa1", "E", "S", "A", "B", "V"]

# --- 输入合法性边界 ---------------------------------------------------------

# 物理上不能为负的字段：下界即使由数据推出的范围更宽，也收紧到 0。
# （Kow、pKa1 允许为负，故不在此列）
NON_NEGATIVE_FIELDS = [
    "SBET", "VTotal", "Dp", "C", "H", "O", "N",
    "Dosage", "Initial concentration", "Temperature",
    "MW", "E", "S", "A", "B", "V",
]

# 有明确定义域的字段：与数据推出的范围取交集，避免余量把显然不可能的取值放进来
# 形式为 (下界 或 None, 上界 或 None)
FIELD_HARD_BOUNDS = {
    "C": (1e-9, None),          # 元素比值以 C 为分母，必须严格为正
    "Initial pH": (0.0, 14.0),  # pH 的定义域
    "Temperature": (200.0, 400.0),   # 开尔文，覆盖常压实验范围
}

# --- 模型清单 ---------------------------------------------------------------

MODELS = [
    {
        "key": "xgb_amount",
        "label": "XGBoost",
        "family": "梯度提升树",
        "target": "amount",
        "featureSet": "A25",
        "modelFile": "xgb_amount.joblib",
        "scalerFile": "scaler_amount.joblib",
        "metrics": {"r2": 0.9669, "rmse": 19.83, "protocol": "5 折交叉验证",
                    "source": "WGAN_Boost_Xgboost/README.md（最优参数 5 折 CV 记录）"},
        "note": "贝叶斯超参数优化（BayesSearchCV，5 折 + 负 RMSE，50 轮），输入需标准化",
    },
    {
        "key": "catboost_amount",
        "label": "CatBoost",
        "family": "梯度提升树",
        "target": "amount",
        "featureSet": "A25",
        "modelFile": "catboost_amount.joblib",
        "scalerFile": None,
        "isDefault": True,          # 原项目结论：CatBoost 为当前全场最优模型
        "metrics": {"r2": 0.9619, "rmse": 15.70, "protocol": "80/20 留出测试集",
                    "source": "WGAN_Boost_Xgboost/results/lightgbm_catboost/result_adsorption_amount.txt"},
        "note": "同为贝叶斯调参、同一套 25 维特征；直接吃原始特征，不做标准化",
    },
    {
        "key": "xgb_capacity",
        "label": "XGBoost",
        "family": "梯度提升树",
        "target": "capacity",
        "featureSet": "A25",
        "modelFile": "xgb_capacity.joblib",
        "scalerFile": "scaler_capacity.joblib",
        "isDefault": True,          # 该目标下无 CatBoost 对照，默认用调参后的 XGBoost
        "metrics": {"r2": 0.9756, "rmse": 20.40, "protocol": "5 折交叉验证",
                    "source": "WGAN_Boost_Xgboost/results/Adsorption_capacity/result.txt（cv_metrics）"},
        "note": "与吸附量同口径的贝叶斯调参流程，仅切换目标变量",
    },
    {
        "key": "xgb_capacity_wgan",
        "label": "XGBoost + WGAN-GP 增强",
        "family": "梯度提升树（本项目主线）",
        "target": "capacity",
        "featureSet": "B19",
        "modelFile": "xgb_capacity_wgan.joblib",
        "scalerFile": "scaler_capacity_wgan.joblib",
        "metrics": {"r2": 0.9614, "rmse": 25.90, "protocol": "80/20 留出测试集",
                    "source": "复算：build/measure_wgan_model.py（随机种子 42，划分复现一致）"},
        "note": "原始 940 行 + WGAN-GP 生成 2000 行混合训练，特征集为论文 Fig.S11 的 19 维",
    },
]

# --- 便于查找的派生索引（仍属常量，启动时算一次）----------------------------

MODELS_BY_KEY = {spec["key"]: spec for spec in MODELS}


def models_for_target(target):
    """返回某个目标下的全部模型条目，保持清单顺序。"""
    return [spec for spec in MODELS if spec["target"] == target]
