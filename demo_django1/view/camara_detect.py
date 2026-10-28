import cv2
from ultralytics import YOLO
from django.http import HttpResponse
import threading
import os
from django.conf import settings

def open_camara():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():   #检测摄像头
        print("摄像头未开启")
        return

    model_path = os.path.join(settings.BASE_DIR, "model", "best.pt")
    model = YOLO(model_path)     #找模型，调用模型

    while True:
        ret, frame = cap.read()
        if ret:
            rs = model(frame)             #读取（一帧）调用模型
            rs_frame = rs[0].plot()       #拉框
            cv2.imshow("Camera Detection", rs_frame)  #在 OpenCV 窗口显示带框的画面
        if cv2.waitKey(20) & 0xFF == ord('q'):      #停止条件
            break

    cap.release()
    cv2.destroyAllWindows()  #关闭摄像头，注销cv窗口

def start_camera(request):
    thread = threading.Thread(target=open_camara)     #创建一个新的线程程
    thread.start()                           #启动线程
    return HttpResponse("摄像头窗口已启动")     #返回信息

##Ég vona að einn daginn munir þú finna heiminn aftur, Rezóna.#
#镇楼圣经#
# The Zen of Python, by Tim Peters
#
# Beautiful is better than ugly.
# Explicit is better than implicit.
# Simple is better than complex.
# Complex is better than complicated.
# Flat is better than nested.
# Sparse is better than dense.
# Readability counts.
# Special cases aren't special enough to break the rules.
# Although practicality beats purity.
# Errors should never pass silently.
# Unless explicitly silenced.
# In the face of ambiguity, refuse the temptation to guess.
# There should be one-- and preferably only one --obvious way to do it.
# Although that way may not be obvious at first unless you're Dutch.
# Now is better than never.
# Although never is often better than *right* now.
# If the implementation is hard to explain, it's a bad idea.
# If the implementation is easy to explain, it may be a good idea.
# Namespaces are one honking great idea -- let's do more of those!