# -*- coding: utf-8 -*-
"""数据集元信息层：读取表单所需的字段元数据与示例样本。

职责
    包装 frontend/field_meta.json 与 frontend/samples.json 的读取，
    提供「污染物 → 分子描述符」的查表能力。

被谁调用
    app（入口层编排时调用；本模块不调用其他功能层模块）
调用谁
    backend.paths（共用层）

两个 JSON 由 build/make_field_meta.py 与 build/make_samples.py 离线生成，
运行期不重新统计数据集，保证页面启动即可用。
"""

import json

from backend import model_registry as registry
from backend import paths

_FIELD_META = None
_SAMPLES = None

# 数据范围向外放宽的比例：留出合理外推空间，同时仍能挡住明显的输入笔误
HEADROOM_RATIO = 0.5


def load_field_meta():
    """读取并缓存字段元数据（字段范围、典型值、污染物描述符）。"""
    global _FIELD_META
    if _FIELD_META is None:
        with open(paths.FIELD_META_JSON, "r", encoding="utf-8") as fh:
            _FIELD_META = json.load(fh)
    return _FIELD_META


def load_samples():
    """读取并缓存示例样本；文件缺失时返回空列表而不是报错。"""
    global _SAMPLES
    if _SAMPLES is None:
        try:
            with open(paths.SAMPLES_JSON, "r", encoding="utf-8") as fh:
                _SAMPLES = json.load(fh)
        except FileNotFoundError:
            _SAMPLES = []
    return _SAMPLES


def pollutant_descriptors():
    """返回 {污染物名: {描述符: 取值}}，供前端选完污染物后自动带出。"""
    meta = load_field_meta()
    return {entry["name"]: entry["descriptors"] for entry in meta.get("pollutants", [])}


def descriptor_is_constant():
    """分子描述符是否对每种污染物都唯一确定（决定前端能否自动填充）。"""
    return bool(load_field_meta().get("allDescriptorsConstant", False))


def typical_values():
    """返回 {字段: 中位数}，供页面「填充典型值」按钮使用。"""
    meta = load_field_meta()
    return {name: info["median"] for name, info in meta.get("fields", {}).items()
            if "median" in info}


def field_limits():
    """返回 {字段: (下界, 上界)}，由数据实际范围推出并与物理边界取交集。

    为什么不在代码里写死
        初版把每个字段的上下界写成常量，结果平均孔径 Dp 的上界写成了 100，
        而数据实际到 256.4，导致全部真实记录都被判为越界。
        改为由 field_meta.json（离线统计产物）推导，常量与数据不会再脱节。

    规则
        以数据 [min, max] 为中心向外放宽 HEADROOM_RATIO 倍跨度；
        非负字段下界抬到 0；有定义域的字段与 FIELD_HARD_BOUNDS 取交集。
    """
    meta = load_field_meta()
    limits = {}
    for name, info in meta.get("fields", {}).items():
        low, high = info.get("min"), info.get("max")
        if low is None or high is None:
            continue
        span = float(high) - float(low)
        if span <= 0:
            span = abs(float(high)) * 0.5 + 1.0
        low = float(low) - HEADROOM_RATIO * span
        high = float(high) + HEADROOM_RATIO * span

        if name in registry.NON_NEGATIVE_FIELDS:
            low = max(low, 0.0)

        hard_low, hard_high = registry.FIELD_HARD_BOUNDS.get(name, (None, None))
        if hard_low is not None:
            low = max(low, hard_low)
        if hard_high is not None:
            high = min(high, hard_high)

        limits[name] = (low, high)
    return limits
