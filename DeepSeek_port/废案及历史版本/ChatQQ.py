# qq_bot.py
import os
from qg_botsdk import BOT, Model
def deliver(data: Model.MESSAGE):
    """收到任何消息都回复“收到”"""
    user_input = data.treated_msg
    print(f"📩 收到消息: {user_input}")

    # 回复
    data.reply("收到！")


def start_bot():
    """启动机器人"""
    print("🤖 正在启动机器人...")

    bot = BOT(
        bot_id="1905382649",
        bot_secret="QTWaejou07EMVeoy9KWjwAOds8OfwEXq",
        is_private=True, 
        is_sandbox=True     # 沙箱模式
    )

    # 直接绑定，不传 intents 参数
    bot.bind_msg(deliver)
    bot.start()


if __name__ == "__main__":
    start_bot()