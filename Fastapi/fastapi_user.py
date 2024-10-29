from fastapi import Form, File, UploadFile, Depends, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import Model.ToDoModel as ToDoModel
import Tool.email_send as email_send
import Tool.cache_code as cache_code
import Tool.tokens as token
import Tool.password as password
from Tool.face_recognize import face_recognize
from connect_tool.sql import MySQLConnectionPool
from concurrent.futures import ThreadPoolExecutor, as_completed
from seetaface.api import *

router = APIRouter()

# import logging
#
# logging.basicConfig(level=logging.DEBUG)

#  seetaface初始化
init_mask = FACE_DETECT | FACERECOGNITION | LANDMARKER5
seetaFace = SeetaFace(init_mask)  # 初始化

executor = ThreadPoolExecutor(max_workers=10)  # 线程池最大线程数为10
"""
创建一个线程池
"""

"""
账户
用户注册、登录、邮箱验证、修改密码相关接口=============================================================================

"""


def select_one_sql():
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM name_feature"
            cursor.execute(sql)
            results = cursor.fetchall()
            return results
    except Exception as e:
        return False

    finally:
        db_pool.close_connection(conn)


@router.post("/register_mission", summary="注册用户", description="注册用户", tags=['账户'])
async def register_user(user_name: str = Form(...),
                        user_id: str = Form(...),
                        password: str = Form(...),
                        email: str = Form(...),
                        file: UploadFile = File(...)):  # 接收前端传来的图片文件
    if user_name == '' or user_id == '' or password == '' or email == '':
        return JSONResponse(content={"msg": False, "error": "信息不能为空", "status_code": 400})
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    file_content = await file.read()
    _, people_face, similar = face_recognize(file_content)
    if similar is False:
        return JSONResponse(content="登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                            status_code=400)
    elif similar == 0:
        return JSONResponse(content="人员不在库中,请联系管理员!!!", status_code=400)
    try:
        with conn.cursor() as cursor:
            if float(max(similar)) > 0.65:  # 当相似度大于0.65时
                sql = "SELECT * FROM user WHERE id = '{}'".format(user_id)
                try:
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    print(result)
                    if result:
                        # 用户已存在
                        return JSONResponse(content="该人员已注册！", status_code=400)
                    else:
                        # 用户不存在，插入数据
                        sql = "INSERT INTO user (id, name,face password,email) VALUES ('{}', '{}', '{}', '{}', '{}')".format(
                            user_id, user_name, people_face, password, email)
                        try:
                            cursor.execute(sql)
                            conn.commit()
                            return JSONResponse(content={"msg": True, "data": "注册成功", "status_code": 200})
                        except Exception as e:
                            conn.rollback()
                            return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

            else:
                # 用户不存在，插入数据
                sql = "INSERT INTO user (id, name, password,email) VALUES ('{}', '{}', '{}', '{}')".format(
                    user_id, user_name, password, email)
                try:
                    cursor.execute(sql)
                    conn.commit()
                    return JSONResponse(content={"msg": True, "data": "注册成功", "status_code": 200})
                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
                finally:
                    db_pool.close_connection(conn)

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})


@router.post("/login", summary="账号密码登录", description="账号密码登录", tags=['账户'])
async def login(login: ToDoModel.login_user):
    """
    账号密码登录
    """
    User_id = login.User_id
    Password = password.encrypt_password(login.Password)

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
                if token.check_token_expiration(access_token):  # 假设有这样一个方法判断token是否过期
                    return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})
                else:
                    return JSONResponse(content={"msg": True, "data": access_token, "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "学号或密码错误", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


@router.get("/get_Token", summary="Token获取信息", description="Token获取信息", tags=['账户'])
async def protected_route(access_Token: dict = Depends(token.verify_token)):
    """
    Token获取信息
    """
    print(access_Token)  # 输出字典 {'sub': '123456'}
    User_id = access_Token.get('sub')  # 提取'sub'的值
    Token = token.get_token_data(access_Token)
    if token.check_token_expiration(Token):  # 假设有这样一个方法判断token是否过期
        return JSONResponse(content={"msg": False, "error": "Token已过期", "status_code": 201})

    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE id = '{}'".format(User_id)
            cursor.execute(sql)
            result = cursor.fetchone()
            User_id, Name, _, _, _, _ = result
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


@router.post("/send_email", summary="发送验证码", description="发送邮件,发送验证码", tags=['邮箱'])
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
                return JSONResponse(content={"msg": True, "data": "验证码已发送至邮箱,请注意查收", "status_code": 200})
            else:
                return JSONResponse(content={"msg": False, "error": "该邮箱未注册", "status_code": 400})
    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 验证验证码
@router.post("/verify_email", summary="验证验证码", description="验证验证码", tags=['邮箱'])
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
@router.post("/modify_password_by_email", summary="修改密码", description="接收验证码和邮箱账号修改密码", tags=['邮箱'])
async def modify_password(modify: ToDoModel.modify_password):
    """
    修改密码
    """
    Password = password.encrypt_password(modify.Password)
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


@router.post("/sign_in", summary="签到", description="签到", tags=['签到'])
async def sign_in(access_Token: dict = Depends(token.verify_token), file: UploadFile = File(...)):
    """
    签到
    """
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            file_content = await file.read()
            name, _, similar = face_recognize(file_content)
            if similar is False:
                return JSONResponse(content={"msg": False,
                                             "error": "登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                             "status_code": 400})
            elif similar == 0:
                return JSONResponse(content={"msg": False, "error": "人员不在库中,请联系管理员!!!", "status_code": 400})
            if float(max(similar)) > 0.65:  # 当相似度大于0.65时
                # 向数据库中插入签到记录
                User_id = access_Token.get('sub')
                # 获取当前时间
                Create_time = datetime.now().strftime('%Y-%m-%d-%H:%M')
                day_time = datetime.now().strftime('%Y-%m-%d')
                sql = "SELECT end_time FROM sign_time WHERE id = '{}'".format(User_id)  # 防止重复签到
                cursor.execute(sql)
                result = cursor.fetchone()
                if result is None:
                    # 签到失败，提示用户 已签到
                    return JSONResponse(content={"msg": False, "error": "您今天已经签到,请勿重复操作！", "status_code": 400})
                else:

                    # 向数据库中插入签到记录
                    sql_1 = "INSERT INTO participate_time (id,date) VALUES ('{}', '{}')".format(User_id,day_time)
                    sql_2 = "INSERT INTO sign_time (id,name,begin_time) VALUES ('{}', '{}', '{}')".format(User_id, name,
                                                                                                        Create_time)
                    try:
                        cursor.execute(sql_1)
                        cursor.execute(sql_2)
                        conn.commit()
                        return JSONResponse(content={"msg": True, "data": "{}签到成功".format(name), "status_code": 200})
                    except Exception as e:
                        conn.rollback()
                        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})

            else:
                # 登录失败，提示用户
                return JSONResponse(content="登录失败,请确认人脸是否录入!!!\n若已录入请面向摄像头切勿遮挡人脸!!!",
                                    status_code=400)

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)


# 签退
@router.post("/sign_out", summary="签退", description="签退", tags=['签到'])
async def sign_out(access_Token: dict = Depends(token.verify_token)):
    """
    签退
    """
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            User_id = access_Token.get('sub')
            # 获取当前时间
            Create_time = datetime.now().strftime('%Y-%m-%d-%H:%M')
            # 查询同一天里的最后一次签到记录
            sql = ("SELECT begin_time,end_time FROM sign_time WHERE id = '{}' AND DATE(begin_time) = DATE('{}') ORDER "
                   "BY begin_time DESC LIMIT 1").format(User_id, Create_time)

            cursor.execute(sql)
            result = cursor.fetchall()
            begin_time = result[0][0]
            end_time = result[0][1]
            if end_time is None and begin_time is not None:
                # 向数据库中插入签退记录
                sql = (
                    "UPDATE sign_time SET end_time = '{}', duration = TIMEDIFF(NOW(), begin_time) WHERE id = '{}' AND "
                    "begin_time = '{}'").format(Create_time, User_id, begin_time)

                try:
                    cursor.execute(sql)
                    conn.commit()
                    return JSONResponse(content={"msg": True, "data": "签退成功", "status_code": 200})
                except Exception as e:
                    conn.rollback()
                    return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
                finally:
                    db_pool.close_connection(conn)
            elif result is None:
                # 签退失败，提示用户
                return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})
            else:
                # 签退失败，提示用户
                return JSONResponse(content={"msg": False, "error": "您今天已经签退,请勿重复操作！", "status_code": 400})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})


@router.get("/get_sign_time", summary="一天内签到时间截止", description="一天内签到时间截止", tags=['签到'])
async def get_sign_time(access_Token: dict = Depends(token.verify_token)):
    """
    一天内签到时间截止 ,没有签到则返回未签到
    """
    pass


#
# from fastapi import BackgroundTasks
# from sqlalchemy.orm import Session
# from app import models, database
#
#
# @router.on_event("shutdown")
# async def update_sign_in_records(background_tasks: BackgroundTasks):
#     background_tasks.add_task(archive_unfinished_sign_ins)
#
#
# async def archive_unfinished_sign_ins():
#     async with database.SessionLocal() as db:
#         # Fetch users who have not signed out
#         unfinished_sign_ins = db.query(models.SignIn).filter(models.SignIn.signed_out == False).all()
#
#         for sign_in in unfinished_sign_ins:
#             # Update the sign_in records, e.g. incrementing late counts
#             sign_in.late_count += 1
#             sign_in.signed_out = True  # Mark as signed out
#
#         db.commit()


# 添加或修改头像
@router.post("/modify_avatar", summary="添加或修改头像", description="添加或修改头像", tags=['账户'])
async def modify_avatar(modify: ToDoModel.modify_avatar, file: UploadFile = File(...)):
    """
    添加或修改头像
    """
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            # Save the uploaded file
            file_location = f"avatars/{file.filename}"
            with open(file_location, "wb+") as file_object:
                file_object.write(await file.read())

            # Update the user's avatar in the database
            cursor.execute("UPDATE users SET avatar = %s WHERE id = %s", (file_location, modify.user_id))
            conn.commit()

            return {"message": "Avatar updated successfully", "avatar_url": file_location}

    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# 计算今日，本周学习时长
@router.get("/get_study_time", summary="获取学习时长", description="获取学习时长", tags=['学习'])
async def get_study_time(access_Token: dict = Depends(token.verify_token)):
    """
    获取学习时长
    """
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    User_id = access_Token.get('sub')
    try:
        with conn.cursor() as cursor:
            # 查询同一天里的所有签到记录
            sql = "SELECT begin_time,end_time FROM sign_time WHERE id = '{}' AND DATE(begin_time) = CURDATE()".format(User_id)
            cursor.execute(sql)
            result = cursor.fetchall()
            if result is None:
                return JSONResponse(content={"msg": False, "error": "您今天还未签到,请先签到！", "status_code": 400})
            else:
                # 计算学习时长
                total_time = 0
                for i in range(len(result)):
                    if result[i][1] is not None:
                        total_time += (datetime.strptime(result[i][1], '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                            result[i][0], '%Y-%m-%d %H:%M:%S')).seconds
                # 计算学习时长     单位：分钟
                total_time = total_time // 60
                return JSONResponse(content={"msg": True, "data": {"total_time": total_time}, "status_code": 200})

    except Exception as e:
        return JSONResponse(content={"msg": False, "error": str(e), "status_code": 400})
    finally:
        db_pool.close_connection(conn)



