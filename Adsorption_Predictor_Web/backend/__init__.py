# -*- coding: utf-8 -*-
"""后端包：磺胺类抗生素在生物炭上吸附性能的离线预测服务。

分层（依赖方向单向向下，功能层之间互不 import）
    入口层   app.py                   路由与编排
    功能层   features.py              表单 → 特征行
             model_store.py           模型装载与预测
             dataset_meta.py          字段元数据与示例
    共用层   paths.py                 路径地址簿
             model_registry.py        模型清单与特征集定义
"""
