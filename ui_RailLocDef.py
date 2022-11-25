from PyQt5.QtWidgets import QDialog, QLabel
from VBCDatGenerators import *
from UIRailLocDef import Ui_RailLocDef


class GuideRailLocDefDialog(QDialog, Ui_RailLocDef):
    def __init__(self, rail_name, rail_names_exist, rail_pts_already_defined):
        super(GuideRailLocDefDialog, self).__init__()
        # 初始化ui
        self.setupUi(self)
        self.setWindowTitle("行车轨道控制点编辑 - " + rail_name)
        # 控制点信息用二维list存储
        # 第一个元素是轨距float，后面是控制点表格的每一行list
        # 回到主窗口后，

        self.rail_name = rail_name
        self.rail_names_exist = rail_names_exist
        self.save_flag = False

        # 轨道名初始化
        self.railNameEdit.setText(self.rail_name)
        # 轨距初始化
        self.track_width = self.trackWidthEnter.value()
        self.trackWidthEnter.valueChanged.connect(self.track_width_enter)
        # 表格初始化
        self.railCtrlPtTable.setRowCount(1)
        header_pt_order = QLabel()
        header_pt_order.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_pt_order.setText('<b>控制点号</b>')
        self.railCtrlPtTable.setCellWidget(0, 0, header_pt_order)

        header_x = QLabel()
        header_x.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_x.setText('<b>x(m)</b>')
        self.railCtrlPtTable.setCellWidget(0, 1, header_x)

        header_y = QLabel()
        header_y.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_y.setText('<b>y(m)</b>')
        self.railCtrlPtTable.setCellWidget(0, 2, header_y)

        header_z = QLabel()
        header_z.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_z.setText('<b>z(m)</b>')
        self.railCtrlPtTable.setCellWidget(0, 3, header_z)

        header_k = QLabel()
        header_k.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_k.setText('<b>平曲线斜率</b>')
        self.railCtrlPtTable.setCellWidget(0, 4, header_k)

        header_r = QLabel()
        header_r.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_r.setText('<b>平曲线曲率(m<sup>-1</sup>)</b>')
        self.railCtrlPtTable.setCellWidget(0, 5, header_r)

        header_s = QLabel()
        header_s.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_s.setText('<b>弧长坐标(m)</b>')
        self.railCtrlPtTable.setCellWidget(0, 6, header_s)

        header_sh = QLabel()
        header_sh.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        header_sh.setText('<b>超高角(rad)</b>')
        self.railCtrlPtTable.setCellWidget(0, 7, header_sh)

        def rail_ctrl_pt_tb_ist(i, j, k):
            if j != 0:
                table_set_align_center_readonly(self.railCtrlPtTable, [j], [0])
            table_auto_numbering(self.railCtrlPtTable, row_to_start=1)

        self.railCtrlPtTable.model().rowsInserted.connect(rail_ctrl_pt_tb_ist)
        self.railCtrlPtTable.model().rowsRemoved.connect(lambda i, j, k: table_auto_numbering(self.railCtrlPtTable, row_to_start=1))
        self.railCtrlPtTable.setColumnWidth(0, 78)
        [self.railCtrlPtTable.insertRow(1) for i in range(0, 10)]
        if rail_pts_already_defined:
            self.write_table_from_list(self.railCtrlPtTable, rail_pts_already_defined)

        # 轨道名实时更新
        self.railNameEdit.textChanged.connect(self.rail_name_update)
        self.railNameEdit.textChanged.connect(self.window_title_update)
        # 增加按钮
        self.railCtrlPtAdd.clicked.connect(lambda: self.rail_ctrl_pt_add(self.railCtrlPtTable))
        # 删除按钮
        self.railCtrlPtDel.clicked.connect(lambda: self.rail_ctrl_pt_del(self.railCtrlPtTable))
        # 反向按钮
        self.railDirectRev.clicked.connect(lambda: self.rail_direct_rev(self.railCtrlPtTable))
        # 上移按钮
        self.railCtrlPtUp.clicked.connect(lambda: table_row_order_up(self, self.railCtrlPtTable, rows_to_ign=[1]))
        # 下移按钮
        self.railCtrlPtDown.clicked.connect(lambda: table_row_order_down(self, self.railCtrlPtTable, rows_to_ign=[0]))
        # 保存按钮
        self.railCtrlPtSave.clicked.connect(self.rail_ctrl_pt_save)
        # 放弃按钮
        self.railCtrlPtAbandon.clicked.connect(self.close)

        # 表格复制、粘贴功能
        self.clipboard = QApplication.clipboard()  # 初始化剪贴板

    def track_width_enter(self):
        self.track_width = self.trackWidthEnter.value()

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    def rail_name_update(self):
        self.rail_name = self.railNameEdit.text()

    def window_title_update(self):
        self.setWindowTitle("行车轨道控制点编辑 - " + self.railNameEdit.text())

    def rail_ctrl_pt_add(self, table_obj):
        table_add_row(table_obj, always_to_last=True)

    def rail_ctrl_pt_del(self, target_table_obj):
        table_delete_row(target_table_obj, rows_to_ign=[0])

    def rail_direct_rev(self, table_obj):
        # 思路：先检查、整理已有表格，存入临时list（格式同最终list），再重新解析写入表格
        # 存储、读取和写表可考虑另用函数，和最终的读写数据共用
        data_list_temp = self.save_table_to_list(table_obj)
        if data_list_temp != -1:
            ctrl_pt_list_temp = data_list_temp[1:len(data_list_temp)]
            ctrl_pt_list_temp.reverse()
            data_list_temp_new = [data_list_temp[0]] + ctrl_pt_list_temp
            self.write_table_from_list(table_obj, data_list_temp_new)

    def save_table_to_list(self, table_obj):  # 仅适用于已经初始化过单元格的表格；序号行不保存
        not_empty_row_idx = []
        for i_row in range(1, table_obj.rowCount()):
            empty_flag_this_row = True
            for i_col in range(1, table_obj.columnCount()):
                if table_obj.item(i_row, i_col).text():
                    empty_flag_this_row = False
                    break
            if not empty_flag_this_row:
                not_empty_row_idx.append(i_row)
        data_list = [self.track_width]
        for i_row in not_empty_row_idx:
            valid_flag_this_row = False
            data_list_this_row = []
            for i_col in range(1, table_obj.columnCount()):
                if table_obj.item(i_row, i_col).text():
                    try:
                        data_list_this_row.append(float(table_obj.item(i_row, i_col).text()))
                        valid_flag_this_row = True
                    except:
                        QMessageBox.warning(self, "警告", "存在非法输入。")
                        return -1
                else:
                    valid_flag_this_row = False
                    break
            if valid_flag_this_row:
                data_list.append(data_list_this_row)
            else:
                QMessageBox.warning(self, "警告", "列表中包含不完整数据，操作已取消。")
                return -1
        return data_list

    def write_table_from_list(self, table_obj, data_list):
        row_num = len(data_list)
        col_num = table_obj.columnCount()
        table_obj.setRowCount(1)  # 给表头留一行
        self.trackWidthEnter.setValue(data_list[0])
        for i_row in range(1, row_num):  # 注意list的第一位是轨距float
            table_obj.insertRow(table_obj.rowCount())
            for i_col in range(1, col_num):  # 注意表中的序号列未存进list
                table_obj.item(i_row, i_col).setText(str(float(data_list[i_row][i_col-1])))  # 给表头留一行，刚好对应了轨距在datalist中占掉的一个位置

    def rail_ctrl_pt_save(self):
        if self.rail_name in self.rail_names_exist:  # 先检查轨道名有没有重复
            QMessageBox.warning(self, "警告", "当前轨道名称已经存在，请重新命名。")
            return
        if not self.rail_name:
            QMessageBox.warning(self, "警告", "轨道名称不能为空。")
            return
        data_to_save = self.save_table_to_list(self.railCtrlPtTable)
        if data_to_save == -1:
            return
        if len(data_to_save) < 3:
            QMessageBox.warning(self, "警告", "请至少定义2个控制点。")
            return
        else:
            self.rail_ctrl_pts = data_to_save
            self.save_flag = True
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    # rail_loc_dia = GuideRailLocDefDialog('testname', ['123', 'abc'], [])
    rail_loc_dia = GuideRailLocDefDialog('testname', ['123', 'abc'], [18, [1, 2, 3, 4, 5, 6, 7], [2, 3, 4, 5, 6, 7, 8]])
    rail_loc_dia.show()
    app.exec_()
    print(rail_loc_dia.rail_ctrl_pts)
