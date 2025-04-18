# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'face.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
"""
    synopsis: This module is responsible for the UI of the face detection module.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(768, 929)
        Form.setMinimumSize(QtCore.QSize(768, 0))
        Form.setMaximumSize(QtCore.QSize(768, 16777215))
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setMinimumSize(QtCore.QSize(768, 10))
        self.frame.setMaximumSize(QtCore.QSize(768, 16777215))
        self.frame.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.46798, y1:0, x2:0.483, y2:1, stop:0 rgba(67, 182, 253, 255), stop:1 rgba(0, 147, 238, 255));")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 10)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.frame_2 = QtWidgets.QFrame(self.frame)
        self.frame_2.setMinimumSize(QtCore.QSize(421, 61))
        self.frame_2.setMaximumSize(QtCore.QSize(421, 61))
        self.frame_2.setStyleSheet(".QFrame{\n"
"    width: 580px;\n"
"height: 96px;\n"
"background: #1B4ADB;\n"
"border-radius: 30px 30px 30px 30px;\n"
"opacity: 1;\n"
"}")
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.label_2 = QtWidgets.QLabel(self.frame_2)
        self.label_2.setMinimumSize(QtCore.QSize(10, 10))
        self.label_2.setMaximumSize(QtCore.QSize(10, 10))
        self.label_2.setStyleSheet("background-color: rgb(255, 255, 255);\n"
"border-radius: 5px")
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.label = QtWidgets.QLabel(self.frame_2)
        self.label.setStyleSheet(".QLabel{\n"
"    color: rgb(255, 255, 255);\n"
"    font-size: 25px;\n"
"    font-weight: 700;\n"
"    \n"
"    background-color: rgba(255, 255, 255, 0);\n"
"}\n"
"")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.label_3 = QtWidgets.QLabel(self.frame_2)
        self.label_3.setMinimumSize(QtCore.QSize(10, 10))
        self.label_3.setMaximumSize(QtCore.QSize(10, 10))
        self.label_3.setStyleSheet("background-color: rgb(255, 255, 255);\n"
"border-radius: 5px")
        self.label_3.setText("")
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.horizontalLayout_4.addWidget(self.frame_2)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem5)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.frame_3 = QtWidgets.QFrame(self.frame)
        self.frame_3.setMinimumSize(QtCore.QSize(691, 601))
        self.frame_3.setMaximumSize(QtCore.QSize(691, 601))
        self.frame_3.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.537, y1:1, x2:0.517, y2:0, stop:0 rgba(17, 181, 243, 255), stop:1 rgba(27, 73, 219, 255));\n"
"border-radius: 40px;")
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_3)
        self.gridLayout.setObjectName("gridLayout")
        self.face_frame = QtWidgets.QLabel(self.frame_3)
        self.face_frame.setStyleSheet("border-radius: 0px;\n"
"background-color: rgb(20, 20, 20);")
        self.face_frame.setText("")
        self.face_frame.setObjectName("face_frame")
        self.gridLayout.addWidget(self.face_frame, 0, 0, 1, 1)
        self.horizontalLayout_7.addWidget(self.frame_3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.sign_in = QtWidgets.QPushButton(self.frame)
        self.sign_in.setMinimumSize(QtCore.QSize(221, 51))
        self.sign_in.setMaximumSize(QtCore.QSize(221, 51))
        self.sign_in.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.492611, y1:0, x2:0.482759, y2:1, stop:0 rgba(0, 255, 28, 255), stop:1 rgba(50, 169, 107, 255));\n"
"\n"
"border-radius: 20px;\n"
"color: #FFFFFF;\n"
"font-size: 20px;")
        self.sign_in.setObjectName("sign_in")
        self.horizontalLayout_5.addWidget(self.sign_in)
        self.sign_out = QtWidgets.QPushButton(self.frame)
        self.sign_out.setMinimumSize(QtCore.QSize(221, 51))
        self.sign_out.setMaximumSize(QtCore.QSize(221, 51))
        self.sign_out.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.492611, y1:0, x2:0.482759, y2:1, stop:0 rgba(0, 255, 28, 255), stop:1 rgba(50, 169, 107, 255));\n"
"\n"
"border-radius: 20px;\n"
"color: #FFFFFF;\n"
"font-size: 20px;")
        self.sign_out.setObjectName("sign_out")
        self.horizontalLayout_5.addWidget(self.sign_out)
        self.log_out = QtWidgets.QPushButton(self.frame)
        self.log_out.setMinimumSize(QtCore.QSize(221, 51))
        self.log_out.setMaximumSize(QtCore.QSize(221, 51))
        self.log_out.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.492611, y1:0, x2:0.482759, y2:1, stop:0 rgba(255, 58, 0, 255), stop:1 rgba(169, 0, 0, 255));\n"
"\n"
"border-radius: 20px;\n"
"color: #FFFFFF;\n"
"font-size: 20px")
        self.log_out.setObjectName("log_out")
        self.horizontalLayout_5.addWidget(self.log_out)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.gridLayout_2.addWidget(self.frame, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "2111实验室打卡系统"))
        self.sign_in.setText(_translate("Form", "签到"))
        self.sign_out.setText(_translate("Form", "签退"))
        self.log_out.setText(_translate("Form", "退出"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
