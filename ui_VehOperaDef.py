from PyQt5.QtWidgets import QDialog, QHeaderView, QLabel
from VBCDatGenerators import *
from UIVehOperaDef import Ui_vehOperaDef


class GuideVehOperaDialog(QDialog, Ui_vehOperaDef):
    def __init__(self, rail_name, speed_num_selected, veh_opera_already_defined):
        super(GuideVehOperaDialog, self).__init__()
        # 初始化ui
        self.setupUi(self)
        if rail_name == '请选择':
            self.setWindowTitle("车列运行工况编辑 - 尚未选择轨道")
        else:
            self.setWindowTitle("车列运行工况编辑 - " + rail_name)
        # 车辆运行信息用二维list存储，不包含首列序号

        self.veh_opera_mode_dict = {0: '匀速', 1: '空气制动', 2: '动力制动+空气制动', 3: '加速'}

        self.rail_name = rail_name
        self.veh_opera_already_defined = veh_opera_already_defined
        self.speed_num_selected = speed_num_selected
        self.save_flag = False
        self.veh_opera_mode_combo_num = 0

        # 表格初始化
        self.vehOperaTable.setRowCount(1)
        header_label_speed_switch = QLabel()
        header_label_speed_switch.setText('<b>速度档位</b>')
        header_label_speed_switch.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.vehOperaTable.setCellWidget(0, 0, header_label_speed_switch)

        header_label_speed = QLabel()
        header_label_speed.setText('<b>初速度(km/h)</b>')
        header_label_speed.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.vehOperaTable.setCellWidget(0, 1, header_label_speed)

        header_label_pre_length = QLabel()
        header_label_pre_length.setText('<b>预振距离(m)</b>')
        header_label_pre_length.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.vehOperaTable.setCellWidget(0, 2, header_label_pre_length)

        header_label_post_length = QLabel()
        header_label_post_length.setText('<b>余振距离(m)</b>')
        header_label_post_length.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.vehOperaTable.setCellWidget(0, 3, header_label_post_length)

        header_label_acc = QLabel()
        header_label_acc.setText('<b>加速度(m/s<sup>2</sup>)</b>')
        header_label_acc.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.vehOperaTable.setCellWidget(0, 4, header_label_acc)

        header_label_acc_time = QLabel()
        header_label_acc_time.setText('<b>加速或制动开始时刻(s)</b>')
        header_label_acc_time.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.vehOperaTable.setCellWidget(0, 5, header_label_acc_time)

        def veh_opera_tb_ist(i, j, k):
            if j != 0:
                table_set_align_center_readonly(self.vehOperaTable, [j], [0])
            table_auto_numbering(self.vehOperaTable, row_to_start=1)

        self.vehOperaTable.model().rowsInserted.connect(veh_opera_tb_ist)
        self.vehOperaTable.model().rowsRemoved.connect(lambda i, j, k: table_auto_numbering(self.vehOperaTable, row_to_start=1))

        row_num = max(len(self.veh_opera_already_defined), self.speed_num_selected)  # 防止主窗口把速度档数改小时导致数据丢失

        [self.vehOperaTable.insertRow(i) for i in range(1, row_num+1)]  # +1：给表头留一行
        self.vehOperaTable.setColumnWidth(0, 70)
        self.vehOperaTable.setColumnWidth(1, 130)
        self.vehOperaTable.setColumnWidth(2, 130)
        self.vehOperaTable.setColumnWidth(3, 130)
        self.vehOperaTable.setColumnWidth(4, 130)
        self.vehOperaTable.setColumnWidth(5, 130)

        if veh_opera_already_defined:
            self.write_table_from_list(self.vehOperaTable, veh_opera_already_defined)
        self.vehOperaTable.setCurrentCell(-1, -1)

        # 增加按钮
        self.vehOperaAdd.clicked.connect(lambda: table_add_row(self.vehOperaTable, always_to_last=True))
        # 删除按钮
        self.vehOperaDel.clicked.connect(lambda: table_delete_row(self.vehOperaTable, rows_to_ign=[0]))
        # 上移按钮
        self.vehOperaUp.clicked.connect(self.veh_opera_order_up)
        # 下移按钮
        self.vehOperaDown.clicked.connect(self.veh_opera_order_down)
        # 保存按钮
        self.vehOperaSave.clicked.connect(self.veh_opera_save)
        # 放弃按钮
        self.vehOperaAbandon.clicked.connect(self.close)

        # 表格复制、粘贴功能
        self.clipboard = QApplication.clipboard()  # 初始化剪贴板

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    # 排序涉及到行的插入删除，容易和cellChanged信号对应的slot打架，必须临时断开
    def veh_opera_order_up(self):
        # self.vehOperaTable.cellChanged.disconnect(self.table_state_update)
        table_row_order_up(self, self.vehOperaTable, rows_to_ign=[1])
        # self.vehOperaTable.cellChanged.connect(self.table_state_update)

    def veh_opera_order_down(self):
        # self.vehOperaTable.cellChanged.disconnect(self.table_state_update)
        table_row_order_down(self, self.vehOperaTable, rows_to_ign=[0])
        # self.vehOperaTable.cellChanged.connect(self.table_state_update)

    @staticmethod
    def write_table_from_list(table_obj, data_list):
        table_obj.setRowCount(1)
        row_num = len(data_list)
        col_num = table_obj.columnCount()
        for i_row in range(1, row_num+1):  # 避开表头行
            table_obj.insertRow(i_row)
            for i_col in range(1, col_num):
                table_obj.item(i_row, i_col).setText(str(float(data_list[i_row-1][i_col-1])))  # 注意表中的序号列未存进list

    def save_table_to_list(self, table_obj):  # 仅适用于已经初始化过单元格的表格；序号行不保存
        not_empty_row_idx = []
        for i_row in range(1, table_obj.rowCount()):  # 避开表头行
            empty_flag_this_row = True
            for i_col in range(1, table_obj.columnCount()):
                if table_obj.item(i_row, i_col).text():
                    empty_flag_this_row = False
                    break
            if not empty_flag_this_row:
                not_empty_row_idx.append(i_row)
        if len(not_empty_row_idx) != table_obj.rowCount()-1:
            QMessageBox.warning(self, "警告", "列表中包含不完整数据，操作已取消。")
            return -1
        data_list = []
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

    def veh_opera_save(self):
        data_to_save = self.save_table_to_list(self.vehOperaTable)
        if data_to_save == -1:
            return
        self.veh_opera_data = data_to_save
        self.save_flag = True
        self.close()

    # 如果加速度为零，则加减速开始时间单元格无效
    # 这个过程中极易和复制粘贴的数据打架，暂时弃用
    def table_state_update(self, row, col):
        table_obj = self.vehOperaTable
        if col == 4:
            if table_obj.item(row, 4).text():
                acc = float(table_obj.item(row, 4).text())
                if acc:
                    table_obj.item(row, 5).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                else:
                    table_obj.item(row, 5).setText(str(0))
                    table_obj.item(row, 5).setFlags(Qt.ItemIsSelectable)

'''
    # 运行工况改为仅支持匀加速匀减速，此函数暂时停用
    def veh_opera_mode_combo_place(self, row_to_place_new):
        self.veh_opera_mode_combo_num += 1
        no_this_combo = self.veh_opera_mode_combo_num
        new_combo = 'veh_opera_mode_combo' + str(no_this_combo)
        new_widget_item = 'veh_opera_mode_widget_item' + str(no_this_combo)
        expr1 = """new_combo = QComboBox()
new_combo.addItem('请选择')
for i in range(0, len(self.veh_opera_mode_dict)):
    new_combo.addItem(self.veh_opera_mode_dict[i])
self.vehOperaTable.setCellWidget(row_to_place_new, 4, new_combo)
new_widget_item = QTableWidgetItem()  # 空白item，仅用于定位（因为pyqt只能对item定位，不能对cellWidget定位）
self.vehOperaTable.setItem(row_to_place_new, 4, new_widget_item)
new_combo.currentIndexChanged.connect(self.table_state_update)"""
        exec(expr1)

    def table_state_update(self, i):
        for i_row in range(0, self.vehOperaTable.rowCount()):
            if self.vehOperaTable.cellWidget(i_row, 4).currentIndex() > 0:
                i_item = QTableWidgetItem(str(self.vehOperaTable.cellWidget(i_row, 4).currentIndex()-1))
            else:
                i_item = QTableWidgetItem('')
            i_item.setFlags(Qt.ItemIsSelectable)
            self.vehOperaTable.setItem(i_row, 4, i_item)
            if self.vehOperaTable.cellWidget(i_row, 4).currentIndex() in [0, 1]:
                self.vehOperaTable.item(i_row, 5).setText('0')
                self.vehOperaTable.item(i_row, 5).setFlags(Qt.ItemIsSelectable)
            else:
                self.vehOperaTable.item(i_row, 5).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
'''


if __name__ == '__main__':
    app = QApplication([])
    rail_loc_dia = GuideVehOperaDialog('testname', 6, [[1, 2, 3, 2, 2], [11, 12, 13, 0, 2]])
    rail_loc_dia.show()
    app.exec_()
    print(rail_loc_dia.veh_opera_data)
