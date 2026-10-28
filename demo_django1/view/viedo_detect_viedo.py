from django.http import HttpResponse, StreamingHttpResponse
import json
import time
from django.views.decorators import gzip
from django.conf import settings
from ultralytics import YOLO
import os
import cv2
def upload_viedo(request):        #上传模块

#-------------------获取前端Ajax发来的视频--------------------------#
    file = request.FILES.get("file")
    print(f"file{file}")#打印视频原始名称


    file_name=str(time.time())          #生成文件名称并打印
    print(f"文件名{file_name}")


    stuffix=file.name.split(".")[1]          #获取后缀并取名为stuffix(文件组成  文件名.后缀  )split返回列表（无需可重复）
    file_name=file_name+"."+stuffix          #用时间组成唯一的新的文件名
    print(f"新的文件名:{file_name}")


    save_path = os.path.join(settings.BASE_DIR, "static", "upload", file_name)
#牵涉import os 	拼接路径（自动处理不同操作系统的路径分隔符） 与from django.conf import settings头文件 获取 Django 项目的根目录
#-------------------settings.BASE_DIR项目的根目录，用根目录与static/upload凑出一个绝对路径----------------------#
    with open(save_path, "wb") as f:         #打开文件
        for chunk in file.chunks():         #分块读取，避免RAM溢出
            f.write(chunk)


    data={"code":200,"msg":"上传成功","viedo_name":file_name}
    return HttpResponse(json.dumps(data),content_type="application/json")

# open_viedo
# 这段代码是一个视频检测生成器，作用是：逐帧读取视频，用 YOLO 检测每一帧，并不断产生（yield）带检测框的 JPEG 图片数据流
#
def open_viedo(viedo_path):
    cap = cv2.VideoCapture(viedo_path)      #打开视频文件
    if not cap.isOpened():
        print("无法正常打开")
    else:
        model_path = os.path.join(settings.BASE_DIR, "model", "best.pt")    #从相对路径加载YOLO模型
        model=YOLO(model_path)   #加载YOLO
        while True:          #循环处理每一帧
            ret, frame = cap.read()   #读取一帧画面
            if ret:
                rs = model(frame)      #检测
                rs_frame = rs[0].plot()    #套上识别框
                ret,jpeg = cv2.imencode(".jpg",rs_frame)    #把带框的图片编码成 JPEG 格式
                fram_bytes = jpeg.tobytes()                       #转换成字节流（适合网络传输）
                yield(b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + fram_bytes + b'\r\n')   #	产生一个 MJPEG 流片段（用于视频流传输）
                #----------------------------就是把原来的每一帧都套上识别框压缩为jpeg再编码为mjpge---------------------------#
@gzip.gzip_page
#--------------------------------这个装饰器相当于一个 “压缩打包服务”。它告诉 Django：在把数据发给用户之前，如果用户的浏览器支持压缩格式，可以先把它压缩一下，这样传输速度会更快。--------#


def play_viedo(request):
    viedo_name=request.GET.get("viedo_name")       #要检测什么
    viedo_path = os.path.join(settings.BASE_DIR, "static", "upload", viedo_name)     #根据名字找路径
    rs=open_viedo(viedo_path)                         #调用open_viedo去检测这个视频
    return StreamingHttpResponse(rs, content_type='multipart/x-mixed-replace; boundary=frame')   #输出一帧画面
#-----------------open_viedo就像一个拉屎的，play_viedo就像一个吃屎的
# 当play_viedo说我要吃屎的时候，不用等open_viedo全部拉完，可以open_viedo拉一点，play_viedo吃一点

#Ég vona að einn daginn munir þú finna heiminn aftur, Rezóna.#
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