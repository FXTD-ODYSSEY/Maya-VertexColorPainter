#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Time      : 2016/1/8 02:46
# Email     : spirit_az@foxmail.com
# File      : dragOnMeshCmds.py
__author__ = 'ChenLiang.Miao'

# import --+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
import math
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds
from .. import baseEnv as baseEnv
import pymel.core as pm
import random

# function +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
_dragOnMeshContext = baseEnv.dragOnMeshContext
_abcFlag = baseEnv.dragOnMeshDescribeFlag
_iconFlag = baseEnv.dragOnMeshIconsFlag

dev = 180 / math.pi / 10


# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ #
def runApply(*args):
    cmds.setToolTo('moveSuperContext')


def run(initTrans, growSel, copyNum=1, rotate=0, randomRotate=0, secondRotate=0, sca=1.0, randomSca=0.0, secondSca=1):
    """

    :return:
    """
    # 加载插件
    # plugName = "modelEditor.mll"
    # if not cmds.pluginInfo(plugName, q=True, l=True):
    #     try:
    #         cmds.loadPlugin(plugName)
    #     except Exception as e:
    #         om.MGlobal_displayError("no found plugin : {}\nplease call author: QQ: 1204172445 ")
    ctxt = context(initTrans, growSel,
                   copyNum=copyNum,
                   rotate=rotate, randomRotate=randomRotate, secondRotate=secondRotate,
                   sca=sca, randomSca=randomSca, secondSca=secondSca)
    ctxt.createContext()
    return ctxt


def updateView():
    omui.M3dView().active3dView().refresh(False, True)


def getIntersect(vpX, vpY):
    pos = om.MPoint()
    intersect = om.MVector()
    omui.M3dView().active3dView().viewToWorld(int(vpX), int(vpY), pos, intersect)
    # 射线
    stPos = om.MFloatPoint(pos)
    intersect = om.MFloatVector(intersect)
    return stPos, intersect


def getPoints(inMesh, sourcePoint, direction, maxParam=99999):
    hitPoint = om.MFloatPoint()
    selectionList = om.MSelectionList()
    selectionList.add(inMesh)
    dagPath = om.MDagPath()
    selectionList.getDagPath(0, dagPath)
    fnMesh = om.MFnMesh(dagPath)
    intersection = fnMesh.closestIntersection(
        sourcePoint,
        direction,
        None,
        None,
        False,
        om.MSpace.kWorld,
        maxParam,
        False,
        None,
        hitPoint,
        None,
        None,
        None,
        None,
        None)
    if intersection:
        return hitPoint
    else:
        return None


class context(object):
    _initTrans = ''
    _currentTrans = None
    _growSel = ''
    context = _dragOnMeshContext

    @property
    def initTrans(self):
        return self._initTrans

    @initTrans.setter
    def initTrans(self, val):
        self._initTrans = val

    @initTrans.deleter
    def initTrans(self):
        self._initTrans = ''

    @property
    def currentTrans(self):
        return self._currentTrans  # type: om.MFnTransform

    @currentTrans.setter
    def currentTrans(self, val):
        self._currentTrans = val

    @currentTrans.deleter
    def currentTrans(self):
        self._currentTrans = list()

    @property
    def growSel(self):
        return self._growSel

    @growSel.setter
    def growSel(self, val):
        self._growSel = val

    @growSel.deleter
    def growSel(self):
        self._growSel = ''

    def __init__(self, initTrans, growSel,
                 copyNum=1,
                 rotate=0, randomRotate=0, secondRotate=0.0,
                 sca=1.0, randomSca=0.0, secondSca=1.0):
        om.MGlobal_clearSelectionList()
        self.mainGrp = ''
        self.currentTransRotXYZ = list()
        self.dragInitPos = [0, 0, 0]
        self.dragEndPos = [0, 0, 0]
        self.initTrans = initTrans
        self.growSel = om.MFnDagNode(pm.PyNode(growSel).__apimdagpath__().transform()).partialPathName()
        self.mouseX = 0

        self.copyNum = copyNum
        self.rotate = rotate
        self.randomRotate = randomRotate
        self.secondRotate = secondRotate
        self.sca = sca
        self.randomSca = randomSca
        self.secondSca = secondSca

        if randomRotate == 0:
            self.rotateList = [rotate for i in range(copyNum)]
        else:
            rotateMin = rotate - randomRotate
            rotateMax = rotate + randomRotate
            getDev = abs(randomRotate) * 2 / copyNum
            self.rotateList = [random.randrange(rotateMin, rotateMax + getDev, getDev) for i in range(0, copyNum)]

        if randomSca == 0:
            self.scaList = [sca for i in range(0, copyNum)]
        else:
            scaMin = int(sca * 100 * (1 - randomSca))
            scaMax = int(sca * 100 * (1 + randomSca))
            getDev = int(abs(randomSca) * 200 / copyNum)
            self.scaList = [random.randrange(scaMin, scaMax + getDev, getDev) / 100.00 for i in range(0, copyNum)]

        #
        cmds.setAttr('{}.visibility'.format(self.initTrans), True)

    def contextDrag(self):
        button = cmds.draggerContext(_dragOnMeshContext, query=True, button=True)  # left : 1, middle: 2
        if button == 1:
            # 创建后的移动
            vpX, vpY, _ = cmds.draggerContext(self.context, q=True, dragPoint=True)
            # 得到射线的点，以及距离
            sourcePoint, direction = getIntersect(vpX, vpY)
            # 得到模型上的点
            hitPoint = getPoints(self.growSel, sourcePoint, direction)
            if hitPoint:
                self.dragEndPos = vpX, vpY, _
                if self.copyNum == 1:
                    self.consGrp[0].translate.set(hitPoint)
                else:
                    endX, endY, _ = self.dragInitPos
                    numLen = self.copyNum - 1.0
                    devX = (endX - vpX) / numLen
                    devY = (endY - vpY) / numLen
                    for i in range(self.copyNum):
                        finX, finY = endX - i * devX, endY - i * devY
                        sourcePoint, direction = getIntersect(finX, finY)
                        hitPoint = getPoints(self.growSel, sourcePoint, direction)
                        self.consGrp[i].translate.set(hitPoint)

            updateView()

        if button == 2:
            pressPosition = cmds.draggerContext(self.context, query=True, dragPoint=True)
            moveDis = self.mouseX - pressPosition[0]
            self.currentTrans.rotate.set(self.currentTransXYZ[0],
                                         self.currentTransXYZ[1] - moveDis / dev,
                                         self.currentTransXYZ[2])
            updateView()
        pass

    def contextPress(self):
        button = cmds.draggerContext(_dragOnMeshContext, query=True, button=True)  # left : 1, middle: 2
        if button == 1:
            self.mainGrp = pm.group(em=True)
            pm.parent(self.mainGrp, self.growSel)
            # create trans
            self.currentTrans = list()
            self.consGrp = list()
            for i in range(0, self.copyNum):
                currentTrans = pm.duplicate(self.initTrans, rr=1)[0]  # type: str
                self.currentTrans.append(currentTrans)

                consGrp = pm.group(em=1, name='dragOnMesh#')
                pm.parent(consGrp, self.mainGrp)
                pm.parent(currentTrans, consGrp)
                consGrp.scale.set(self.scaList[i] * self.secondSca,
                                  self.scaList[i] * self.secondSca,
                                  self.scaList[i] * self.secondSca)
                currentTrans.rotate.set(0, self.rotateList[i] + self.secondRotate, 0)

                self.consGrp.append(consGrp)

                pm.geometryConstraint(self.growSel, consGrp, weight=1)
                pm.normalConstraint(self.growSel, consGrp, weight=1,
                                    aimVector=(0, 1, 0),
                                    upVector=(0, 0, 1),
                                    worldUpType="scene")

            vpX, vpY, _ = cmds.draggerContext(self.context, q=True, anchorPoint=True)
            sourcePoint, direction = getIntersect(vpX, vpY)
            hitPoint = getPoints(self.growSel, sourcePoint, direction)
            for consGrp in self.consGrp:
                if hitPoint:
                    consGrp.translate.set(hitPoint)
                else:
                    consGrp.translate.set(sourcePoint)
            if hitPoint:
                self.dragInitPos = vpX, vpY, _

            updateView()

        elif button == 2:
            pressPosition = cmds.draggerContext(self.context, query=True, anchorPoint=True)
            self.mouseX = pressPosition[0]
            self.currentTransRotXYZ = list()
            for each in self.currentTrans:
                self.currentTransRotXYZ.append(each.rotate.get())

    def contextDragFinalize(self):
        cmds.hide(self.initTrans)
        cmds.select(self.growSel, r=1)

    def createContext(self):
        # 安装鼠标事件
        cmds.setToolTo('moveSuperContext')
        # # 事件名称
        if not cmds.draggerContext(self.context, ex=1):
            cmds.draggerContext(self.context,
                                pressCommand=self.contextPress,
                                dragCommand=self.contextDrag,
                                finalize=self.contextDragFinalize,
                                cursor='hand'
                                )
        else:
            cmds.draggerContext(self.context, e=1,
                                pressCommand=self.contextPress,
                                dragCommand=self.contextDrag,
                                finalize=self.contextDragFinalize,
                                cursor='hand'
                                )
        # # 开始注册事件
        cmds.setToolTo(self.context)

    def scale_changed(self, sca, randomSca):
        copyNum = self.copyNum
        if randomSca == 0:
            self.scaList = [sca for i in range(0, copyNum)]
        else:
            scaMin = int(sca * 100 * (1 - randomSca))
            scaMax = math.ceil(sca * 100 * (1 + randomSca))
            getDev = int((scaMax - scaMin) / copyNum) + 1
            self.scaList = [round(random.randrange(scaMin, scaMax + getDev + 1, getDev) / 100.00, 4) for i in
                            range(0, copyNum)]

        for (i, consGrp) in enumerate(self.consGrp):
            consGrp.scale.set(self.scaList[i] * self.secondSca, self.scaList[i] * self.secondSca,
                              self.scaList[i] * self.secondSca)

        updateView()

    def secondScale_changed(self, sca):
        self.secondSca = sca
        for (i, consGrp) in enumerate(self.consGrp):
            consGrp.scale.set(self.scaList[i] * self.secondSca, self.scaList[i] * self.secondSca,
                              self.scaList[i] * self.secondSca)

        updateView()

    def rotate_changed(self, rotate, randomRotate):
        if randomRotate == 0:
            self.rotateList = [rotate for i in range(self.copyNum)]
        else:
            rotateMin = rotate - randomRotate
            rotateMax = rotate + randomRotate
            getDev = abs(randomRotate) * 2 / self.copyNum
            self.rotateList = [random.randrange(rotateMin, rotateMax + getDev, getDev) for i in range(0, self.copyNum)]

        for (i, consGrp) in enumerate(self.consGrp):
            currentTrans = consGrp.childAtIndex(0)
            currentTrans.rotate.set(0, self.rotateList[i] + self.secondRotate, 0)

        updateView()

    def secondRotate_changed(self, rot):
        self.secondRotate = rot
        for (i, consGrp) in enumerate(self.consGrp):
            currentTrans = consGrp.childAtIndex(0)
            currentTrans.rotate.set(0, self.rotateList[i] + self.secondRotate, 0)

        updateView()

    def copyNum_changed(self, copyNum, rotate, randomRotate, secondRotate, sca, randomSca, secondSca):
        if not cmds.objExists(self.initTrans):
            return
        cmds.setAttr('{}.visibility'.format(self.initTrans), True)
        pm.delete(self.mainGrp)
        self.copyNum = copyNum
        self.rotate = rotate
        self.randomRotate = randomRotate
        self.secondRotate = secondRotate
        self.sca = sca
        self.randomSca = randomSca
        self.secondSca = secondSca

        if randomRotate == 0:
            self.rotateList = [rotate for i in range(copyNum)]
        else:
            rotateMin = rotate - randomRotate
            rotateMax = rotate + randomRotate
            getDev = abs(randomRotate) * 2 / copyNum
            self.rotateList = [random.randrange(rotateMin, rotateMax + getDev, getDev) for i in range(0, copyNum)]

        if randomSca == 0:
            self.scaList = [sca for i in range(0, copyNum)]
        else:
            scaMin = int(sca * 100 * (1 - randomSca))
            scaMax = int(sca * 100 * (1 + randomSca))
            getDev = int(abs(randomSca) * 200 / copyNum)
            self.scaList = [random.randrange(scaMin, scaMax + getDev, getDev) / 100.00 for i in range(0, copyNum)]

        self.mainGrp = pm.group(em=True)
        pm.parent(self.mainGrp, self.growSel)
        # create trans
        self.currentTrans = list()
        self.consGrp = list()
        for i in range(0, self.copyNum):
            currentTrans = pm.duplicate(self.initTrans, rr=1)[0]  # type: str
            self.currentTrans.append(currentTrans)

            consGrp = pm.group(em=1, name='dragOnMesh#')
            pm.parent(consGrp, self.mainGrp)
            pm.parent(currentTrans, consGrp)
            consGrp.scale.set(self.scaList[i] * self.secondSca,
                              self.scaList[i] * self.secondSca,
                              self.scaList[i] * self.secondSca)
            currentTrans.rotate.set(0, self.rotateList[i] + self.secondRotate, 0)

            self.consGrp.append(consGrp)

            pm.geometryConstraint(self.growSel, consGrp, weight=1)
            pm.normalConstraint(self.growSel, consGrp, weight=1,
                                aimVector=(0, 1, 0),
                                upVector=(0, 0, 1),
                                worldUpType="scene")

        vpX, vpY, _ = self.dragEndPos
        sourcePoint, direction = getIntersect(vpX, vpY)
        hitPoint = getPoints(self.growSel, sourcePoint, direction)
        if hitPoint:
            if self.copyNum == 1:
                self.consGrp[0].translate.set(hitPoint)
            else:
                endX, endY, _ = self.dragInitPos
                numLen = self.copyNum - 1.0
                devX = (endX - vpX) / numLen
                devY = (endY - vpY) / numLen
                for i in range(self.copyNum):
                    finX, finY = endX - i * devX, endY - i * devY
                    sourcePoint, direction = getIntersect(finX, finY)
                    hitPoint = getPoints(self.growSel, sourcePoint, direction)
                    self.consGrp[i].translate.set(hitPoint)

        updateView()
