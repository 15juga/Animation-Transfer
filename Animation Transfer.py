import sys
from pymel.core import *
from maya import OpenMayaUI as omui
from pymel.core.datatypes import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance
from PySide2.QtCore import *
from PySide2.QtGui import *
from shutil import *
import shutil
import os

width = 700
height = 800

sourceBone = []
targetBone = []
#Functions__________________________________________________________________________________________
def LoadBones(bone, view):
    for child in bone.getChildren():
        view.append(child) #Append lägger till element i en lista
        if child.numChildren():
            LoadBones(child, view) #Fortsätt tills det finns inga children kvar

def addToList(bone, view):
    
    skeleton = ls(sl = True)
    del bone[:]
    view.clear()
    bones = [skeleton[0]]
    LoadBones(bones[0], bones)
    for i in range(0, len(bones)):
        view.addItem(str(i) + "    " + str(bones[i]))
        bone.append(bones[i])

def remove(view):
    small = 500 #In case a skeleton has a lot of joints
    if(len(view.selectedIndexes()) == 0): #Om inget är selected radera allt i listan
        view.clear()
    else:
        for item in view.selectedIndexes():
            if(small > item.row()): #Gör small till sakerna som vi har selected som siffror
                small = item.row()
        for item in view.selectedIndexes():
            view.takeItem(small) #radera selected items
            
def getMatrix(bone):#Går in i varje skelett och sparar info
    trix = Matrix()
    if(str(bone.getParent()) != "None"): #går till root jointen
        trix = getMatrix(bone.getParent())
    else:
        return bone.getRotation().asMatrix() * bone.getOrientation().asMatrix() #Tills det inte finns en parent kvar
        
    return bone.getRotation().asMatrix() * bone.getOrientation().asMatrix() * trix #Lägga ihop matriserna

def exitB(Window):
    Window.close() 


def TransferB():
    rot = []
    sourceList = []
    targetList = []
    keys = keyframe(sourceBone[0], at = "rotateX", q = True)
    
    sPO = Matrix()
    tPO = Matrix()
    currentTime(0, e = True)#sätter time till 0
    for i in range(0, LWindow.count()):
        
        #Hämtar skelettet från listan
        sItem = int(LWindow.item(i).text().partition(" ")[0])
        tItem = int(RWindow.item(i).text().partition(" ")[0]) 
        sourceList.append(sourceBone[sItem])#Sätter skelett i en lista
        targetList.append(targetBone[tItem])
        
        sO = sourceList[i].getOrientation().asMatrix()
        tO = targetList[i].getOrientation().asMatrix()
        if(i > 0): #Hämtar bindpos av skelettet, händer bara en gång
            sPO = getMatrix(sourceList[i - 1]) #-1 få jointen innan sig själv, alltså parent jointen
            tPO = getMatrix(targetList[i - 1])
        
        #childSource/Target Parent Inverse
        cSTPOI = sPO * sO * tPO.inverse() * tO.inverse() # en del av ekvationen för att lösa rotation problem
        cTSPOI = tO * tPO * sO.inverse() * sPO.inverse()
        
        rots = []
        rX = keyframe(sourceList[i], at = "rotateX", vc = True, q = True)
        rY = keyframe(sourceList[i], at = "rotateY", vc = True, q = True)
        rZ = keyframe(sourceList[i], at = "rotateZ", vc = True, q = True)
        cR = targetList[i].getRotation().asMatrix() * cTSPOI * sourceList[i].getRotation().asMatrix().inverse()#child rotation #denna rad händer 1 gång
        for j in range(0, len(keys)):
            rots.append(cR * EulerRotation(rX[j], rY[j], rZ[j]).asMatrix() * cSTPOI)#final rotation
        rot.append(rots)
    
    sOrigin = sourceList[0].getTranslation() #Hämtar pos av root joint  
    tOrigin = targetList[0].getTranslation()
    for i in range(0, len(keys)):#för över source data till target data
        currentTime(keys[i], e = True)
        pos = tOrigin + sourceList[0].getTranslation() - sOrigin#Jämför root joint av source från förra keyframe
        targetList[0].setTranslation(pos)
        for j in range(0, len(sourceList)):
            targetList[j].setRotation(degrees(rot[j][i].rotate)) #Sättet target skelettet till samma som source skelettet, keyframe wise
        setKeyframe(targetList, at = "translate")
        setKeyframe(targetList, at = "rotate")    
    
#UI___________________________________________________________________________________________________
uiWindow = omui.MQtUtil.mainWindow()
mayaWindow = wrapInstance(int(uiWindow), QWidget)

Window = QWidget(mayaWindow)
Window.resize(width,height)
Window.setWindowFlags(Qt.Window)
Window.setMaximumSize(width, height)
Window.setMinimumSize(width, height)
Window.setWindowTitle("Animation transfer")

listViewLayout = QHBoxLayout()

#Left Buttons Layout
LBLayout = QVBoxLayout()
LBLayout.addSpacing(500)
LBLoad = QPushButton("Load Skeleton")
LBDelete = QPushButton("Delete")
LBLayout.addWidget(LBLoad)
LBLayout.addWidget(LBDelete)
LBLayout.addSpacing(500)

#Left Window Layout
LWView = QVBoxLayout()
LWindow = QListWidget()
LWindow.setDragDropMode(QAbstractItemView.InternalMove)
LWindow.setStyleSheet("QListView::item { height: 24px; }")
LWindow.setSelectionMode(QAbstractItemView.ContiguousSelection)

lText = QLabel("Source: ", Window)
lText.setAlignment(Qt.AlignHCenter)
lText.setMargin(10)

QuitB = QPushButton("Quit")
QuitB.setFixedHeight(40)

LWView.addWidget(lText)
LWView.addWidget(LWindow)
LWView.addWidget(QuitB)

#Right Window Layout
RWView = QVBoxLayout()
RWindow = QListWidget()
RWindow.setDragDropMode(QAbstractItemView.InternalMove)
RWindow.setStyleSheet("QListView::item { height: 24px; }")
RWindow.setSelectionMode(QAbstractItemView.ContiguousSelection)
TButton = QPushButton("Transfer")
TButton.setFixedHeight(40)

RText = QLabel("Target: ", Window)
RText.setAlignment(Qt.AlignHCenter)
RText.setMargin(10)

RWView.addWidget(RText)
RWView.addWidget(RWindow)
RWView.addWidget(TButton)

listViewLayout.addLayout(LBLayout)
listViewLayout.addLayout(LWView)
listViewLayout.addLayout(RWView)

#Right Side Button Layout
RBLayout = QVBoxLayout()
RBLayout.addSpacing(500)
RBLoad = QPushButton("Load Skeleton")
RBDelete = QPushButton("Delete")

RBLayout.addWidget(RBLoad)
RBLayout.addWidget(RBDelete)
listViewLayout.addLayout(RBLayout)
RBLayout.addSpacing(500)

#Buttons
LBDelete.clicked.connect(lambda: remove(LWindow)) #lambda om den tar flera parameterar
RBDelete.clicked.connect(lambda: remove(RWindow))
LBLoad.clicked.connect(lambda: addToList(sourceBone, LWindow))
RBLoad.clicked.connect(lambda: addToList(targetBone, RWindow))

QuitB.clicked.connect(lambda: exitB(Window))
TButton.clicked.connect(TransferB)

Window.setLayout(listViewLayout)
Window.show()


























