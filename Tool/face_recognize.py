from seetaface.api import *
from connect_tool.sql import MySQLConnectionPool

#  seetaface初始化
init_mask = FACE_DETECT | FACERECOGNITION | LANDMARKER5
seetaFace = SeetaFace(init_mask)  # 初始化


def select_face_sql():
    db_pool = MySQLConnectionPool()
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, face FROM user"
            cursor.execute(sql)
            results = cursor.fetchall()
            if results:
                user_id = results[0][0]
                name = results[0][1]
                face = results[0][2]
                return user_id, name, face
            else:
                return None, None, None  # 或其他逻辑来处理没有结果的情况
    except Exception as e:
        return False, False, False
    finally:
        db_pool.close_connection(conn)


def face_recognize(file_content):
    # file_content = await file.read()
    frame = cv2.imdecode(np.frombuffer(file_content, np.uint8), cv2.IMREAD_COLOR)  # 读取图片数据
    detect_result = seetaFace.Detect(frame)  # 人脸检测，返回人脸检测信息数组
    Feature = []
    if detect_result.size == 0:  # 当未检测到人脸时
        return False, False, False, False
    for i in range(detect_result.size):  # 遍历每一个人的人脸数据
        face = detect_result.data[i].pos
        points = seetaFace.mark5(frame, face)  # 5点检测模型检测
        feature = seetaFace.Extract(frame, points)  # 在一张图片中提取指定人脸关键点区域的人脸的特征值
        feature = seetaFace.get_feature_numpy(feature)  # 获取feature的numpy表示数据
        Feature.append(feature)
    people_face = feature.tostring()  # 将 NumPy 数组转换为 Python 列表
    user_id, name, face = select_face_sql()
    if face is False:
        return 0, 0, 0, 0
    similar = []
    for i in Feature:
        # 判断是否存在数据库中，如果存在使用numpy计算，比较人脸特征值相似度
        if face is not None:
            feature_sql = np.frombuffer(face, dtype=np.float32)
            similar1 = seetaFace.compare_feature_np(feature_sql, i)  # 计算两个特征值之间的相似度
            similar.append(similar1)
            # print(similar)
    return user_id, name, people_face, similar
