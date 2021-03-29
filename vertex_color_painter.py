# -*- coding: utf-8 -*-
"""
单通道顶点色绘制工具
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-03-29 23:10:09"

from maya import OpenMayaUI
import pymel.core as pm
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCompat import wrapInstance

import vertex_color_painter_ui

reload(vertex_color_painter_ui)


class VertexColorPainter(QtWidgets.QWidget, vertex_color_painter_ui.Ui_Form):
    def __init__(self):
        super(VertexColorPainter, self).__init__()
        self.setupUi(self)

        self.context = pm.artUserPaintCtx('artUserPaintCtx')

        
        
    @staticmethod
    def mayaToQT(name):
        # Maya -> QWidget
        ptr = OpenMayaUI.MQtUtil.findControl(name)
        if ptr is None:
            ptr = OpenMayaUI.MQtUtil.findLayout(name)
        if ptr is None:
            ptr = OpenMayaUI.MQtUtil.findMenuItem(name)
        if ptr is not None:
            return wrapInstance(long(ptr), QtWidgets.QWidget)

    def mayaShow(self, name=None):
        name = self.__class__.__name__ if name is None else name
        # NOTE 如果变量存在 就检查窗口多开
        if pm.workspaceControl(name, q=1, ex=1):
            pm.deleteUI(name)
        window = pm.workspaceControl(name, label=self.windowTitle())
        pm.showWindow(window)
        # NOTE 将Maya窗口转换成 Qt 组件
        ptr = self.mayaToQT(window)
        ptr.setLayout(QtWidgets.QVBoxLayout())
        ptr.layout().setContentsMargins(0, 0, 0, 0)
        ptr.layout().addWidget(self)
        return ptr


# import sys
# MODULE = r"D:\repo\MayaVexterColorPainter"
# sys.path.insert(0,MODULE) if MODULE not in sys.path else None
# import vertex_color_painter
# reload(vertex_color_painter)
# painter = vertex_color_painter.VertexColorPainter()
# painter.mayaShow()
