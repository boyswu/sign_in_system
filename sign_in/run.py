"""
用户端人脸登录系统

"""

import cv2
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QGuiApplication
from UI.face import Ui_Form


class face_MainWindow(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(face_MainWindow, self).__init__()
        self.setupUi(self)
        self.update_timer = QtCore.QTimer()

        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.camera.set(6, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))  # 转换为MJPG格式
        self.camera.set(3, 480)
        self.camera.set(4, 640)
        # self.camera.get(cv2.CAP_PROP_FPS)

        self.update_timer.start(30)
        self.init_solt()

    def init_solt(self):
        self.update_timer.timeout.connect(self.show_camera)  # 定时器连接显示摄像头画面槽函数
        self.sign_in.clicked.connect(self.sign_in_system)  # 签到系统
        self.sign_out.clicked.connect(self.sign_out_system)  # 签出系统
        self.log_out.clicked.connect(self.log_out_system)  # 退出系统

    def show_camera(self):
        ret, frame = self.camera.read()
        if not ret:
            print("ret != True")
            mesBox = QMessageBox()  # 创建消息对话框
            mesBox.setWindowTitle('提示信息')
            mesBox.setText('摄像头连接异常 \n请检查摄像头连接...')
            mesBox.setIcon(QMessageBox.Information)
            mesBox.exec_()
        else:
            # 原始图像显示
            srcFrame = cv2.resize(frame,
                                  (self.face_frame.width(), self.face_frame.height()))  # 把读到的帧的大小重新设置为 640x480
            srcFrame = cv2.cvtColor(srcFrame, cv2.COLOR_BGR2RGB)  # 视频色彩转换回RGB，这样才是现实的颜色
            srcFrame = QtGui.QImage(srcFrame.data, srcFrame.shape[1], srcFrame.shape[0],
                                    int(srcFrame.shape[1]) * 3,
                                    QtGui.QImage.Format_RGB888)  # 把读取到的视频数据变成QImage形式
            self.face_frame.setPixmap(QtGui.QPixmap.fromImage(srcFrame))  # 往显示视频的Label里 显示QImage

    def sign_in_system(self):
        # 签到系统
        """
        # 人脸识别
        :param frame: 用户的人脸图片
        :return:
        """
        print("签到系统")
        _, frame = self.camera.read()  # 读取摄像头数据
        cv2.imwrite('image.jpg', frame)  # 保存图片
        print("图片保存成功")

        url = 'http://43.143.229.40:8080/sign_in'

        # 准备表单数据
        files = {
            'file': ('image.jpg', open('image.jpg', 'rb'))
        }
        response = requests.post(url, files=files)
        result = response.json()
        print(result)
        # 获取所有值
        values = list(result.values())
        message = values[1]
        status_code = values[2]
        if status_code == 200:
            QtWidgets.QMessageBox.information(self, '提示', f'{message}')
            # self.new_page()
            return
        if status_code == 400:
            QtWidgets.QMessageBox.warning(self, '警告', f'{message}')
            return
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)

    def sign_out_system(self):
        # 签出系统
        """
        # 人脸识别
        :param frame: 用户的人脸图片
        :return:
        """
        print("签出系统")
        _, frame = self.camera.read()  # 读取摄像头数据
        cv2.imwrite('image.jpg', frame)  # 保存图片
        print("图片保存成功")

        url = 'http://43.143.229.40:8080/face_sign_out'

        # 准备表单数据
        files = {
            'file': ('image.jpg', open('image.jpg', 'rb'))
        }
        response = requests.post(url, files=files)
        result = response.json()
        print(result)

        values = list(result.values())
        message = values[1]
        status_code = values[2]
        if status_code == 200:
            QtWidgets.QMessageBox.information(self, '提示', f'{message}')
            # self.new_page()
            return
        if status_code == 400:
            QtWidgets.QMessageBox.warning(self, '警告', f'{message}')
            return
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)

    def log_out_system(self):
        self.face_frame.clear()  # 清空摄像头显示
        # 关闭窗口
        self.close()

if __name__ == '__main__':
    import sys
    from PyQt5.QtGui import QIcon

    QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    icon_1 = QIcon("../UI/iocn.png")
    app.setWindowIcon(icon_1)
    main = face_MainWindow()
    main.show()
    sys.exit(app.exec_())
