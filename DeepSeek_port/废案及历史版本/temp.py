import os
from openai import OpenAI
import json                         #搞json的
import csv                          #搞csv的
from openpyxl import load_workbook   #搞excel的
import pandas as pd                 #搞表格的
import base64
from docx import Document
from datetime import datetime
import sys
from dotenv import load_dotenv   #加载env文件
import Compress_mudel         #手搓的py文件，记忆压缩模块
script= os.path.dirname(os.path.abspath(__file__))
#相对路径寻址找到当前文件夹的位置
path_liberary= os.path.join(script, "Menorise", "Original_Memory.md")
prompt_path=os.path.join(script, "Menorise", "System_prompt.md")
presonal_setting_path=os.path.join(script, "Menorise", "Personal_setting.md")
load_dotenv()


def Liberary_Read_Or_Write(model, path, content=None):
    if model == "read":
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    elif model == "write":
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{content}")


def Ai_compress(content):
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": "将这段记忆压缩提取重点到100K左右的tokens"},
            {"role": "user", "content": content}
        ],
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    return response.choices[0].message.content


def Compress_control(path):
    """只取最后 10 万字进行压缩"""
    text = Liberary_Read_Or_Write("read", path, None)
    
    if not text or len(text) < 1000:
        print("📭 记忆库为空或太短，无需压缩")
        return
    
    total_len = len(text)
    print(f"📊 原始记忆长度: {total_len} 字符")
    
    # 只取最后 10 万字
    MAX_CHARS = 100000
    if len(text) > MAX_CHARS:
        text = text[-MAX_CHARS:]
        print(f"✂️ 截取最后 {MAX_CHARS} 字符（原始 {total_len} 字符）")
    
    print("🔄 正在压缩...")
    result = Ai_compress(text)
    Liberary_Read_Or_Write("write", path, result)
    print(f"✅ 压缩完成！压缩后长度: {len(result)} 字符")
Compress_control(path_liberary)