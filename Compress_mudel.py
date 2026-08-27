import os
from openai import OpenAI
from dotenv import load_dotenv

def Liberary_Read_Or_Write(model,path,content=None):
    if model=="read":
        with open(path,"r",encoding="utf-8") as f:
            content=f.read()
            return content
    if model=="write":
        with open(path,"w",encoding="utf-8") as f:
            f.write(f"{content}")

def Ai_compress (content):
    print("Compress_mudel link Ok,start Compress")
    client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "system", "content": "将这段记忆压缩提取重点到5万字左右"},{"role": "user", "content": content},],
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    result=response.choices[0].message.content
    print("Compress_finish")
    return result

def Compress_control(file_path):
    load_dotenv()
    print("Compress_mudel Engage")
    text=Liberary_Read_Or_Write(model="read",path=file_path)
    result=Ai_compress(text)
    Liberary_Read_Or_Write(model="write",path=file_path,content=result)
    print("记忆压缩完成")

def Compress_mudel_link_test():
    print("可以接入Compress模块")