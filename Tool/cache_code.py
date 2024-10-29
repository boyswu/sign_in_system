"""
缓存工具验证码和验证邮箱的缓存工具
"""
from cachetools import cached, TTLCache

# 创建两个缓存对象，设置最大容量和过期时间（例如，100个条目，每个条目5分钟过期）
email_to_code_cache = TTLCache(maxsize=100, ttl=900)
code_to_email_cache = TTLCache(maxsize=100, ttl=900)


@cached(email_to_code_cache)
def get_security_code(security_code):
    print("Getting security code from database...")
    return security_code


@cached(code_to_email_cache)
def get_receiver_email(receiver_email):
    print("Getting receiver email from database...")
    return receiver_email
# # 第一次调用，计算结果并缓存
# print(get_data("key1"))  # 输出: Getting data from database... key1
#
# # 第二次调用，直接从缓存中获取结果
# print(get_data("key1"))  # 输出: key1
#
# # 等待10秒后再次调用，缓存已过期，重新计算
# import time
#
# time.sleep(10)
# print(get_data("key1"))  # 输出: Getting data from database... key1
