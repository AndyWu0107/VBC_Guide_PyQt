# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RailLocDef.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RailLocDef(object):
    def setupUi(self, RailLocDef):
        RailLocDef.setObjectName("RailLocDef")
        RailLocDef.resize(801, 601)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RailLocDef.sizePolicy().hasHeightForWidth())
        RailLocDef.setSizePolicy(sizePolicy)
        RailLocDef.setMinimumSize(QtCore.QSize(801, 601))
        RailLocDef.setMaximumSize(QtCore.QSize(801, 601))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("VBC.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        RailLocDef.setWindowIcon(icon)
        self.label = QtWidgets.QLabel(RailLocDef)
        self.label.setGeometry(QtCore.QRect(20, 60, 251, 21))
        self.label.setTextFormat(QtCore.Qt.AutoText)
        self.label.setWordWrap(False)
        self.label.setObjectName("label")
        self.railCtrlPtTable = QtWidgets.QTableWidget(RailLocDef)
        self.railCtrlPtTable.setGeometry(QtCore.QRect(20, 90, 762, 451))
        self.railCtrlPtTable.setRowCount(10)
        self.railCtrlPtTable.setObjectName("railCtrlPtTable")
        self.railCtrlPtTable.setColumnCount(8)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.railCtrlPtTable.setHorizontalHeaderItem(7, item)
        self.railCtrlPtTable.horizontalHeader().setVisible(False)
        self.railCtrlPtTable.horizontalHeader().setDefaultSectionSize(95)
        self.railCtrlPtTable.horizontalHeader().setHighlightSections(True)
        self.railCtrlPtTable.horizontalHeader().setMinimumSectionSize(50)
        self.railCtrlPtTable.verticalHeader().setVisible(False)
        self.railCtrlPtAdd = QtWidgets.QPushButton(RailLocDef)
        self.railCtrlPtAdd.setGeometry(QtCore.QRect(420, 60, 61, 23))
        self.railCtrlPtAdd.setObjectName("railCtrlPtAdd")
        self.railCtrlPtDel = QtWidgets.QPushButton(RailLocDef)
        self.railCtrlPtDel.setGeometry(QtCore.QRect(500, 60, 61, 23))
        self.railCtrlPtDel.setObjectName("railCtrlPtDel")
        self.railCtrlPtAbandon = QtWidgets.QPushButton(RailLocDef)
        self.railCtrlPtAbandon.setGeometry(QtCore.QRect(400, 560, 75, 23))
        self.railCtrlPtAbandon.setObjectName("railCtrlPtAbandon")
        self.railCtrlPtSave = QtWidgets.QPushButton(RailLocDef)
        self.railCtrlPtSave.setGeometry(QtCore.QRect(310, 560, 75, 23))
        self.railCtrlPtSave.setObjectName("railCtrlPtSave")
        self.railDirectRev = QtWidgets.QPushButton(RailLocDef)
        self.railDirectRev.setGeometry(QtCore.QRect(580, 60, 61, 23))
        self.railDirectRev.setObjectName("railDirectRev")
        self.label_2 = QtWidgets.QLabel(RailLocDef)
        self.label_2.setGeometry(QtCore.QRect(20, 20, 91, 21))
        self.label_2.setTextFormat(QtCore.Qt.AutoText)
        self.label_2.setWordWrap(False)
        self.label_2.setObjectName("label_2")
        self.railNameEdit = QtWidgets.QLineEdit(RailLocDef)
        self.railNameEdit.setGeometry(QtCore.QRect(120, 20, 251, 20))
        self.railNameEdit.setObjectName("railNameEdit")
        self.label_3 = QtWidgets.QLabel(RailLocDef)
        self.label_3.setGeometry(QtCore.QRect(430, 20, 51, 21))
        self.label_3.setObjectName("label_3")
        self.trackWidthEnter = QtWidgets.QDoubleSpinBox(RailLocDef)
        self.trackWidthEnter.setGeometry(QtCore.QRect(490, 20, 101, 22))
        self.trackWidthEnter.setDecimals(4)
        self.trackWidthEnter.setMinimum(0.0)
        self.trackWidthEnter.setSingleStep(0.005)
        self.trackWidthEnter.setProperty("value", 1.435)
        self.trackWidthEnter.setObjectName("trackWidthEnter")
        self.railCtrlPtUp = QtWidgets.QPushButton(RailLocDef)
        self.railCtrlPtUp.setGeometry(QtCore.QRect(680, 60, 41, 23))
        self.railCtrlPtUp.setObjectName("railCtrlPtUp")
        self.railCtrlPtDown = QtWidgets.QPushButton(RailLocDef)
        self.railCtrlPtDown.setGeometry(QtCore.QRect(740, 60, 41, 23))
        self.railCtrlPtDown.setObjectName("railCtrlPtDown")
        self.label_4 = QtWidgets.QLabel(RailLocDef)
        self.label_4.setGeometry(QtCore.QRect(600, 20, 51, 21))
        self.label_4.setObjectName("label_4")

        self.retranslateUi(RailLocDef)
        QtCore.QMetaObject.connectSlotsByName(RailLocDef)

    def retranslateUi(self, RailLocDef):
        _translate = QtCore.QCoreApplication.translate
        RailLocDef.setWindowTitle(_translate("RailLocDef", "?????????????????????"))
        self.label.setText(_translate("RailLocDef", "???????????????????????????????????????"))
        item = self.railCtrlPtTable.horizontalHeaderItem(0)
        item.setText(_translate("RailLocDef", "????????????"))
        item = self.railCtrlPtTable.horizontalHeaderItem(1)
        item.setText(_translate("RailLocDef", "x/m"))
        item = self.railCtrlPtTable.horizontalHeaderItem(2)
        item.setText(_translate("RailLocDef", "y/m"))
        item = self.railCtrlPtTable.horizontalHeaderItem(3)
        item.setText(_translate("RailLocDef", "z/m"))
        item = self.railCtrlPtTable.horizontalHeaderItem(4)
        item.setText(_translate("RailLocDef", "???????????????"))
        item = self.railCtrlPtTable.horizontalHeaderItem(5)
        item.setText(_translate("RailLocDef", "???????????????/m^-1"))
        item = self.railCtrlPtTable.horizontalHeaderItem(6)
        item.setText(_translate("RailLocDef", "????????????/m"))
        item = self.railCtrlPtTable.horizontalHeaderItem(7)
        item.setText(_translate("RailLocDef", "?????????/rad"))
        self.railCtrlPtAdd.setText(_translate("RailLocDef", "+"))
        self.railCtrlPtDel.setText(_translate("RailLocDef", "-"))
        self.railCtrlPtAbandon.setText(_translate("RailLocDef", "??????"))
        self.railCtrlPtSave.setText(_translate("RailLocDef", "??????"))
        self.railDirectRev.setText(_translate("RailLocDef", "??????"))
        self.label_2.setText(_translate("RailLocDef", "????????????"))
        self.label_3.setText(_translate("RailLocDef", "??????"))
        self.railCtrlPtUp.setText(_translate("RailLocDef", "???"))
        self.railCtrlPtDown.setText(_translate("RailLocDef", "???"))
        self.label_4.setText(_translate("RailLocDef", "m"))
