# -*- coding: utf-8 -*-
"""模型层：加载 joblib 模型与标准化器，并执行一次预测。

职责
    按模型登记信息从磁盘装载模型/标准化器（首次装载后缓存），
    依据该模型训练时是否做过标准化，决定预测前要不要 transform。

被谁调用
    app（入口层编排时调用；本模块不调用其他功能层模块）
调用谁
    backend.paths, backend.model_registry（共用层）

为什么缓存
    模型文件合计约 9 MB，每次请求都重新 joblib.load 会让页面明显变慢；
    joblib.load 是只读操作，进程内复用同一对象是安全的。
"""

import threading

import joblib
import numpy as np

from backend import model_registry as registry
from backend import paths

# key -> {"model": ..., "scaler": ...}
_CACHE = {}
_LOCK = threading.Lock()


def load_model(spec):
    """装载并缓存一个模型条目，返回 (model, scaler 或 None)。"""
    key = spec["key"]
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]["model"], _CACHE[key]["scaler"]

        model = joblib.load(paths.model_path(spec["modelFile"]))
        scaler = None
        if spec["scalerFile"]:
            scaler = joblib.load(paths.model_path(spec["scalerFile"]))

        _CACHE[key] = {"model": model, "scaler": scaler}
        return model, scaler


def warm_up():
    """启动时预装载全部模型，把首次请求的等待时间挪到启动阶段。

    返回 list，每项为 {"key", "ok", "detail"}；装载失败不抛出，
    由调用方决定如何提示（避免一个坏模型拖垮整个服务）。
    """
    report = []
    for spec in registry.MODELS:
        try:
            load_model(spec)
            report.append({"key": spec["key"], "ok": True, "detail": "已装载"})
        except Exception as exc:  # noqa: BLE001 - 单个模型失败不能中断启动
            report.append({"key": spec["key"], "ok": False,
                           "detail": "%s: %s" % (type(exc).__name__, exc)})
    return report


def predict(spec, feature_row):
    """对一行特征做预测。

    参数
        spec: model_registry.MODELS 中的一条
        feature_row: numpy 数组，形状 (1, n_features)，列顺序与特征集一致
    返回
        {"prediction": float, "scaled": bool}
    """
    model, scaler = load_model(spec)

    if feature_row.shape[1] != len(registry.FEATURE_SETS[spec["featureSet"]]["columns"]):
        raise ValueError("特征维数与模型登记不一致：输入 %d 列，登记 %d 列"
                         % (feature_row.shape[1],
                            len(registry.FEATURE_SETS[spec["featureSet"]]["columns"])))

    payload = scaler.transform(feature_row) if scaler is not None else feature_row
    raw = np.asarray(model.predict(payload), dtype="float64").ravel()
    if raw.size != 1:
        raise ValueError("模型返回了 %d 个预测值，预期 1 个" % raw.size)

    return {"prediction": float(raw[0]), "scaled": scaler is not None}


def loaded_keys():
    """返回当前已缓存的模型 key，供健康检查接口使用。"""
    return sorted(_CACHE.keys())
