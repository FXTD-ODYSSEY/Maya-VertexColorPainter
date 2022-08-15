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
cmds.polyColorPerVertex( rgb=(1,1, 0) )
if cmds.pluginInfo('verter_color_painter',q=1,l=1):
    cmds.unloadPlugin('verter_color_painter')
cmds.loadPlugin(r"F:\repo\Maya-VertexColorPainter\plug-ins\verter_color_painter.py")
pm.artAttrPaintVertexCtx('artAttrColorPerVertexContext', e=1, alp="")

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
    property_showed = QtCore.Signal()
    inst = None

    channel_color_config = {
        0: lambda color: OpenMaya.MColor(color[0], 0, 0, 1),
        1: lambda color: OpenMaya.MColor(0, color[1], 0, 1),
        2: lambda color: OpenMaya.MColor(0, 0, color[2], 1),
        3: lambda color: OpenMaya.MColor(0, 0, 0, color[3]),
    }

    color_set_representation = {
        "R": "RGB",
        "G": "RGB",
        "B": "RGB",
        "A": "A",
    }

    SINGLE_CONTROL = "artAttrColorSingleColorChannel"
    OPTION_CONTROL = "artAttrColorSingleColorOptionMenu"
    OPTION_ITEMS = ["Auto", "RGB", "R", "G", "B", "A"]
    CHANNELS = "RGBA"

    def __init__(self, *args, **kwargs):
        super(AppVertexColorFilter, self).__init__(*args, **kwargs)
        self.pressed.connect(self.press_viewport)
        self.released.connect(lambda: pm.evalDeferred(self.release_viewport))
        self.property_showed.connect(
            lambda: pm.evalDeferred(self.modify_property_window)
        )
        self.color = (0.0, 0.0, 0.0, 1.0)

    @staticmethod
    def get_paint_nodes():
        for node in set(pm.artAttrPaintVertexCtx(PAINT_CTX, q=1, pna=1).split()):
            yield pm.PyNode(node)

    @staticmethod
    def get_color_sets(node):
        color_sets = pm.polyColorSet(node, q=1, allColorSets=1)
        return color_sets or pm.polyColorSet(node, create=1)

    @classmethod
    def setup_color_set(cls):
        for node in cls.get_paint_nodes():
            node.displayColors.set(1)
            color_sets = cls.get_color_sets(node)
            main_color_set = color_sets[0]

            dag_path = node.__apimdagpath__()
            mesh = OpenMaya.MFnMesh(dag_path)
            color_array = OpenMaya.MColorArray()
            mesh.getVertexColors(color_array, main_color_set)

            for color_index, color_channel in enumerate(cls.CHANNELS):
                color_set = "VertexColor{0}".format(color_channel)
                if color_set not in color_sets:
                    rpt = cls.color_set_representation.get(color_channel)
                    pm.polyColorSet(node, create=1, rpt=rpt, colorSet=color_set)
                mesh.setCurrentColorSetName(color_set)
                for array_index in range(color_array.length()):
                    full_color = color_array[array_index]
                    color = cls.channel_color_config[color_index](full_color)
                    mesh.setVertexColor(color, array_index)
            mesh.setCurrentColorSetName(main_color_set)

    @classmethod
    def reset_color_set(cls):
        for node in cls.get_paint_nodes():
            color_sets = cls.get_color_sets(node)
            for color_channel in cls.CHANNELS:
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
        # NOTES(timmyliang): hack maya properties window open
        elif event.type() == QtCore.QEvent.WindowTitleChange:
            label = receiver.findChild(QtWidgets.QLabel)
            if label and label.text() == "Paint Vertex Color Tool":
                self.property_showed.emit()
        return False

    def is_viewport(self, viewport):
        panel = isinstance(viewport, QtCore.QObject) and viewport.parent()
        name = panel and panel.objectName()
        return name and pm.objectTypeUI(name, i="modelEditor")

    def press_viewport(self):
        print("press_viewport")

        rgb = pm.colorSliderGrp("colorPerVertexColor", q=1, rgb=1)
        alpha = pm.floatSliderGrp("colorPerVertexAlpha", q=1, value=1)
        rgb.append(alpha)

        self.color = rgb or self.color
        sel = pm.radioButtonGrp(self.SINGLE_CONTROL, q=1, sl=1) - 2
        color_callback = self.channel_color_config.get(sel, lambda color: color)
        color = tuple(color_callback(self.color))
        pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, cl4=color)

        # TODO(timmyliang): collect viewport color set
        # collect_viewport_vertex_color()

    def release_viewport(self):
        print("release_viewport")
        # NOTE: reset vertex color
        pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, cl4=self.color)

        # TODO(timmyliang): get color channel apply to main color set

    def modify_property_window(self):
        layout = pm.radioButtonGrp("artAttrColorChannelChoices", q=1, parent=1)
        pm.setParent(layout)
        pm.setUITemplate("OptionsTemplate", pushTemplate=1)
        column_layout = pm.columnLayout()

        for child in pm.layout(layout, q=1, childArray=1):
            pm.control(child, e=1, p=column_layout)
            # NOTES(timmyliang): insert new ui
            if child == "artAttrColorChannelChoices":
                pm.radioButtonGrp(
                    self.SINGLE_CONTROL,
                    label="Single Channel:",
                    nrb=4,
                    sl=1,
                    la4=self.OPTION_ITEMS[1:-1],
                    changeCommand=self.on_channel_change,
                )
                pm.optionMenuGrp(
                    self.OPTION_CONTROL,
                    label="Color Display:",
                    changeCommand=self.on_display_mode_change,
                )
                for item in self.OPTION_ITEMS:
                    pm.menuItem(label=item)

        pm.setUITemplate(popTemplate=1)

    def on_channel_change(self, *args):
        if pm.optionMenuGrp(self.OPTION_CONTROL, q=1, sl=1) == 1:
            index = pm.radioButtonGrp(self.SINGLE_CONTROL, q=1, sl=1)
            self.on_display_mode_change(self.OPTION_ITEMS[index])

    @classmethod
    def on_display_mode_change(cls, item):
        if item == "Auto":
            sel = pm.radioButtonGrp(cls.SINGLE_CONTROL, q=1, sl=1)
            item = cls.OPTION_ITEMS[sel]
        for node in cls.get_paint_nodes():
            color_sets = cls.get_color_sets(node)
            main_color_set = color_sets[0]
            if item == "RGB":
                pm.polyColorSet(node, currentColorSet=1, colorSet=main_color_set)
            else:
                color_set = "VertexColor{0}".format(item)
                pm.polyColorSet(node, currentColorSet=1, colorSet=color_set)


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
    # NOTES(timmyliang): close Tool Settings UI
    pm.uitypes.toQtObject("ToolSettings").window().close()
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="vertex_color_tool_on")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="vertex_color_tool_off")
    pm.mel.artAttrColorPerVertexToolScript(5)

    # TODO(timmyliang): remove this
    pm.toolPropertyWindow()


# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="")
