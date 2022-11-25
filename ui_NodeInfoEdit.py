from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QMessageBox, QApplication, QComboBox
from VBCDatGenerators import *
from UINodeInfoEdit import Ui_NodeInfoEdit


class GuideNodeInfoEdit(QDialog, Ui_NodeInfoEdit):
    def __init__(self, bri_nodes_already_entered):
        super(GuideNodeInfoEdit, self).__init__()
        # 初始化ui
        self.setupUi(self)
        self.setWindowTitle("结构结点坐标信息填录")
        # 坐标信息用list存储

        self.bri_nodes_already_entered = bri_nodes_already_entered
        self.save_flag = False

        # 表格初始化
        table_auto_numbering(self.bridgeNodeTable)
        if bri_nodes_already_entered:
            self.write_table_from_list(self.bridgeNodeTable, self.bri_nodes_already_entered)
        else:
            table_set_align_center_readonly(self.bridgeNodeTable, range(self.bridgeNodeTable.rowCount()))
            table_auto_numbering(self.bridgeNodeTable)
        self.bridgeNodeTable.model().rowsInserted.connect(lambda i, j, k:
                                                          table_set_align_center_readonly(self.bridgeNodeTable, [j]))
        self.bridgeNodeTable.model().rowsInserted.connect(lambda i, j, k: table_auto_numbering(self.bridgeNodeTable))
        self.bridgeNodeTable.model().rowsRemoved.connect(lambda i, j, k: table_auto_numbering(self.bridgeNodeTable))
        # 初始化剪贴板
        self.clipboard = QApplication.clipboard()

        # 增加按钮
        self.nodeAdd.clicked.connect(lambda: self.node_add(self.bridgeNodeTable))
        # 删除按钮
        self.nodeDel.clicked.connect(lambda: self.node_del(self.bridgeNodeTable))
        # 保存按钮
        self.nodesSave.clicked.connect(self.node_save)
        # 放弃按钮
        self.nodesAbandon.clicked.connect(self.close)

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    def node_add(self, table_obj):
        row_to_insert = table_obj.rowCount()
        table_obj.insertRow(row_to_insert)
        table_set_align_center_readonly(table_obj, [row_to_insert])
        table_auto_numbering(table_obj)

    def node_del(self, target_table_obj):
        self.current_selected_table = target_table_obj  # 保证删除的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(target_table_obj)
        if top != -1:
            for i_row in range(bottom, top - 1, -1):
                target_table_obj.removeCellWidget(i_row, 1)
                target_table_obj.removeRow(i_row)
        table_auto_numbering(target_table_obj)

    def save_table_to_list(self, table_obj):  # 仅适用于已经初始化过单元格的表格；序号行不保存
        not_empty_row_idx = []
        data_list = []
        data_id_list = []
        for i_row in range(0, table_obj.rowCount()):
            for i_col in range(1, 5):
                if table_obj.item(i_row, i_col).text():
                    if (not not_empty_row_idx) or (not_empty_row_idx and not_empty_row_idx[-1] != i_row):
                        not_empty_row_idx.append(i_row)
        for i_row in not_empty_row_idx:
            data_list_i_row = []
            for i_col in range(1, 5):
                if not table_obj.item(i_row, i_col).text():
                    QMessageBox.warning(self, "警告", "列表中包含不完整数据，操作已取消。")
                    return -1
                if i_col == 1:
                    try:
                        i_id = int(table_obj.item(i_row, i_col).text())
                        data_list_i_row.append(i_id)
                    except:
                        QMessageBox.warning(self, "警告", "表格中存在非法输入，操作已取消。")
                        return -1
                    if i_id in data_id_list:
                        QMessageBox.warning(self, "警告", "表格中存在重复结点号，操作已取消。")
                        return -1
                    else:
                        data_id_list.append(i_id)
                else:
                    try:
                        data_list_i_row.append(float(table_obj.item(i_row, i_col).text()))
                    except:
                        QMessageBox.warning(self, "警告", "表格中存在非法输入，操作已取消。")
                        return -1
            data_list.append(data_list_i_row)
        if not data_list:
            QMessageBox.warning(self, "警告", "表格为空，操作已取消。")
            return -1
        return data_list

    def write_table_from_list(self, table_obj, data_list):
        row_num = len(data_list)
        table_obj.setRowCount(row_num)
        table_set_align_center_readonly(table_obj, range(0, row_num), )
        for i_row in range(0, row_num):
            for i_col in range(1, 5):
                table_obj.item(i_row, i_col).setText(str(data_list[i_row][i_col - 1]))
        table_auto_numbering(table_obj)

    def node_save(self):
        data_to_save = self.save_table_to_list(self.bridgeNodeTable)
        if data_to_save == -1:
            return
        else:
            self.bri_nodes = data_to_save
            self.save_flag = True
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    node_edit_dia = GuideNodeInfoEdit([[1, 1.0, 2.0, 3.0], [2, 11.0, 12.0, 13.0]])
    node_edit_dia.show()
    app.exec()
    print(node_edit_dia.bri_nodes)
