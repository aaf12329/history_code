# -*- coding: utf-8 -*-
"""源项目定位：为 build/ 下的校验脚本提供 WGAN_Boost_Xgboost 原始项目的路径。

主题
    可移植性。校验脚本要读取原项目的模型与结果文件做比对，但把开发机的绝对路径
    写死会让脚本换台机器就跑不了。本模块把定位逻辑收敛到一处。

职责
    按优先级搜索原项目目录，返回路径与来源说明；找不到时给出可操作的提示。
    只做定位，不读写原项目内容。

被谁调用
    build 下的全部校验脚本（make_field_meta / make_samples /
    measure_wgan_model / verify_models / test_api）
调用谁
    无（仅标准库）

搜索顺序
    1. 环境变量 SOURCE_PROJECT        —— 显式指定，优先级最高
    2. 本项目的同级目录                —— 交付物与原项目并排放在一起时的默认情况
    3. 用户桌面下的同名目录            —— 覆盖"交付物被单独挪走"的情况

用法
    from source_project import find_source_project
    SOURCE_PROJECT, SOURCE_LABEL = find_source_project()

    或指定一个相对路径：
    SOURCE_PROJECT, SOURCE_LABEL = find_source_project(extra=r"..\WGAN_Boost_Xgboost")
"""

import os

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.dirname(BUILD_DIR)

# 原项目目录名（与交付物同级）
SOURCE_PROJECT_NAME = "WGAN_Boost_Xgboost"


class SourceProjectNotFound(FileNotFoundError):
    """找不到原项目目录。消息面向使用者，说明如何指定。"""


def candidate_paths(extra=None):
    """返回 [(来源说明, 路径)] 候选列表，供调试与报错展示。"""
    candidates = []

    env_value = os.environ.get("SOURCE_PROJECT", "").strip()
    if env_value:
        candidates.append(("环境变量 SOURCE_PROJECT", env_value))

    if extra:
        candidates.append(("调用方指定", os.path.abspath(
            extra if os.path.isabs(extra) else os.path.join(WEB_DIR, extra))))

    candidates.append(("本项目的同级目录",
                       os.path.join(os.path.dirname(WEB_DIR), SOURCE_PROJECT_NAME)))
    candidates.append(("用户桌面",
                       os.path.join(os.path.expanduser("~"), "Desktop", SOURCE_PROJECT_NAME)))
    return candidates


def find_source_project(extra=None):
    """定位原项目目录，返回 (绝对路径, 来源说明)。

    找不到时抛 SourceProjectNotFound，消息里列出所有找过的位置与解决办法。
    """
    tried = candidate_paths(extra)
    for label, path in tried:
        if path and os.path.isdir(path):
            return os.path.abspath(path), label

    detail = "\n".join("    %-24s %s" % (label, path) for label, path in tried)
    raise SourceProjectNotFound(
        "找不到原始项目 %s 目录。已尝试：\n%s\n"
        "  解决办法（任选其一）：\n"
        "    1) 把本交付物与 %s 放在同一个父目录下（推荐）\n"
        "    2) 设置环境变量：set SOURCE_PROJECT=D:\\path\\to\\%s\n"
        "    3) 直接构造：find_source_project(extra=r\"..\\%s\")"
        % (SOURCE_PROJECT_NAME, detail, SOURCE_PROJECT_NAME,
           SOURCE_PROJECT_NAME, SOURCE_PROJECT_NAME))
