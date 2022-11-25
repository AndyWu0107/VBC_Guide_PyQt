from PyQt5.QtWidgets import QDialog, QComboBox  # 小心！！Combo是文本exec时用到的，编译器检测不出来！
from UITrainDef import Ui_TrainDef
from VBCDatGenerators import *


class GuideTrainDefDialog(QDialog, Ui_TrainDef):
    def __init__(self, train_name, train_names_exist, vehicle_type_dict, common_train_dict, train_vehicles_already_defined):
        super(GuideTrainDefDialog, self).__init__()
        # 初始化ui
        self.setupUi(self)
        self.setWindowTitle("车列编辑 - " + train_name)
        # 编组信息用list存储

        self.train_name = train_name
        self.train_names_exist = train_names_exist
        self.vehicle_type_dict = vehicle_type_dict
        self.vehicle_id_list = list(self.vehicle_type_dict.keys())
        self.vehicle_id_list.sort()
        self.vehicle_name_list = [self.vehicle_type_dict[i][0] for i in self.vehicle_id_list]
        self.common_train_dict = common_train_dict
        self.train_vehicles_already_defined = train_vehicles_already_defined
        self.save_flag = False
        self.train_table_combo_num = 0

        # 车列名初始化
        self.trainNameEdit.setText(self.train_name)
        # 表格初始化
        # self.table_set_align_center_readonly(self.trainVehicleTable, range(0, self.trainVehicleTable.rowCount()), [])
        self.trainVehicleTable.setColumnWidth(0, 78)
        self.trainVehicleTable.setColumnWidth(1, 200)

        def train_veh_tb_ist(i, j, k):
            table_set_align_center_readonly(self.trainVehicleTable, [j], [0])
            table_auto_numbering(self.trainVehicleTable)

        self.trainVehicleTable.model().rowsInserted.connect(train_veh_tb_ist)
        self.trainVehicleTable.model().rowsRemoved.connect(lambda i, j, k: table_auto_numbering(self.trainVehicleTable))
        if train_vehicles_already_defined:
            self.write_table_from_list(self.trainVehicleTable, self.train_vehicles_already_defined)
        # 常用车列清单初始化
        if train_vehicles_already_defined:
            self.selfDefineTrain.setChecked(True)
        else:
            self.useCommonTrain.setChecked(True)
        self.commonTrainsList.clear()
        for i_ct in self.common_train_dict.keys():
            self.commonTrainsList.addItem(i_ct)

        # 轨道名实时更新
        self.trainNameEdit.textChanged.connect(self.train_name_update)
        self.trainNameEdit.textChanged.connect(self.window_title_update)
        # 车列定义方式选择
        self.switch_define_method()
        self.trainDefMethod.idClicked.connect(self.switch_define_method)
        # 常见车列直接命名
        self.commonTrainsList.currentRowChanged.connect(self.select_common_train)
        # 增加按钮
        self.vehicleAdd.clicked.connect(lambda: self.vehicle_add(self.trainVehicleTable))
        # 删除按钮
        self.vehicleDel.clicked.connect(lambda: self.vehicle_del(self.trainVehicleTable))
        # 保存按钮
        self.trainSave.clicked.connect(self.train_save)
        # 放弃按钮
        self.trainAbandon.clicked.connect(self.close)

    def train_name_update(self):
        self.train_name = self.trainNameEdit.text()

    def window_title_update(self):
        self.setWindowTitle("车列编辑 - " + self.trainNameEdit.text())

    def switch_define_method(self):
        if self.useCommonTrain.isChecked():
            self.commonTrainsList.setVisible(True)
            self.trainVehicleTable.setVisible(False)
            self.vehicleAdd.setVisible(False)
            self.vehicleDel.setVisible(False)
        else:
            self.commonTrainsList.setVisible(False)
            self.trainVehicleTable.setVisible(True)
            self.vehicleAdd.setVisible(True)
            self.vehicleDel.setVisible(True)

    def select_common_train(self):
        self.trainNameEdit.setText(self.commonTrainsList.currentItem().text())

    def vehicle_add(self, table_obj):
        row_to_insert = table_obj.rowCount()
        table_obj.insertRow(row_to_insert)
        self.train_combo_place(row_to_insert)

    def vehicle_del(self, target_table_obj):
        top, left, bottom, right = table_select_range(target_table_obj)
        if top != -1:
            for i_row in range(bottom, top - 1, -1):
                target_table_obj.removeCellWidget(i_row, 1)
                target_table_obj.removeRow(i_row)

    # 安置非线性弹簧连接结点表格中的控件（在每个新增行动作之后执行）
    def train_combo_place(self, row_to_place_new):
        # 第一部分：新增行中放新控件
        self.train_table_combo_num += 1
        new_combo = 'train_table_combo' + str(self.train_table_combo_num)
        expr = """new_combo = QComboBox()
new_combo.addItem('请选择')
#item_num = len(self.vehicle_type_dict)
#for i in range(1, item_num+1):
#    new_combo.addItem(self.vehicle_type_dict[i])
new_combo.addItems(self.vehicle_name_list)
self.trainVehicleTable.setCellWidget(row_to_place_new, 1, new_combo)"""
        exec(expr)

    # 删除非线性弹簧连接结点表格中的控件（在每个删除动作之前执行）
    def train_combo_del(self, row_to_del_old):
        # 第二部分：被删除的行中去除旧控件
        self.trainVehicleTable.removeCellWidget(row_to_del_old, 1)

    def save_table_to_list(self, table_obj):  # 仅适用于已经初始化过单元格的表格；序号行不保存
        if self.useCommonTrain.isChecked():
            if self.commonTrainsList.currentRow() == -1:
                QMessageBox.warning(self, "警告", "未选中任何车列，操作已取消。")
                return -1
            else:
                data_list = self.common_train_dict[self.commonTrainsList.currentItem().text()]
        else:
            not_empty_row_idx = []
            data_list = []
            for i_row in range(0, table_obj.rowCount()):
                if table_obj.cellWidget(i_row, 1).currentIndex():
                    not_empty_row_idx.append(i_row)
                    if (i_row + 1) != len(not_empty_row_idx):
                        QMessageBox.warning(self, "警告", "列表中包含不完整数据，操作已取消。")
                        return -1
                    id_this_veh_in_combo = table_obj.cellWidget(i_row, 1).currentIndex()
                    id_this_veh_in_vbc = self.vehicle_id_list[id_this_veh_in_combo-1]
                    data_list.append(id_this_veh_in_vbc)
            if not data_list:
                QMessageBox.warning(self, "警告", "车列未包含任何车辆，操作已取消。")
                return -1
        return data_list

    def write_table_from_list(self, table_obj, data_list):
        row_num = len(data_list)
        table_obj.setRowCount(0)
        for i_row in range(0, row_num):
            table_obj.insertRow(i_row)
            self.train_combo_place(i_row)
            id_this_veh_in_vbc = data_list[i_row]
            name_this_veh = self.vehicle_type_dict[id_this_veh_in_vbc][0]
            id_this_veh_in_combo = self.vehicle_name_list.index(name_this_veh) + 1
            table_obj.cellWidget(i_row, 1).setCurrentIndex(id_this_veh_in_combo)

    def train_save(self):
        if self.train_name in self.train_names_exist:  # 先检查轨道名有没有重复
            QMessageBox.warning(self, "警告", "当前车列名称已经存在，请重新命名。")
            return
        if not self.train_name:
            QMessageBox.warning(self, "警告", "车列名称不能为空。")
            return
        data_to_save = self.save_table_to_list(self.trainVehicleTable)
        if data_to_save == -1:
            return
        else:
            self.train_vehicles = data_to_save
            self.save_flag = True
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    msv = SubVeh()
    msv.read_dat('.\\')
    vehicle_type_dict = msv.vehicle_type_dict  # 永远从窗口安装目录的dat中动态更新，不理睬项目工况文件
    del msv
    common_train_dict = {'CRH2-8节编组': [6, 5, 5, 6, 6, 5, 5, 6],
                         'CRH2-16节编组': [6, 5, 5, 6, 6, 5, 5, 6, 6, 5, 5, 6, 6, 5, 5, 6],
                         'CRH3-8节编组': [1, 2, 1, 2, 2, 1, 2, 1],
                         'CRH3-16节编组': [1, 2, 1, 2, 2, 1, 2, 1, 1, 2, 1, 2, 2, 1, 2, 1]}
    train_def_dia = GuideTrainDefDialog('新车列', ['新车列'], vehicle_type_dict, common_train_dict, [1, 2, 2, 1])
    train_def_dia.show()
    app.exec()
    print(train_def_dia.train_vehicles)
