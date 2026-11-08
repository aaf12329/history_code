# -*- coding: utf-8 -*-
"""离线预测服务入口（Flask）。

主题
    磺胺类抗生素在生物炭上吸附性能的本地网页预测器。
    JS 只负责页面交互与结果展示，模型加载、特征工程、标准化、预测全部在 Python 侧完成。

任务
    启动本地 HTTP 服务，对外提供：
        GET  /                页面
        GET  /api/meta        表单与模型元信息（前端据此渲染界面）
        POST /api/predict     单条预测（指定模型）
        POST /api/compare     同一输入下多模型横向对比
        GET  /api/health      健康检查（已装载哪些模型）
    浏览器只与本机通信，不向外发送任何数据。

结构（单文件三段式）
    ① 应用装配    创建 Flask 应用、注册静态目录
    ② 接口实现    各路由的处理函数（只做编排，细节在 backend/ 各层）
    ③ 主流程      main：装载模型 → 启动服务 → 打开浏览器

调用树
    main
    ├── model_store.warm_up            （预装载模型，只执行一次）
    ├── open_browser                   （只执行一次）
    └── app.run                        （进入请求循环；以下由 Flask 框架调用）
        ├── api_meta                   → dataset_meta.*, model_registry.*
        ├── api_predict                → features.build_row → model_store.predict
        ├── api_compare                → features.build_row → model_store.predict（逐模型）
        └── api_health                 → model_store.loaded_keys

数据流
    表单 JSON → features.build_row → (1, n_features) 矩阵
        → model_store.predict（按需标准化）→ 预测值 → 页面

依赖
    flask, joblib, numpy, pandas, scikit-learn, xgboost, catboost
    运行：python app.py        （或双击 start.bat）
"""

import argparse
import json
import os
import sys
import threading
import webbrowser

from flask import Flask, jsonify, request, send_from_directory

from backend import dataset_meta
from backend import features
from backend import model_registry as registry
from backend import model_store
from backend import paths

# ============================================================================
# ① 应用装配
# ============================================================================

app = Flask(__name__, static_folder=paths.FRONTEND_DIR, static_url_path="")
app.config["JSON_AS_ASCII"] = False
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0      # 本地开发，禁用静态缓存便于改样式


# ============================================================================
# ② 接口实现
# ============================================================================

@app.route("/")
def index():
    """返回单页界面。"""
    return send_from_directory(paths.FRONTEND_DIR, "index.html")


@app.route("/api/meta")
def api_meta():
    """表单与模型元信息：前端据此渲染下拉框、滑块范围与模型说明。"""
    field_meta = dataset_meta.load_field_meta()

    models = []
    for spec in registry.MODELS:
        target = registry.TARGETS[spec["target"]]
        feature_set = registry.FEATURE_SETS[spec["featureSet"]]
        models.append({
            "key": spec["key"],
            "label": spec["label"],
            "family": spec["family"],
            "target": spec["target"],
            "targetLabel": target["label"],
            "targetUnit": target["unit"],
            "featureSet": spec["featureSet"],
            "featureSetLabel": feature_set["label"],
            "featureSetShort": feature_set["short"],
            "nFeatures": len(feature_set["columns"]),
            "needsScaling": spec["scalerFile"] is not None,
            "isDefault": bool(spec.get("isDefault", False)),
            "metrics": spec["metrics"],
            "note": spec.get("note"),
        })

    limits = dataset_meta.field_limits()
    fields = {}
    for name, info in field_meta.get("fields", {}).items():
        entry = dict(info)
        if name in limits:
            # acceptLow/acceptHigh 是后端真正接受的区间，用于输入框的 min/max；
            # min/max 仍是数据集实际范围，作为填写参考展示在字段下方。
            entry["acceptLow"] = limits[name][0]
            entry["acceptHigh"] = limits[name][1]
        fields[name] = entry

    return jsonify({
        "ok": True,
        "source": field_meta.get("source"),
        "targets": registry.TARGETS,
        "featureSets": registry.FEATURE_SETS,
        "models": models,
        "fields": fields,
        "groups": field_meta.get("groups", {}),
        "pollutants": field_meta.get("pollutants", []),
        "descriptorsConstant": dataset_meta.descriptor_is_constant(),
        "molecularDescriptors": registry.MOLECULAR_DESCRIPTORS,
        "typical": dataset_meta.typical_values(),
        "samples": dataset_meta.load_samples(),
    })


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """单条预测：接收原始表单值，返回预测值与模型实际输入。"""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "请求体必须是 JSON 对象"}), 400

    model_key = payload.get("modelKey")
    spec = registry.MODELS_BY_KEY.get(model_key)
    if spec is None:
        return jsonify({"ok": False,
                        "error": "未知模型 %r，可选：%s"
                                 % (model_key, "、".join(registry.MODELS_BY_KEY))}), 400

    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        return jsonify({"ok": False, "error": "缺少 inputs 字段或格式不是对象"}), 400

    try:
        row, cleaned = features.build_row(spec, inputs, dataset_meta.field_limits())
        result = model_store.predict(spec, row)
    except features.InputError as exc:
        # 面向使用者的可修正提示：直接说明哪个字段不对
        return jsonify({"ok": False, "error": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({"ok": False,
                        "error": "模型文件缺失：%s。请确认 models/ 目录完整。" % exc}), 500
    except Exception as exc:  # noqa: BLE001 - 兜住意外错误，避免页面拿到空白响应
        return jsonify({"ok": False,
                        "error": "预测失败（%s）：%s" % (type(exc).__name__, exc)}), 500

    target = registry.TARGETS[spec["target"]]
    feature_set = registry.FEATURE_SETS[spec["featureSet"]]
    return jsonify({
        "ok": True,
        "modelKey": spec["key"],
        "modelLabel": spec["label"],
        "target": spec["target"],
        "targetLabel": target["label"],
        "unit": target["unit"],
        "prediction": result["prediction"],
        "standardized": result["scaled"],
        "metrics": spec["metrics"],
        "featureSetLabel": feature_set["label"],
        "featureRow": features.describe_feature_row(spec, inputs, dataset_meta.field_limits()),
        "inputs": cleaned,
    })


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """同一份输入下，用某个目标的所有可用模型各预测一次，供页面横向对比。"""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "请求体必须是 JSON 对象"}), 400

    target = payload.get("target")
    if target not in registry.TARGETS:
        return jsonify({"ok": False,
                        "error": "target 必须是 amount 或 capacity"}), 400

    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        return jsonify({"ok": False, "error": "缺少 inputs 字段或格式不是对象"}), 400

    results = []
    for spec in registry.models_for_target(target):
        item = {
            "modelKey": spec["key"], "label": spec["label"], "family": spec["family"],
            "featureSetLabel": registry.FEATURE_SETS[spec["featureSet"]]["label"],
            "featureSetShort": registry.FEATURE_SETS[spec["featureSet"]]["short"],
            "metrics": spec["metrics"],
        }
        try:
            row, _ = features.build_row(spec, inputs, dataset_meta.field_limits())
            item["prediction"] = model_store.predict(spec, row)["prediction"]
            item["ok"] = True
        except features.InputError as exc:
            item["ok"] = False
            item["error"] = str(exc)
        except Exception as exc:  # noqa: BLE001 - 单个模型失败不影响其余对比
            item["ok"] = False
            item["error"] = "%s: %s" % (type(exc).__name__, exc)
        results.append(item)

    usable = [r for r in results if r["ok"]]
    spread = None
    if len(usable) >= 2:
        values = [r["prediction"] for r in usable]
        spread = {"min": min(values), "max": max(values),
                  "range": max(values) - min(values)}

    return jsonify({
        "ok": True,
        "target": target,
        "targetLabel": registry.TARGETS[target]["label"],
        "unit": registry.TARGETS[target]["unit"],
        "results": results,
        "spread": spread,
    })


@app.route("/api/health")
def api_health():
    """健康检查：报告各模型是否已成功装载。"""
    loaded = set(model_store.loaded_keys())
    return jsonify({
        "ok": True,
        "models": [{"key": spec["key"], "loaded": spec["key"] in loaded}
                   for spec in registry.MODELS],
    })


@app.errorhandler(404)
def handle_404(_err):
    """未命中的路径给出可读提示（本地服务常见于手输地址打错）。"""
    return jsonify({"ok": False, "error": "路径不存在"}), 404


# ============================================================================
# ③ 主流程
# ============================================================================

def open_browser(url, delay=1.2):
    """延迟打开浏览器：等服务工作线程起来再跳转。"""
    def _open():
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - 打不开浏览器不影响服务本身
            pass
    timer = threading.Timer(delay, _open)
    timer.daemon = True
    timer.start()


def main(argv=None):
    parser = argparse.ArgumentParser(description="生物炭吸附性能离线预测服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认仅本机）")
    parser.add_argument("--port", type=int, default=8765, help="监听端口（默认 8765）")
    parser.add_argument("--no-browser", action="store_true", help="启动后不自动打开浏览器")
    parser.add_argument("--debug", action="store_true", help="开启 Flask 调试模式")
    args = parser.parse_args(argv)

    print("=" * 68)
    print("生物炭吸附性能预测器 · 本地服务")
    print("=" * 68)

    for path, label in ((paths.FIELD_META_JSON, "字段元数据"),
                        (paths.SAMPLES_JSON, "示例样本")):
        if not os.path.exists(path):
            print("提示：%s 不存在（%s），请先运行 build/ 下的生成脚本。" % (label, path))

    print("\n正在装载模型 ...")
    report = model_store.warm_up()
    for item in report:
        flag = "✓" if item["ok"] else "✗"
        spec = registry.MODELS_BY_KEY[item["key"]]
        print("  %s %-18s %-22s %s" % (flag, item["key"], spec["label"], item["detail"]))

    failed = [item for item in report if not item["ok"]]
    if failed:
        print("\n有 %d 个模型装载失败，页面仍会启动，但对应模型不可用。" % len(failed))

    url = "http://%s:%d/" % (args.host, args.port)
    print("\n服务地址：%s" % url)
    print("按 Ctrl+C 停止服务\n")

    if not args.no_browser:
        open_browser(url)

    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
