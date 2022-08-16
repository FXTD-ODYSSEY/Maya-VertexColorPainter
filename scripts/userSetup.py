# -*- coding: utf-8 -*-
"""
load vertex color painter plugin when maya startup.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2022-08-16 15:31:02"

from maya import cmds
import os


def load_vertex_painter_plugin():
    root = cmds.moduleInfo(mn="VertexColorPainter", path=1)
    if cmds.pluginInfo("vertex_color_painter", q=1, l=1):
        cmds.unloadPlugin("vertex_color_painter")
    cmds.loadPlugin(os.path.join(root, "plug-ins", "vertex_color_painter.py"))


if not cmds.about(batch=1):
    load_vertex_painter_plugin()
