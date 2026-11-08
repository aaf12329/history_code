# -*- coding: utf-8 -*-
"""路径地址簿（Store 模式）。

职责
    全项目的文件与目录位置集中登记在此，且只登记、不做读写。
    其它模块一律从这里取路径，禁止自行拼接。

被谁调用
    backend.features, backend.predictor, backend.dataset_meta, app
调用谁
    无（只依赖标准库，是依赖方向的最底层）

新增产物（模型、元数据、静态资源）时，先在此登记再使用。
"""

import os

# --- 目录 ---
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BACKEND_DIR)              # 项目根目录

MODELS_DIR = os.path.join(BASE_DIR, "models")          # 模型与原始数据
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")      # 页面资源
BUILD_DIR = os.path.join(BASE_DIR, "build")            # 离线构建脚本

# --- 文件 ---
DATASET_CSV = os.path.join(MODELS_DIR, "Dataset.csv")
FIELD_META_JSON = os.path.join(FRONTEND_DIR, "field_meta.json")
SAMPLES_JSON = os.path.join(FRONTEND_DIR, "samples.json")
INDEX_HTML = os.path.join(FRONTEND_DIR, "index.html")


def model_path(filename):
    """返回 models/ 下某个文件的完整路径。"""
    return os.path.join(MODELS_DIR, filename)
