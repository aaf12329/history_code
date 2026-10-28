from django.http import HttpResponse
import json
import time
from ultralytics import YOLO
import os
from django.conf import settings
def image_detect(request):

    file = request.FILES.get("file")  #接收上传文件
    print(f"file{file}")              #文件原始名

    file_name=str(time.time())         #时间命名
    print(f"文件名{file_name}")
    stuffix=file.name.split(".")[1]
    file_name=file_name+"."+stuffix
    print(f"新的文件名:{file_name}")

    with open(os.path.join(settings.BASE_DIR, "static", "upload", file_name), "wb") as f:
        for c in file:    #分多次写入硬盘防止遭不住4K超高清或者你拿stc89c52当作主控芯片处理不来
            f.write(c)


    model_path = os.path.join(settings.BASE_DIR, "model", "best.pt")   #找模型路径
    print(f"模型路径:{model_path}")
    model = YOLO(model_path)                #调用模型

    image_path = os.path.join(settings.BASE_DIR, "static", "upload", file_name)   #构造文件路径
    print(f"图片路径:{image_path}")
    rs=model([image_path])      #调用模型检测
    image_result_path = os.path.join(settings.BASE_DIR, "static", "result", file_name)   #把拉完框后的文件存入result
    for r in rs:          #遍历检测结果列表把有框的放回result（代码在之后可能一次性上传多个）
        r.save(filename=f"{image_result_path}")
    data={"code":200,"msg":"成功","url": f"/static/result/{file_name}"}         #检测结果，文件路径
    return HttpResponse(json.dumps(data),content_type="application/json")

