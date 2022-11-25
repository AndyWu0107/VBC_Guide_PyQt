from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from UITimeHistPlotDef import *


class GuideTimeHistPlotDef(QDialog, Ui_TimeHistPlotDef):
    def __init__(self, speed_num, bri_post_node_list, train_ow_list, train_dict, vehicle_type_dict,
                 paras_already_defined=[]):
        super(GuideTimeHistPlotDef, self).__init__()
        self.setupUi(self)

        self.train_ow_list = train_ow_list
        self.train_dict = train_dict
        self.vehicle_type_dict = vehicle_type_dict

        self.save_flag = False

        self.speedSel.clear()
        [self.speedSel.addItem('速度档位%d' % i) for i in range(1, speed_num + 1)]

        # bri_post_node_list = [[结点号1, 结点名称1], [结点号2, 结点名称2], ...]
        self.unit_sel1_item_list_bri = ['结点%d:%s' % (i[0], i[1]) for i in bri_post_node_list]

        # train_ow_list = [[车道1名称, 车道1上车列名称], [车道2名称, 车道2上车列名称], ...]
        self.unit_sel1_item_list_veh = ['%s - %s' % (i[0], i[1]) for i in train_ow_list]

        self.on_bri_or_veh_changed()
        self.briOrVehSel.currentIndexChanged.connect(self.on_bri_or_veh_changed)

        self.on_unit_changed()
        self.unitSel.currentIndexChanged.connect(self.on_unit_changed)

        self.on_sub_unit_changed()
        self.subUnitSel.currentIndexChanged.connect(self.on_sub_unit_changed)

        self.on_response_changed()
        self.responseSel.currentIndexChanged.connect(self.on_response_changed)

        self.on_if_filt_changed()
        self.ifFiltSel.currentIndexChanged.connect(self.on_if_filt_changed)

        self.timeHistPlotSave.clicked.connect(self.save_action)
        self.timeHistPlotAbandon.clicked.connect(self.close)

        self.on_self_def_legend_changed()
        self.selfDefLegend.stateChanged.connect(self.on_self_def_legend_changed)

        if paras_already_defined:
            self.speedSel.setCurrentIndex(paras_already_defined[0])
            self.briOrVehSel.setCurrentText(paras_already_defined[1])
            self.unitSel.setCurrentIndex(paras_already_defined[2])
            self.subUnitSel.setCurrentIndex(paras_already_defined[3])
            self.responseSel.setCurrentIndex(paras_already_defined[4])
            self.responsePositionSel.setCurrentIndex(paras_already_defined[5])
            self.lineStyleSel.setCurrentIndex(paras_already_defined[6])
            self.lineColorSel.setCurrentIndex(paras_already_defined[7])
            self.ifFiltSel.setCurrentIndex(paras_already_defined[8][0])
            self.minFreqEnter.setValue(paras_already_defined[8][1])
            self.maxFreqEnter.setValue(paras_already_defined[8][2])
            self.legendEnter.setText(paras_already_defined[9][1])
            self.selfDefLegend.setCheckState(paras_already_defined[9][0])

    def on_bri_or_veh_changed(self):
        if self.briOrVehSel.currentText() == '结构':
            self.unitSel.clear()
            self.unitSel.addItems(self.unit_sel1_item_list_bri)
            self.unitLabel.setText('关注结点：')
            self.subUnitLabel.setVisible(False)
            self.subUnitSel.setVisible(False)
            self.responsePositionLabel.setVisible(False)
            self.responsePositionSel.setVisible(False)
            self.response_item_list = ['dx', 'ax', 'dy', 'ay', 'dz', 'az',
                                       'rx', 'arx', 'ry', 'ary', 'rz', 'arz']
            self.responseSel.clear()
            self.responseSel.addItems(self.response_item_list)
        else:
            self.unitSel.clear()
            self.unitSel.addItems(self.unit_sel1_item_list_veh)
            self.unitLabel.setText('关注车列：')
            self.subUnitLabel.setVisible(True)
            self.subUnitSel.setVisible(True)
            self.responsePositionLabel.setVisible(True)
            self.responsePositionSel.setVisible(True)
            self.response_item_list = ['轮重减载率', '轮轨竖向力',
                                       '脱轨系数', '轮轨横向力',
                                       '轮下轨道位移-竖向', '轮下轨道位移-横向', '轮下轨道位移-摇头',
                                       '轮轨相对位移-竖向', '轮轨相对位移-横向', '轮轨相对位移-摇头',
                                       '车体加速度-横向', '车体加速度-竖向']
            self.responseSel.clear()
            self.responseSel.addItems(self.response_item_list)

    def on_unit_changed(self):
        if self.briOrVehSel.currentText() == '车辆':
            self.subUnitSel.clear()
            self.current_train_name = self.train_ow_list[self.unitSel.currentIndex()][1]
            sub_unit_item_list_temp = [self.vehicle_type_dict[i][0] for i in self.train_dict[self.current_train_name]]
            sub_unit_item_list = [('%d车:' % (i+1)) + sub_unit_item_list_temp[i]
                                  for i in range(0, len(sub_unit_item_list_temp))]
            self.subUnitSel.addItems(sub_unit_item_list)

    def on_sub_unit_changed(self):
        if self.briOrVehSel.currentText() == '车辆':
            current_veh = self.train_dict[self.current_train_name][self.subUnitSel.currentIndex()]
            self.wheelset_num = int(self.vehicle_type_dict[current_veh][1] / 2)
            self.on_response_changed()

    def on_response_changed(self):
        if self.responseSel.currentText() in ['轮重减载率', '轮轨竖向力', '脱轨系数', '轮轨横向力',
                                              '轮下轨道位移-竖向', '轮下轨道位移-横向', '轮下轨道位移-摇头',
                                              '轮轨相对位移-竖向', '轮轨相对位移-横向', '轮轨相对位移-摇头']:
            self.responsePositionLabel.setText('关注轮对：')
            self.response_position_item_list = ['第%d轮对' % i for i in range(1, self.wheelset_num+1)]
            self.responsePositionSel.clear()
            self.responsePositionSel.addItems(self.response_position_item_list)
        else:
            self.responsePositionLabel.setText('关注位置：')
            self.responsePositionSel.clear()
            self.responsePositionSel.addItems(['车体前部', '车体后部'])
        if self.responseSel.currentText() in ['轮重减载率', '轮轨竖向力', '脱轨系数', '轮轨横向力']:
            item_list = ['不处理', '带通滤波', '移动平均']
        else:
            item_list = ['不处理', '带通滤波']
        self.ifFiltSel.clear()
        self.ifFiltSel.addItems(item_list)


    def on_if_filt_changed(self):
        if self.ifFiltSel.currentIndex() == 1:  # 带通滤波
            self.maxFreqLabel.setText('Hz')
            self.maxFreqLabel.setVisible(True)
            self.maxFreqEnter.setVisible(True)
            self.minFreqLabel.setText('Hz ~')
            self.minFreqLabel.setVisible(True)
            self.minFreqEnter.setVisible(True)
        elif self.ifFiltSel.currentIndex() == 2:  # 移动平均
            self.maxFreqLabel.setVisible(False)
            self.maxFreqEnter.setVisible(False)
            self.minFreqLabel.setText('m')
            self.minFreqLabel.setVisible(True)
            self.minFreqEnter.setVisible(True)
        else:  # 不滤波
            self.maxFreqLabel.setVisible(False)
            self.maxFreqEnter.setVisible(False)
            self.minFreqLabel.setVisible(False)
            self.minFreqEnter.setVisible(False)

    def on_self_def_legend_changed(self):
        if self.selfDefLegend.checkState() == 2:
            self.legendEnter.setEnabled(True)
        else:
            self.legendEnter.setEnabled(False)

    def save_action(self):
        if (self.ifFiltSel.currentIndex() == 1) and (self.maxFreqEnter.value() == self.minFreqEnter.value()):
            QMessageBox.warning(self, '警告', '带通滤波输入范围无效。')
            return
        if (self.ifFiltSel.currentIndex() == 2) and (self.minFreqEnter.value() == 0):
            QMessageBox.warning(self, '警告', '移动平均窗口长度输入无效。')
            return
        self.speed_selected = self.speedSel.currentIndex()
        self.bri_or_veh = self.briOrVehSel.currentText()
        self.unit_selected = self.unitSel.currentIndex()
        self.sub_unit_selected = self.subUnitSel.currentIndex()
        self.response_selected = self.responseSel.currentIndex()
        self.response_position_selected = self.responsePositionSel.currentIndex()
        self.line_style_selected = self.lineStyleSel.currentIndex()
        self.line_color_selected = self.lineColorSel.currentIndex()
        if (self.ifFiltSel.currentIndex() == 1) and (self.maxFreqEnter.value() < self.minFreqEnter.value()):
            temp = self.maxFreqEnter.value()
            self.maxFreqEnter.setValue(self.minFreqEnter.value())
            self.minFreqEnter.setValue(temp)
        self.filt_selected = [self.ifFiltSel.currentIndex(), self.minFreqEnter.value(), self.maxFreqEnter.value()]
        self.self_def_legend = [self.selfDefLegend.checkState(), self.legendEnter.text()]
        self.save_flag = True
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    time_hist_plot_def_dia = GuideTimeHistPlotDef(6, [[11, 'a'], [12, 'b'], [13, 'c'], [14, 'd']],
                                                  [['1道', 'CRH3-8'], ['2道', 'CRH3-8']],
                                                  {'CRH3-8': [1, 2, 2, 1, 1, 2, 2, 1]},
                                                  {1: ['CRH3T', 8], 2: ['CRH3M', 8]})
    time_hist_plot_def_dia.show()
    app.exec_()
    print(time_hist_plot_def_dia.line_color_selected)
    print(time_hist_plot_def_dia.filt_selected)
