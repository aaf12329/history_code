import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import requests

# ============================================================
# 配置区（可根据需要修改）
# ============================================================
CONFIG = {
    "history_file": "chat_history.json",
    "model": "deepseek-v4-flash",
    "base_url": "https://api.deepseek.com",
    "system_prompt": "你是我最好的助手和朋友以及我手下最好的技术人员，专业方向是人工智能与电子信息，对游戏也比较精通",
    "exit_commands": ["exit", "quit", "q", "退出"],
}

# ============================================================
# 初始化
# ============================================================
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("❌ 错误：未找到 DEEPSEEK_API_KEY")
    print("💡 请在项目根目录下创建 .env 文件，并添加：")
    print('   DEEPSEEK_API_KEY="your_api_key_here"')
    sys.exit(1)

client = OpenAI(api_key=api_key, base_url=CONFIG["base_url"])

# ============================================================
# 加载 / 初始化对话历史
# ============================================================
if os.path.exists(CONFIG["history_file"]):
    try:
        with open(CONFIG["history_file"], "r", encoding="utf-8") as f:
            messages = json.load(f)
        print(f"📂 已加载对话历史，共 {len(messages)} 条消息")
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ 历史文件损坏，将开始新对话（错误信息：{e}）")
        messages = [{"role": "system", "content": CONFIG["system_prompt"]}]
else:
    messages = [{"role": "system", "content": CONFIG["system_prompt"]}]
    print("🆕 新对话已创建")

# ============================================================
# 工具函数
# ============================================================
def save_history():
    """保存对话历史到文件"""
    try:
        with open(CONFIG["history_file"], "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"⚠️ 保存历史失败：{e}")
        return False

# ============================================================
# 对话主循环
# ============================================================
print("\n" + "=" * 50)
print("🤖 DeepSeek 对话助手已启动")
print(f"💡 输入 {CONFIG['exit_commands'][:-1]} 或 {CONFIG['exit_commands'][-1]} 退出")
print("=" * 50)

while True:


    # --- 获取用户输入 ---
    user_input=input("\n👤 你: ")
    if user_input.startswith("Code_Send:"):
        temp=input("请输入路径:")
        with open(temp,"r",encoding="utf-8") as f:
            content=f.read()
            print(content)
        user_input=user_input+"\n"+content
    now = datetime.now()
    print(f"\n{now}\n")
    user_input=user_input+"\n"+str(now)

    # --- 检查退出命令 ---
    if user_input.lower() in CONFIG["exit_commands"]:
        print("💾 正在保存对话历史...", end=" ")
        if save_history():
            print("✅ 已保存")
        print("👋 再见！")
        break

    # --- 忽略空输入 ---
    if not user_input:
        print("💡 输入不能为空，请重新输入")
        continue

    # --- 追加用户消息 ---
    messages.append({"role": "user", "content": user_input})

    # --- 调用 API ---
    try:
        response = client.chat.completions.create(
            model=CONFIG["model"],
            messages=messages,
            stream=True,
            extra_body={"thinking": {"type": "disabled"}}
        )

        # --- 流式输出 ---
        print("\n🤖 AI: ", end="", flush=True)
        full_response = ""

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content

        print("\n")  # 输出结束换行

        # --- 追加助手回复 ---
        messages.append({"role": "assistant", "content": full_response})

        # --- 自动保存（可选，每轮对话后保存）---
        # 如果不需要每轮都保存，可以注释掉下一行
        save_history()

    except Exception as e:
        print(f"\n❌ 请求出错: {e}")
        print("💡 请检查网络连接和 API Key 是否正确")