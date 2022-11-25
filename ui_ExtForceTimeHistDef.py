from PyQt5.QtWidgets import QDialog
from UIExtForceTimeHistDef import *
from VBCDatGenerators import *


class GuideExtForceTimeHistDef(QDialog, Ui_ExtForceTimeHistDef):
    def __init__(self, node_id_text, dof_name, time_hist_already_defined=[]):
        super(GuideExtForceTimeHistDef, self).__init__()
        # 初始化ui
        self.setupUi(self)
        self.extForceTimeHistTable.setRowCount(0)

        self.clipboard = QApplication.clipboard()

        self.extForceTimeHistAdd.clicked.connect(lambda: table_add_row(self.extForceTimeHistTable, always_to_last=True))
        self.extForceTimeHistDel.clicked.connect(lambda: table_delete_row(self.extForceTimeHistTable))
        self.refreshPlot.clicked.connect(self.refresh_plot)
        self.extForceSave.clicked.connect(self.save_action)
        self.extForceAbandon.clicked.connect(self.close)
        self.save_flag = False

        def ext_force_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.extForceTimeHistTable, [j], [0])
            table_auto_numbering(self.extForceTimeHistTable)

        def ext_force_tb_row_rmv(i, j, k):
            table_auto_numbering(self.extForceTimeHistTable)

        self.extForceTimeHistTable.model().rowsInserted.connect(ext_force_tb_row_ist)
        self.extForceTimeHistTable.model().rowsRemoved.connect(ext_force_tb_row_rmv)

        self.node_id_text = node_id_text
        self.dof_name = dof_name
        self.setWindowTitle('外荷载时程定义 (结点: %s, 自由度: %s)' % (self.node_id_text, self.dof_name))
        self.time_hist_already_defined = time_hist_already_defined

        if self.time_hist_already_defined:
            self.write_table_from_list(self.time_hist_already_defined)

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard)

    def refresh_plot(self):
        plot_x = []
        plot_y = []
        try:
            for i_row in range(0, self.extForceTimeHistTable.rowCount()):
                i_time = float(self.extForceTimeHistTable.item(i_row, 1).text())
                i_force = float(self.extForceTimeHistTable.item(i_row, 2).text())
                plot_x.append(i_time)
                plot_y.append(i_force)
            self.extForcePlot.mpl.clear_static_plot()
            self.extForcePlot.mpl.start_static_plot(x=plot_x, y=plot_y, plot_title='外力时程',
                                                    x_label='时间(s)', y_label='力(N)', line_styles=['-'])
            self.extForcePlot.mpl.draw()
        except:
            QMessageBox.warning(self, '警告', '表中存在不完整或非法输入。')
            self.extForcePlot.mpl.clear_static_plot()
            self.extForcePlot.mpl.draw()
            return

    def write_table_from_list(self, data_list):
        self.extForceTimeHistTable.setRowCount(0)
        for i_pt in range(0, len(data_list)):
            self.extForceTimeHistTable.insertRow(self.extForceTimeHistTable.rowCount())
            i_time_str = str(data_list[i_pt][0])
            i_force_str = str(data_list[i_pt][1])
            self.extForceTimeHistTable.item(i_pt, 1).setText(i_time_str)
            self.extForceTimeHistTable.item(i_pt, 2).setText(i_force_str)
        self.refresh_plot()

    def save_table_to_list(self):
        data_list = []
        try:
            for i_row in range(0, self.extForceTimeHistTable.rowCount()):
                i_time = float(self.extForceTimeHistTable.item(i_row, 1).text())
                i_force = float(self.extForceTimeHistTable.item(i_row, 2).text())
                data_list.append([i_time, i_force])
            return data_list
        except:
            return -1

    def save_action(self):
        data_list = self.save_table_to_list()
        if data_list == -1:
            QMessageBox.warning(self, '警告', '表中存在不完整或非法输入。')
        else:
            self.external_force_time_history = data_list
            self.save_flag = True
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    data_list_already_defined = [[1, 1], [2, 4], [3, 5], [4, 2], [5, 0]]
    wg_dialog = GuideExtForceTimeHistDef(node_id=201, dof_name='X', time_hist_already_defined=data_list_already_defined)
    wg_dialog.show()
    app.exec_()
