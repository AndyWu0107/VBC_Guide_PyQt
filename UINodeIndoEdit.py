# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NodeInfoEdit.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_NodeInfoEdit(object):
    def setupUi(self, NodeInfoEdit):
        NodeInfoEdit.setObjectName("NodeInfoEdit")
        NodeInfoEdit.resize(619, 562)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NodeInfoEdit.sizePolicy().hasHeightForWidth())
        NodeInfoEdit.setSizePolicy(sizePolicy)
        self.bridgeNodeTable = QtWidgets.QTableWidget(NodeInfoEdit)
        self.bridgeNodeTable.setGeometry(QtCore.QRect(20, 40, 581, 481))
        self.bridgeNodeTable.setRowCount(10)
        self.bridgeNodeTable.setObjectName("bridgeNodeTable")
        self.bridgeNodeTable.setColumnCount(5)
        item = QtWidgets.QTableWidgetItem()
        self.bridgeNodeTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.bridgeNodeTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.bridgeNodeTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.bridgeNodeTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.bridgeNodeTable.setHorizontalHeaderItem(4, item)
        self.bridgeNodeTable.horizontalHeader().setDefaultSectionSize(111)
        self.bridgeNodeTable.verticalHeader().setVisible(False)
        self.nodeAdd = QtWidgets.QPushButton(NodeInfoEdit)
        self.nodeAdd.setGeometry(QtCore.QRect(420, 10, 75, 23))
        self.nodeAdd.setObjectName("nodeAdd")
        self.nodeDel = QtWidgets.QPushButton(NodeInfoEdit)
        self.nodeDel.setGeometry(QtCore.QRect(520, 10, 75, 23))
        self.nodeDel.setObjectName("nodeDel")
        self.nodesAbandon = QtWidgets.QPushButton(NodeInfoEdit)
        self.nodesAbandon.setGeometry(QtCore.QRect(330, 530, 71, 23))
        self.nodesAbandon.setObjectName("nodesAbandon")
        self.nodesSave = QtWidgets.QPushButton(NodeInfoEdit)
        self.nodesSave.setGeometry(QtCore.QRect(220, 530, 71, 23))
        self.nodesSave.setObjectName("nodesSave")
        self.label = QtWidgets.QLabel(NodeInfoEdit)
        self.label.setGeometry(QtCore.QRect(30, 10, 331, 21))
        self.label.setObjectName("label")

        self.retranslateUi(NodeInfoEdit)
        QtCore.QMetaObject.connectSlotsByName(NodeInfoEdit)

    def retranslateUi(self, NodeInfoEdit):
        _translate = QtCore.QCoreApplication.translate
        NodeInfoEdit.setWindowTitle(_translate("NodeInfoEdit", "Dialog"))
        item = self.bridgeNodeTable.horizontalHeaderItem(0)
        item.setText(_translate("NodeInfoEdit", "??????"))
        item = self.bridgeNodeTable.horizontalHeaderItem(1)
        item.setText(_translate("NodeInfoEdit", "?????????"))
        item = self.bridgeNodeTable.horizontalHeaderItem(2)
        item.setText(_translate("NodeInfoEdit", "X"))
        item = self.bridgeNodeTable.horizontalHeaderItem(3)
        item.setText(_translate("NodeInfoEdit", "Y"))
        item = self.bridgeNodeTable.horizontalHeaderItem(4)
        item.setText(_translate("NodeInfoEdit", "Z"))
        self.nodeAdd.setText(_translate("NodeInfoEdit", "+"))
        self.nodeDel.setText(_translate("NodeInfoEdit", "-"))
        self.nodesAbandon.setText(_translate("NodeInfoEdit", "??????"))
        self.nodesSave.setText(_translate("NodeInfoEdit", "??????"))
        self.label.setText(_translate("NodeInfoEdit", "????????????????????????????????????????????????/???????????????????????????"))
