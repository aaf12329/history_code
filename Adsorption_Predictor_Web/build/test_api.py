# -*- coding: utf-8 -*-
"""接口端到端测试：验证运行中的服务返回值与直接调用模型完全一致。

主题
    接口正确性验证。只测"服务能返回 200"是不够的——必须断言数值本身正确。

任务
    对每个模型、每条示例样本：
      1. 用 pandas 独立重建设计矩阵（不走 backend/ 的代码路径）
      2. 直接 joblib 调用模型得到参考值
      3. 调用运行中服务的 /api/predict
      4. 断言两者一致（容差 1e-6）
    另外验证：/api/compare 覆盖该目标下全部模型、错误输入被正确拒绝。

结构
    ① 常量区    路径与服务地址
    ② 独立参考实现：手工构造设计矩阵（与 backend 无关）
    ③ 接口调用    urllib 发请求
    ④ 出口 main   逐项断言并汇总

调用树
    main
    ├── build_reference_row      （独立复算：pandas 造特征）
    ├── post_json                （接口调用）
    └── check_rejections         （异常路径：校验是否真的被拦下）

数据流
    samples.json → 输入 → 参考值（直连模型）与实际值（走接口）→ 断言比对
"""

import json
import os
import sys
import urllib.error
import urllib.request

import joblib
import numpy as np
import pandas as pd

# ============================================================================
# ① 常量区
# ============================================================================

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(BUILD_DIR)
# 原项目路径由同目录的 source_project.py 统一解析：
# 环境变量 SOURCE_PROJECT → 本项目同级目录 → 用户桌面
from source_project import find_source_project                 # noqa: E402
SOURCE_PROJECT, SOURCE_LABEL = find_source_project()

BASE_URL = "http://127.0.0.1:8765"
SAMPLES_JSON = os.path.join(WEB_DIR, "frontend", "samples.json")
TOLERANCE = 1e-6

# 每个模型的参考实现所需信息（独立于 backend/model_registry.py 书写）
REFERENCES = {
    "xgb_amount": {
        "model": r"results\result2\xgboost_model_adsorption_amount.joblib",
        "scaler": r"results\result2\scaler_adsorption_amount.joblib",
        "mode": "A25",
    },
    "catboost_amount": {
        "model": r"results\lightgbm_catboost\catboost_model_adsorption_amount.joblib",
        "scaler": None,
        "mode": "A25",
    },
    "xgb_capacity": {
        "model": r"results\Adsorption_capacity\xgboost_model_adsorption_capacity.joblib",
        "scaler": r"results\Adsorption_capacity\scaler_adsorption_capacity.joblib",
        "mode": "A25",
    },
    "xgb_capacity_wgan": {
        "model": r"WGanBoost_Xgboost\xgboost_model_adsorption_capacity.joblib",
        "scaler": r"WGanBoost_Xgboost\scaler_adsorption_capacity.joblib",
        "mode": "B19",
    },
}

EXCLUDE_COLUMNS = ["Number", "Reference", "Adsorption amount", "Adsorption capacity",
                   "pKa3", "pKa2", "pKa1"]

ENV_ADS = ["SBET", "VTotal", "Dp", "H/C", "N/C", "O+N/C", "O/C",
           "Initial concentration", "Dosage", "Temperature", "Initial pH",
           "E", "S", "A", "B", "V", "Kow", "pKa1", "MW"]


# ============================================================================
# ② 独立参考实现
# ============================================================================

def build_reference_row(ref, inputs, feature_names):
    """不依赖 backend/，用 pandas 手工构造一行特征。

    参数
        ref: REFERENCES 中的一条
        inputs: 表单原始输入
        feature_names: 该模型训练时的特征顺序
    返回
        numpy 数组，形状 (1, n_features)
    """
    row = dict(inputs)
    if ref["mode"] == "B19":
        c = row["C"]
        row["H/C"] = row["H"] / c
        row["N/C"] = row["N"] / c
        row["O/C"] = row["O"] / c
        row["O+N/C"] = (row["O"] + row["N"]) / c
    else:
        for name in ["Sulfadiazine", "Sulfamerazine", "Sulfamethazine",
                     "Sulfamethoxazole", "Sulfapyridine", "Sulfathiazole",
                     "Sulfonamide"]:
            row["Pollutant_" + name] = 1.0 if inputs["Pollutant"] == name else 0.0

    missing = [c for c in feature_names if c not in row]
    if missing:
        raise KeyError("参考实现缺少字段: %s" % missing)
    return np.array([[float(row[c]) for c in feature_names]], dtype="float64")


def reference_prediction(key, inputs):
    """直接加载模型算参考预测值。"""
    ref = REFERENCES[key]
    model = joblib.load(os.path.join(SOURCE_PROJECT, ref["model"]))
    scaler = (joblib.load(os.path.join(SOURCE_PROJECT, ref["scaler"]))
              if ref["scaler"] else None)

    names = ([str(c) for c in scaler.feature_names_in_] if scaler is not None
             else [str(c) for c in model.feature_names_])
    names = [n.replace("Initial_concentration", "Initial concentration")
              .replace("Initial_pH", "Initial pH") for n in names]

    row = build_reference_row(ref, inputs, names)
    payload = scaler.transform(row) if scaler is not None else row
    return float(np.asarray(model.predict(payload)).ravel()[0])


# ============================================================================
# ③ 接口调用
# ============================================================================

def post_json(path, payload):
    """POST JSON 并返回 (状态码, 解析后的响应)。"""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(BASE_URL + path, timeout=60) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


# ============================================================================
# ④ 出口 main
# ============================================================================

def check_predictions(samples, failures):
    """逐个模型 × 逐条样本，比对接口值与直连模型参考值。"""
    print("\n=== 1. 逐模型预测值与直连模型比对（容差 %g）===" % TOLERANCE)
    worst = 0.0
    checked = 0
    for key in REFERENCES:
        diffs = []
        for sample in samples:
            status, body = post_json("/api/predict",
                                     {"modelKey": key, "inputs": sample["inputs"]})
            if status != 200 or not body.get("ok"):
                failures.append("%s / %s 接口失败：%s" % (key, sample["pollutant"], body))
                continue
            expected = reference_prediction(key, sample["inputs"])
            diff = abs(body["prediction"] - expected)
            diffs.append(diff)
            checked += 1
            if diff > TOLERANCE:
                failures.append("%s / %s 数值不符：接口 %.10f vs 直连 %.10f（差 %.3g）"
                                % (key, sample["pollutant"], body["prediction"],
                                   expected, diff))
        if diffs:
            worst = max(worst, max(diffs))
            print("  %-18s 比对 %d 条，最大偏差 %.3g" % (key, len(diffs), max(diffs)))
    print("  合计比对 %d 次，最大偏差 %.3g" % (checked, worst))
    return worst


def check_compare(samples, failures):
    """验证 /api/compare 覆盖该目标下的全部模型。"""
    print("\n=== 2. 多模型对比接口 ===")
    for target, expected_keys in (("amount", ["xgb_amount", "catboost_amount"]),
                                  ("capacity", ["xgb_capacity", "xgb_capacity_wgan"])):
        status, body = post_json("/api/compare",
                                 {"target": target, "inputs": samples[0]["inputs"]})
        if status != 200 or not body.get("ok"):
            failures.append("/api/compare %s 失败：%s" % (target, body))
            continue
        got = sorted(item["modelKey"] for item in body["results"])
        ok = (got == sorted(expected_keys))
        print("  target=%-9s 返回 %d 个模型 %s  %s"
              % (target, len(got), got, "✓" if ok else "✗ 与预期不符"))
        if not ok:
            failures.append("/api/compare %s 返回模型集合不符：%s" % (target, got))
        usable = [it for it in body["results"] if it["ok"]]
        print("      预测值: %s" % ", ".join(
            "%s=%.3f" % (it["label"], it["prediction"]) for it in usable))


def check_rejections(samples, failures):
    """异常路径：非法输入必须被拒绝，且给出可读原因。"""
    print("\n=== 3. 异常输入拦截 ===")
    good = dict(samples[0]["inputs"])

    cases = []
    bad_pollutant = dict(good)
    bad_pollutant["Pollutant"] = "NotAPollutant"
    cases.append(("污染物非法", {"modelKey": "xgb_amount", "inputs": bad_pollutant}))

    missing_field = dict(good)
    missing_field.pop("SBET", None)
    cases.append(("字段缺失", {"modelKey": "xgb_amount", "inputs": missing_field}))

    out_of_range = dict(good)
    out_of_range["Initial pH"] = 999
    cases.append(("数值越界", {"modelKey": "xgb_amount", "inputs": out_of_range}))

    not_a_number = dict(good)
    not_a_number["Temperature"] = "abc"
    cases.append(("非数字", {"modelKey": "xgb_amount", "inputs": not_a_number}))

    cases.append(("模型不存在", {"modelKey": "no_such_model", "inputs": good}))

    for name, payload in cases:
        status, body = post_json("/api/predict", payload)
        rejected = (status == 400 and not body.get("ok") and body.get("error"))
        print("  %-10s → HTTP %s %s" % (name, status,
              ("已拦截：" + body.get("error", ""))[:70] if rejected else "未拦截！"))
        if not rejected:
            failures.append("异常输入未被正确拒绝：%s → %s" % (name, body))


def main():
    with open(SAMPLES_JSON, "r", encoding="utf-8") as fh:
        samples = json.load(fh)
    print("示例样本 %d 条，服务地址 %s" % (len(samples), BASE_URL))

    failures = []

    status, health = get_json("/api/health")
    print("\n=== 0. 健康检查 ===")
    for item in health["models"]:
        print("  %-18s %s" % (item["key"], "已装载" if item["loaded"] else "未装载"))
        if not item["loaded"]:
            failures.append("模型未装载：%s" % item["key"])

    worst = check_predictions(samples, failures)
    check_compare(samples, failures)
    check_rejections(samples, failures)

    print("\n" + "=" * 68)
    if failures:
        print("测试未通过，%d 项问题：" % len(failures))
        for item in failures:
            print("  ✗ %s" % item)
        return 1
    print("全部测试通过：接口数值与直连模型一致（最大偏差 %.3g）" % worst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
