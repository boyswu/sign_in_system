"""
发送邮件验证码
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random


# 生成随机的6位验证码
def generate_security_code():
    return ''.join(random.choices('0123456789', k=6))


def send_email(receiver_email):
    # 邮箱账号信息
    sender_email = "2976699191@qq.com"
    password = "gypvlbmegjdtdfjb"

    # 创建邮件
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "验证码"
    security_code = generate_security_code()  # 使用随机生成的验证码

    # 邮件正文
    body = f"验证码：{security_code}"
    message.attach(MIMEText(body, "plain"))

    # 连接到QQ邮箱的SMTP服务器
    server = smtplib.SMTP("smtp.qq.com", 587)
    server.starttls()
    try:
        server.login(sender_email, password)
    except smtplib.SMTPAuthenticationError as e:
        print("登录失败，请检查邮箱账号和授权码是否正确。")
        server.quit()
        exit()

    # 发送邮件
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)

    # 关闭连接
    server.quit()

    print("邮件发送成功")
    return security_code
