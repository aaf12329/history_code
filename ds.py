import os
import json
from datetime import datetime
from openai import OpenAI
import csv                          #搞csv的
from openpyxl import load_workbook   #搞excel的
import base64
from docx import Document
import sys
from dotenv import load_dotenv   #加载env文件
import Compress_mudel         #手搓的py文件，记忆压缩模块
import pandas as pd
from Compress_mudel import Compress_control,Compress_mudel_link_test
from Py_SQL import SQL_Instruction


def file_detect():
    #路径区(start)
    base_path = os.path.dirname(os.path.abspath(__file__))
    Chat_History_path = os.path.join(base_path, "Memories", "Chat_History.json")
    AI_Memories_path = os.path.join(base_path, "Memories", "AI_Memories.md")
    System_Prompt_path = os.path.join(base_path, "Prompt", "System_Prompt.md")
    Privacy_Setting_path = os.path.join(base_path, "Prompt", "Privacy_Setting.md")
    #路径区(stop)
    print("文件完整性自检查开始")
    paths = [Chat_History_path, AI_Memories_path, System_Prompt_path, Privacy_Setting_path]
    for file_path in paths:
        if os.path.exists(file_path):
            print(f" 路径 {file_path} 存在")
        else:
            print(f" 路径 {file_path} 不存在，创建空文件")
            # 确保文件夹存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                if file_path.endswith(".json"):
                    json.dump([], f, ensure_ascii=False, indent=2)
                else:
                    f.write("")
    SQL_path=os.path.join(base_path,"Memories","Chat_History.csv")
    if os.path.exists(SQL_path):
        print(f"{SQL_path}存在")
    else:
        with open(SQL_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "role", "content", "time"])
        print(f"{SQL_path}不存在,已建立")

def file_read_write(file_path,mode,role=None,content=None):
    if mode == "write":
        if file_path.endswith(".json"):
            if os.path.getsize(file_path)==0:
                data = []
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data.append({
                "role": role,
                "content": content,
                "time": f"{datetime.now()}"
            })
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now()}  {role}:{content}\n")
    elif mode == "read":
        with open(file_path,"r",encoding="utf-8") as f:
            return f.read()
    else:
        print("mode error: 请使用'read'或'write'")

def Core(prompt,user_input):
    load_dotenv()
    client = OpenAI(api_key="sk-0fa7400cfe4c486584d6102d5c312ed2",base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "system", "content": prompt},{"role": "user", "content": user_input },],
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
    user_input = input(f"{datetime.now()}  用户输入:")
    if user_input == "exit()":
        print("程序正常退出")
        sys.exit(0)
    if user_input.startswith("Code_Send:"):
        local = input("\n文件路径(带后缀):")
        # 1. 检查文件是否存在且是文件
        if not os.path.isfile(local):
            print("文件不存在")
            return user_input
        # 2. 定义允许的扩展名
        ALLOWED_EXTENSIONS = (".txt", ".md", ".csv", ".py", ".html", ".xml", ".log", ".yaml", ".json", ".jpg", ".png", ".gif", ".mp4", ".mp3", ".pdf", ".zip", ".exe", ".xlsx", ".docx")
        # 3. 检查扩展名是否支持
        if not local.endswith(ALLOWED_EXTENSIONS):
            print("不支持的文件类型")
            return user_input
        # 4. 检查文件大小（防止内存爆炸）
        file_size = os.path.getsize(local)
        if file_size > 5 * 1024 * 1024:  # 5MB
            print("文件超过 5MB")
            return "Send_oversize"
        # 5. 根据扩展名读取文件
        data = None  # 初始化
        if local.endswith((".txt", ".md", ".py", ".html", ".xml", ".log", ".yaml", ".json")):
            # 处理文本文件（尝试多个编码）
            encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
            for enc in encodings:
                try:
                    with open(local, "r", encoding=enc) as f:
                        data = f.read()
                    print(f"\n已读取文本文件(编码:{enc}),共 {len(data)} 字符")
                    break
                except UnicodeDecodeError:
                    continue
            if data is None:
                print("无法解码文本文件")
                return user_input
        elif local.endswith((".jpg", ".png", ".gif", ".mp4", ".mp3", ".pdf", ".zip", ".exe")):
            with open(local, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            print("\n 成功读取二进制文件，转为base64编码")
            
        elif local.endswith((".xlsx", ".docx")):
            print("\n上传Office文档，启动额外处理程序")
            try:
                if local.endswith(".docx"):
                    doc = Document(local)
                    data = "\n".join([p.text for p in doc.paragraphs])
                elif local.endswith(".xlsx"):
                    df = pd.read_excel(local)
                    data = df.to_string()
                print(f"成功读取Office文档，共 {len(data)} 字符")
            except ImportError as e:
                print(f"缺少依赖包: {e}")
                return user_input
            except Exception as e:
                print(f"读取Office文档失败: {e}")
                return user_input
        # 6. 拼接文件内容
        if data is not None:
            user_input = user_input + "\n" + data
        else:
            print("文件读取失败")
            return user_input
            # 7. 检查输入大小(用实际字节数)
    if len(user_input.encode('utf-8')) / (1024 * 1024) >= 1.5:
        print("输入过大，被拦截请重新输入")
        return "Send_oversize"
    return user_input

def Memory_Scale_detect():
    base_path = os.path.dirname(os.path.abspath(__file__))
    AI_Memories_path = os.path.join(base_path, "Memories", "AI_Memories.md")
    #临时路径补丁后期修复
    size_bytes = os.path.getsize(AI_Memories_path)
    if size_bytes/(1024*1024) >=1.5:
        Compress_mudel.Compress_control(file_path=AI_Memories_path)


"""
中控代码(control)调用就可以在终端直接对话
规范:chat_history与user_input分开读取并且严禁合并(谁TM这么写我把它抽成陀螺)
"""
def control():
    history_chat=file_read_write(file_path=AI_Memories_path,mode="read")
    Total_prompt=file_read_write(file_path=Privacy_Setting_path,mode="read")+file_read_write(file_path=System_Prompt_path,mode="read")
    print("=" * 40)
    user_input=U_Input()
    try:
        response=Core(history_chat+user_input,Total_prompt)
    except Exception as e:
        print("调用错误，请检查错误，重启端口")
        print(f"\n错误来源{e}\n")
        print("\n程序异常结束\n")
        sys.exit(1)
    #user_input记录到Chat_History_path
    file_read_write(file_path=Chat_History_path,mode="write",role="user",content=user_input)
    #user_input记录到AI_Memories_path
    file_read_write(file_path=AI_Memories_path,mode="write",role="user",content=user_input)
    #记录AI_response到Chat_History_path
    file_read_write(file_path=Chat_History_path,mode="write",role="Assitant",content=response)
    #记录AI_response到AI_Memories_path
    file_read_write(file_path=AI_Memories_path,mode="write",role="Assitant",content=response)
    #记录到SQL
    SQL_Instruction(file_path=SQL_path,model="write",role="user",content=user_input)
    SQL_Instruction(file_path=SQL_path,model="write",role="Assitant",content=response)
    Memory_Scale_detect()

if __name__ == "__main__":
    #路径区(start)
    base_path = os.path.dirname(os.path.abspath(__file__))
    Chat_History_path = os.path.join(base_path, "Memories", "Chat_History.json")
    AI_Memories_path = os.path.join(base_path, "Memories", "AI_Memories.md")
    System_Prompt_path = os.path.join(base_path, "Prompt", "System_Prompt.md")
    Privacy_Setting_path = os.path.join(base_path, "Prompt", "Privacy_Setting.md")
    SQL_path= os.path.join(base_path,"Memories","Chat_History.csv")
    #路径区(stop)
    file_detect()
    while 1:
        control()