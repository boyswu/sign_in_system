# 后端

#### 介绍

本项目旨在完成签到打卡系统，通过人脸识别完成签到，APP显示用户一天和一周的学习时长。

#### 软件架构

使用fastapi快速搭建一套使用minio做为文件存储，MySQL做为数据库。

#### 接口文档
1. 用户注册接口

请求方式：POST

请求地址：/register_mission

请求参数：
| 参数名 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 | 
| user_id | string | 是 | 用户id |
| password | string | 是 | 密码 |
| email | string | 是 | 邮箱 |
| file | file | 是 | 人脸照片 |


返回参数：
| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| msg | string | True/False |
| data | object | 提示信息 |
| code | int | 状态码 |
返回示例：
```
{
    "code": 200,
    "message": "注册成功",
    "data": {
        "id": 1,
        "username": "test",
        "email": "test@test.com"
    }
}   
```
2. 用户登录接口
请求方式：POST

请求地址：/login


#### 参与贡献

1. 吴佳航
2. 邵玉春


#### 敬请期待

1.增加便签功能
2.增加用户定位功能

