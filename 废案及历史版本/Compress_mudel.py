"""
记忆压缩1.0版本
"""
import os
from openai import OpenAI
def Liberary_Read_Or_Write(model,content=None):
    script= os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script, "Menorise", "Memory_Library.md")
    if model=="read":
        with open(path,"r",encoding="utf-8") as f:
            content=f.read()
            return content
    if model=="write":
        with open(path,"w",encoding="utf-8") as f:
            f.write(f"{content}")

def Ai_compress (content):
    client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "system", "content": "将这段记忆压缩提取重点到100K左右的tokens"},{"role": "user", "content": content},],
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    result=response.choices[0].message.content
    return result

def control():
    text=Liberary_Read_Or_Write("read")
    content=Ai_compress(text)
    Liberary_Read_Or_Write("write",content)

