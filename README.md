# DeepSeek_port —— SQL 记忆实验

> 记忆存储转向数据库的第一步

![version](https://img.shields.io/badge/阶段-SQL实验-yellow)
![DB](https://img.shields.io/badge/DB-MySQL-4479A1?logo=mysql&logoColor=white)

## 📖 简介

纯 Markdown 记忆"全量载入"的方式，在记忆膨胀后 token 成本越来越高。
本阶段开始探索**把对话记录落到数据库**，为将来的记忆检索（按需取段）
铺路。同时附带一组 Selenium 爬虫实验。

## 📦 模块一览

| 文件 | 职责 | 状态 |
|------|------|------|
| `Model_SQL.py` | DeepSeek 调用封装，模型参数集中管理 | 实验中（参数签名待修） |
| `Py_SQL.py` | `SQL_Instruction()`：按 id / role / content / 时间戳 追加记录 | 可用（当前落 CSV，接口先定型） |
| `SQL_Link.py` | MySQL 连接配置（DB_HOST / DB_NAME / DB_USER / DB_PASSWORD 环境变量，utf8mb4） | 就绪待切换 |
| `Crawler_test.py` | Selenium + Edge 无头模式抓取行情页面，存 output_full.html | 配套实验 |
| `Data_test.py` | BeautifulSoup 解析抓取结果 | 配套实验 |

## 🧭 现状

主对话流程仍使用文件记忆；CSV 落库已接入主程序（每轮 user / assistant
各记一条）；MySQL 通道已就绪，等待正式切换。
