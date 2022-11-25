from PyQt5.QtWidgets import QDialog
from VBCDatGenerators import *
from UIWindNodeGroupDef import Ui_WindNodeGroupDef


class GuideWindNodeGroupDefDialog(QDialog, Ui_WindNodeGroupDef):
    def __init__(self, group_name, group_name_exist, group_already_defined):
        super(GuideWindNodeGroupDefDialog, self).__init__()
        # 初始化ui
        self.setupUi(self)

        self.group_name = group_name
        self.group_name_exist = group_name_exist
        self.group_already_defined = group_already_defined
        self.save_flag = False

        # 风荷载作用结点组名称初始化
        self.windNodeGroupNameEnter.setText(self.group_name)
        self.window_title_update()

        # 结点组名称、窗口标题实时更新
        self.windNodeGroupNameEnter.textChanged.connect(self.group_name_update)
        self.windNodeGroupNameEnter.textChanged.connect(self.window_title_update)

        # 将已有数据显示在窗口中
        if self.group_already_defined:
            id_str_list = [str(int(i)) for i in self.group_already_defined]
            id_wind_group_nodes_str = ', '.join(id_str_list)
            self.windNodeGroupEnter.setPlainText(id_wind_group_nodes_str)

        # 按钮响应
        self.SaveWindNodeGroup.clicked.connect(self.save_wind_node_group)
        self.AbandonWindNodeGroup.clicked.connect(self.close)

    def window_title_update(self):
        self.setWindowTitle('风荷载作用结点组编辑 - ' + self.windNodeGroupNameEnter.text())

    def group_name_update(self):
        self.group_name = self.windNodeGroupNameEnter.text()

    def save_wind_node_group(self):
        if self.group_name in self.group_name_exist:
            QMessageBox.warning(self, '警告', '当前结点组名称已经存在，请重新命名。')
            return
        if not self.group_name:
            QMessageBox.warning(self, '警告', '当前结点组名称为空，请重新命名。')
            return
        try:
            self.wind_node_list = get_num_list_from_text(self.windNodeGroupEnter.toPlainText())
            if not self.wind_node_list:
                QMessageBox.warning(self, '警告', '当前结点组为空。')
                return
        except:
            QMessageBox.warning(self, '警告', '存在非法输入')
            return
        if len(self.wind_node_list) != len(set(self.wind_node_list)):
            QMessageBox.warning(self, '警告', '存在重复节点。')
            return
        self.save_flag = True
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    wg_dialog = GuideWindNodeGroupDefDialog('新风荷载作用结点组', ['新风荷载作用结点组'], [1, 2, 3, 4])
    wg_dialog.show()
    app.exec_()
    print(wg_dialog.wind_node_list)
