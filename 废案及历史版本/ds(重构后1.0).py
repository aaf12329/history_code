# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
import json                         #搞json的
import csv                          #搞csv的
from openpyxl import load_workbook   #搞excel的
import pandas as pd                 #搞表格的
import base64
from docx import Document
import re                           #解析markdown
from datetime import datetime
import sys
from dotenv import load_dotenv   #加载env文件
"""
开发者备注:此端口为重构1.0版本
开发者技术有限
环境需求包指令：pip install openai openpyxl pandas python-docx
"""

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
            print(delta,end="")
    print("\n")
    return collected

#输入逻辑
def U_Input():
    user_input=input("用户输入:")
    if user_input=="exit()":
        print("程序正常退出")
        sys.exit(1)
    if user_input.startswith("Code_Send:"):
        local=input("\n文件路径(带后缀)):")
        if local.endswith((".txt",".md",".csv",".py",".html",".xml",".log",".yaml",".json")):
            with open(local,"r",encoding="utf-8") as f:
                data=f.read()
            print(f"\n已读取文本文件，共 {len(data)} 字符")
            user_input=user_input+"\n\n"+data
            return user_input
        elif local.endswith((".jpg", ".png", ".gif", ".mp4", ".mp3", ".pdf", ".zip", ".exe")):
            with open(local,"rb") as f:
                data=base64.b64encode(f.read()).decode()
            print("\n成功读取二进制文件，转为base64编码")
            user_input=user_input+"\n\n"+data
            return user_input
        elif local.endswith((".xlsx", ".docx")):
            print("\n上传的属于Office文档，启动额外处理程序")
            if local.endswith(".docx"):
                doc=Document(local)
                data="\n".join([p.text for p in doc.paragraphs])
            elif local.endswith(".xlsx"):
                df = pd.read_excel(local)
                data = df.to_string()
            user_input=user_input+"\n\n"+data
            return user_input
    return user_input

#记忆函数:
def Memory(mode,message=None):
    filepath="Memory.md"
    if mode=="read":
        with open(filepath,"r",encoding="utf-8") as f:
            result=f.read()
            return result
    elif mode=="write":
        with open(filepath,"a",encoding="utf-8") as f:
            f.write(f"{message}\n")
            return None

#中控函数
def control():
    user_input=U_Input()
    user_input=f"Time:{datetime.now()}\n"+"\n"+"user:"+user_input+"\n"
    Memory("write",user_input)
    try:
        memory=Memory("read")
        response=Use(user_input,memory)
    except Exception as e:
        print("调用错误，请检查网络，重启端口")
        print(f"\n错误来源{e}\n")
        print("\n程序异常结束\n")
        sys.exit(1)
    Memory("write",f"Time:{datetime.now()}\n"+"Ai_response:"+response)


#检测记忆文件是否存在
def memoryfile_detect():
    filepath="Memory.md"
    if os.path.exists(filepath):
        print("\n文件存在")
    else:
        print("\n文件不存，在创建新文件")
        with open(filepath,"w",encoding="utf-8") as f:
            f.write("#记忆存储区")
        print(f"\n空白Markdown文件已建立,建立时间{datetime.now()}\n")


print("程序启动")
print("\n退出在输入框里面输入'exti()'\n")
memoryfile_detect()
while 1:
    control()