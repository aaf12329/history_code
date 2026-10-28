import os
import tkinter as tk
from tkinter import scrolledtext, Entry, Button
import ds

#路径区
base_path = os.path.dirname(os.path.abspath(__file__))
Chat_History_path = os.path.join(base_path, "Memories", "Chat_History.json")
AI_Memories_path = os.path.join(base_path, "Memories", "AI_Memories.md")
System_Prompt_path = os.path.join(base_path, "Prompt", "System_Prompt.md")
Privacy_Setting_path = os.path.join(base_path, "Prompt", "Privacy_Setting.md")
#路径区

root = tk.Tk()
root.title("DeepSeek 端口")
root.geometry("600x700")
root.configure(bg="#1a1a1a")
root.resizable(False, False)

# 显示区
display = scrolledtext.ScrolledText(root,bg="#0d0d0d",fg="#e0e0e0",font=("Consolas", 12))
display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
display.config(state=tk.DISABLED)

# 底部容器
bottom_frame = tk.Frame(root, bg="#1a1a1a", height=100)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))
bottom_frame.pack_propagate(False)

# 输入框
entry = Entry(bottom_frame,bg="#2a2a2a",fg="#ffffff",font=("Consolas", 13))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=10)


def GUI_Control():
    user_input = entry.get().strip()
    if not user_input:
        return
    # 显示用户消息
    display.config(state=tk.NORMAL)
    display.insert(tk.END, f"\nuser:{user_input}\n")
    display.see(tk.END)
    display.config(state=tk.DISABLED)
    entry.delete(0, tk.END)
    
    #交互逻辑
    history_chat=ds.file_read_write(file_path=AI_Memories_path,mode="read")
    Total_prompt=ds.file_read_write(file_path=Privacy_Setting_path,mode="read")+ds.file_read_write(file_path=System_Prompt_path,mode="read")

    response=ds.Core(Total_prompt,history_chat+user_input)

    #user_input记录到Chat_History_path
    ds.file_read_write(file_path=Chat_History_path,mode="write",role="user",content=user_input)
    #user_input记录到AI_Memories_path
    ds.file_read_write(file_path=AI_Memories_path,mode="write",role="user",content=user_input)
    #记录AI_response到Chat_History_path
    ds.file_read_write(file_path=Chat_History_path,mode="write",role="Assitant",content=response)
    #记录AI_response到AI_Memories_path
    ds.file_read_write(file_path=AI_Memories_path,mode="write",role="Assitant",content=response)
    ds.Memory_Scale_detect()

    # 显示 AI 回复
    display.config(state=tk.NORMAL)
    display.insert(tk.END, f"可露希尔: {response}\n")
    display.see(tk.END)
    display.config(state=tk.DISABLED)   

#发送按钮
btn = Button(bottom_frame,text="发送",command=GUI_Control,bg="#0078ff",fg="white",font=("Consolas", 12, "bold"))
btn.pack(side=tk.RIGHT)
entry.bind("<Return>", lambda e: GUI_Control())

ds.file_detect()

root.mainloop()