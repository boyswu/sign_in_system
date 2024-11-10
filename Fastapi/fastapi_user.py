import os
import asyncio
import threading
from fastapi import Form, File, UploadFile, Depends, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import Model.ToDoModel as ToDoModel
import Tool.email_send as email_send
import Tool.cache_code as cache_code
import Tool.tokens as token
import Tool.password_utf as password_utf
import Tool.minion_bag as minion_bag
from Tool.face_recognize import face_recognize
from Tool.upload import upload_files
from connect_tool.sql import MySQLConnectionPool
from concurrent.futures import ThreadPoolExecutor
from Tool.timer_task import run_schedule

router = APIRouter()

# import logging
#
# logging.basicConfig(level=logging.DEBUG)
"""
创建一个线程池
"""

executor = ThreadPoolExecutor(max_workers=10)  # 线程池最大线程数为10


@router.on_event("startup")
def startup_event():
    # 启动调度任务的线程
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.start()
    print("调度器已启动")


"""
账户
用户注册、登录、邮箱验证、修改密码相关接口=============================================================================

"""


@router.post("/register_mission", summary="注册用户", description="注册用户", tags=['面面通'])
async def register_user(user_name: str = Form(...),
                        user_id: str = Form(...),
                        Password: str = Form(...),
                        email: str = Form(...),
                        file: UploadFile = File(...)):  # 接收前端传来的图片文件
    password = password_utf.encrypt_password(Password)
    if user_name == '' or user_id == '' or password == '' or email == '':
        return JSONResponse(content={"msg": False, "error": "信息不能为空", "status_code": 400})

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    file_content = await file.read()
    _, _, people_face, similar = face_recognize(file_content)

    if similar is False:
        return JSONResponse(content="登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                            status_code=400)
    elif similar == 0:
        return JSONResponse(content="人员不在库中,请联系管理员!!!", status_code=400)
    try:
        with conn.cursor() as cursor:
            if similar and float(similar) > 0.65:
                sql = "SELECT * FROM user WHERE id = '{}'".format(user_id)
                try:
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    if result:
                        # 用户已存在
                        return JSONResponse(content="该人员已注册！", status_code=400)
                    else:
                        # 用户不存在，插入数据
                        sql = "INSERT INTO user (id, name,face ,password,email) VALUES (%s, %s, %s, %s, %s)"
                        try:

                            cursor.execute(sql, (user_id, user_name, people_face, password, email))
                            conn.commit()
                            return JSONResponse(content={"msg": True, "info": "注册成功", "status_code": 200})
                        except Exception as e:
                            conn.rollback()
                            return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

            else:
                # 用户不存在，插入数据
                sql = "INSERT INTO user (id, name,face ,password,email) VALUES (%s, %s, %s, %s, %s)"
                try:
                    cursor.execute(sql, (user_id, user_name, people_face, password, email))
                    conn.commit()
                    return JSONResponse(content={"msg": True, "info": "注册成功", "status_code": 200})
                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/login", summary="账号密码登录", description="账号密码登录", tags=['面面通'])
async def login(login: ToDoModel.login_user):
    """
    账号密码登录
    """
    User_id = login.User_id
    Password = password_utf.encrypt_password(login.Password)
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE id = '{}' AND password = '{}' ".format(User_id, Password)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = token.create_access_token(data={"sub": User_id}, expires_delta=access_token_expires)
                if token.verify_token(access_token) is False:  # 有这样一个方法判断token是否过期
                    return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
                else:
                    return JSONResponse(content={"msg": True, "token": access_token, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "学号或密码错误", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/get_Token", summary="Token获取信息", description="Token获取信息", tags=['面面通'])
async def protected_route(access_Token: dict = Depends(token.verify_token)):
    """
    Token获取信息
    """
    if access_Token is None:
        return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
    print(access_Token)  # 输出字典 {'sub': '123456'}
    User_id = access_Token.get('sub')  # 提取'sub'的值
    Token = token.get_token_data(access_Token)

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT name FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql)
            result = cursor.fetchall()
            Name = result[0][0]
            if result:
                return JSONResponse(
                    content={"msg": True, "User_id": User_id, "Name": Name, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


"""

邮箱相关接口=============================================================================

"""


@router.post("/send_email", summary="发送验证码", description="发送邮件,发送验证码", tags=['面面通'])
async def send_email(email: ToDoModel.get_email):
    """
    发送邮件
    """
    Email = email.Email
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE email = '{}'".format(Email)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                security_code = email_send.send_email(Email)
                # 将receiver_email和security_code以key-value形式缓存起来

                cache_code.get_receiver_email(Email)  # 两个缓存函数，分别缓存receiver_email和security_code
                cache_code.get_security_code(security_code)  # 第一次调用，计算并缓存结果

                # 发送邮件
                return JSONResponse(content={"msg": True, "info": "验证码已发送至邮箱,请注意查收", "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "该邮箱未注册", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 验证验证码
@router.post("/verify_email", summary="验证验证码", description="验证验证码", tags=['面面通'])
async def verify_email(verify: ToDoModel.check_security_code):
    """
    验证验证码
    """
    Email = verify.Email
    Security_code = verify.Security_code
    # 验证验证码
    security_code_in_cache = cache_code.get_security_code(Security_code)
    email_in_cache = cache_code.get_receiver_email(Email)

    if security_code_in_cache is not None and email_in_cache is not None:
        if security_code_in_cache == Security_code and email_in_cache == Email:
            # 执行后续逻辑
            return JSONResponse(content={"msg": True, "status_code": 200})
        else:
            return JSONResponse(content={"msg": False, "error": "验证码错误或邮箱不正确", "status_code": 400})
    else:
        return JSONResponse(content={"msg": False, "error": "验证码或邮箱未找到", "status_code": 404})


# 接收验证码和邮箱账号修改密码
@router.post("/modify_password_by_email", summary="修改密码", description="接收验证码和邮箱账号修改密码",
             tags=['面面通'])
async def modify_password(modify: ToDoModel.modify_password):
    """
    修改密码
    """
    Password = password_utf.encrypt_password(modify.Password)
    Email = modify.Email
    Security_code = modify.Security_code
    # 验证验证码
    if cache_code.get_security_code(Security_code) == Security_code and cache_code.get_receiver_email(Email) == Email:
        # 修改密码
        db_pool = MySQLConnectionPool()
        conn = db_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                print(Password)

                print(Email)
                sql = "UPDATE user SET password = '{}' WHERE email = '{}'".format(Password, Email)
                cursor.execute(sql)
                conn.commit()
                # 缓存修改密码成功
                if cursor.rowcount > 0:
                    return JSONResponse(content={"msg": True, "status_code": 200})
                else:
                    return JSONResponse(content={"msg": False, "error": "修改密码与原密码相同", "status_code": 400})
        except Exception as e:
            return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
        finally:
            db_pool.close_connection(conn)
    else:
        return JSONResponse(content={"msg": False, "error": "验证码错误或邮箱不正确", "status_code": 400})


"""
    签到相关接口===    
    
"""


@router.post("/sign_in", summary="签到", description="签到", tags=['面面通'])
async def sign_in(file: UploadFile = File(...)):
    """
    签到
    """
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            file_content = await file.read()
            User_id, name, _, similar = face_recognize(file_content)
            if similar is False:
                return JSONResponse(content={"msg": False,
                                             "error": "登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})
            elif similar == 0:
                return JSONResponse(content={"msg": False, "error": "人员不在库中,请联系管理员!!!", "status_code": 400})
            if float(similar) > 0.65:  # 当相似度大于0.65时
                # 向数据库中插入签到记录
                # 获取当前时间
                Current_time = datetime.now()

                # 查询同一天里的最后一次签到记录
                sql = (
                    "SELECT begin_time,end_time FROM sign_time WHERE id = '{}' AND DATE(begin_time) = DATE('{}') ORDER "
                    "BY begin_time DESC LIMIT 1").format(User_id, Current_time)
                try:
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    if not result:
                        sql_2 = "INSERT INTO sign_time (id,name,begin_time) VALUES ('{}', '{}', '{}')".format(User_id,
                                                                                                              name,
                                                                                                              Current_time)
                        try:
                            cursor.execute(sql_2)
                            conn.commit()
                            return JSONResponse(
                                content={"msg": True, "info": "{}签到成功".format(name), "status_code": 200})
                        except Exception as e:
                            conn.rollback()
                            return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
                else:

                    being_time = result[0][0]
                    end_time = result[0][1]
                    print(being_time, end_time)

                    if (being_time is None and end_time is None) or (being_time is not None and end_time is not None):

                        # 向数据库中插入签到记录
                        sql_2 = "INSERT INTO sign_time (id,name,begin_time) VALUES ('{}', '{}', '{}')".format(User_id,
                                                                                                              name,
                                                                                                              Current_time)
                        try:
                            cursor.execute(sql_2)
                            conn.commit()
                            return JSONResponse(
                                content={"msg": True, "info": "{}签到成功".format(name), "status_code": 200})
                        except Exception as e:
                            conn.rollback()
                            return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
                    else:
                        # 签到失败，提示用户
                        return JSONResponse(
                            content={"msg": False, "error": "您今天已经签到,请勿重复操作！", "status_code": 400})
            else:
                print("登录失败，提示用户")
                # 登录失败，提示用户
                return JSONResponse(content="登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                    status_code=400)

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 签退
# @router.post("/sign_out", summary="签退", description="签退", tags=['面面通'])
# async def sign_out(access_Token: dict = Depends(token.verify_token)):
#     """
#     签退
#     """

#     db_pool = MySQLConnectionPool()
#     conn = db_pool.get_connection()
#     User_id = access_Token.get('sub')
#     # Token = token.get_token_data(access_Token)  # 获取Token

#     try:
#         with conn.cursor() as cursor:
#
#             # 获取当前时间
#             Current_time = datetime.now()
#             # 查询同一天里的最后一次签到记录
#             sql = ("SELECT begin_time,end_time,name FROM sign_time WHERE id = '{}' AND DATE(begin_time) = DATE('{}') "
#                    "ORDER BY begin_time DESC LIMIT 1").format(User_id, Current_time)
#
#             cursor.execute(sql)
#             result = cursor.fetchall()
#             if result:
#                 begin_time = result[0][0]
#                 end_time = result[0][1]
#                 name = result[0][2]
#                 if end_time is None and begin_time is not None:
#                     # 查询
#                     sql_1 = "SELECT * FROM day_time WHERE id = '{}' AND DATE(date)= DATE('{}')".format(User_id,
#                                                                                                        begin_time)
#                     try:
#                         cursor.execute(sql_1)
#                         result1 = cursor.fetchall()
#                     except Exception as e:
#                         print(2)
#                         return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#                     # 查询学习时长
#                     sql_2 = "SELECT * FROM week_time WHERE YEARWEEK(date) = YEARWEEK(NOW())"
#                     try:
#                         cursor.execute(sql_2)
#                         result2 = cursor.fetchall()
#                     except Exception as e:
#                         return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#                     now_time = datetime.now()  # 不使用 strftime，直接使用 datetime 对象
#                     # 计算时间差
#                     duration = now_time - begin_time
#                     # 将时间差转换为小时
#                     duration = duration.total_seconds() / 3600
#                     duration = round(duration, 2)  # 保留两位小数
#                     if result1:
#                         # 向数据库中插入签退记录
#                         sql = (
#                             "UPDATE sign_time SET end_time = '{}', duration = '{}', status = '{}' WHERE id = '{}' "
#                             "AND begin_time = '{}'").format(Current_time, duration, "已签退", User_id, begin_time)
#                         sql_1 = "UPDATE day_time SET duration = +'{}' WHERE id = '{}' AND DATE(date) = DATE('{}')".format(
#                             duration, User_id, Current_time)
#                         if result2:
#                             sql_2 = ("UPDATE week_time SET duration = +'{}' WHERE id = '{}' AND YEARWEEK(date) = "
#                                      "YEARWEEK(NOW())").format(duration, User_id, Current_time)
#                             try:
#                                 cursor.execute(sql)
#                                 cursor.execute(sql_1)
#                                 cursor.execute(sql_2)
#                                 conn.commit()
#                                 return JSONResponse(content={"msg": True, "info": "签退成功", "status_code": 200})
#                             except Exception as e:
#                                 conn.rollback()
#                                 return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#                         else:
#                             sql_2 = "INSERT INTO week_time (id,name,date,duration) VALUES ('{}', '{}', '{}', '{}')".format(
#                                 User_id,
#                                 name,
#                                 Current_time,
#                                 0)
#                             try:
#                                 cursor.execute(sql)
#                                 cursor.execute(sql_1)
#                                 cursor.execute(sql_2)
#                                 conn.commit()
#                                 return JSONResponse(content={"msg": True, "info": "签退成功", "status_code": 200})
#                             except Exception as e:
#                                 conn.rollback()
#                                 return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#                     else:
#                         # 向数据库中插入签退记录
#                         sql = (
#                             "UPDATE sign_time SET end_time = '{}', duration = '{}', status = '{}' WHERE id = '{}' "
#                             "AND begin_time = '{}'").format(Current_time, duration, "已签退", User_id, begin_time)
#                         sql_1 = "INSERT INTO day_time (id,name,date,duration) VALUES ('{}', '{}', '{}', '{}')".format(
#                             User_id, name, Current_time, duration)
#                         if result2:
#                             sql_2 = ("UPDATE week_time SET duration = +'{}' WHERE id = '{}' AND YEARWEEK(date) = "
#                                      "YEARWEEK(NOW())").format(duration, User_id, Current_time)
#                             try:
#                                 cursor.execute(sql)
#                                 cursor.execute(sql_1)
#                                 cursor.execute(sql_2)
#                                 conn.commit()
#                                 return JSONResponse(content={"msg": True, "info": "签退成功", "status_code": 200})
#                             except Exception as e:
#                                 conn.rollback()
#                                 return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#                         else:
#                             sql_2 = "INSERT INTO week_time (id,name,date,duration) VALUES ('{}', '{}', '{}', '{}')".format(
#                                 User_id,
#                                 name,
#                                 Current_time,
#                                 0)
#                             try:
#                                 cursor.execute(sql)
#                                 cursor.execute(sql_1)
#                                 cursor.execute(sql_2)
#                                 conn.commit()
#                                 return JSONResponse(content={"msg": True, "info": "签退成功", "status_code": 200})
#                             except Exception as e:
#                                 conn.rollback()
#                                 return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#                 else:
#                     print("签退失败，提示用户")
#                     # 签退失败，提示用户
#                     return JSONResponse(
#                         content={"msg": False, "error": "您今天已经签退,请勿重复操作！", "status_code": 400})
#             else:
#                 # 签退失败，提示用户
#                 return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})
#
#     except Exception as e:
#         print("1")
#         return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#
#     finally:
#         db_pool.close_connection(conn)


@router.post("/sign_out", summary="签退", description="签退", tags=['面面通'])
async def sign_out(access_Token: dict = Depends(token.verify_token)):
    """
    签退
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    User_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:
            # 获取当前时间
            Current_time = datetime.now()

            # 查询同一天里的最后一次签到记录
            sql = ("SELECT begin_time, end_time, name FROM sign_time "
                   "WHERE id = %s AND DATE(begin_time) = DATE(%s) "
                   "ORDER BY begin_time DESC LIMIT 1")
            cursor.execute(sql, (User_id, Current_time))
            result = cursor.fetchone()

            if result:
                begin_time, end_time, name = result

                if end_time is not None:
                    return JSONResponse(
                        content={"msg": False, "error": "您今天已经签退,请勿重复操作！", "status_code": 400})

                now_time = datetime.now()
                # 计算时间差
                duration = round((now_time - begin_time).total_seconds() / 3600, 2)  # 转换为小时并保留两位小数
                if duration > 0:
                    # 更新数据库
                    update_sql = (
                        "UPDATE sign_time SET end_time = '{}', duration = '{}', status = '{}' WHERE id = '{}' AND "
                        "begin_time = '{}'").format(Current_time, duration, "已签退", User_id, begin_time)
                    cursor.execute(update_sql)

                    # 先尝试更新，如果没有更新到行数，则插入
                    update_sql = (
                        "UPDATE day_time SET duration = duration + '{}' WHERE id = '{}' AND DATE(date) = DATE('{"
                        "}')").format(duration, User_id, Current_time)
                    cursor.execute(update_sql)

                    if cursor.rowcount == 0:  # 如果没有更新到任何行
                        insert_sql = ("INSERT INTO day_time (id, name, description, date, duration) "
                                      "VALUES ('{}', '{}' ,'{}','{}','{}')").format(User_id, name, "无", Current_time,
                                                                                    duration)
                        cursor.execute(insert_sql)

                    # 如果记录存在，则更新其时长
                    update_week_time_sql = ("UPDATE week_time SET duration = duration +'{}' "
                                            "WHERE id = '{}' AND  YEARWEEK(date) = YEARWEEK(NOW())").format(duration,
                                                                                                            User_id)
                    cursor.execute(update_week_time_sql)
                    if cursor.rowcount == 0:  # 如果没有更新到任何行
                        # 如果记录不存在，则插入新记录
                        insert_week_time_sql = ("INSERT INTO week_time (id, name, date, duration) VALUES"
                                                " ('{}', '{}', '{}', '{}')").format(User_id, name, Current_time,
                                                                                    duration)
                        cursor.execute(insert_week_time_sql)

                    conn.commit()

                    return JSONResponse(content={"msg": True, "info": "{}签退成功".format(name), "status_code": 200})
                else:
                    delete_sql = ("DELETE FROM sign_time WHERE id = '{}' AND  DATE(begin_time) = DATE(CURDATE()) "
                                  "ORDER BY begin_time DESC LIMIT 1").format(User_id)
                    cursor.execute(delete_sql)
                    conn.commit()
                    return JSONResponse(
                        content={"msg": False, "error": "学习时长为0,不予记录！", "status_code": 400})
            else:
                return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.post("/face_sign_out", summary="人脸签退", description="人脸签退", tags=['面面通'])
async def face_sign_out(file: UploadFile = File(...)):
    """
    人脸签退
    """

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            file_content = await file.read()
            User_id, name, _, similar = face_recognize(file_content)
            if similar is False:
                return JSONResponse(content={"msg": False,
                                             "error": "登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})
            elif similar == 0:
                return JSONResponse(content={"msg": False, "error": "人员不在库中,请联系管理员!!!", "status_code": 400})
            if float(similar) > 0.65:  # 当相似度大于0.65时
                # 获取当前时间
                Current_time = datetime.now()

                # 查询同一天里的最后一次签到记录
                sql = ("SELECT begin_time, end_time, name FROM sign_time "
                       "WHERE id = %s AND DATE(begin_time) = DATE(%s) "
                       "ORDER BY begin_time DESC LIMIT 1")
                cursor.execute(sql, (User_id, Current_time))
                result = cursor.fetchone()

                if result:
                    begin_time, end_time, name = result

                    if end_time is not None:
                        return JSONResponse(
                            content={"msg": False, "error": "您今天已经签退,请勿重复操作！", "status_code": 400})

                    now_time = datetime.now()
                    # 计算时间差
                    duration = round((now_time - begin_time).total_seconds() / 3600, 2)  # 转换为小时并保留两位小数

                    if duration > 0:

                        # 更新数据库
                        update_sql = (
                            "UPDATE sign_time SET end_time = '{}', duration = '{}', status = '{}' WHERE id = '{}' AND "
                            "begin_time = '{}'").format(Current_time, duration, "已签退", User_id, begin_time)
                        cursor.execute(update_sql)
                        # 先尝试更新，如果没有更新到行数，则插入
                        update_sql = (
                            "UPDATE day_time SET duration = duration + '{}' WHERE id = '{}' AND DATE(date) = DATE('{"
                            "}')").format(duration, User_id, Current_time)
                        cursor.execute(update_sql)

                        if cursor.rowcount == 0:  # 如果没有更新到任何行
                            insert_sql = ("INSERT INTO day_time (id, name, description, date, duration) "
                                          "VALUES ('{}', '{}' ,'{}','{}','{}')").format(User_id, name, "无",
                                                                                        Current_time,
                                                                                        duration)
                            cursor.execute(insert_sql)

                        # 如果记录存在，则更新其时长
                        update_week_time_sql = ("UPDATE week_time SET duration = duration +'{}' "
                                                "WHERE id = '{}' AND  YEARWEEK(date) = YEARWEEK(NOW())").format(
                            duration,
                            User_id)
                        cursor.execute(update_week_time_sql)
                        if cursor.rowcount == 0:  # 如果没有更新到任何行
                            # 如果记录不存在，则插入新记录
                            insert_week_time_sql = ("INSERT INTO week_time (id, name, date, duration) VALUES"
                                                    " ('{}', '{}', '{}', '{}')").format(User_id, name, Current_time,
                                                                                        duration)
                            cursor.execute(insert_week_time_sql)

                        conn.commit()
                        return JSONResponse(
                            content={"msg": True, "info": "{}签退成功".format(name), "status_code": 200})
                    else:
                        delete_sql = ("DELETE FROM sign_time WHERE id = '{}' AND  DATE(begin_time) = DATE(CURDATE()) "
                                      "ORDER BY begin_time DESC LIMIT 1").format(User_id)
                        cursor.execute(delete_sql)
                        conn.commit()
                        return JSONResponse(
                            content={"msg": False, "error": "学习时长为0,不予记录！", "status_code": 400})
                else:
                    return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})

    except Exception as e:
        conn.rollback()
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

    finally:
        db_pool.close_connection(conn)


# # 获取所有人一天的学习时长
# @router.get("/get_all_study_time", summary="获取所有人一天的学习时长", description="获取所有人一天的学习时长",
#             tags=['面面通'])
# async def get_all_study_time(access_Token: dict = Depends(token.verify_token)):
#     db_pool = MySQLConnectionPool()
#     conn = db_pool.get_connection()
#     try:
#         with conn.cursor() as cursor:
#             sql_1 = "SELECT id,name,picture FROM user"
#             cursor.execute(sql_1)
#             result1 = cursor.fetchall()
#             infor = []
#             if result1:
#                 for i in range(len(result1)):
#                     id1, name1, picture1 = result1[i]
#                     infor.append({"id": id1, "name": name1, "day_duration": 0, "picture": picture1})
#             else:
#                 return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})
#
#             # 查询所有人同一天里的end_time为空的签到记录
#             sql = "SELECT id,begin_time FROM sign_time WHERE DATE(begin_time) = CURDATE() AND end_time IS NULL"
#
#             cursor.execute(sql)
#             result = cursor.fetchall()
#             # 有部分人签到，有部分人没签到
#             if result:
#                 Current_time = datetime.now()  # 不使用 strftime，直接使用 datetime 对象
#
#                 info1 = []
#                 for i in range(len(result)):
#                     # 计算时间差
#                     User_id = result[i][0]
#                     begin_time = result[i][1]
#                     duration = Current_time - begin_time
#                     # 将时间差转换为小时
#                     duration = duration.total_seconds() / 3600
#                     duration = round(duration, 2)  # 保留两位小数
#                     info1.append((User_id, duration))
#
#                     # 查询学习时长
#                 sql = "SELECT id,name,duration FROM day_time WHERE DATE(date) = CURDATE()"
#
#                 cursor.execute(sql)
#                 result1 = cursor.fetchall()
#                 info2 = []
#                 # 今天签到过并且今天签退后再次签到，未签退的记录
#                 if result1:
#                     for x in range(len(result1)):
#                         id, name, day_duration = result1[x]
#                         for z in range(len(infor)):  # 遍历infor列表
#                             id_infor = infor[z]["id"]  # 从infor获取当前用户的id
#                             user_found = False  # 标记是否找到对应用户
#                             for y in range(len(info1)):  # 遍历info1列表 sign_time表
#                                 if info1[y][0] == id_infor:
#                                     # 今天签到过并且今天签退后再次签到，未签退的加上未签退的记录的学习时长
#                                     name_infor, picture_infor = infor[z]["name"], infor[z]["picture"]
#                                     if info1[y][0] == id:
#                                         day_duration = float(day_duration) + float(info1[y][1])  # 累加学习时长
#                                         info2.append(
#                                             {"id": id_infor, "name": name_infor, "day_duration": day_duration,
#                                              "picture": picture_infor})
#                                         user_found = True  # 找到对应用户，设置标记为True
#                                         break  # 找到后跳出内层循环
#                                     else:
#                                         # 签到过一次，但没签退
#                                         id1, name1 = infor[y]["id"], infor[y]["name"]
#                                         info2.append(
#                                             {"id": id1, "name": name1, "day_duration": float(info1[y][1]),
#                                              "picture": picture_infor})
#                                         user_found = True  # 找到对应用户，设置标记为True
#                                         break
#
#                             if not user_found:  # 如果没有找到对应用户
#                                 # 今天没签到
#                                 print("今天没签到")
#
#                                 info2.append({"id": id_infor, "name": name_infor, "day_duration": 0,
#                                               "picture": picture_infor})
#                     return JSONResponse(content={"msg": True, "info": info2, "status_code": 200})
#                 # 部分人今天都签到过，但今天都没签退，day_time表没有记录
#                 else:
#                     for z in range(len(infor)):
#                         id_infor = infor[z]["id"]  # 从infor获取当前用户的id
#                         user_found = False  # 标记是否找到对应用户
#                         for y in range(len(info1)):  # 遍历info1列表
#                             if info1[y][0] == id_infor:  # 检查info1中的用户id是否与infor的用户id匹配
#                                 print("部分人今天都签到过并且今天都没签退，day_time表没有记录")
#                                 id1, name1, picture = infor[z]["id"], infor[z]["name"], infor[z]["picture"]
#                                 info2.append({"id": id1, "name": name1, "day_duration": float(info1[y][1]),
#                                               "picture": picture})
#                                 user_found = True  # 找到对应用户，设置标记为True
#                                 break  # 找到后跳出内层循环
#                         if not user_found:  # 如果没有找到对应用户
#                             print("今天没签到")  # 输出签到信息
#                             id1, name1, picture = infor[z]["id"], infor[z]["name"], infor[z]["picture"]
#                             info2.append({"id": id1, "name": name1, "day_duration": 0, "picture": picture})
#                     return JSONResponse(content={"msg": True, "info": info2, "status_code": 200})
#
#             # 要么今天部分人都签退了，要么今天所有人都没签到
#             else:
#                 # 查询学习时长
#                 sql = "SELECT id,name,duration FROM day_time WHERE DATE(date) = CURDATE()"
#                 cursor.execute(sql)
#                 result = cursor.fetchall()
#                 info2 = []
#                 if result:
#                     for i in range(len(result)):
#                         id2, name2, day_duration = result[i]
#                         user_found = False  # 标记是否找到对应用户
#                         for j in range(len(infor)):
#                             picture = infor[j]["picture"]
#                             # 今天部分人有签到记录
#                             if infor[j]["id"] == id2:
#                                 print("今天部分人有签到记录")
#                                 info2.append(
#                                     {"id": id2, "name": name2, "day_duration": day_duration, "picture": picture})
#                                 user_found = True  # 找到对应用户，设置标记为True
#                                 break  # 找到后跳出内层循环
#                             # 今天部分人无签到记录
#                         if not user_found:
#                             print("今天部分人无签到记录")
#                             id1, name1 = infor[j]["id"], infor[j]["name"]
#                             info2.append({"id": id1, "name": name1, "day_duration": 0, "picture": picture})
#                     return JSONResponse(content={"msg": True, "info": infor, "status_code": 200})
#                 # 今天所有人都没签到
#                 else:
#                     print("今天所有人都没签到")
#                     return JSONResponse(content={"msg": True, "info": infor, "status_code": 200})
#
#     except Exception as e:
#         return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#     finally:
#         db_pool.close_connection(conn)
#

@router.get("/get_all_study_time", summary="获取所有人一天的学习排名", description="获取所有人一天的学习排名",
            tags=['面面通'])
async def get_all_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取所有人一天的学习排名
    return:
        {
            "msg": True,
            "info": {
                "id": "123456",
                "name": "张三",
                "day_duration": 10,
                "picture": "http://43.143.229.40:9000/photo/1.jpg",
            },
            "status_code": 200
        }
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            # 获取用户信息
            cursor.execute("SELECT id, name, picture FROM user")
            results = cursor.fetchall()

            if not results:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            user_info = [{"id": user[0], "name": user[1], "day_duration": 0, "picture": user[2]} for user in results]

            # 查询今天签到记录
            cursor.execute(
                "SELECT id, begin_time FROM sign_time WHERE DATE(begin_time) = CURDATE() AND end_time IS NULL")
            sign_in_records = cursor.fetchall()

            current_time = datetime.now()
            duration_info = {user["id"]: 0 for user in user_info}  # 初始化学习时长字典

            if sign_in_records:
                for user_id, begin_time in sign_in_records:
                    duration = round((current_time - begin_time).total_seconds() / 3600, 2)
                    duration_info[user_id] += duration

            # 查询今天的学习时长
            cursor.execute("SELECT id,duration FROM day_time WHERE DATE(date) = CURDATE()")
            day_time_records = cursor.fetchall()

            for record in day_time_records:
                user_id, day_duration = record
                duration_info[user_id] += day_duration  # 累加今天的学习时长

            for user in user_info:
                user["day_duration"] = duration_info[user["id"]]

            # 排序
            user_info.sort(key=lambda x: x["day_duration"], reverse=True)
            return JSONResponse(content={"msg": True, "info": user_info, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


#
# # 获取所有人一周的学习时长
# @router.get("/get_week_all_study_time", summary="获取所有人一周的学习时长", description="获取所有人一周的学习时长",
#             tags=['面面通'])
# async def get_week_all_study_time(access_Token: dict = Depends(token.verify_token)):
#     """
#     获取所有人一周的学习时长
#     """
#     db_pool = MySQLConnectionPool()
#     conn = db_pool.get_connection()
#
#     try:
#         with conn.cursor() as cursor:
#             sql_1 = "SELECT id,name,picture FROM user"
#             cursor.execute(sql_1)
#             result1 = cursor.fetchall()
#             info = []
#             if result1:
#                 for i in range(len(result1)):
#                     id1, name1, picture1 = result1[i]
#                     info.append({"id": id1, "name": name1, "week_duration": 0, "picture": picture1})
#             else:
#                 return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})
#             # 查询同一周的某一天里的end_time为空的签到记录
#             sql = ("SELECT id,begin_time FROM sign_time WHERE YEARWEEK(begin_time) = YEARWEEK(NOW()) AND end_time IS "
#                    "NULL")
#
#             cursor.execute(sql)
#             result = cursor.fetchall()
#             # 有部分人签到过多次，有部分人签到过一次,有部分人没签到
#             if result:
#                 Current_time = datetime.now()  # 不使用 strftime，直接使用 datetime 对象
#                 #
#                 info1 = []
#                 for i in range(len(result)):
#                     # 计算时间差
#                     User_id = result[i][0]
#                     begin_time = result[i][1]
#                     duration = Current_time - begin_time
#                     # 将时间差转换为小时
#                     duration = duration.total_seconds() / 3600
#                     duration = round(duration, 2)  # 保留两位小数
#                     info1.append((User_id, duration))
#                 sql = "SELECT id,name,duration FROM week_time WHERE YEARWEEK(date) = YEARWEEK(NOW())"
#                 cursor.execute(sql)
#                 result1 = cursor.fetchall()
#                 info2 = []
#                 # 部分人本周签到过并且本周有签退后再次签到,未签退的记录，部分人本周没签到
#                 if result1:
#                     for x in range(len(result1)):
#                         id, name, week_duration = result1[x]
#
#                         for z in range(len(info)):
#                             user_found = False  # 标记是否找到对应用户
#                             # 判断用户表id是否在sign_time表中,没有就是本周没签到
#                             id2, name2, picture = info[z]["id"], info[z]["name"], info[z]["picture"]
#                             for y in range(len(info1)):
#                                 if info1[y][0] == info[z]["id"]:
#                                     # 本周签到过并且本周有签退后再次签到,未签退的加上未签退的记录的学习时长
#                                     if info1[y][0] == id:
#                                         week_duration = float(week_duration) + float(info1[y][1])
#                                         info2.append(
#                                             {"id": id2, "name": name2, "week_duration": week_duration,
#                                              "picture": picture})
#                                         user_found = True  # 找到对应用户，设置标记为True
#                                         break  # 找到后跳出内层循环
#                                     # 本周签到过但本周没签退的记录(签到过一次，但没签退)
#                                     else:
#                                         id1, name1 = info[z]["id"], info[z]["name"]
#                                         info2.append(
#                                             {"id": id1, "name": name1, "week_duration": float(info1[y][1]),
#                                              "picture": picture})
#                                         user_found = True  # 找到对应用户，设置标记为True
#                                         break  # 找到后跳出内层循环
#                             if not user_found:  # 如果没有找到对应用户
#                                 # 本周没签到
#                                 info2.append(
#                                     {"id": id2, "name": name2, "week_duration": 0, "picture": picture})
#
#                     return JSONResponse(content={"msg": True, "info": info2, "status_code": 200})
#                 # 部分人本周都签到过，但本周都没签退，week_time表没有记录
#                 else:
#                     for z in range(len(info)):
#                         id2, name2, picture = info[z]["id"], info[z]["name"], info[z]["picture"]
#                         user_found = False  # 标记是否找到对应用户
#                         for y in range(len(info1)):
#                             # 判断用户表id是否在sign_time表中,没有就是本周没签到
#                             if info[y][0] == id2:
#                                 info2.append(
#                                     {"id": id2, "name": name2, "week_duration": float(info1[y][1]),
#                                      "picture": picture})
#                                 user_found = True
#                                 break
#                         if not user_found:
#                             # 本周没签到
#                             info2.append({"id": id2, "name": name2, "week_duration": 0, "picture": picture})
#
#                     return JSONResponse(content={"msg": True, "info": info2, "status_code": 200})
#
#             # 要么本周部分人都签退了，要么本周所有人都没签到
#             else:
#                 # 查询学习时长
#                 sql = "SELECT id,name,duration FROM week_time WHERE YEARWEEK(date) = YEARWEEK(NOW())"
#
#                 cursor.execute(sql)
#                 result = cursor.fetchall()
#                 info3 = []
#                 if result:
#                     for i in range(len(result)):
#                         id2, name2, week_duration = result[i]
#                         user_found = False  # 标记是否找到对应用户
#                         for j in range(len(info)):
#                             picture = info[j]["picture"]
#                             # 本周有签到记录
#                             if info[j]["id"] == id2:
#                                 info3.append(
#                                     {"id": id2, "name": name2, "week_duration": week_duration,
#                                      "picture": picture})
#                                 user_found = True
#                                 break
#                         if not user_found:
#                             info3.append({"id": id2, "name": name2, "week_duration": 0, "picture": picture})
#                     return JSONResponse(content={"msg": True, "info": info3, "status_code": 200})
#                 # 本周所有人都没签到
#                 else:
#                     return JSONResponse(content={"msg": True, "info": info, "status_code": 200})
#     except Exception as e:
#         return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#     finally:
#         db_pool.close_connection(conn)


@router.get("/get_week_all_study_time", summary="获取所有人一周的学习排名", description="获取所有人一周的学习排名",
            tags=['面面通'])
async def get_week_all_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取所有人一周的学习排名
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, picture FROM user")
            results = cursor.fetchall()
            if not results:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            # 初始化用户信息
            user_info = [{"id": user[0], "name": user[1], "week_duration": 0, "picture": user[2]} for user in results]

            # 查询本周内的签到记录
            cursor.execute(
                "SELECT id, begin_time FROM sign_time WHERE YEARWEEK(begin_time) = YEARWEEK(NOW()) AND end_time IS NULL")
            sign_in_records = cursor.fetchall()

            current_time = datetime.now()
            duration_info = {user["id"]: 0 for user in user_info}  # 初始化学习时长字典

            # 计算签到用户的学习时长
            for user_id, begin_time in sign_in_records:
                duration = round((current_time - begin_time).total_seconds() / 3600, 2)
                duration_info[user_id] += duration

            # 查询本周的学习时长
            cursor.execute("SELECT id, duration FROM week_time WHERE YEARWEEK(date) = YEARWEEK(NOW())")
            week_time_records = cursor.fetchall()

            # 将本周学习时长添加到用户信息
            for user_id, week_duration in week_time_records:
                duration_info[user_id] += week_duration

            for user in user_info:
                user["week_duration"] = duration_info[user["id"]]
            # 排序
            user_info.sort(key=lambda x: x["week_duration"], reverse=True)
            return JSONResponse(content={"msg": True, "info": user_info, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# @router.get("/get_one_study_time", summary="获取一个人两周周里每一天的学习时长",
#             description="获取一个人前两周里每一天的学习时长不包括今天",
#             tags=['面面通'])
# async def get_one_study_time(access_Token: dict = Depends(token.verify_token)):
#     """
#     获取一个人前两周里每一天的学习时长不包括今天
#     """
#     db_pool = MySQLConnectionPool()
#     conn = db_pool.get_connection()
#     User_id = access_Token.get('sub')
#     try:
#         with conn.cursor() as cursor:
#             # 查询用户信息
#             sql_1 = "SELECT id,name,picture FROM user WHERE id = '{}'".format(User_id)
#
#             cursor.execute(sql_1)
#             result1 = cursor.fetchall()
#             if result1:
#                 id1, name1, picture1 = result1[0]
#             else:
#                 return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})
#
#             # 查询day_time表中该用户14天的学习时长,日期,心得不包括今天的记录
#             sql = ("SELECT DATE(date),duration,description FROM day_time WHERE id = '{}' "
#                    "AND DATE(date) NOT IN (CURDATE()) AND DATE(date) BETWEEN DATE_SUB(NOW(), INTERVAL 7 DAY) AND NOW()").format(
#                 User_id)
#             cursor.execute(sql)
#             result = cursor.fetchall()
#             data = []
#             if result:
#                 for i in range(len(result)):
#                     date, duration, description = result[i][0], result[i][1], result[i][2]
#                     data.append(
#                         {"id": id1, "name": name1, "date": date, "duration": duration, "description": description,
#                          "picture": picture1})
#                     return JSONResponse(content={"msg": True, "info": data, "status_code": 200})
#             else:
#                 return JSONResponse(content={"msg": True, "info": data, "status_code": 200})
#     except Exception as e:
#         return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
#     finally:
#         db_pool.close_connection(conn)


@router.get("/get_one_study_time", summary="获取一个人七天的学习时长",
            description="获取一个人七天的学习时长",
            tags=['面面通'])
async def get_one_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取一个人七天的学习时长
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    User_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:
            # 查询用户信息
            cursor.execute("SELECT id, name, picture FROM user WHERE id = %s", (User_id,))
            result1 = cursor.fetchone()

            if not result1:
                return JSONResponse(content={"msg": False, "error": "用户信息获取失败", "status_code": 400})

            # 查询day_time表中该用户14天的学习时长,日期,心得不包括今天的记录
            cursor.execute("SELECT DATE(date), duration, description FROM day_time WHERE id = %s "
                           "AND DATE(date) NOT IN (CURDATE()) AND DATE(date) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
                           (User_id,))
            result = cursor.fetchall()

            date = [date.strftime("%m-%d") for date, duration, description in result]  # 使用列表生成式
            duration = [duration for date, duration, description in result]

            return JSONResponse(content={"msg": True, "date": date, "duration": duration, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

    finally:
        db_pool.close_connection(conn)


async def upload_file_to_minion_bag(bucket_name, object_name, file_path, content_type):
    loop = asyncio.get_event_loop()
    # 使用线程池提交任务
    msg = await loop.run_in_executor(executor, minion_bag.UploadObject, bucket_name, object_name, file_path,
                                     content_type, False)
    return msg


@router.post("/upload_file", summary="上传/修改头像", description="上传/修改头像", tags=['面面通'])
async def upload_file(file: UploadFile = File(...), access_Token: dict = Depends(token.verify_token)):
    """
    上传/修改头像
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})

    User_id = access_Token.get('sub')
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:

            Bucket_name = "photo"
            # 上传文件的方法返回文件路径
            file_path = upload_files(file)
            # 上传文件到minion_bag
            object_name = file.filename
            content_type = file.content_type
            # 将文件上传任务交给线程池
            msg = await upload_file_to_minion_bag(Bucket_name, object_name, file_path, content_type)
            if msg:
                os.remove(file_path)
                file_url = f'http://43.143.229.40:9000/{Bucket_name}/{file.filename}'
                # 更新用户头像
                sql = "UPDATE user SET picture = '{}' WHERE id = '{}'".format(file_url, User_id)
                try:
                    cursor.execute(sql)
                    conn.commit()
                    return JSONResponse(content={"msg": True, "info": {"file_url": file_url}, "status_code": 200})
                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

            else:
                return JSONResponse(content={"msg": False, "error": "上传失败", "status_code": 400})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 添加每日心得
@router.post("/add_day_description", summary="添加每日心得", description="添加每日心得", tags=['面面通'])
async def add_day_description(day_description: ToDoModel.description, access_Token: dict = Depends(token.verify_token)):
    """
    添加每日心得
    """
    if access_Token is False:
        return JSONResponse(content={"msg": False, "error": "登录已过期,请重新登录", "status_code": 401})
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()  # 获取数据库连接

    description = day_description.description
    # 获取用户id
    User_id = access_Token.get('sub')

    try:
        with conn.cursor() as cursor:
            # 更新day_time表只要今天的记录
            day_time = datetime.now()
            sql = "UPDATE day_time SET description = '{}' WHERE id = '{}' AND DATE(date) = '{}'".format(description,
                                                                                                        User_id,
                                                                                                        day_time)
            cursor.execute(sql)
            conn.commit()

            return JSONResponse(content={"msg": True, "description": description, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)
