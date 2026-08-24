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
开发者备注:此端口为重构1.5.1版本
开发者技术有限
环境需求包指令：pip install openai openpyxl pandas python-docx
较于1.0版本新增记忆压缩功能与System_prompt(系统提示词)和personal_prompt(个人私设)
26-8-6  0:42
较于上一个版本增加了虚拟环境可以直接一次性打包一键启动
26-8-13 15.39
"""


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
        messages=[{"role": "system", "content": system},{"role": "user", "content": user_input },],
        stream=True,reasoning_effort="high",
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
    user_input=input(f"{datetime.now()}  用户输入:")
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
            user_input=user_input+"\n"+data
            return user_input
    return user_input


#检测记忆文件是否存在
def memory_existence_file_detect(path):
    if os.path.exists(path):
        print(f"{path}文件存在")
    else:
        print(f"{path}文件不存，在创建新文件")
        if path==path_liberary:
            with open(path,"w",encoding="utf-8") as f:
                f.write("#记忆存储区\n")
        else:
            with open(path,"w",encoding="utf-8") as f:
                f.write("")
        print(f"\n空白Markdown文件{path}已建立,建立时间{datetime.now()}\n")

"""
记忆检测模块，在检测到记忆到600K左右的tokens时就会启动进行记忆压缩
"""
def Memory_Scale_detect(path):
    size_bytes = os.path.getsize(path)
    if size_bytes/(1024*1024) >=1.5:
        Compress_mudel.Compress_control(path_liberary)


"""
总区注释规范:第一个括号是作用，第二个括号是函数输入值,输入值不包括在函数内部要手动输入的inupt包括缺省值与返回值
"""

"""
函数总区:
Memory_Scale_detect(检测记忆规模到600K的时候自动压缩)         (输入参数:路径  返回:无)
memory_existence_file_detect(检测记忆是否存在)               (输入参数:固定路径  返回:无)

U_Input(输入)                                               (输入:无  返回:用户在input中输入的信息与文件路径读取信息)
Use(收发及其参数控制)                                        (输入:user_input,system  返回:Ai的API调用的回复)
Memory(记忆读取)                                             (输入:mode,message=None,path=None  返回:path文件路径读取到的东西)
#函数注解:
mode传入参数有write与read
在传入write它没有返回会往相应的文件夹中追加写入message的内容
在传入read时它会返回path中读取的内容
"""

"""
路径文件架构有点乱在下一个版本会修复

文件路径总区(备注:都是相对地址):
script(记忆基地址)                     (Menorise文件夹路径,其中有三个.md文件)  
path_liberary(统一记忆存储空间)          Original_Memory.md    记忆文件
prompt_path(系统提示词路径)              System_prompt.md      系统提示词
presonal_setting_path(私人设定路径)     Personal_setting.md    个人私设(可以让它COS你喜欢的角色)
"""

#中控函数
def control():
    history_chat=Memory(mode="read",message=None,path=path_liberary)
    Total_prompt=Memory(mode="read",path=prompt_path)+Memory(mode="read",path=presonal_setting_path)
    print("=" * 40)
    user_input=U_Input()
    try:
        response=Use(history_chat+user_input,Total_prompt)
    except Exception as e:
        print("调用错误，请检查错误，重启端口")
        print(f"\n错误来源{e}\n")
        print("\n程序异常结束\n")
        sys.exit(1)
    """
    记忆写入最后是记忆规模的检测
    """
    Memory(mode="write",message="\n"+"user_input_start:"+"\n"+user_input+"\n"+"user_input_end"+"\n",path=path_liberary)
    Memory("write",f"\nTime:{datetime.now()}"+"\n"+"Ai_response_start:"+response+""+"Ai_response_end"+"\n",path_liberary)
    Memory_Scale_detect(path_liberary)


"""
保留一个黑框端口以求可以回调
"""
if __name__=="__main__":
    script= os.path.dirname(os.path.abspath(__file__))
    #相对路径寻址找到当前文件夹的位置
    path_liberary= os.path.join(script, "Menorise", "Original_Memory.md")
    prompt_path=os.path.join(script, "Menorise", "System_prompt.md")
    presonal_setting_path=os.path.join(script, "Menorise", "Personal_setting.md")
    #拼凑出其他文件的路径
    print("程序启动")
    print("自检启动:")
    memory_existence_file_detect(path_liberary)          #检测记忆文件是否存在的
    memory_existence_file_detect(prompt_path)            #检测prompt_path文件是否存在的
    memory_existence_file_detect(presonal_setting_path)  #检测presonal_setting文件是否存在的
    Compress_mudel.Compress_mudel_link_test()
    print("退出在输入框里面输入'exit()'")
    print("要传输文件用Code_Send:作为开头")
    while 1:
        control()