# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'WindNodeGroupDef.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_WindNodeGroupDef(object):
    def setupUi(self, WindNodeGroupDef):
        WindNodeGroupDef.setObjectName("WindNodeGroupDef")
        WindNodeGroupDef.resize(700, 651)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(WindNodeGroupDef.sizePolicy().hasHeightForWidth())
        WindNodeGroupDef.setSizePolicy(sizePolicy)
        WindNodeGroupDef.setMinimumSize(QtCore.QSize(700, 651))
        WindNodeGroupDef.setMaximumSize(QtCore.QSize(700, 651))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("VBC.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        WindNodeGroupDef.setWindowIcon(icon)
        self.SaveWindNodeGroup = QtWidgets.QPushButton(WindNodeGroupDef)
        self.SaveWindNodeGroup.setGeometry(QtCore.QRect(200, 610, 75, 23))
        self.SaveWindNodeGroup.setObjectName("SaveWindNodeGroup")
        self.AbandonWindNodeGroup = QtWidgets.QPushButton(WindNodeGroupDef)
        self.AbandonWindNodeGroup.setGeometry(QtCore.QRect(390, 610, 75, 23))
        self.AbandonWindNodeGroup.setObjectName("AbandonWindNodeGroup")
        self.label_7 = QtWidgets.QLabel(WindNodeGroupDef)
        self.label_7.setGeometry(QtCore.QRect(20, 30, 151, 21))
        self.label_7.setObjectName("label_7")
        self.windNodeGroupNameEnter = QtWidgets.QLineEdit(WindNodeGroupDef)
        self.windNodeGroupNameEnter.setGeometry(QtCore.QRect(150, 30, 531, 21))
        self.windNodeGroupNameEnter.setObjectName("windNodeGroupNameEnter")
        self.windNodeGroupEnter = QtWidgets.QPlainTextEdit(WindNodeGroupDef)
        self.windNodeGroupEnter.setGeometry(QtCore.QRect(20, 100, 661, 481))
        self.windNodeGroupEnter.setObjectName("windNodeGroupEnter")
        self.label_14 = QtWidgets.QLabel(WindNodeGroupDef)
        self.label_14.setGeometry(QtCore.QRect(20, 70, 531, 21))
        self.label_14.setObjectName("label_14")

        self.retranslateUi(WindNodeGroupDef)
        QtCore.QMetaObject.connectSlotsByName(WindNodeGroupDef)

    def retranslateUi(self, WindNodeGroupDef):
        _translate = QtCore.QCoreApplication.translate
        WindNodeGroupDef.setWindowTitle(_translate("WindNodeGroupDef", "风荷载作用结点组编辑"))
        self.SaveWindNodeGroup.setText(_translate("WindNodeGroupDef", "保存"))
        self.AbandonWindNodeGroup.setText(_translate("WindNodeGroupDef", "放弃"))
        self.label_7.setText(_translate("WindNodeGroupDef", "风荷载作用结点组名称"))
        self.label_14.setText(_translate("WindNodeGroupDef", "本组结点号(支持格式：1, 2-5, 101to200by10, 250-300by15)"))