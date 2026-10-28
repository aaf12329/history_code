from django.http import HttpResponse
import json
from email.mime.text import MIMEText
import smtplib
import random
import pymysql
from urllib.parse import quote
from urllib.parse import unquote
#发送验证码
def send_code(request):
    email = request.GET.get('email')
    print(f"邮箱{email}")


#Ég vona að einn daginn munir þú finna heiminn aftur, Rezóna.#
#----------------------------------------看看哪一个小倒霉蛋子在黑名单里面---------------------------------------#


    con2 = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="guishiyuan_25", charset="utf8")
    sql=f"select * from Black_Name where email='{email}'"
    print(f"sql_guishiyuan_25_Black_Name={sql}")
    cursor=con2.cursor()
    cursor.execute(sql)
    result1 = cursor.fetchall()
    if len(result1)>0:
        data = {"code": 500, "msg": "您在黑名单中，无法使用该系统"}
        return HttpResponse(json.dumps(data), content_type="application/json")
#---------------------------------------看看哪一个小倒霉蛋子在黑名单里面---------------------------------------#


    con = pymysql.connect(host="localhost",port=3306,user="root",password="1234",db="guishiyuan_25",charset="utf8")
    sql=f"select * from user_info where email='{email}'"  #在后台告诉你是在哪里查询的然后在后一句打印出来，并不是在查询
    print(f"sql_guishiyuan25_Wite_Name={sql}")
    #---------------------------------在mysql库中查询邮箱-----------------------------------------#
    cursor=con.cursor()           #这三句是标准的查询程序，把查询结果返回rs查到几个
    cursor.execute(sql)           #返回的是一个元组组成的集合如果有3个((1, 'a@qq.com'), (2, 'b@qq.com'), (3, 'c@qq.com'))
    result=cursor.fetchall()
    #------------------------------------在mysql库中查询邮箱--------------------------------------#
    print(f"查询结果{result}")
    print(len(result))
    if len(result)==0:                #在mysql查不到
        data={"code":500,"msg":"邮件失败，你的邮箱未注册"}
        return HttpResponse(json.dumps(data),content_type="application/json")   #以http格式响应（将data转换成json格式，声明返回的数据是json格式）
    try:                                            #代码没有问题，但是支持其的硬件或者网络会出问题导致执行出错或者代码跑不通#
        code = random.randint(1000, 9999)


        #--------------------------创建一个邮件--------------------------------#
        msg = MIMEText(f"你的验证码是:{code}")      #创建一个变量msg就是邮件
        msg["To"] = email
        msg["From"] = "1705731472@qq.com"
        msg["subject"] = "基于YOLO目标检测系统的登陆验证码"
        #---------------------------创建一个邮件-----------------------------------#
        #print(msg)


        #------------------------------------------------发送邮件----------------------------------------#
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
          smtp.login("1705731472@qq.com", "vlechrtpiadgcjjh")
          smtp.sendmail("1705731472@qq.com", email, msg.as_string())
        #------------------------------------------------发送邮件-----------------------------------------#


        data ={"code":200,"msg":"发送成功"}
        rs=HttpResponse(json.dumps(data), content_type="application/json")
        rs.set_cookie("code",str(code))   # 存验证码
        user_name=result[0][1]                 # 从数据库取出用户名
        rs.set_cookie("user_name",quote(str(user_name)))   # URL 编码后存
        return rs
    except Exception as e:
        print(e)
        print("发送失败")
        data={"code":500,"msg":"邮件失败"}
        return HttpResponse(json.dumps(data),content_type="application/json")




def login(request):
   #-------------------------------------------------把刚刚存的东西从cooike中摸出来-user_name要解码--------------------#
    code=request.GET.get("code")
    code_cookie=request.COOKIES.get("code")
    user_name=request.COOKIES.get("user_name")
    print("原始 Cookie 值:", user_name)
    user_name=unquote(user_name)
    print("解码后:",user_name)
#-------------------------------------------------把刚刚存的东西从cooike中摸出来-user_name要解码---------------------------#
    if code==code_cookie:
        data={"code":200,"msg":"登陆成功","data":user_name}
    else:
        data={"code":500,"msg":"验证码不正确"}
    return HttpResponse(json.dumps(data),content_type="application/json")
def register(request):



#---------------------------------------request就是前端发过来的参数包----------------------------------------#
    user_name=request.GET.get("user_name")
    email=request.GET.get("email")
    print(f"用户名{user_name},邮箱{email}")


#------------------------------------看看那个小倒霉蛋子在黑名单里面----------------------------------------#
    con1 = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="guishiyuan_25", charset="utf8")
    sql = f"select * from Black_Name where email='{email}' or user_name='{user_name}'"
    cursor=con1.cursor()
    cursor.execute(sql)
    rs = cursor.fetchall()
    if len(rs)>0:
        data = {"code": 500, "msg": "您在黑名单中，无法使用该系统"}
        return HttpResponse(json.dumps(data), content_type="application/json")
#------------------------------------看看那个小倒霉蛋子在黑名单里面-----------------------------------------------------#



    con = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="guishiyuan_25", charset="utf8")
    sql = f"select * from user_info where email='{email}' or user_name='{user_name}'"
    cursor = con.cursor()  # 这三句是标准的查询程序，把查询结果返回rs查到几个
    cursor.execute(sql)  # 返回的是一个元组组成的集合如果有3个((1, 'a@qq.com'), (2, 'b@qq.com'), (3, 'c@qq.com'))
    rs = cursor.fetchall()
    if len(rs)>0:
        data ={"code":500,"msg":"用户名或者邮箱已被注册"}
        return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="guishiyuan_25",charset="utf8")
        sql = "insert into user_info (user_name,email) values(%s,%s)"
        cursor = conn.cursor()
        cursor.execute(sql,(user_name,email))
        conn.commit()
        num=cursor.rowcount
        if num>0:
            data={"code":200,"msg":"注册成功"}
        else:
            data={"code":500,"msg":"注册失败"}
        return HttpResponse(json.dumps(data),content_type="application/json")

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