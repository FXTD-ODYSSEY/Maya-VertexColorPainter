# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:/repo/MayaVexterColorPainter\vertex_color_painter.ui'
#
# Created: Mon Mar 29 23:36:32 2021
#      by: pyside2-uic  running on PySide2 2.0.0~alpha0
#
# WARNING! All changes made in this file will be lost!

from Qt import QtCompat, QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(483, 363)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.R_BTN = QtWidgets.QPushButton(Form)
        self.R_BTN.setStyleSheet("background:red;color:white;")
        self.R_BTN.setObjectName("R_BTN")
        self.horizontalLayout.addWidget(self.R_BTN)
        self.B_BTN = QtWidgets.QPushButton(Form)
        self.B_BTN.setStyleSheet("background:blue;color:white;")
        self.B_BTN.setObjectName("B_BTN")
        self.horizontalLayout.addWidget(self.B_BTN)
        self.G_BTN = QtWidgets.QPushButton(Form)
        self.G_BTN.setStyleSheet("background:green;color:white;")
        self.G_BTN.setObjectName("G_BTN")
        self.horizontalLayout.addWidget(self.G_BTN)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.RGB_BTN = QtWidgets.QPushButton(Form)
        self.RGB_BTN.setObjectName("RGB_BTN")
        self.verticalLayout.addWidget(self.RGB_BTN)
        self.line = QtWidgets.QFrame(Form)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.Soft_BTN = QtWidgets.QPushButton(Form)
        self.Soft_BTN.setObjectName("Soft_BTN")
        self.verticalLayout.addWidget(self.Soft_BTN)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtCompat.translate("Form", "顶点色单通道绘制工具", None, -1))
        self.label.setText(QtCompat.translate("Form", "顶点色单通道绘制工具", None, -1))
        self.R_BTN.setText(QtCompat.translate("Form", "R", None, -1))
        self.B_BTN.setText(QtCompat.translate("Form", "B", None, -1))
        self.G_BTN.setText(QtCompat.translate("Form", "G", None, -1))
        self.RGB_BTN.setText(QtCompat.translate("Form", "RGB 全通道", None, -1))
        self.Soft_BTN.setText(QtCompat.translate("Form", "软选择转顶点色", None, -1))

