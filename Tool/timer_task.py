import schedule
import time
from connect_tool.sql import MySQLConnectionPool
from datetime import datetime, timedelta

"""
定时任务
"""


# 如果未签退就自动签退并且记录未签退
def my_function():
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            # 获取当前时间
            create_time = datetime.now()
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
