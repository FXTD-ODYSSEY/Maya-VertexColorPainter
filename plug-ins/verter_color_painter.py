# -*- coding: utf-8 -*-
"""
- [x] limit the vertex color
点击 viewport 的时候记录当前的顶点颜色，根据 rgb 选项锁定颜色通道 

- [ ] setup UI
UI setup callback then do another setup

- [ ] single color channel Display
use different color set

- [ ] fix app_filter not remove yet
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2022-08-12 15:31:41'



from collections import defaultdict

from maya import OpenMaya, OpenMayaMPx, OpenMayaUI
from pymel import core as pm
from pymel.tools import py2mel
from Qt import QtCore, QtGui, QtWidgets

vertex_color_data = defaultdict(dict)
PAINT_CTX = "artAttrColorPerVertexContext"

def collect_vertex_color():
    selections = OpenMaya.MSelectionList()
    component_selections = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selections)

    view = OpenMayaUI.M3dView.active3dView()
    OpenMaya.MGlobal.selectFromScreen(
        0, 0, view.portWidth(), view.portHeight(), OpenMaya.MGlobal.kReplaceList
    )
    OpenMaya.MGlobal.getActiveSelectionList(component_selections)
    OpenMaya.MGlobal.setActiveSelectionList(selections)
    itr = OpenMaya.MItSelectionList(component_selections)

    while not itr.isDone():
        dag_path = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        itr.getDagPath(dag_path, component)

        vtx_itr = OpenMaya.MItMeshVertex(dag_path, component)
        while not vtx_itr.isDone():
            index = vtx_itr.index()
            color = OpenMaya.MColor()
            vtx_itr.getColor(color)
            vertex_color_data[dag_path][index] = color
            vtx_itr.next()
        itr.next()

class AppFilter(QtCore.QObject):
    pressed = QtCore.Signal()
    released = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(AppFilter, self).__init__(*args, **kwargs)
        self.pressed.connect(self.press_viewport)
        self.released.connect(self.release_viewport)
        self.color = (0, 0, 0)

    def eventFilter(self, receiver, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if self.is_viewport(receiver):
                self.pressed.emit()
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if self.is_viewport(receiver):
                self.released.emit()
        return False

    def is_viewport(self, viewport):
        panel = isinstance(viewport, QtCore.QObject) and viewport.parent()
        name = panel and panel.objectName()
        return name and pm.objectTypeUI(name, i="modelEditor")

    def press_viewport(self):
        print("press_viewport")
        self.color = pm.artAttrPaintVertexCtx(PAINT_CTX, q=1, colorRGBValue=1)
        pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, colorRGBValue=[self.color[0], 0, 0])

    def release_viewport(self):
        print("release_viewport")
        # NOTE: reset vertex color
        pm.evalDeferred(lambda:pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, colorRGBValue=self.color))

global app_filter
app_filter = AppFilter()

def vertex_color_tool_on():
    # TODO(timmyliang): listen viewport press then modify the vertex color
    print("vertex_color_tool_on")
    app = QtWidgets.QApplication.instance()
    global app_filter
    app.installEventFilter(app_filter)


def vertex_color_tool_off():
    print("vertex_color_tool_off")
    app = QtWidgets.QApplication.instance()
    global app_filter
    app.removeEventFilter(app_filter)

def py2mel_proc(func):
    py2mel.py2melProc(func, procName=func.__name__)

def setup_mel():
    py2mel_proc(vertex_color_tool_on)
    py2mel_proc(vertex_color_tool_off)

    PAINT_CTX = pm.mel.artAttrColorPerVertexToolScript(5)

    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="vertex_color_tool_on")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="vertex_color_tool_off")
    
    pm.mel.artAttrColorPerVertexToolScript(4)


# Initialize the script plug-in
def initializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj, "timmyliang", "1.0.0")
    
    setup_mel()
    

# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)
    
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="")

