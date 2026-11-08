# -*- coding: utf-8 -*-
"""生成网页表单所需的字段元数据，并核对「分子描述符是否只由污染物决定」。

主题
    表单输入契约：确定用户需要手填哪些字段、哪些可由污染物种类自动带出，
    以及每个数值字段的合理取值范围与典型值。

任务
    读 Dataset.csv，产出 frontend/field_meta.json：
      - pollutants : 7 种磺胺，各自的分子描述符（若逐个核对为常数则标记 constant）
      - fields     : 生物炭性质与吸附条件字段的 min / max / 中位数 / 分位数 / 单位 / 说明
      - targets    : 两个目标变量的取值分布

结构
    ① 常量区    ：路径、字段分组、单位与说明
    ② 描述符核对：按污染物分组统计，判断是否常数
    ③ 数值字段  ：分位数统计，供前端滑块与「填充典型值」使用
    ④ 出口 main ：写 field_meta.json

调用树
    main
    ├── inspect_pollutant_descriptors    （描述符是否只与污染物有关）
    ├── summarize_numeric_fields         （数值字段分布）
    └── write_meta                       （输出）

数据流
    Dataset.csv → 分组统计 → field_meta.json → 前端表单默认值 / 取值范围
"""

import json
import os
import sys

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
DATASET_CSV = os.path.join(SOURCE_PROJECT, "Dataset.csv")
OUT_JSON = os.path.join(WEB_DIR, "frontend", "field_meta.json")

# 分子描述符：理论上由污染物分子结构决定，与实验条件无关
DESCRIPTOR_FIELDS = ["MW", "Kow", "pKa1", "E", "S", "A", "B", "V"]

# 生物炭性质
BIOCHAR_FIELDS = {
    "SBET": {"label": "比表面积 SBET", "unit": "m²/g", "desc": "生物炭的 BET 比表面积"},
    "VTotal": {"label": "总孔容 VTotal", "unit": "cm³/g", "desc": "总孔体积"},
    "Dp": {"label": "平均孔径 Dp", "unit": "nm", "desc": "平均孔径"},
    "C": {"label": "碳含量 C", "unit": "%", "desc": "元素分析碳质量分数"},
    "H": {"label": "氢含量 H", "unit": "%", "desc": "元素分析氢质量分数"},
    "O": {"label": "氧含量 O", "unit": "%", "desc": "元素分析氧质量分数"},
    "N": {"label": "氮含量 N", "unit": "%", "desc": "元素分析氮质量分数"},
}

# 吸附条件
CONDITION_FIELDS = {
    "Dosage": {"label": "投加量 Dosage", "unit": "g/L", "desc": "吸附剂投加浓度"},
    "Initial concentration": {"label": "初始浓度", "unit": "mg/L", "desc": "污染物初始质量浓度"},
    "Temperature": {"label": "温度", "unit": "K", "desc": "实验温度（开尔文）"},
    "Initial pH": {"label": "初始 pH", "unit": "—", "desc": "溶液初始酸碱度"},
}

TARGET_FIELDS = {
    "Adsorption amount": {"key": "amount", "label": "吸附量 Adsorption amount",
                          "unit": "mg/g", "desc": "单位质量吸附剂吸附的污染物质量"},
    "Adsorption capacity": {"key": "capacity", "label": "吸附容量 Adsorption capacity",
                            "unit": "mg/g", "desc": "吸附剂对污染物的饱和吸附容量"},
}


# ============================================================================
# ② 描述符核对
# ============================================================================

def inspect_pollutant_descriptors(df):
    """按污染物分组统计分子描述符，判断是否每种污染物只有唯一取值。

    返回 list，每项为一种污染物及其描述符取值与是否常数。
    """
    result = []
    for name, group in df.groupby("Pollutant", sort=True):
        entry = {"name": str(name), "nRecords": int(len(group)), "descriptors": {}}
        all_constant = True
        for field in DESCRIPTOR_FIELDS:
            if field not in group.columns:
                continue
            values = group[field].dropna().unique()
            if len(values) == 1:
                entry["descriptors"][field] = float(values[0])
            elif len(values) == 0:
                entry["descriptors"][field] = None
            else:
                # 该描述符在同一污染物下并不唯一，只能给中位数并标记
                all_constant = False
                entry["descriptors"][field] = float(np.median(group[field].dropna()))
        entry["descriptorsConstant"] = all_constant
        result.append(entry)
    return result


# ============================================================================
# ③ 数值字段
# ============================================================================

def summarize_numeric_fields(df, field_map):
    """统计数值字段的分布，供前端设置输入范围与「填充典型值」。"""
    summary = {}
    for field, meta in field_map.items():
        if field not in df.columns:
            continue
        values = pd.to_numeric(df[field], errors="coerce").dropna()
        if values.empty:
            continue
        summary[field] = {
            "label": meta["label"],
            "unit": meta["unit"],
            "desc": meta["desc"],
            "min": float(values.min()),
            "max": float(values.max()),
            "p05": float(np.percentile(values, 5)),
            "p25": float(np.percentile(values, 25)),
            "median": float(np.median(values)),
            "p75": float(np.percentile(values, 75)),
            "p95": float(np.percentile(values, 95)),
            "mean": float(values.mean()),
            "nValid": int(values.size),
            "nMissing": int(len(df) - values.size),
        }
    return summary


def summarize_targets(df):
    out = {}
    for field, meta in TARGET_FIELDS.items():
        if field not in df.columns:
            continue
        values = pd.to_numeric(df[field], errors="coerce").dropna()
        out[meta["key"]] = {
            "column": field, "label": meta["label"], "unit": meta["unit"],
            "desc": meta["desc"],
            "min": float(values.min()), "max": float(values.max()),
            "median": float(np.median(values)),
            "mean": float(values.mean()),
            "nValid": int(values.size),
        }
    return out


# ============================================================================
# ④ 出口 main
# ============================================================================

def write_meta(payload, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return os.path.getsize(path) / 1024.0


def main():
    df = pd.read_csv(DATASET_CSV)
    print("数据集: %d 行 × %d 列" % df.shape)

    pollutants = inspect_pollutant_descriptors(df)
    print("\n=== 分子描述符按污染物核对 ===")
    print("%-24s %-8s %s" % ("污染物", "记录数", "描述符是否唯一确定"))
    for entry in pollutants:
        print("%-24s %-8d %s" % (entry["name"], entry["nRecords"],
                                 "是（可自动带出）" if entry["descriptorsConstant"]
                                 else "否（存在多值，取中位数）"))
        if not entry["descriptorsConstant"]:
            for field in DESCRIPTOR_FIELDS:
                sub = df[df["Pollutant"] == entry["name"]][field].dropna().unique()
                if len(sub) > 1:
                    print("      %s 有 %d 个不同取值: %s" % (field, len(sub), np.round(sub[:5], 4)))

    combined_fields = {}
    combined_fields.update(BIOCHAR_FIELDS)
    combined_fields.update(CONDITION_FIELDS)
    name_to_desc = {
        "MW": ("分子量 MW", "g/mol"), "Kow": ("辛醇-水分配系数 Kow", "—"),
        "pKa1": ("一级解离常数 pKa1", "—"), "E": ("分子描述符 E", "—"),
        "S": ("分子描述符 S", "—"), "A": ("分子描述符 A", "—"),
        "B": ("分子描述符 B", "—"), "V": ("分子描述符 V", "—"),
    }
    for field, (label, unit) in name_to_desc.items():
        combined_fields[field] = {"label": label, "unit": unit, "desc": "污染物分子固有描述符"}

    fields = summarize_numeric_fields(df, combined_fields)
    targets = summarize_targets(df)

    payload = {
        "source": "Dataset.csv (%d 行 × %d 列)" % df.shape,
        "pollutantColumn": "Pollutant",
        "descriptorFields": DESCRIPTOR_FIELDS,
        "pollutants": pollutants,
        "allDescriptorsConstant": all(e["descriptorsConstant"] for e in pollutants),
        "groups": {
            "pollutant": {"label": "污染物", "fields": DESCRIPTOR_FIELDS},
            "biochar": {"label": "生物炭性质", "fields": list(BIOCHAR_FIELDS.keys())},
            "condition": {"label": "吸附条件", "fields": list(CONDITION_FIELDS.keys())},
        },
        "fields": fields,
        "targets": targets,
    }

    size_kb = write_meta(payload, OUT_JSON)
    print("\n已写 %s (%.1f KB)" % (OUT_JSON, size_kb))
    print("全部描述符均可由污染物唯一确定: %s" % payload["allDescriptorsConstant"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
