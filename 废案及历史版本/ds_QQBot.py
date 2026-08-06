# Please install OpenAI SDK first: `pip3 install openai`
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
"""
开发者备注:此端口为重构1.5版本
开发者技术有限
环境需求包指令：pip install openai openpyxl pandas python-docx

较于1.0版本新增记忆压缩功能与System_prompt(系统提示词)和personal_prompt(个人私设)
26-8-6  0:42

QQBot特殊版本特化用于接入QQBot
pip install qg-botsdk
"""

script= os.path.dirname(os.path.abspath(__file__))
#相对路径寻址找到当前文件夹的位置


path_liberary= os.path.join(script, "Menorise", "Memory_Library.md")
system_prompt_path=os.path.join(script, "Menorise", "System_prompt.md")
presonal_setting_path=os.path.join(script, "Menorise", "Personal_setting.md")
#拼凑出其他文件的路径

def prompt_read(path):
    with open(path,"r",encoding="utf-8") as f:
        result=f.read()
    return result

"""
临时补丁读取两个prompt(你最好是不要乱动那俩文件我没写错误校验)
"""
def prompt():
    result=prompt_read(system_prompt_path)+prompt_read(presonal_setting_path)
    return result

#记忆函数:
def Memory(mode,message=None,path=None):
    if mode=="read":
        with open(path,"r",encoding="utf-8") as f:
            result=f.read()
            return result
    elif mode=="write":
        with open(path,"a",encoding="utf-8") as f:
            f.write(f"{message}\n")
            return None


#发送接收及模型参数控制
def Use(user_input,system):
    load_dotenv()
    client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_input },
        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    collected=""
    print("Ai_response:")
    for chunk in response:
        delta=chunk.choices[0].delta.content
        if delta:
            collected+=delta
    return collected

#输入逻辑(记忆算作user_input载入)
def U_Input(user_input):
    user_input=Memory("read",None,path_liberary)+"\n"+f"{datetime.now()}"+user_input
    return user_input


#检测记忆文件是否存在
def memoryfile_detect(path):
    if os.path.exists(path):
        print("\n文件存在")
    else:
        print("\n文件不存，在创建新文件")
        with open(path,"w",encoding="utf-8") as f:
            f.write("#记忆存储区")
        print(f"\n空白Markdown文件已建立,建立时间{datetime.now()}\n")

"""
记忆检测模块，在检测到记忆到600K的tokens时就会启动进行记忆压缩
"""
def Memory_detect(path):
    size_bytes = os.path.getsize(path)
    if size_bytes/(1024*1024) >=2.5:
        Compress_mudel.control()

#开机检测函数检测记忆模块是否存在是否齐全
def detect():
    print("程序启动")
    print("\n退出在输入框里面输入'exit()'\n")
    try:
        memoryfile_detect(path_liberary)  #检测记忆文件是否存在的
        memoryfile_detect(system_prompt_path)  #检测system_prompt_path文件是否存在的
        memoryfile_detect(presonal_setting_path)  #检测presonal_setting文件是否存在的
    except Exception as e:
        print(f"\n错误来源{e}\n")