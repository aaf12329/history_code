# -*- coding: utf-8 -*-
"""生成页面示例样本（frontend/samples.json）。

主题
    演示用真实案例：让访问者一键载入一条真实实验记录，
    把模型的预测值与实测值并排对照，而不是只看一个孤立数字。

任务
    从 Dataset.csv 中为 7 种污染物各选一条代表性记录：
    取该污染物「吸附量」最接近其中位数的那条，避免挑到极端值造成误解。
    导出原始表单输入与两个目标的实测值。

结构
    ① 常量区   ：路径、字段清单
    ② 选样     ：按污染物分组，取中位样本
    ③ 出口 main：写 samples.json

调用树
    main
    ├── pick_representative   （准备：按污染物取中位样本）
    └── write_samples         （输出）

数据流
    Dataset.csv → 分组 → 每污染物一条 → samples.json → 页面「载入示例」
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
OUT_JSON = os.path.join(WEB_DIR, "frontend", "samples.json")

# 表单需要的原始输入字段
INPUT_FIELDS = ["SBET", "VTotal", "Dp", "C", "H", "O", "N",
                "Dosage", "Initial concentration", "Temperature", "Initial pH",
                "MW", "Kow", "pKa1", "E", "S", "A", "B", "V"]

TARGETS = {"amount": "Adsorption amount", "capacity": "Adsorption capacity"}


# ============================================================================
# ② 选样
# ============================================================================

def pick_representative(df):
    """每种污染物取一条吸附量最接近组内中位数的记录。"""
    picked = []
    for name, group in df.groupby("Pollutant", sort=True):
        valid = group.dropna(subset=list(TARGETS.values()))
        if valid.empty:
            continue
        median = valid["Adsorption amount"].median()
        row = valid.iloc[(valid["Adsorption amount"] - median).abs().argsort().iloc[0]]

        inputs = {"Pollutant": str(name)}
        for field in INPUT_FIELDS:
            raw = row.get(field)
            inputs[field] = None if pd.isna(raw) else round(float(raw), 6)

        missing = [c for c, v in inputs.items() if v is None]
        picked.append({
            "id": "%s · 组内中位样本" % name,
            "pollutant": str(name),
            "nRecordsInGroup": int(len(group)),
            "inputs": inputs,
            "missingFields": missing,
            "truth": {key: (None if pd.isna(row[col]) else round(float(row[col]), 4))
                      for key, col in TARGETS.items()},
        })
    return picked


# ============================================================================
# ③ 出口 main
# ============================================================================

def write_samples(payload, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return os.path.getsize(path) / 1024.0


def main():
    df = pd.read_csv(DATASET_CSV)
    samples = pick_representative(df)

    print("数据集: %d 行" % len(df))
    print("\n%-24s %-8s %-12s %-12s %s"
          % ("污染物", "组内条数", "实测吸附量", "实测吸附容量", "缺失字段"))
    for item in samples:
        print("%-24s %-8d %-12s %-12s %s"
              % (item["pollutant"], item["nRecordsInGroup"],
                 item["truth"]["amount"], item["truth"]["capacity"],
                 "、".join(item["missingFields"]) or "无"))

    size_kb = write_samples(samples, OUT_JSON)
    print("\n已写 %s（%d 条示例，%.1f KB）" % (OUT_JSON, len(samples), size_kb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
