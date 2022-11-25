from PyQt5.QtWidgets import QDialog
from VBCDatGenerators import *
from UIWindForceDef import Ui_WindForceDef


class GuideWindForceDefDialog(QDialog, Ui_WindForceDef):
    def __init__(self, bri_or_veh, wind_force_name, wind_force_name_exist, forces_already_defined):
        super(GuideWindForceDefDialog, self).__init__()
        # 初始化ui
        self.setupUi(self)

        self.bri_or_veh = bri_or_veh
        self.wind_force_name = wind_force_name
        self.wind_force_name_exist = wind_force_name_exist

        # 风力名初始化
        self.windForceNameEnter.setText(self.wind_force_name)
        self.window_title_update()

        # 风力名、窗口标题实时更新
        self.windForceNameEnter.textChanged.connect(self.force_name_update)
        self.windForceNameEnter.textChanged.connect(self.window_title_update)

        # 表格初始化
        table_set_align_center_readonly(self.lengthParasTable, range(0, self.lengthParasTable.rowCount()))
        table_set_align_center_readonly(self.windForceCoeTable, range(0, self.windForceCoeTable.rowCount()))

        if forces_already_defined:
            self.wind_force_read(forces_already_defined)

        # 车桥模式选择
        if self.bri_or_veh == 'bri':
            self.angleLabel.setText('<html><head/><body><p><span style=" font-size:9pt;">（</span>α: <span style=" '
                                    'font-size:9pt;">风攻角, rad）</span></p></body></html>')
            self.lengthParasTable.item(0, 2).setText('1.0')
            self.lengthParasTable.item(0, 2).setFlags(Qt.ItemIsSelectable)
            self.bri_or_veh_id = 1
        else:
            self.angleLabel.setText('<html><head/><body><p><span style=" font-size:9pt;">（</span>α: <span style=" '
                                    'font-size:9pt;">风偏角, rad）</span></p></body></html>')
            self.bri_or_veh_id = 0

        # 剪贴板初始化
        self.clipboard = QApplication.clipboard()

        # 6个方向的分力系数用list存储，其中第一个元素为尺寸参数+车桥识别码：[[高度, 宽度, 长度, 车桥识别码], [D(, C, B, A)], [D(, C, B, A)], [], ...]
        self.wind_force_list = [[0.0, 0.0, 0.0], [0], [0], [0], [0], [0], [0]]
        self.save_flag = False

        self.SaveWindForce.clicked.connect(self.wind_force_save)
        self.AbandonWindForce.clicked.connect(self.close)

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    def force_name_update(self):
        self.wind_force_name = self.windForceNameEnter.text()

    def window_title_update(self):
        if self.bri_or_veh == 'bri':
            title_str = '结构风力系数编辑 - '
        else:
            title_str = '车辆风力系数编辑 - '
        self.setWindowTitle(title_str + self.windForceNameEnter.text())

    def wind_force_save(self):
        if self.windForceNameEnter.text() in self.wind_force_name_exist:
            QMessageBox.warning(self, "警告", "当前风力系数名称已经存在，请重新命名。")
            return
        if not self.windForceNameEnter.text():
            QMessageBox.warning(self, "警告", "风力系数名称不能为空。")
            return
        try:
            self.wind_force_list[0] = []
            for i_col in range(0, 3):
                if self.lengthParasTable.item(0, i_col).text():
                    if float(self.lengthParasTable.item(0, i_col).text()) == 0:
                        QMessageBox.warning(self, '警告', '尺寸参数均必填，且不得为零。')
                        return
                    self.wind_force_list[0].append(float(self.lengthParasTable.item(0, i_col).text()))
                else:
                    QMessageBox.warning(self, '警告', '尺寸参数均必填，且不得为零。')
                    return
            self.wind_force_list[0].append(self.bri_or_veh_id)
            for i_row in range(0, 6):
                self.wind_force_list[i_row+1] = []
                for j_col in range(0, self.windForceCoeTable.columnCount()):
                    if self.windForceCoeTable.item(i_row, j_col).text():
                        self.wind_force_list[i_row+1].append(float(self.windForceCoeTable.item(i_row, j_col).text()))
                    else:
                        self.wind_force_list[i_row+1].append(0.0)
        except:
            QMessageBox.warning(self, '警告', '存在非法输入。')
            return
        # 从高阶向低阶检查系数，为零的全部忽略
        for i_dof in range(0, 6):
            for i_coe in range(-1, -6, -1):  # 第一阶常数项不必检查，无论是否为零都肯定要保留
                if self.wind_force_list[i_dof + 1][-1] == 0:  # 注意！如果高阶的都被删了，那到了这一步需要检查的就是第-1个，而不是第i个！
                    del self.wind_force_list[i_dof + 1][-1]
                else:
                    break
        # 检查是否整张表都为零
        if self.wind_force_list[1:7] == [[0], [0], [0], [0], [0], [0]]:
            QMessageBox.warning(self, '警告', '所有分力系数均为零。')
            return
        self.save_flag = True
        self.close()

    def wind_force_read(self, force_list):
        for i_col in range(0, 3):
            self.lengthParasTable.item(0, i_col).setText(str(force_list[0][i_col]))
        for i_row in range(0, self.windForceCoeTable.rowCount()):
            for i_col in range(0, len(force_list[i_row+1])):
                self.windForceCoeTable.item(i_row, i_col).setText(str(force_list[i_row+1][i_col]))


if __name__ == '__main__':
    app = QApplication([])
    wf_dialog = GuideWindForceDefDialog('bri', 'testname', ['testname'], [[1, 2, 3.5], [6, 2], [0, 3], [0], [0], [0], [0]])
    wf_dialog.show()
    app.exec_()
    print(wf_dialog.wind_force_list)
