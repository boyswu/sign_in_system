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
            Create_time = datetime.now()
            # 查询前一天里是否有未签退记录
            yesterday = Create_time - timedelta(days=1)
            sql = "SELECT * FROM sign_time WHERE DATE(begin_time) = DATE('{}') AND end_time IS NULL".format(yesterday)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                # 修改所有未签退记录的end_time为当前时间
                sql = ("UPDATE sign_time SET end_time = '{}',duration = '{}',status ='{}' WHERE DATE(begin_time) = "
                       "DATE('{}') AND end_time IS NULL").format(Create_time, 0, '未签退', yesterday)
                try:
                    cursor.execute(sql)
                    conn.commit()
                    print("签退成功")
                    return True
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("签退失败")
            else:
                # 未签退记录不存在
                return True

    except Exception as e:
        print(e)
    finally:
        db_pool.close_connection(conn)


# 定义在晚上12点调用的任务
schedule.every().day.at("00:00").do(my_function)


def run_schedule():
    while True:
        schedule.run_pending()  # 执行已安排的任务
        time.sleep(1)  # 等待一秒再检查
