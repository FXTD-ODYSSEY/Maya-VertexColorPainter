# -*- coding: utf-8 -*-
"""
- [x] limit the vertex color
点击 viewport 的时候记录当前的顶点颜色，根据 rgb 选项锁定颜色通道 

- [ ] setup UI
UI setup callback then do another setup

- [ ] single color channel Display
use different color set

- [ ] fix app_filter not remove yet

--- Test Code ---

from maya import cmds
cmds.file(f=1, new=1)
cmds.polySphere()
if cmds.pluginInfo('verter_color_painter',q=1,l=1):
    cmds.unloadPlugin('verter_color_painter')
cmds.loadPlugin(r"F:\repo\Maya-VertexColorPainter\plug-ins\verter_color_painter.py")

"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from collections import defaultdict
import sys

# Import third-party modules
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
from maya import OpenMaya
from maya import OpenMayaMPx
from maya import OpenMayaUI
from pymel import core as pm
from pymel.tools import py2mel


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2022-08-12 15:31:41"


vertex_color_data = defaultdict(dict)
PAINT_CTX = "artAttrColorPerVertexContext"


def iterate_mit(itr):
    while not itr.isDone():
        yield itr
        itr.next()


def collect_viewport_vertex_color():
    selections = OpenMaya.MSelectionList()
    component_selections = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selections)

    view = OpenMayaUI.M3dView.active3dView()
    OpenMaya.MGlobal.selectFromScreen(
        0, 0, view.portWidth(), view.portHeight(), OpenMaya.MGlobal.kReplaceList
    )
    OpenMaya.MGlobal.getActiveSelectionList(component_selections)
    OpenMaya.MGlobal.setActiveSelectionList(selections)

    vertex_color_data.clear()
    for itr in iterate_mit(OpenMaya.MItSelectionList(component_selections)):
        dag_path = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        itr.getDagPath(dag_path, component)

        for vtx_itr in iterate_mit(OpenMaya.MItMeshVertex(dag_path, component)):
            index = vtx_itr.index()
            color = OpenMaya.MColor()
            vtx_itr.getColor(color)
            vertex_color_data[dag_path][index] = color


class AppVertexColorFilter(QtCore.QObject):
    pressed = QtCore.Signal()
    released = QtCore.Signal()
    channels = "RGBA"
    inst = None

    def __init__(self, *args, **kwargs):
        super(AppVertexColorFilter, self).__init__(*args, **kwargs)
        self.pressed.connect(self.press_viewport)
        self.released.connect(lambda: pm.evalDeferred(self.release_viewport))
        self.color = (0, 0, 0)

    @staticmethod
    def get_paint_nodes():
        for node in set(pm.artAttrPaintVertexCtx(PAINT_CTX, q=1, pna=1).split()):
            yield pm.PyNode(node)

    @classmethod
    def setup_color_set(cls):
        for node in cls.get_paint_nodes():
            node.displayColors.set(1)
            color_sets = pm.polyColorSet(node, q=1, allColorSets=1)
            color_sets = color_sets or pm.polyColorSet(node, create=1)
            main_color_set = color_sets[0]

            for color_channel in cls.channels:
                color_set = "VertexColor{0}".format(color_channel)
                if color_set not in color_sets:
                    pm.polyColorSet(node, create=1, colorSet=color_set)
            pm.polyColorSet(node, currentColorSet=1, colorSet=main_color_set)
        # TODO(timmyliang): extract main color set to color channel set

    @classmethod
    def reset_color_set(cls):
        for node in cls.get_paint_nodes():
            color_sets = pm.polyColorSet(node, q=1, allColorSets=1)
            for color_channel in cls.channels:
                color_set = "VertexColor{0}".format(color_channel)
                if color_set in color_sets:
                    pm.polyColorSet(node, delete=1, colorSet=color_set)

    @classmethod
    def apply_color_channel(cls):
        pass

    @classmethod
    def install(cls):
        cls.inst = cls()
        app = QtWidgets.QApplication.instance()
        app.installEventFilter(cls.inst)
        cls.inst.setup_color_set()

    @classmethod
    def uninstall(cls):
        if not cls.inst:
            return

        app = QtWidgets.QApplication.instance()
        app.removeEventFilter(cls.inst)
        cls.inst.reset_color_set()
        cls.inst.deleteLater()
        cls.inst = None

    def eventFilter(self, receiver, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if self.is_viewport(receiver):
                self.pressed.emit()
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
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

        # TODO(timmyliang): collect viewport color set
        collect_viewport_vertex_color()

    def release_viewport(self):
        print("release_viewport")
        # NOTE: reset vertex color
        pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, colorRGBValue=self.color)

        # TODO(timmyliang): get color channel apply to main color set


def mel_proc(func):
    py2mel.py2melProc(func, procName=func.__name__)


@mel_proc
def vertex_color_tool_on():
    # TODO(timmyliang): listen viewport press then modify the vertex color
    print("vertex_color_tool_on")
    AppVertexColorFilter.install()


@mel_proc
def vertex_color_tool_off():
    print("vertex_color_tool_off")
    AppVertexColorFilter.uninstall()


# Initialize the script plug-in
def initializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj, "timmyliang", "1.0.0")

    PAINT_CTX = pm.mel.artAttrColorPerVertexToolScript(5)
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="vertex_color_tool_on")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="vertex_color_tool_off")
    pm.mel.artAttrColorPerVertexToolScript(4)

    # TODO(timmyliang): hack ui to property window and values


# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="")
