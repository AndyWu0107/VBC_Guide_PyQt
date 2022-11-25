from PyQt5.QtWidgets import QDialog
from VBCDatGenerators import *
from UIWindFieldCtrlPtDef import *


class GuideWindFieldCtrlPtDefDialog(QDialog, Ui_windFieldCtrlPtDef):
    def __init__(self, ctrl_pt_list_already_defined):
        super(GuideWindFieldCtrlPtDefDialog, self).__init__()
        self.setupUi(self)

        self.save_flag = False
        self.old_ctrl_pt_num = len(ctrl_pt_list_already_defined)

        # 表格初始化
        def wfcp_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.windFieldCtrlPointTable, [j], [0])
            table_auto_numbering(self.windFieldCtrlPointTable)

        def wfcp_tb_row_rmv(i, j, k):
            table_auto_numbering(self.windFieldCtrlPointTable)

        self.windFieldCtrlPointTable.model().rowsInserted.connect(wfcp_tb_row_ist)
        self.windFieldCtrlPointTable.model().rowsRemoved.connect(wfcp_tb_row_rmv)
        self.windFieldCtrlPointAdd.clicked.connect(lambda: table_add_row(self.windFieldCtrlPointTable))
        self.windFieldCtrlPointDel.clicked.connect(lambda: table_delete_row(self.windFieldCtrlPointTable))
        self.windFieldCtrlPointOrderUp.clicked.connect(lambda: table_row_order_up(self, self.windFieldCtrlPointTable))
        self.windFieldCtrlPointOrderDown.clicked.connect(lambda: table_row_order_down(self, self.windFieldCtrlPointTable))

        if ctrl_pt_list_already_defined:
            self.write_list_to_table(ctrl_pt_list_already_defined)

        # 剪切板初始化
        self.clipboard = QApplication.clipboard()  # 初始化剪贴板

        # 按钮
        self.windFieldCtrlPointSave.clicked.connect(self.ctrl_pt_save)
        self.windFieldCtrlPointAbandon.clicked.connect(self.close)

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    def write_list_to_table(self, data_list):
        self.windFieldCtrlPointTable.setRowCount(0)
        for i_row in range(0, len(data_list)):
            self.windFieldCtrlPointTable.insertRow(self.windFieldCtrlPointTable.rowCount())
            self.windFieldCtrlPointTable.item(i_row, 1).setText(str(data_list[i_row]))

    def save_table_to_list(self):
        try:
            data_list = []
            for i_row in range(0, self.windFieldCtrlPointTable.rowCount()):
                if self.windFieldCtrlPointTable.item(i_row, 1).text():
                    data_list.append(float(self.windFieldCtrlPointTable.item(i_row, 1).text()))
            return data_list
        except:
            return -1

    def ctrl_pt_save(self):
        data_list = self.save_table_to_list()
        if data_list == -1:
            QMessageBox.warning(self, '警告', '存在非法输入，操作已取消。')
            return
        else:
            new_ctrl_pt_num = len(data_list)
            if new_ctrl_pt_num < 2:
                QMessageBox.warning(self, '警告', '请定义至少2个风场控制点。')
                return
            data_list_sorted = data_list.copy()
            data_list_sorted.sort()
            for i in range(len(data_list_sorted)-1):
                if data_list_sorted[i] == data_list_sorted[i+1]:
                    QMessageBox.warning(self, '警告', '存在重复的控制点坐标，请检查。')
                    return
            if data_list != data_list_sorted:
                reply = QMessageBox.warning(self, '警告', '控制点坐标未按升序排列，\n是否进行自动排序并保存？',
                                            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    data_list = data_list_sorted
                else:
                    return
            warn_flag = False
            if new_ctrl_pt_num > self.old_ctrl_pt_num != 0:
                warn_flag = True
                warn_text = '将保存的控制点数量(%d个)多于现有(%d个)，\n各车辆在新增的控制点处将被分配默认的风力系数。\n是否继续？' \
                            % (new_ctrl_pt_num, self.old_ctrl_pt_num)
            if new_ctrl_pt_num < self.old_ctrl_pt_num:
                warn_flag = True
                warn_text = '将保存的控制点数量(%d个)少于现有(%d个)，\n各车辆末尾%d个控制点处的风力系数将被删除。\n是否继续？' \
                            % (new_ctrl_pt_num, self.old_ctrl_pt_num, self.old_ctrl_pt_num-new_ctrl_pt_num)
            if warn_flag:
                reply = QMessageBox.warning(self, '警告', warn_text,
                                            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            else:
                reply = QMessageBox.Cancel
            if (not warn_flag) or (warn_flag and reply == QMessageBox.Yes):
                self.ctrl_pt_list = data_list
                self.save_flag = True
                self.close()
            else:
                return


if __name__ == '__main__':
    app = QApplication([])
    ctrl_pt_def_dia = GuideWindFieldCtrlPtDefDialog([5, 6, 8, 9, 10.5])
    ctrl_pt_def_dia.show()
    app.exec_()
    print(ctrl_pt_def_dia.ctrl_pt_list)
