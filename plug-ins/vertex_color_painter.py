# -*- coding: utf-8 -*-
"""
Paint Vertex Color with single Channel support.

--- Test Code ---

from maya import cmds
cmds.file(f=1, new=1)
cmds.polySphere()
cmds.polyColorPerVertex( rgb=(1,1, 0) )
if cmds.pluginInfo('vertex_color_painter',q=1,l=1):
    cmds.unloadPlugin('vertex_color_painter')
cmds.loadPlugin(r"F:/repo/Maya-VertexColorPainter/plug-ins/vertex_color_painter.py")
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from collections import defaultdict
from contextlib import contextmanager
from functools import partial
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


PAINT_CTX = "artAttrColorPerVertexContext"
SINGLE_CONTROL = "artAttrColorSingleColorChannel"
OPTION_CONTROL = "artAttrColorSingleColorOptionMenu"
CHANNELS = "RGBA"
OPTION_ITEMS = ["Auto", "RGB"] + list(CHANNELS)


def iterate_mit(itr):
    while not itr.isDone():
        yield itr
        itr.next()


def use_select_depth(func):
    """Activate Select Base on camera."""

    def decorator(*args, **kwargs):
        is_use_depth = pm.selectPref(q=1, ud=1)
        pm.selectPref(ud=True)
        result = func(*args, **kwargs)
        pm.selectPref(ud=is_use_depth)
        return result

    return decorator


def to_component_mode(func):
    """Convert Selection to Component mode."""

    def decorator(*args, **kwargs):
        flags = ["co", "h", "l", "o", "p", "r", "t"]
        select_modes = [flag for flag in flags if pm.selectMode(**{"q": 1, flag: 1})]
        pm.selectMode(component=1)
        # NOTES(timmyliang): update viewport
        pm.refresh()
        func(*args, **kwargs)
        pm.selectMode(**{select_modes[0]: True})

    return decorator


class ApplyVertexColorBase(object):
    @staticmethod
    def get_paint_nodes():
        for node in set(pm.artAttrPaintVertexCtx(PAINT_CTX, q=1, pna=1).split()):
            yield pm.PyNode(node)

    @staticmethod
    def get_color_sets(node):
        color_sets = pm.polyColorSet(node, q=1, allColorSets=1)
        return color_sets or pm.polyColorSet(node, create=1)

    @staticmethod
    def filter_color(color, index, base_color=None):
        if index > 3:
            return color
        is_color = isinstance(base_color, OpenMaya.MColor)
        color_list = list(base_color) if is_color else [0, 0, 0, 1]
        color_list[index] = color[index]
        return OpenMaya.MColor(*color_list)


class AppVertexColorFilter(ApplyVertexColorBase, QtCore.QObject):
    pressed = QtCore.Signal()
    released = QtCore.Signal()
    property_showed = QtCore.Signal()
    inst = None

    color_set_representation = {
        "R": "RGB",
        "G": "RGB",
        "B": "RGB",
        "A": "A",
    }

    def __init__(self, *args, **kwargs):
        super(AppVertexColorFilter, self).__init__(*args, **kwargs)
        self.is_press_alt = False
        self.pressed.connect(self.press_viewport)
        # NOTE(timmyliang): collect viewport color set
        self.pressed.connect(ApplyVertexColorCommand.collect_viewport_vertex_ids)
        self.released.connect(lambda: pm.evalDeferred(self.release_viewport))
        self.property_showed.connect(lambda: pm.evalDeferred(self.modify_property_window))
        self.color = (0, 0, 0, 1.0)

    @classmethod
    def setup_color_set(cls):
        for node in cls.get_paint_nodes():
            node.displayColors.set(1)
            color_sets = cls.get_color_sets(node)
            main_color_set = color_sets[0]

            mesh = node.__apimfn__()
            mesh.updateSurface()
            color_array = OpenMaya.MColorArray()
            mesh.getVertexColors(color_array, main_color_set)

            vtx_array = OpenMaya.MIntArray()
            vtx_list = range(color_array.length())
            OpenMaya.MScriptUtil.createIntArrayFromList(vtx_list, vtx_array)

            final_colors = OpenMaya.MColorArray()
            for channel_index, color_channel in enumerate(CHANNELS):
                color_set = "VertexColor{0}".format(color_channel)
                if color_set not in color_sets:
                    rpt = cls.color_set_representation.get(color_channel)
                    pm.polyColorSet(node, create=1, rpt=rpt, colorSet=color_set)
                mesh.setCurrentColorSetName(color_set)
                final_colors.clear()
                for array_index in vtx_array:
                    full_color = color_array[array_index]
                    color = cls.filter_color(full_color, index=channel_index)
                    final_colors.append(color)
                mesh.setVertexColors(final_colors, vtx_array)
            mesh.setCurrentColorSetName(main_color_set)

    @classmethod
    def reset_color_set(cls):
        for node in cls.get_paint_nodes():
            color_sets = cls.get_color_sets(node)
            for color_channel in CHANNELS:
                color_set = "VertexColor{0}".format(color_channel)
                if color_set in color_sets:
                    pm.polyColorSet(node, delete=1, colorSet=color_set)

    @classmethod
    def install(cls):
        if not cls.inst:
            cls.inst = cls()
            app = QtWidgets.QApplication.instance()
            app.installEventFilter(cls.inst)
        pm.evalDeferred(cls.inst.setup_color_set, lp=1)

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
            if self.is_viewport(receiver) and not self.is_press_alt:
                self.pressed.emit()
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            if self.is_viewport(receiver) and not self.is_press_alt:
                self.released.emit()
        elif isinstance(event, QtGui.QKeyEvent) and not event.isAutoRepeat():
            # NOTES(timmyliang): check alt key press
            self.is_press_alt = event.modifiers() == QtCore.Qt.AltModifier
        # NOTES(timmyliang): hack maya properties window open
        elif event.type() == QtCore.QEvent.WinIdChange:
            label = receiver.findChild(QtWidgets.QLabel)
            if label and pm.currentCtx() == "artAttrColorPerVertexContext":
                self.property_showed.emit()
        return False

    def is_viewport(self, viewport):
        panel = isinstance(viewport, QtCore.QObject) and viewport.parent()
        name = panel and panel.objectName()
        return name and pm.objectTypeUI(name, i="modelEditor")

    def press_viewport(self):
        rgb = pm.colorSliderGrp("colorPerVertexColor", q=1, rgb=1)
        alpha = pm.floatSliderGrp("colorPerVertexAlpha", q=1, value=1)
        rgb.append(alpha)

        self.color = rgb or self.color
        index = pm.radioButtonGrp(SINGLE_CONTROL, q=1, sl=1)
        channel = index - 1
        color = self.filter_color(self.color, index=channel) if channel - 1 >= 0 else self.color
        pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, cl4=tuple(color))

        # NOTE(timmyliang): change color set
        mode = OPTION_ITEMS[index + 1]
        if mode == "Auto":
            return
        for node in self.get_paint_nodes():
            original_color_set = node.getCurrentColorSetName()
            pm.evalDeferred(partial(node.setCurrentColorSetName, original_color_set))
            if mode == "RGB":
                color_sets = self.get_color_sets(node)
                color_set = color_sets[0]
            else:
                color_set = "VertexColor{0}".format(mode)
            node.setCurrentColorSetName(color_set)

    def release_viewport(self):
        # NOTE(timmyliang): reset vertex color
        pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, cl4=self.color)

        # NOTE(timmyliang): get color channel apply to main color set
        # self.apply_color_channel()
        pm.applyVertexColorCommand()

    def modify_property_window(self):

        # NOTES(timmyliang): avoid multiple ui modifications
        if pm.radioButtonGrp(SINGLE_CONTROL, q=1, ex=1):
            return
        row_layout = pm.rowLayout(numberOfColumns=2)
        grp = pm.radioButtonGrp(
            label="Single Channel:",
            nrb=1,
            sl=1,
            l1=OPTION_ITEMS[1],
            columnWidth=[(1, 130)],
            onCommand=self.on_channel_change,
        )
        pm.radioButtonGrp(
            SINGLE_CONTROL,
            shareCollection=grp,
            numberOfRadioButtons=4,
            labelArray4=OPTION_ITEMS[2:],
            columnWidth=list(enumerate([35] * 4, 1)),
            onCommand=self.on_channel_change,
        )

        layout = pm.radioButtonGrp("artAttrColorChannelChoices", q=1, parent=1)
        pm.setParent(layout)
        pm.setUITemplate("OptionsTemplate", pushTemplate=1)
        column_layout = pm.columnLayout()

        for child in pm.layout(layout, q=1, childArray=1):
            pm.control(child, e=1, p=column_layout)
            # NOTES(timmyliang): insert new ui
            if child == "artAttrColorChannelChoices":
                pm.rowLayout(row_layout, e=1, parent=column_layout)
                pm.optionMenuGrp(
                    OPTION_CONTROL,
                    label="Color Display:",
                    changeCommand=self.on_display_mode_change,
                )
                for option_item in OPTION_ITEMS:
                    pm.menuItem(label=option_item)

        pm.setUITemplate(popTemplate=1)

    def on_channel_change(self, *args):
        if pm.optionMenuGrp(OPTION_CONTROL, q=1, sl=1) == 1:
            index = pm.radioButtonGrp(SINGLE_CONTROL, q=1, sl=1)
            channel = OPTION_ITEMS[index + 1]
            self.on_display_mode_change(channel)

    @classmethod
    def on_display_mode_change(cls, mode):
        if mode == "Auto":
            sel = pm.radioButtonGrp(SINGLE_CONTROL, q=1, sl=1)
            mode = OPTION_ITEMS[sel + 1]
        for node in cls.get_paint_nodes():
            color_sets = cls.get_color_sets(node)
            main_color_set = color_sets[0]
            if mode == "RGB":
                pm.polyColorSet(node, currentColorSet=1, colorSet=main_color_set)
            else:
                color_set = "VertexColor{0}".format(mode)
                pm.polyColorSet(node, currentColorSet=1, colorSet=color_set)
        # NOTE(timmyliang): update panel
        pm.mel.syncColorPerVertexTool()


class ApplyVertexColorCommand(ApplyVertexColorBase, OpenMayaMPx.MPxCommand):

    vertex_ids_data = defaultdict(OpenMaya.MIntArray)
    vertex_color_data = defaultdict(lambda: defaultdict(OpenMaya.MColorArray))
    chunk_num = 0

    @classmethod
    def command_name(cls):
        return cls.__name__[0].lower() + cls.__name__[1:]

    @classmethod
    def creator(cls):
        return OpenMayaMPx.asMPxPtr(cls())

    def doIt(self, args):
        return self.redoIt()

    def undoIt(self):
        self.__class__.chunk_num -= 1
        for node in self.get_paint_nodes():
            main_colors = self.vertex_color_data[self.chunk_num][node.fullPathName()]
            if not main_colors.length():
                continue

            mesh = node.__apimfn__()
            current_color_set = mesh.currentColorSetName()
            color_sets = self.get_color_sets(node)
            main_color_set = color_sets[0]
            mesh.setCurrentColorSetName(main_color_set)
            vtx_array = OpenMaya.MIntArray()
            for vtx_index in range(main_colors.length()):
                vtx_array.append(vtx_index)

            mesh.setVertexColors(main_colors, vtx_array)
            for channel_index, color_channel in enumerate(CHANNELS):
                colors = OpenMaya.MColorArray()
                color_set = "VertexColor{0}".format(color_channel)
                mesh.setCurrentColorSetName(color_set)
                for vtx_index in vtx_array:
                    main_color = main_colors[vtx_index]
                    color = self.filter_color(main_color, channel_index)
                    colors.append(color)
                mesh.setVertexColors(colors, vtx_array)
            mesh.setCurrentColorSetName(current_color_set)

    def redoIt(self):
        self.__class__.chunk_num += 1
        index = pm.radioButtonGrp(SINGLE_CONTROL, q=1, sl=1)
        mode = OPTION_ITEMS[index + 1]
        for node in self.get_paint_nodes():
            self.apply_color_channel(node, mode)

    @classmethod
    def apply_color_channel(cls, node, mode):
        is_rgb = mode == "RGB"

        mesh = node.__apimfn__()
        color_sets = cls.get_color_sets(node)
        main_color_set = color_sets[0]

        current_color_set = mesh.currentColorSetName()

        main_colors = OpenMaya.MColorArray()
        mesh.getVertexColors(main_colors, main_color_set)
        vtx_array = cls.vertex_ids_data[node.fullPathName()]
        final_colors = OpenMaya.MColorArray()

        if is_rgb:
            for channel_index, color_channel in enumerate(CHANNELS):
                final_colors.clear()
                color_set = "VertexColor{0}".format(color_channel)
                mesh.setCurrentColorSetName(color_set)
                for vtx_index in vtx_array:
                    main_color = main_colors[vtx_index]
                    color = cls.filter_color(main_color, channel_index)
                    final_colors.append(color)
                mesh.setVertexColors(final_colors, vtx_array)
        else:
            mode_index = OPTION_ITEMS.index(mode) - 2
            channel_colors = OpenMaya.MColorArray()
            fix_colors = OpenMaya.MColorArray()
            color_set = "VertexColor{0}".format(mode)
            mesh.getVertexColors(channel_colors, color_set)
            for vtx_index in vtx_array:
                channel_color = channel_colors[vtx_index]
                main_color = main_colors[vtx_index]
                color = cls.filter_color(channel_color, mode_index, main_color)
                final_colors.append(color)
                fix_color = cls.filter_color(channel_color, mode_index)
                fix_colors.append(fix_color)

            mesh.setVertexColors(fix_colors, vtx_array)
            mesh.setCurrentColorSetName(main_color_set)
            mesh.setVertexColors(final_colors, vtx_array)

        mesh.setCurrentColorSetName(current_color_set)

    @classmethod
    @to_component_mode
    @use_select_depth
    def collect_viewport_vertex_ids(cls):
        """Collect Viewport Paintable Component."""
        selections = OpenMaya.MSelectionList()
        component_selections = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList(selections)

        view = OpenMayaUI.M3dView.active3dView()
        OpenMaya.MGlobal.selectFromScreen(0, 0, view.portWidth(), view.portHeight(), OpenMaya.MGlobal.kReplaceList)
        # NOTES(timmyliang): expand select index
        pm.polySelectConstraint(pp=1)
        pm.polySelectConstraint(pp=1)
        OpenMaya.MGlobal.getActiveSelectionList(component_selections)
        OpenMaya.MGlobal.setActiveSelectionList(selections)

        for itr in iterate_mit(OpenMaya.MItSelectionList(component_selections)):
            dag_path = OpenMaya.MDagPath()
            component = OpenMaya.MObject()
            itr.getDagPath(dag_path, component)

            mesh = OpenMaya.MFnMesh(dag_path)
            color_sets = []
            mesh.getColorSetNames(color_sets)
            mesh.getVertexColors(
                cls.vertex_color_data[cls.chunk_num][dag_path.fullPathName()],
                color_sets[0],
            )
            vtx_array = cls.vertex_ids_data[dag_path.fullPathName()]
            vtx_array.clear()
            for vtx_itr in iterate_mit(OpenMaya.MItMeshVertex(dag_path, component)):
                index = vtx_itr.index()
                vtx_array.append(index)

    def isUndoable(self):
        return True


def mel_proc(func):
    py2mel.py2melProc(func, procName=func.__name__)


@mel_proc
def vertex_color_tool_on():
    AppVertexColorFilter.install()
    if not pm.artAttrPaintVertexCtx(PAINT_CTX, q=1, pna=1):
        pm.headsUpMessage("Please Select Mesh")


@mel_proc
def vertex_color_tool_off():
    AppVertexColorFilter.uninstall()


@contextmanager
def try_run(name):
    try:
        yield name
    except Exception:
        sys.stderr.write("Failed to register: %s/n" % name)
        raise


# Initialize the script plug-in
def initializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj, "timmyliang", "1.0.0")
    with try_run(ApplyVertexColorCommand.command_name()) as name:
        plugin_fn.registerCommand(name, ApplyVertexColorCommand.creator)

    PAINT_CTX = pm.mel.artAttrColorPerVertexToolScript(5)
    # NOTES(timmyliang): close Tool Settings UI
    pm.uitypes.toQtObject("ToolSettings").window().close()
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="vertex_color_tool_on")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="vertex_color_tool_off")
    pm.mel.artAttrColorPerVertexToolScript(3)


# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)
    with try_run(ApplyVertexColorCommand.command_name()) as name:
        plugin_fn.deregisterCommand(name)
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, top="")
    pm.artAttrPaintVertexCtx(PAINT_CTX, e=1, tfp="")
