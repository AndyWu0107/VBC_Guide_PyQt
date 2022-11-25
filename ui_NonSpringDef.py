from PyQt5.QtWidgets import QDialog
from VBCDatGenerators import *
from UINonSpringDef import Ui_NonSpringDef


class GuideNonSpringDefDialog(QDialog, Ui_NonSpringDef):
    def __init__(self, spring_name, spring_name_exist, non_spring_class_dict, paras_already_defined):
        super(GuideNonSpringDefDialog, self).__init__()
        # 初始化ui
        self.setupUi(self)

        self.non_spring_class_dict = non_spring_class_dict
        self.spring_name = spring_name
        self.spring_name_exist = spring_name_exist

        # 弹簧单元名初始化
        self.nonSpringNameEnter.setText(self.spring_name)
        self.window_title_update()

        # 弹簧单元名、窗口标题实时更新
        self.nonSpringNameEnter.textChanged.connect(self.spring_name_update)
        self.nonSpringNameEnter.textChanged.connect(self.window_title_update)

        # 剪贴板初始化
        self.clipboard = QApplication.clipboard()

        # 6个方向的参数用list存储，[[X参数类型, X参数1, ...], [Y参数类型, Y参数1, ...], [], ...]
        self.non_spring_paras = [[0], [0], [0], [0], [0], [0]]
        self.save_flag = False

        self.combo_obj_list = [self.NonClassSel_X, self.NonClassSel_Y, self.NonClassSel_Z,
                               self.NonClassSel_RX, self.NonClassSel_RY, self.NonClassSel_RZ]
        self.table_obj_list = [self.NonParaTable_X, self.NonParaTable_Y, self.NonParaTable_Z,
                               self.NonParaTable_RX, self.NonParaTable_RY, self.NonParaTable_RZ]

        combo_items = [self.non_spring_class_dict[i][0] for i in self.non_spring_class_dict.keys()]
        for i_combo in self.combo_obj_list:
            i_combo.clear()
            i_combo.addItems(combo_items)

        self.non_class_select(self.NonClassSel_X.currentIndex(), 1)
        self.NonClassSel_X.currentIndexChanged.connect(lambda i: self.non_class_select(i, 1))
        self.non_class_select(self.NonClassSel_Y.currentIndex(), 2)
        self.NonClassSel_Y.currentIndexChanged.connect(lambda i: self.non_class_select(i, 2))
        self.non_class_select(self.NonClassSel_Z.currentIndex(), 3)
        self.NonClassSel_Z.currentIndexChanged.connect(lambda i: self.non_class_select(i, 3))
        self.non_class_select(self.NonClassSel_RX.currentIndex(), 4)
        self.NonClassSel_RX.currentIndexChanged.connect(lambda i: self.non_class_select(i, 4))
        self.non_class_select(self.NonClassSel_RY.currentIndex(), 5)
        self.NonClassSel_RY.currentIndexChanged.connect(lambda i: self.non_class_select(i, 5))
        self.non_class_select(self.NonClassSel_RZ.currentIndex(), 6)
        self.NonClassSel_RZ.currentIndexChanged.connect(lambda i: self.non_class_select(i, 6))

        if paras_already_defined:
            self.non_paras_read(paras_already_defined)

        self.SaveNonPara.clicked.connect(self.non_paras_save)
        self.AbandonNonPara.clicked.connect(self.close)

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    def spring_name_update(self):
        self.spring_name = self.nonSpringNameEnter.text()

    def window_title_update(self):
        self.setWindowTitle('非线性弹簧及阻尼单元参数编辑 - ' + self.nonSpringNameEnter.text())

    def non_class_select(self, i, dof):
        combo_obj = self.combo_obj_list[dof - 1]
        table_obj = self.table_obj_list[dof - 1]

        if self.non_spring_class_dict[combo_obj.currentIndex()][1] is None:
            table_obj.setVisible(False)
            self.non_spring_paras[dof - 1] = []
        else:
            para_num = len(self.non_spring_class_dict[combo_obj.currentIndex()][2])
            table_obj.setColumnCount(0)  # 先给对应表格清零，不然靠前的参数会在左边的combo翻页过程中一直保留
            table_obj.setColumnCount(para_num)
            table_obj.setRowCount(1)
            table_obj.setHorizontalHeaderLabels(self.non_spring_class_dict[combo_obj.currentIndex()][2])
            table_set_align_center_readonly(table_obj, [0])
            table_obj.setVisible(True)
            self.non_spring_paras[dof - 1] = [self.non_spring_class_dict[combo_obj.currentIndex()][1]]
            # 非线性类别有改动时，立即将存储数据的list的对应行初始化，仅在保存时再逐一append具体参数
            # 这里存储的非线性类别是VBC代号

    def non_paras_save(self):
        if self.spring_name in self.spring_name_exist:
            QMessageBox.warning(self, "警告", "当前弹簧/阻尼单元名称已经存在，请重新命名。")
            return
        if not self.spring_name:
            QMessageBox.warning(self, "警告", "弹簧/阻尼单元名称不能为空。")
            return
        pure_linear_flag = True  # 用来判断这个弹簧是不是所有dof都没有采用非线性本构，是则报错
        for i_dof in range(1, 7):
            para_num_this_dof = len(self.non_spring_class_dict[self.combo_obj_list[i_dof - 1].currentIndex()][2])
            if para_num_this_dof:
                pure_linear_flag = False
            for i_para in range(1, para_num_this_dof + 1):
                try:
                    data2append = float(self.table_obj_list[i_dof - 1].item(0, i_para - 1).text())
                    self.non_spring_paras[i_dof - 1].append(data2append)
                except:
                    QMessageBox.warning(self, "警告", "输入有误。")
                    return
        if pure_linear_flag:
            QMessageBox.warning(self, "警告", "请至少为一个方向定义非线性本构。")
            return
        self.save_flag = True
        self.close()

    def non_paras_read(self, paras):
        spring_idx_vbc = [list(self.non_spring_class_dict.values())[i][1] for i in self.non_spring_class_dict.keys()]
        for i_dof in range(1, 7):
            if paras[i_dof-1]:
                current_combo_idx = spring_idx_vbc.index(paras[i_dof - 1][0])
                self.combo_obj_list[i_dof - 1].setCurrentIndex(current_combo_idx)
                para_num_this_dof = len(paras[i_dof - 1]) - 1
            else:
                current_combo_idx = spring_idx_vbc.index(None)
                self.combo_obj_list[i_dof - 1].setCurrentIndex(current_combo_idx)
                para_num_this_dof = 0
            for i_para in range(1, para_num_this_dof + 1):
                self.table_obj_list[i_dof - 1].item(0, i_para - 1).setText(str(paras[i_dof - 1][i_para]))


if __name__ == '__main__':
    app = QApplication([])
    non_spring_class_dict = {0: ['无', None, []],
                             1: ['线性弹簧阻尼', 1, ['线弹性刚度K/(N/m)', '粘滞阻尼系数C/(N·s/m)']],
                             2: ['双线性粘滞阻尼', 2, ['阻尼力F1/N', '卸荷速度V1/(m/s)', '阻尼力F2/N', '卸荷速度V2/(m/s)']],
                             3: ['扣件非线性弹性', 3, ['压刚度/(N/m)', '拉刚度(N/m)', '临界位移/m', '阻尼系数:刚度/s']],
                             4: ['线性弹簧+指数形式粘滞阻尼', 4, ['K/(N/m)', 'C', 'α']],
                             5: ['三次非线性', 5, ['非线性系数cs']],
                             6: ['库伦摩擦阻尼', 6, ['阻力F0/N']],
                             7: ['双线性弹簧', 100, ['初始刚度K0/(N/m)', '屈服后刚度KU/(N/m)', '屈服荷载FU/(N)']]}
    ns_dialog = GuideNonSpringDefDialog('testname', ['testname'], non_spring_class_dict,
                                        [[1, 5, 8], [], [], [3, 30.0, 0.0, 0.0, 0.0], [], [100, 1, 2, 3]])
    ns_dialog.show()
    app.exec_()
    print(ns_dialog.non_spring_paras)
