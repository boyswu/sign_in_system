import schedule
import time
from connect_tool.sql import MySQLConnectionPool
from datetime import datetime
from Tool.email_send import send_warning_email

"""
定时任务
"""


# 如果未签退就自动签退并且记录未签退
def my_function():
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            # # 获取当前时间
            # create_time = datetime.now()
            # select_sql = """
            #             SELECT u.email
            #             FROM sign_time s
            #             JOIN user u ON s.id = u.id
            #             WHERE s.end_time IS NULL
            #             """
            # # 获取所有未签退记录
            # select_sql = "SELECT id FROM sign_time WHERE end_time IS NULL"
            # cursor.execute(select_sql)
            # result = cursor.fetchall()
            # ids = [item[0] for item in result]
            # for id in ids:
            #     # 查询用户表里的email
            #     select_user_sql = "SELECT email FROM user WHERE id = {}".format(id)
            #     cursor.execute(select_user_sql)
            #     result = cursor.fetchall()
            #     email = result[0][0]
            #     send_warning_email(email)
            # 获取当前时间
            create_time = datetime.now()
            # 获取所有未签退记录的用户email
            select_sql = """
            SELECT u.email 
            FROM sign_time s 
            JOIN user u ON s.id = u.id 
            WHERE s.end_time IS NULL
            """
            cursor.execute(select_sql)
            emails = cursor.fetchall()

            # 发送警告邮件
            for email_tuple in emails:
                email = email_tuple[0]
                send_warning_email(email)

            # 修改所有未签退记录的end_time为当前时间
            update_sql = ("UPDATE sign_time SET end_time = '{}',duration = '{}',status = '{}' "
                          "WHERE end_time IS NULL").format(create_time, 0, '未签退')
            cursor.execute(update_sql)
            conn.commit()
            print("签退成功")

    except Exception as e:
        print(f"错误发生: {e}")
        if conn:
            conn.rollback()  # 确保在出现异常时回滚
    finally:
        db_pool.close_connection(conn)


# 定义在点调用的任务
schedule.every().day.at("00:00").do(my_function)


def run_schedule():
    while True:
        schedule.run_pending()  # 执行已安排的任务
        time.sleep(1)  # 等待一秒再检查
