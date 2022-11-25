from PyQt5.QtWidgets import QDialog, QCheckBox, QComboBox
from UIWindForceVehAssign import *
from VBCDatGenerators import *


class GuideWindForceVehAssign(QDialog, Ui_windForceVehAssign):
    def __init__(self, train_and_way_name, veh_name_list, ctrl_pt_num, wind_force_name_list,
                 wind_force_already_defined=None):
        super(GuideWindForceVehAssign, self).__init__()

        self.setupUi(self)

        self.setWindowTitle('列车风力系数分配 - '+train_and_way_name)

        if wind_force_already_defined is None:
            wind_force_already_defined = []
        self.train_and_way_name = train_and_way_name
        self.veh_name_list = veh_name_list
        self.ctrl_pt_num = ctrl_pt_num
        self.wind_force_name_list = wind_force_name_list
        self.wind_force_already_defined = wind_force_already_defined
        self.save_flag = False

        self.table_set_up()

        if self.wind_force_already_defined:
            self.write_list_to_table(self.wind_force_already_defined)

        self.windForceVehAssignSave.clicked.connect(self.save_wind_force_veh_assign)
        self.windForceVehAssignAbandon.clicked.connect(self.close)

    def table_set_up(self):
        self.windForceVehAssignTable.setRowCount(len(self.veh_name_list))
        self.windForceVehAssignTable.setColumnCount(self.ctrl_pt_num+3)
        table_set_align_center_readonly(self.windForceVehAssignTable, range(0, self.windForceVehAssignTable.rowCount()), [0, 1])
        table_auto_numbering(self.windForceVehAssignTable)

        # 表头设置
        header_label_list = ['车辆序号', '车辆名称', '是否均匀风场']
        if self.ctrl_pt_num == 1:
            header_label_list.append('车辆风力系数')
        else:
            for i_col in range(3, self.windForceVehAssignTable.columnCount()):
                i_header_str = '控制点%d' %(i_col-2)
                header_label_list.append(i_header_str)
        self.windForceVehAssignTable.setHorizontalHeaderLabels(header_label_list)

        # 车辆信息填写
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            self.windForceVehAssignTable.item(i_row, 1).setText(self.veh_name_list[i_row])

        # 风荷载combo控件安置
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            for i_col in range(3, self.windForceVehAssignTable.columnCount()):
                new_combo = QComboBox()
                new_combo.addItem('无风荷载')
                new_combo.addItems(self.wind_force_name_list)
                self.windForceVehAssignTable.setCellWidget(i_row, i_col, new_combo)

        # 均匀风场check控件安置
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            new_check_box = QCheckBox()
            if self.ctrl_pt_num == 1:
                new_check_box.setCheckState(2)
                new_check_box.setEnabled(False)
            else:
                # new_check_box.setCheckState(0)
                new_check_box.setEnabled(True)
            self.windForceVehAssignTable.setCellWidget(i_row, 2, new_check_box)
            new_check_box.stateChanged.connect(self.table_state_update)

    def table_state_update(self):
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            if self.windForceVehAssignTable.cellWidget(i_row, 2).checkState() == 2:
                enabled_flag = False
                try:
                    self.windForceVehAssignTable.cellWidget(i_row, 3).currentIndexChanged.connect(self.row_combo_sync)
                except:
                    pass
            else:
                enabled_flag = True
                try:
                    self.windForceVehAssignTable.cellWidget(i_row, 3).currentIndexChanged.disconnect(self.row_combo_sync)
                except:
                    pass
            for i_col in range(4, self.windForceVehAssignTable.columnCount()):
                self.windForceVehAssignTable.cellWidget(i_row, i_col).setEnabled(enabled_flag)

    def row_combo_sync(self):
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            if self.windForceVehAssignTable.cellWidget(i_row, 2).checkState() == 2:
                for i_col in range(4, self.windForceVehAssignTable.columnCount()):
                    idx = self.windForceVehAssignTable.cellWidget(i_row, 3).currentIndex()
                    self.windForceVehAssignTable.cellWidget(i_row, i_col).setCurrentIndex(idx)

    def save_table_to_list(self):
        data_list = []
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            i_row_list = []
            for j_col in range(3, self.windForceVehAssignTable.columnCount()):
                j_str = self.windForceVehAssignTable.cellWidget(i_row, j_col).currentText()
                # if j_str == '请选择':
                #     QMessageBox.warning(self, '警告', '表中数据不完整。')
                #     return -1
                i_row_list.append(self.windForceVehAssignTable.cellWidget(i_row, j_col).currentText())
            data_list.append(i_row_list)
        return data_list

    def write_list_to_table(self, data_list):
        for i_row in range(0, self.windForceVehAssignTable.rowCount()):
            i_row_same_flag = True
            for j_col in range(3, self.windForceVehAssignTable.columnCount()):
                self.windForceVehAssignTable.cellWidget(i_row, j_col).setCurrentText(data_list[i_row][j_col-3])
                if data_list[i_row][j_col-3] != data_list[i_row][0]:
                    i_row_same_flag = False
            if i_row_same_flag:
                self.windForceVehAssignTable.cellWidget(i_row, 2).setCheckState(2)
            else:
                self.windForceVehAssignTable.cellWidget(i_row, 2).setCheckState(0)

    def save_wind_force_veh_assign(self):
        data_list = self.save_table_to_list()
        if data_list != -1:
            self.wind_force_veh_list = data_list
            self.save_flag = True
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    wind_force_already_defined = [['迎风', '迎风', '迎风', '迎风'],
                                  ['背风', '背风', '背风', '背风'],
                                  ['迎风', '迎风', '迎风', '背风'],
                                  ['背风', '背风', '背风', '背风']]
    wfa_dialog = GuideWindForceVehAssign('1道-CRH3', ['M', 'T', 'T', 'M'], 4, ['迎风', '背风'], wind_force_already_defined)
    wfa_dialog.show()
    app.exec_()
    print(wfa_dialog.wind_force_veh_list)
