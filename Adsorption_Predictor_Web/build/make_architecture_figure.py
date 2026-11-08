# -*- coding: utf-8 -*-
"""生成架构与调用关系图（PNG），供结课报告直接引用。

主题
    README 里的调用关系用 Mermaid 书写，在 GitHub 上能渲染，但放进 Word 报告就失效。
    本脚本把同一套结构画成 PNG，任何编辑器都能看。

任务
    绘制两张图到 docs/figures/：
      1. 架构分层与调用关系：三个入口、运行期四层、第三方依赖
      2. 一次预测的数据流：表单输入 → 特征推导 → 标准化 → 模型 → 结果
    图中文字与实际模块名严格一致，不出现代码里没有的名字。

结构
    ① 常量区   ：输出路径、配色、字体
    ② 绘图工具 ：方框、箭头、分层底纹
    ③ 图一     ：架构分层与调用关系
    ④ 图二     ：一次预测的数据流
    ⑤ 出口 main：逐张绘制并保存

调用树
    main
    ├── draw_architecture     （图一）
    └── draw_dataflow         （图二）

数据流
    代码结构 → 坐标布局 → matplotlib 图形 → PNG 文件
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                               # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

# ============================================================================
# ① 常量区
# ============================================================================

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(BUILD_DIR)
OUT_DIR = os.path.join(WEB_DIR, "docs", "figures")

# 配色（与网页界面同一套色系）
C_ENTRY = "#dbeafe"      # 入口层
C_FUNC = "#dcfce7"       # 功能层
C_COMMON = "#fef3c7"     # 共用层
C_EXT = "#f1f5f9"        # 第三方 / 外部
C_EDGE = "#334155"
C_ENTRY_EDGE = "#2563eb"
C_FUNC_EDGE = "#0f9d58"
C_COMMON_EDGE = "#b45309"

FONT_CANDIDATES = ["Microsoft YaHei", "SimHei", "DengXian", "SimSun"]


def setup_font():
    """挑一个可用的中文字体，否则图上中文会变成方框。"""
    from matplotlib import font_manager
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in FONT_CANDIDATES:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    plt.rcParams["axes.unicode_minus"] = False
    return None


# ============================================================================
# ② 绘图工具
# ============================================================================

def box(ax, x, y, w, h, text, face, edge, fontsize=9, bold=False, radius=0.6):
    """画一个圆角方框并写居中文字。"""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=%s" % radius,
        linewidth=1.3, facecolor=face, edgecolor=edge, zorder=2))
    ax.text(x + w / 2.0, y + h / 2.0, text,
            ha="center", va="center", fontsize=fontsize, zorder=3,
            fontweight="bold" if bold else "normal", linespacing=1.5)


def arrow(ax, xy_from, xy_to, label=None, style="-|>", color=C_EDGE,
          lw=1.2, rad=0.0, fontsize=8, label_offset=(0, 0), dashed=False):
    """画一条箭头，可选在中间标文字。"""
    ax.add_patch(FancyArrowPatch(
        xy_from, xy_to, arrowstyle=style, mutation_scale=11,
        linewidth=lw, color=color, zorder=1,
        linestyle="--" if dashed else "-",
        connectionstyle="arc3,rad=%s" % rad))
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2.0 + label_offset[0]
        my = (xy_from[1] + xy_to[1]) / 2.0 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=fontsize,
                color=color, zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))


def band(ax, x, y, w, h, label):
    """画一层背景底纹，左侧标注层名。"""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
        linewidth=0.8, facecolor="#fafbfd", edgecolor="#dbe2ea",
        linestyle="--", zorder=0))
    ax.text(x + 0.8, y + h - 1.2, label, ha="left", va="top",
            fontsize=9, color="#64748b", fontweight="bold", zorder=1)


def blank_axes(width=13.0, height=9.2):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


# ============================================================================
# ③ 图一：架构分层与调用关系
# ============================================================================

def draw_architecture(path):
    fig, ax = blank_axes(13.5, 9.6)

    # --- 使用者 ---
    box(ax, 40, 92, 20, 6, "使用者", "#e2e8f0", "#94a3b8", fontsize=11, bold=True)

    # --- ① 部署链路（三个入口）---
    box(ax, 6, 80, 22, 6.5, "deploy.bat\n装环境（只需一次）", C_ENTRY, C_ENTRY_EDGE, fontsize=9)
    box(ax, 36, 80, 22, 6.5, "start.bat\n启动服务", C_ENTRY, C_ENTRY_EDGE, fontsize=9)
    box(ax, 66, 80, 26, 6.5, "build/*.py\n可选：复现与校验", C_EXT, "#94a3b8", fontsize=9)
    arrow(ax, (46, 92), (17, 86.5), "①", fontsize=9)
    arrow(ax, (50, 92), (47, 86.5), "②", fontsize=9)
    arrow(ax, (58, 92), (79, 86.5), "③", fontsize=9)

    box(ax, 10, 71.5, 24, 5.5, ".venv/  独立运行环境", "#eef2ff", "#818cf8", fontsize=8.5)
    arrow(ax, (17, 80), (22, 77), "生成", fontsize=8)

    box(ax, 66, 71.5, 26, 5.5, "WGAN_Boost_Xgboost 原始项目\n（由 source_project.py 定位）",
        C_EXT, "#94a3b8", fontsize=8)
    arrow(ax, (81, 80), (79, 77), "只读比对", fontsize=8, dashed=True)

    # --- 运行期四层 ---
    band(ax, 5, 57, 90, 11, "入口层（壳）")
    box(ax, 24, 58.5, 26, 6, "app.py\nFlask 路由与编排", C_ENTRY, C_ENTRY_EDGE, fontsize=9.5, bold=True)
    box(ax, 62, 58.5, 28, 6, "浏览器\nindex.html + style.css + app.js",
        C_EXT, "#94a3b8", fontsize=8.5)
    arrow(ax, (47, 80), (39, 64.5), "启动", fontsize=8)
    arrow(ax, (62, 61.5), (50, 61.5), "HTTP JSON", fontsize=8, label_offset=(0, 2.4))

    band(ax, 5, 41, 90, 13, "功能层（模块之间互不 import）")
    box(ax, 7, 42.5, 25, 6.5, "features.py\n表单 → 特征行\n（校验 / 元素比值 / 独热）",
        C_FUNC, C_FUNC_EDGE, fontsize=8.5)
    box(ax, 36, 42.5, 25, 6.5, "model_store.py\n模型装载与预测\n（按需标准化）",
        C_FUNC, C_FUNC_EDGE, fontsize=8.5)
    box(ax, 65, 42.5, 27, 6.5, "dataset_meta.py\n字段元数据与取值范围",
        C_FUNC, C_FUNC_EDGE, fontsize=8.5)
    arrow(ax, (37, 58.5), (19, 49), None)
    arrow(ax, (39, 58.5), (48, 49), None)
    arrow(ax, (43, 58.5), (78, 49), None)

    band(ax, 5, 27, 90, 11.5, "共用层（只被读，不调用任何人）")
    box(ax, 12, 28.5, 26, 5.5, "model_registry.py\n模型清单 / 特征集 / 边界常量",
        C_COMMON, C_COMMON_EDGE, fontsize=8.5)
    box(ax, 58, 28.5, 26, 5.5, "paths.py\n路径地址簿", C_COMMON, C_COMMON_EDGE, fontsize=8.5)
    # 功能层 → 共用层：features 只用 registry；另外两个都用到 registry 与 paths
    arrow(ax, (19, 42.5), (25, 34), None)
    arrow(ax, (48, 42.5), (33, 34), None)
    arrow(ax, (49, 42.5), (63, 34), None)
    arrow(ax, (78, 42.5), (37, 34), None)
    arrow(ax, (80, 42.5), (76, 34), None)

    band(ax, 5, 12, 90, 11.5, "标准库 / 第三方")
    box(ax, 8, 13.5, 18, 6, "numpy", C_EXT, "#94a3b8", fontsize=9)
    box(ax, 31, 13.5, 20, 6, "joblib\n（装载 .joblib）", C_EXT, "#94a3b8", fontsize=8.5)
    box(ax, 57, 13.5, 18, 6, "xgboost", C_EXT, "#94a3b8", fontsize=9)
    box(ax, 79, 13.5, 14, 6, "catboost", C_EXT, "#94a3b8", fontsize=9)
    # model_store 经 joblib 装载模型；此线走在共用层两个方框之间的空档，不穿框
    arrow(ax, (48, 27), (41, 19.5), None)

    box(ax, 8, 3.5, 85, 6, "models/   xgb_amount · catboost_amount · xgb_capacity · xgb_capacity_wgan · Dataset.csv",
        "#fff7ed", "#fb923c", fontsize=8.5)
    arrow(ax, (41, 13.5), (48, 9.5), None)

    ax.set_title("图 1  架构分层与调用关系", fontsize=13, fontweight="bold", pad=12)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ============================================================================
# ④ 图二：一次预测的数据流
# ============================================================================

def draw_dataflow(path):
    """绘制一次预测的数据流。

    注意框图的语义：特征集是由「选了哪个模型」决定的，属于 build_row 的产物，
    不是 predict 的下游步骤——所以分支箭头统一从 build_row 向下，不画回指。
    """
    fig, ax = blank_axes(15.0, 7.0)

    steps = [
        (2.0, "表单输入\n1 条记录\n19 个标量 + 污染物", "#dbeafe", C_ENTRY_EDGE),
        (18.6, "features\n.validate_inputs\n范围校验（由数据推出）", C_FUNC, C_FUNC_EDGE),
        (35.2, "features\n.derive_values\nH/C N/C O/C O+N/C\nPollutant_* 置 0/1", C_FUNC, C_FUNC_EDGE),
        (51.8, "features\n.build_row\n按模型列序排列", C_FUNC, C_FUNC_EDGE),
        (68.4, "model_store\n.predict\n标准化 → model.predict", C_FUNC, C_FUNC_EDGE),
        (85.0, "预测值\nmg/g", "#fef3c7", C_COMMON_EDGE),
    ]
    width, height, top = 13.0, 22.0, 62.0
    for i, (x, text, face, edge) in enumerate(steps):
        box(ax, x, top, width, height, text, face, edge, fontsize=8.5)
        if i:
            arrow(ax, (steps[i - 1][0] + width, top + height / 2),
                  (x, top + height / 2))

    # build_row 的两种产物：本质是注释而非流程步骤，故只向下引出、不回指，
    # 避免读成"特征集又流回了 predict"
    branch_y, branch_h = 24.0, 17.0
    ax.text(50, branch_y + branch_h + 3.2,
            "build_row 的两种产物（由所选模型的 featureSet 决定）",
            ha="center", fontsize=9, color="#64748b")
    box(ax, 8.0, branch_y, 40.0, branch_h,
        "A25 特征集  (1, 25)\n"
        "18 个原始标量（C/H/O/N 原值）+ 7 个污染物哑变量\n"
        "用于 xgb_amount · catboost_amount · xgb_capacity",
        "#f0fdf4", C_FUNC_EDGE, fontsize=8.5)
    box(ax, 53.0, branch_y, 40.0, branch_h,
        "B19 特征集  (1, 19)\n"
        "11 个原始标量 + 4 个元素比值，含 pKa1，无哑变量\n"
        "用于 xgb_capacity_wgan",
        "#f0fdf4", C_FUNC_EDGE, fontsize=8.5)
    arrow(ax, (56, top), (28, branch_y + branch_h + 1.0), None)
    arrow(ax, (60, top), (73, branch_y + branch_h + 1.0), None)

    ax.text(50, 12,
            "注：两套特征集由同一份表单推出，使用者只需选择模型，无需切换填写方式。",
            ha="center", fontsize=9, color="#64748b")

    ax.set_title("图 2  一次预测的数据流", fontsize=13, fontweight="bold", pad=12)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ============================================================================
# ⑥ 图三：项目完整结构
# ============================================================================

# 每行格式：(缩进层级, 显示文本, 角色, 行内注释)
# 角色决定配色，注释写在右侧说明职责或产物去向
ROLE_COLORS = {
    "root": ("#1f2933", True),
    "entry": ("#2563eb", True),
    "server": ("#0f9d58", False),
    "web": ("#7c3aed", False),
    "model": ("#c2410c", False),
    "build": ("#64748b", False),
    "docs": ("#0e7490", False),
    "env": ("#94a3b8", False),
}

STRUCTURE = [
    (0, "Adsorption_Predictor_Web/", "root", "项目根目录（可直接拷到别的机器）"),

    (1, "deploy.bat", "entry", "① 一键装环境（双击入口）"),
    (1, "deploy.py", "entry", "建 .venv + 装依赖；仅用标准库"),
    (1, "deploy.json", "entry", "部署配置：锁定版本 / pip 源 / 验证项"),
    (1, "start.bat", "entry", "② 一键启动（双击入口）"),
    (1, "app.py", "entry", "③ Flask 入口：路由与编排（入口层）"),
    (1, "requirements.txt", "entry", "依赖清单（带主版本上界）"),
    (1, "README.md", "entry", "说明文档（含全部调用树）"),
    (1, ".gitignore", "entry", "忽略 .venv / __pycache__ 等"),

    (1, "backend/", "server", "服务端 Python（6 个文件）"),
    (2, "__init__.py", "server", "包声明与分层说明"),
    (2, "paths.py", "server", "共用层：路径地址簿（纯常量）"),
    (2, "model_registry.py", "server", "共用层：模型清单 / 特征集 / 边界常量"),
    (2, "features.py", "server", "功能层：表单 → 特征行"),
    (2, "model_store.py", "server", "功能层：模型装载（带缓存）与预测"),
    (2, "dataset_meta.py", "server", "功能层：字段元数据与取值范围"),

    (1, "frontend/", "web", "浏览器端（5 个文件，零框架零构建）"),
    (2, "index.html", "web", "骨架：只有容器与 id"),
    (2, "style.css", "web", "样式：6 个分区"),
    (2, "app.js", "web", "逻辑：5 个分区，只做界面不算数值"),
    (2, "field_meta.json", "web", "字段元数据（离线生成 → 由 /api/meta 下发）"),
    (2, "samples.json", "web", "7 条示例记录（离线生成 → 由 /api/meta 下发）"),

    (1, "models/", "model", "自包含的模型与数据（8 个文件，约 8.8 MB）"),
    (2, "xgb_amount.joblib", "model", "吸附量 · XGBoost · 25 维"),
    (2, "catboost_amount.joblib", "model", "吸附量 · CatBoost · 25 维"),
    (2, "xgb_capacity.joblib", "model", "吸附容量 · XGBoost · 25 维"),
    (2, "xgb_capacity_wgan.joblib", "model", "吸附容量 · XGBoost+WGAN-GP · 19 维"),
    (2, "scaler_amount.joblib", "model", "标准化器（对应 25 维 · 吸附量）"),
    (2, "scaler_capacity.joblib", "model", "标准化器（对应 25 维 · 吸附容量）"),
    (2, "scaler_capacity_wgan.joblib", "model", "标准化器（对应 19 维）"),
    (2, "Dataset.csv", "model", "943 行 × 25 列（供对照与复算）"),

    (1, "build/", "build", "离线构建与校验（10 个文件，运行期不用）"),
    (2, "source_project.py", "build", "原项目路径定位（不写死绝对路径）"),
    (2, "make_field_meta.py", "build", "──→ frontend/field_meta.json"),
    (2, "make_samples.py", "build", "──→ frontend/samples.json"),
    (2, "make_architecture_figure.py", "build", "──→ docs/figures/ 下的图 1~图 3"),
    (2, "measure_wgan_model.py", "build", "──→ build/wgan_metrics.json"),
    (2, "verify_models.py", "build", "副本 vs 原件预测比对"),
    (2, "reproduce_metrics.py", "build", "指标复算与跨版本行为核对"),
    (2, "test_api.py", "build", "接口端到端数值校验"),
    (2, "self_check.py", "build", "交付前总自检（编排以上全部）"),
    (2, "wgan_metrics.json", "build", "复算结果（生成物）"),

    (1, "docs/", "docs", "交付附件（6 个图，可直接放进报告）"),
    (2, "figures/图1_架构与调用关系.png", "docs", "分层与调用关系"),
    (2, "figures/图2_一次预测的数据流.png", "docs", "数据流"),
    (2, "figures/图3_项目完整结构.png", "docs", "本图"),
    (2, "figures/图4_原理与实现对应.png", "docs", "原理步骤 → 函数/库接口"),
    (2, "screenshots/01_吸附量预测.png", "docs", "实际运行截图"),
    (2, "screenshots/02_吸附容量预测.png", "docs", "实际运行截图"),

    (1, ".venv/", "env", "deploy.bat 的产物；已 gitignore，可随时重建"),
]


def draw_full_structure(path):
    """绘制项目完整结构：全部目录、全部文件、职责与产物去向。"""
    fig, ax = blank_axes(15.5, 20.5)

    # --- 顶部：三个入口 ---
    box(ax, 36, 96.6, 18, 3.0, "使用者", "#e2e8f0", "#94a3b8", fontsize=10, bold=True)
    entries = [
        (4.0, "① deploy.bat", "装环境"),
        (30.0, "② start.bat", "启动服务"),
        (56.0, "③ build/*.py", "复现与校验"),
    ]
    for x, name, note in entries:
        box(ax, x, 92.4, 21.0, 3.0, "%s  %s" % (name, note),
            C_ENTRY if x < 56 else C_EXT,
            C_ENTRY_EDGE if x < 56 else "#94a3b8", fontsize=9)
    arrow(ax, (45, 96.6), (14.5, 95.4), None, lw=1.0)
    arrow(ax, (45, 96.6), (40.5, 95.4), None, lw=1.0)
    arrow(ax, (45, 96.6), (66.5, 95.4), None, lw=1.0)

    # --- 主体：文件树 ---
    start_y, step, base_x = 89.0, 1.545, 3.0
    indent_x = {0: base_x, 1: base_x + 2.4, 2: base_x + 5.6}

    for index, (level, name, role, note) in enumerate(STRUCTURE):
        y = start_y - index * step
        color, is_bold = ROLE_COLORS[role]
        x = indent_x[level]
        ax.text(x, y, name, ha="left", va="center",
                fontsize=8.6, color=color,
                fontweight="bold" if is_bold else "normal", zorder=3,
                family="Microsoft YaHei")
        if note:
            ax.text(63.0, y, note, ha="left", va="center",
                    fontsize=7.8, color="#94a3b8", zorder=3)

    # 目录之间的分隔线，便于肉眼分段
    for index, (level, _name, _role, _note) in enumerate(STRUCTURE):
        if level == 1:
            y = start_y - index * step + step * 0.5
            ax.plot([base_x - 0.8, 99.0], [y, y], color="#eef2f7", lw=0.7, zorder=0)

    # --- 右侧角色图例 ---
    legend = [
        ("entry", "启动 / 部署 / 入口"),
        ("server", "服务端 backend/"),
        ("web", "浏览器端 frontend/"),
        ("model", "模型与数据 models/"),
        ("build", "构建与校验 build/"),
        ("docs", "交付附件 docs/"),
        ("env", "虚拟环境（可重建）"),
    ]
    ly = 89.0 - len(STRUCTURE) * step - 2.4
    for role, label in legend:
        color, _ = ROLE_COLORS[role]
        ax.add_patch(FancyBboxPatch((base_x, ly - 0.55), 1.0, 1.1,
                                    boxstyle="round,pad=0,rounding_size=0.2",
                                    linewidth=0, facecolor=color, zorder=3))
        ax.text(base_x + 1.8, ly, label, ha="left", va="center",
                fontsize=8.2, color="#475569")
        ly -= 1.9

    ax.set_title("图 3  项目完整结构（全部目录与文件，共 43 个 / 11.3 MB，不含 .venv）",
                 fontsize=13, fontweight="bold", pad=14)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ============================================================================
# ⑦ 图四：原理与实现对应图
# ============================================================================

# (类型, 原理步骤, 实际实现（函数 / 库接口）, 数据变化)
# 类型 stage = 阶段标题行；row = 正文行
# 所有函数名、参数与库接口均取自实际代码，未凭记忆书写
PRINCIPLE_MAP = [
    ("stage", "阶段一 · WGAN-GP 数据生成", "WGAN/WGAN_Model.py", "解决小样本问题"),

    ("row", "小样本：943 条不足以训练",
     "prepare_dataset() → pd.read_csv + pd.get_dummies",
     "Dataset.csv 943 行 → (940, 25)"),
    ("row", "归一化到生成器输出域",
     "MinMaxScaler(feature_range=(-1, 1))",
     "(940, 25) → 取值落在 [-1, 1]"),
    ("row", "生成器：噪声 → 假样本",
     "build_generator(latent_dim=100, data_dim)\n128→256→512 + BatchNorm + LeakyReLU + tanh",
     "(64, 100) 噪声 → (64, 25) 假样本"),
    ("row", "Critic：输出实数分数（非概率）",
     "build_critic(data_dim)\n256→128→64→1，无激活函数",
     "(64, 25) → (64, 1) 分数"),
    ("row", "WGAN-GP 核心：梯度惩罚替代权重剪枝",
     "gradient_penalty()，内部 tf.GradientTape\nlambda_gp = 10.0",
     "真实/假样本插值 → 梯度范数 → 罚项"),
    ("row", "Critic 与生成器交替训练",
     "train_critic() / train_generator()，@tf.function\nn_critic = 5，epochs = 5000，learning_rate = 0.0002",
     "每轮 5 次 Critic + 1 次生成器"),
    ("row", "生成合成样本并还原量纲",
     "generator(...) → scaler.inverse_transform()",
     "2000 × 25 → 原始量纲 CSV"),
    ("row", "生成质量检验（分布是否重合）",
     "t_SNE.py → sklearn.manifold.TSNE(perplexity=30)",
     "真实 + 生成 → 2 维嵌入图"),

    ("stage", "阶段二 · 数据增强建模（本项目主线）",
     "WGanBoost_Xgboost/Gan_Boost_Xgb.py", "原始 + 合成混合训练"),

    ("row", "元素比值特征工程",
     "add_element_ratios()",
     "C/H/O/N → H/C · N/C · O/C · O+N/C"),
    ("row", "原始数据与合成数据混合",
     "prepare_dataset(file_path, generated_path, target_variable)",
     "940 + 2000 = 2940 行 × 19 维"),
    ("row", "划分训练集与测试集",
     "train_test_split(test_size=0.2, random_state=42)",
     "2352 训练 / 588 测试"),
    ("row", "标准化（消除量纲差异）",
     "sklearn.preprocessing.StandardScaler().fit_transform()",
     "均值 0、标准差 1"),
    ("row", "贝叶斯超参数优化",
     "bayesian_hyperparameter_optimization()\nskopt.BayesSearchCV(5 折, 负 RMSE, n_iter=50)",
     "搜索空间 → 最优参数组合"),
    ("row", "交叉验证（评估泛化）",
     "perform_cross_validation()\nKFold(n_splits=5, shuffle=True, random_state=42)",
     "5 折指标 → 均值与标准差"),
    ("row", "训练最终模型并落盘",
     "xgb.XGBRegressor(**best_params).fit() → joblib.dump()",
     "模型 + 标准化器 → .joblib"),

    ("stage", "阶段三 · 可解释性分析",
     "Boosting/Machine.py · Gan_Boost_Xgb.py", "回答「为什么这样预测」"),

    ("row", "特征贡献（加性归因）",
     "calculate_shap_values()\nshap.TreeExplainer(model).shap_values()",
     "(n, 19) → SHAP 值矩阵"),
    ("row", "两两特征交互作用",
     "explainer.shap_interaction_values()",
     "(n, 19, 19) → 交互强度排序"),
    ("row", "交互强度的非参数检验",
     "calculate_friedman_h_statistic(n_samples=1000)\n蒙特卡洛抽样",
     "H 统计量 → Top 交互对"),
    ("row", "单特征响应曲线",
     "sklearn.inspection.PartialDependenceDisplay.from_estimator()",
     "特征网格 → 部分依赖曲线"),

    ("stage", "阶段四 · 本网页部署推理",
     "app.py + backend/", "把训练好的模型变成可用界面"),

    ("row", "输入合法性与物理边界校验",
     "features.validate_inputs()\n范围由 dataset_meta.field_limits() 从数据推出",
     "表单 JSON → 校验后的标量字典"),
    ("row", "与训练完全一致的特征工程",
     "features.derive_values()",
     "+ 4 个元素比值 + 7 个污染物哑变量"),
    ("row", "按模型声明的列序排成向量",
     "features.build_row()",
     "→ (1, 25) 或 (1, 19)"),
    ("row", "复用训练时的标准化（不重新拟合）",
     "model_store.predict() → scaler.transform()\nCatBoost 条目 scalerFile 为 None，跳过此步",
     "与训练同一套均值 / 标准差"),
    ("row", "树模型推理",
     "XGBRegressor.predict() / CatBoostRegressor.predict()",
     "→ 预测值 (mg/g)"),
]


def draw_principle_map(path):
    """绘制原理与实现对应图：把每一步原理落到具体的函数或库接口上。"""
    fig, ax = blank_axes(16.5, 19.5)

    col_x = (2.0, 25.5, 60.0)          # 三列起点
    col_w = (23.0, 34.0, 37.5)         # 三列宽度
    start_y, step = 91.0, 2.62

    # --- 表头 ---
    headers = ("原理步骤（为什么这么做）", "实际实现（函数 / 库接口）",
               "数据变化（输入 → 中间表示 → 输出）")
    for x, w, text in zip(col_x, col_w, headers):
        box(ax, x, start_y - 0.2, w, 2.6, text, "#e2e8f0", "#94a3b8",
            fontsize=8.8, bold=True)

    y = start_y - 3.4
    for kind, col1, col2, col3 in PRINCIPLE_MAP:
        if kind == "stage":
            # 阶段标题：整行色带，右侧标注所属文件与目的
            ax.add_patch(FancyBboxPatch(
                (col_x[0], y - 0.75), 96.0, 2.35,
                boxstyle="round,pad=0,rounding_size=0.4",
                linewidth=0, facecolor="#dbeafe", zorder=1))
            ax.text(col_x[0] + 1.0, y + 0.42, col1, ha="left", va="center",
                    fontsize=9.2, color="#1e40af", fontweight="bold", zorder=3)
            ax.text(97.0, y + 0.42, "%s   ·   %s" % (col2, col3),
                    ha="right", va="center", fontsize=8.2, color="#3b82f6", zorder=3)
            y -= step * 1.25
            continue

        # 正文行：左侧原理、中间实现（等宽字体便于辨认接口名）、右侧数据变化
        ax.text(col_x[0] + 0.6, y, col1, ha="left", va="center",
                fontsize=8.0, color="#1f2933", zorder=3, linespacing=1.5)
        ax.text(col_x[1] + 0.6, y, col2, ha="left", va="center",
                fontsize=7.6, color="#0f766e", zorder=3, linespacing=1.5)
        ax.text(col_x[2] + 0.6, y, col3, ha="left", va="center",
                fontsize=7.6, color="#64748b", zorder=3, linespacing=1.5)

        ax.plot([col_x[0], 98.0], [y - step / 2, y - step / 2],
                color="#f1f5f9", lw=0.7, zorder=0)
        y -= step

    # --- 列分隔线 ---
    for x in (col_x[1] - 0.8, col_x[2] - 0.8):
        ax.plot([x, x], [y + 0.6, start_y - 0.2], color="#e2e8f0", lw=0.9, zorder=0)

    ax.text(50, y - 0.4,
            "说明：表中函数名、参数与库接口均取自实际代码。"
            "阶段一~三属原始项目 WGAN_Boost_Xgboost，阶段四为本网页新增。",
            ha="center", fontsize=8.4, color="#94a3b8")

    ax.set_title("图 4  原理与实现对应图", fontsize=13, fontweight="bold", pad=14)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ============================================================================
# ⑧ 出口 main
# ============================================================================

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    font = setup_font()
    print("使用中文字体: %s" % (font or "未找到，中文可能显示为方块"))

    outputs = [
        ("图1_架构与调用关系.png", draw_architecture),
        ("图2_一次预测的数据流.png", draw_dataflow),
        ("图3_项目完整结构.png", draw_full_structure),
        ("图4_原理与实现对应.png", draw_principle_map),
    ]
    for filename, draw in outputs:
        target = os.path.join(OUT_DIR, filename)
        draw(target)
        print("已写 %s (%.1f KB)" % (target, os.path.getsize(target) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
