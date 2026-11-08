# -*- coding: utf-8 -*-
"""特征层：把用户填写的原始量转换为模型输入的那一行特征。

职责
    校验表单输入，推导元素比值，做污染物独热编码，
    再按目标模型声明的列顺序排成一行特征向量。

被谁调用
    app（入口层编排时调用；本模块不调用其他功能层模块）
调用谁
    backend.model_registry（共用层）

特征集差异
    A25：直接用 C/H/O/N 原始质量分数，污染物展开为 7 个哑变量
    B19：用 H/C、N/C、O/C、O+N/C 取代原始 C/H/O/N，保留 pKa1，不含哑变量
    两套特征集都由同一份表单输入推出，用户无需切换填写方式。

关于取值范围
    本模块不内置数值上下界，而是由调用方把 limits 传进来。
    范围来自数据实际统计（backend.dataset_meta.field_limits），
    这样常量不会与数据集脱节——初版写死过 Dp 上界 100，而数据实际到 256.4。
"""

import numpy as np

from backend import model_registry as registry


class InputError(ValueError):
    """表单输入不合法。消息面向使用者，直接展示在页面上。"""


def validate_inputs(inputs, limits):
    """校验表单输入，返回规整后的字典；不合法时抛 InputError。

    参数
        inputs: dict，含 "Pollutant" 与 BASE_NUMERIC_FIELDS 中的数值字段
        limits: {字段: (下界, 上界)}，来自 dataset_meta.field_limits()
    返回
        dict，键同输入，值为 float（Pollutant 仍为字符串）
    """
    if not isinstance(inputs, dict):
        raise InputError("请求体必须是 JSON 对象")

    pollutant = inputs.get("Pollutant")
    if pollutant not in registry.POLLUTANTS:
        raise InputError("污染物取值不合法：%r，应为 %s 之一"
                         % (pollutant, "、".join(registry.POLLUTANTS)))

    cleaned = {"Pollutant": pollutant}
    problems = []
    for field in registry.BASE_NUMERIC_FIELDS:
        raw = inputs.get(field)
        if raw is None or raw == "":
            problems.append("%s 未填写" % field)
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            problems.append("%s 不是有效数字：%r" % (field, raw))
            continue
        if not np.isfinite(value):
            problems.append("%s 不是有限数值" % field)
            continue
        bound = limits.get(field)
        if bound and (value < bound[0] or value > bound[1]):
            problems.append("%s = %g 超出可接受范围 [%.4g, %.4g]"
                            % (field, value, bound[0], bound[1]))
            continue
        cleaned[field] = value

    if problems:
        raise InputError("；".join(problems))
    return cleaned


def derive_values(cleaned):
    """在基础字段之上推导出元素比值与污染物哑变量。

    参数
        cleaned: validate_inputs 的返回值
    返回
        dict，可直接按列名取值
    """
    values = dict(cleaned)

    # 元素比值（论文 Fig.S11 口径）；C 已在校验阶段保证为正数
    c = values["C"]
    values["H/C"] = values["H"] / c
    values["N/C"] = values["N"] / c
    values["O/C"] = values["O"] / c
    values["O+N/C"] = (values["O"] + values["N"]) / c

    # 污染物独热编码：与训练时 pd.get_dummies 展开出的 7 列一致
    for name in registry.POLLUTANTS:
        values["Pollutant_" + name] = 1.0 if name == cleaned["Pollutant"] else 0.0

    return values


def build_row(spec, inputs, limits):
    """把表单输入排成目标模型需要的 (1, n_features) 特征矩阵。

    参数
        spec: model_registry.MODELS 中的一条
        inputs: 原始表单输入
        limits: {字段: (下界, 上界)}，来自 dataset_meta.field_limits()
    返回
        (numpy.ndarray 形状 (1, n_features), 规整后的输入字典)
    """
    cleaned = validate_inputs(inputs, limits)
    values = derive_values(cleaned)

    columns = registry.FEATURE_SETS[spec["featureSet"]]["columns"]
    missing = [c for c in columns if c not in values]
    if missing:
        raise InputError("特征集 %s 缺少可推导的列：%s" % (spec["featureSet"], missing))

    row = np.array([[values[c] for c in columns]], dtype="float64")
    return row, cleaned


def describe_feature_row(spec, inputs, limits):
    """返回特征行的可读明细，供页面「查看模型实际输入」用。"""
    cleaned = validate_inputs(inputs, limits)
    values = derive_values(cleaned)
    columns = registry.FEATURE_SETS[spec["featureSet"]]["columns"]
    return [{"name": c, "value": float(values[c])} for c in columns]
