import os
import subprocess
import sys
from time import sleep
from threading import Thread
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QAbstractItemView, QComboBox, QCheckBox  # 小心！！！ComBox采用的是字符串exec运行的方式，这里检测不到，但千万勿删！
from PyQt5 import QtGui, sip
from PyQt5.QtCore import QObject, pyqtSignal

from UIMainWindow import Ui_MainWindow
from VBCDatGenerators import *
from VBCPostFunctions import vbc_data_read, vbc_filter, moving_average, get_data_for_table, sperling
from ui_ExtForceTimeHistDef import GuideExtForceTimeHistDef
from ui_NonSpringDef import GuideNonSpringDefDialog
from ui_PostTableShow import GuidePostTableShowDialog
from ui_RailLocDef import GuideRailLocDefDialog
from ui_TimeHistPlot import GuideTimeHistPlot
from ui_TimeHistPlotDef import GuideTimeHistPlotDef
from ui_TrainDef import GuideTrainDefDialog
from ui_VehOperaDef import GuideVehOperaDialog
from ui_WindFieldCtrlPtDef import GuideWindFieldCtrlPtDefDialog
from ui_WindForceDef import GuideWindForceDefDialog
from ui_WindForceVehAssign import GuideWindForceVehAssign
from ui_WindNodeGroupDef import GuideWindNodeGroupDefDialog
from ui_about import GuideAboutDia

'''
                    ┏┛ ┻━━━━━┛ ┻┓
                    ┃　　　　　　 ┃
                    ┃　　　━　　　┃
                    ┃　┳┛　  ┗┳　┃
                    ┃　　　　　　 ┃
                    ┃　　　┻　　　┃
                    ┃　　　　　　 ┃
                    ┗━┓　　　┏━━━┛
                      ┃　　　┃   神兽保佑
                      ┃　　　┃   代码无BUG！
                      ┃　　　┗━━━━━━━━━┓
                      ┃　　　　　　　    ┣┓
                      ┃　　　　         ┏┛
                      ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
                        ┃ ┫ ┫   ┃ ┫ ┫
                        ┗━┻━┛   ┗━┻━┛
'''


# 自定义信号 http://www.python3.vip/tut/py/gui/qt_08/
class MySignals(QObject):
    new_console_text_ready = pyqtSignal(str)


global_ms = MySignals()


class GuideMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(GuideMainWindow, self).__init__()
        # 初始化ui
        self.setupUi(self)

        # treeItem的文本信息与stack页码的映射
        self.tree_index_dict = {'集中弹簧/阻尼结点号': 1,
                                '承轨结点号': 2,
                                '风荷载作用结点号': 3,
                                '其它外力作用结点号': 4,
                                '后处理结点号': 5,
                                '上述结点坐标': 6,
                                '2.结构模态信息定义': 7,
                                '车道线位': 8,
                                '轨道不平顺': 9,
                                '车列及运行组织': 10,
                                '一般参数': 11,
                                '结构': 12,
                                '车辆': 13,
                                '其它外力时程': 14,
                                '5.求解分析': 15,
                                '响应时程图': 16,
                                '响应汇总表': 17}
        # 非线性弹簧字典，格式：{下拉框位置: [本构名称, 本构在VBC中的代码，[本构参数名称]]}。下拉框位置须排序且连号！
        self.non_spring_class_dict = {0: ['无', None, []],
                                      1: ['线性弹簧阻尼', 1, ['线弹性刚度K(N/m)', '粘滞阻尼系数C(N·s/m)']],
                                      2: ['双线性粘滞阻尼', 2, ['阻尼力F1(N)', '卸荷速度V1(m/s)', '阻尼力F2(N)', '卸荷速度V2(m/s)']],
                                      3: ['扣件非线性弹性', 3, ['压刚度(N/m)', '拉刚度(N/m)', '临界位移(m)', '阻尼系数/刚度(s)']],
                                      4: ['线性弹簧+指数形式粘滞阻尼', 4, ['K(N/m)', 'C', 'α']],
                                      5: ['三次非线性', 5, ['非线性系数cs']],
                                      6: ['库伦摩擦阻尼', 6, ['阻力F0(N)']],
                                      7: ['双线性弹簧', 100, ['初始刚度K0(N/m)', '屈服后刚度KU(N/m)', '屈服荷载FU(N)']]}
        self.dof_dict = {1: 'X', 2: 'Y', 3: 'Z', 4: 'RX', 5: 'RY', 6: 'RZ'}
        # 不平顺谱代码字典，格式：{下拉框位置: [谱名称, 谱在VBC中的代码（除0）]}。其中无不平顺采用不平顺系数模拟，默认采用德国低扰*0
        self.irr_spectrum_dict = {0: ['无不平顺', 0, [1.0, 80.0]], 1: ['美国5级谱', 5, [1.0, 80.0]],
                                  2: ['美国6级谱', 6, [1.0, 80.0]], 3: ['德国高速谱-低干扰', 7, [1.0, 80.0]],
                                  4: ['德国高速谱-高干扰', 8, [1.0, 80.0]], 5: ['中国高速无砟谱', 11, [2.0, 200.0], [1.0, 80.0]],
                                  6: ['日本单轨谱', 701, [1.0, 80.0]],
                                  7: ['ISO3095短波谱', 501, [1.0, 80.0]], 8: ['ISO8608公路谱', 801, [1.0, 80.0]]}
        msv = SubVeh()
        msv.read_dat('.\\')
        self.vehicle_type_dict = msv.vehicle_type_dict  # 永远从窗口安装目录的dat中动态更新，不理睬项目工况文件{vbc代号: 名称}
        del msv
        self.common_train_dict = {'CRH2-8节编组': [6, 5, 5, 6, 6, 5, 5, 6],
                                  'CRH2-16节编组': [6, 5, 5, 6, 6, 5, 5, 6, 6, 5, 5, 6, 6, 5, 5, 6],
                                  'CRH3-8节编组': [1, 2, 1, 2, 2, 1, 2, 1],
                                  'CRH3-16节编组': [1, 2, 1, 2, 2, 1, 2, 1, 1, 2, 1, 2, 2, 1, 2, 1]}
        # 数值积分方法代码字典，格式：{下拉框位置: [方法名称, 方法在VBC中的代码]}。最好按下拉框位置的顺序排列。
        # self.integra_method_dict = {0: ['Wilson', 0], 1: ['Newton-Mark', 1], 2: ['新型显式积分', 2], 3: ['Runge-Kutta', 4]}
        self.integra_method_dict = {0: ['Runge-Kutta', 4], 1: ['新型显式积分', 2], 2: ['Wilson', 0], 3: ['Newton-Mark', 1]}
        # 信号机制
        # 页面切换

        self.save_path = ''
        self.browse_path = './'
        self.setWindowTitle('VBC Guide - 未保存的项目')

        # 保存戳记
        self.saved_flag = True
        self.nonSpringTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.nonSpringTable.model().rowsRemoved.connect(self.change_save_status)
        self.nonSpringNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.nonSpringNodeTable.model().rowsRemoved.connect(self.change_save_status)
        self.railNodeEnter.textChanged.connect(self.change_save_status)
        self.windNodeGroupTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.windNodeGroupTable.model().rowsRemoved.connect(self.change_save_status)
        self.postNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.postNodeTable.model().rowsRemoved.connect(self.change_save_status)
        self.externalForceNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.externalForceNodeTable.model().rowsRemoved.connect(self.change_save_status)
        self.coordSel.currentIndexChanged.connect(self.change_save_status)
        self.bridgeNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.bridgeNodeTable.model().rowsRemoved.connect(self.change_save_status)
        self.modeFileFormSel.currentIndexChanged.connect(self.change_save_status)
        self.modeFile1Path.textChanged.connect(self.change_save_status)
        self.includeModeNumFile1Sel.valueChanged.connect(self.change_save_status)
        self.ctrlMode1DampFile1Enter.valueChanged.connect(self.change_save_status)
        self.ctrlMode1FreqFile1Sel.valueChanged.connect(self.change_save_status)
        self.ctrlMode2DampFile1Enter.valueChanged.connect(self.change_save_status)
        self.ctrlMode2FreqFile1Sel.valueChanged.connect(self.change_save_status)
        self.modeFile2Path.textChanged.connect(self.change_save_status)
        self.includeModeNumFile2Sel.valueChanged.connect(self.change_save_status)
        self.ctrlMode1DampFile2Enter.valueChanged.connect(self.change_save_status)
        self.ctrlMode1FreqFile2Sel.valueChanged.connect(self.change_save_status)
        self.ctrlMode2DampFile2Enter.valueChanged.connect(self.change_save_status)
        self.ctrlMode2FreqFile2Sel.valueChanged.connect(self.change_save_status)
        self.modeFile3Path.textChanged.connect(self.change_save_status)
        self.includeModeNumFile3Sel.valueChanged.connect(self.change_save_status)
        self.ctrlMode1DampFile3Enter.valueChanged.connect(self.change_save_status)
        self.ctrlMode1FreqFile3Sel.valueChanged.connect(self.change_save_status)
        self.ctrlMode2DampFile3Enter.valueChanged.connect(self.change_save_status)
        self.ctrlMode2FreqFile3Sel.valueChanged.connect(self.change_save_status)
        self.railTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.railTable.model().rowsRemoved.connect(self.change_save_status)
        self.modelHaveRailSel.currentIndexChanged.connect(self.change_save_status)
        self.simRailElasticSel.currentIndexChanged.connect(self.change_save_status)
        self.considerVertCurveSel.stateChanged.connect(self.change_save_status)
        self.irrSourceSel.idToggled.connect(self.change_save_status)
        self.irrCoeVertical.valueChanged.connect(self.change_save_status)
        self.irrCoeHorizontal.valueChanged.connect(self.change_save_status)
        self.irrCoeDirectional.valueChanged.connect(self.change_save_status)
        self.irrPtIntervalEnter.valueChanged.connect(self.change_save_status)
        self.irrSampleTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.irrSampleTable.model().rowsRemoved.connect(self.change_save_status)
        self.irrSpectrumSel.currentIndexChanged.connect(self.change_save_status)
        self.irrRandomSeedSel.valueChanged.connect(self.change_save_status)
        self.irrWavelengthMinSel.valueChanged.connect(self.change_save_status)
        self.irrWavelengthMaxSel.valueChanged.connect(self.change_save_status)
        self.irrSmoothLengthSel.valueChanged.connect(self.change_save_status)
        self.trainTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.trainTable.model().rowsRemoved.connect(self.change_save_status)
        self.trainOnWayTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.trainOnWayTable.model().rowsRemoved.connect(self.change_save_status)
        # speedNum不需要绑定保存戳记，因为它已绑定表格的变化，后者会联动保存戳记
        self.airDensEnter.valueChanged.connect(self.change_save_status)
        self.windDirectionEnter.valueChanged.connect(self.change_save_status)
        self.aveWindSpeedEnter.valueChanged.connect(self.change_save_status)
        self.windFieldStartEnter.valueChanged.connect(self.change_save_status)
        self.windFieldEndEnter.valueChanged.connect(self.change_save_status)
        self.considerFluctuatingSel.stateChanged.connect(self.change_save_status)
        self.roughnessEnter.valueChanged.connect(self.change_save_status)
        self.referenceAltitudeEnter.valueChanged.connect(self.change_save_status)
        self.deckAltitudeEnter.valueChanged.connect(self.change_save_status)
        self.spacePtNumEnter.valueChanged.connect(self.change_save_status)
        self.maxFreqEnter.valueChanged.connect(self.change_save_status)
        self.randomSeedWindEnter.valueChanged.connect(self.change_save_status)
        self.lastTimeEnter.valueChanged.connect(self.change_save_status)
        self.smoothDistWindEnter.valueChanged.connect(self.change_save_status)
        self.smoothTimeWindEnter.valueChanged.connect(self.change_save_status)
        self.windForceBriTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.windForceBriTable.model().rowsRemoved.connect(self.change_save_status)
        self.windForceBriAssignTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.windForceBriAssignTable.model().rowsRemoved.connect(self.change_save_status)
        self.windFieldUniformSel.currentIndexChanged.connect(self.change_save_status)
        self.windForceVehTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.windForceTrainAssignTable.cellChanged.connect(lambda i, j: self.change_save_status())
        # self.ifPreprocess.currentIndexChanged.connect(self.change_save_status)
        self.integraStepEnter.valueChanged.connect(self.change_save_status)
        self.integraStepUnit.currentIndexChanged.connect(self.change_save_status)
        self.integraMethodSel.currentIndexChanged.connect(self.change_save_status)
        self.outputIntervalSel.valueChanged.connect(self.change_save_status)
        self.moduleList.currentItemChanged.connect(self.display_module)
        self.actionCheck.triggered.connect(self.check_action)
        self.actionSave.triggered.connect(self.save_action)
        self.actionSaveAs.triggered.connect(self.save_as_action)
        self.actionLoad.triggered.connect(self.load_action)
        self.actionAbout.triggered.connect(self.about_action)
        self.actionSamples.triggered.connect(self.samples_action)
        self.actionAnsys.triggered.connect(self.ansys_action)
        # 程序入口：先选FEM软件。此页顺序始终放在最后。
        self.substructure_name_file1 = ""  # 变量初始化，用于拼接部分Label
        self.fem_software_dict = {"Midas": 1, "Ansys": 0}  # 定义fem软件名和其代码的对应关系
        self.fem_software_name = ''  # 纯粹为了初始化，防止connect的slot中变量不存在，不影响后续业务逻辑
        self.model_file_ext = ''
        #####
        self.moduleStack.setCurrentIndex(0)  # 改回首页选择软件：此行改为0，再把下3行的注释状态反过来
        self.fem_software_select('Midas')
        # self.moduleList.setVisible(False)
        # self.menu.setEnabled(False)
        #####
        self.Midas.clicked.connect(lambda: self.fem_software_select('Midas'))
        # self.Ansys.clicked.connect(lambda: self.fem_software_select('Ansys'))
        self.Ansys.clicked.connect(lambda: QMessageBox.information(self, '暂不可用', '此功能正在建设中。'))

        # ANSYS快速填写向导
        self.ansysGuide.clicked.connect(self.ansys_guide)
        self.ansysGuide.setVisible(False)
        # 页面1：浏览结构命令文件，并将结果赋值给相关参数
        # 机理：通过FileDialog获得文件path，并将path赋值给lineText
        # 模型中是否包含轨道选项
        self.modelHaveRailSel.setCurrentText("否")
        self.model_have_rail_select(self.modelHaveRailSel.currentIndex())
        self.modelHaveRailSel.currentIndexChanged.connect(self.model_have_rail_select)
        # 后处理结点表格输入
        self.postNodeTable.setColumnWidth(0, 60)
        self.postNodeTable.setColumnWidth(1, 550)
        self.postNodeTable.setRowCount(0)
        self.postNodeTable.model().rowsInserted.connect(lambda i, j, k:
                                                        table_set_align_center_readonly(self.postNodeTable, [j]))
        self.postNodeAdd.clicked.connect(lambda: table_add_row(self.postNodeTable))
        self.postNodeDel.clicked.connect(lambda: table_delete_row(self.postNodeTable))
        self.postNodeUp.clicked.connect(lambda: table_row_order_up(self, self.postNodeTable))
        self.postNodeDown.clicked.connect(lambda: table_row_order_down(self, self.postNodeTable))
        # 风荷载作用结点组表格输入
        self.windNodeGroupTable.setColumnWidth(0, 140)
        self.windNodeGroupTable.setColumnWidth(1, 260)
        self.windNodeGroupTable.setColumnWidth(2, 260)
        self.windNodeGroupTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        def wng_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.windNodeGroupTable, [j], [0, 1, 2])
            table_auto_numbering(self.windNodeGroupTable)

        def wng_tb_row_rmv(i, j, k):
            table_auto_numbering(self.windNodeGroupTable)

        self.windNodeGroupTable.model().rowsInserted.connect(wng_tb_row_ist)
        self.windNodeGroupTable.model().rowsRemoved.connect(wng_tb_row_rmv)  # 弹簧结点表格中的combo更新任务未在这里绑定
        self.wind_node_group_dict = {}
        self.windNodeGroupAdd.clicked.connect(self.wind_node_group_add)
        self.windNodeGroupDel.clicked.connect(self.wind_node_group_del)
        self.windNodeGroupEdit.clicked.connect(self.wind_node_group_edit)
        self.windNodeGroupOrderUp.clicked.connect(self.wind_node_group_order_up)
        self.windNodeGroupOrderDown.clicked.connect(self.wind_node_group_order_down)

        # 其它外力时程节点表格输入
        self.externalForceNodeTable.setRowCount(0)

        def ext_node_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.externalForceNodeTable, [j], [0])
            table_auto_numbering(self.externalForceNodeTable)

        def ext_node_tb_row_rmv(i, j, k):
            table_auto_numbering(self.externalForceNodeTable)

        self.externalForceNodeTable.model().rowsInserted.connect(ext_node_tb_row_ist)
        self.externalForceNodeTable.model().rowsRemoved.connect(ext_node_tb_row_rmv)
        self.externalForceNodeAdd.clicked.connect(self.external_force_node_add)
        self.externalForceNodeDel.clicked.connect(self.external_force_node_del)
        self.externalForceNodeUp.clicked.connect(self.external_force_node_up)
        self.externalForceNodeDown.clicked.connect(self.external_force_node_down)
        # 受PYQT信号机制的制约，外力时程作用的结点combo自动更新功能，须通过多处围堵来实现，必要时还须断开cellChanged信号
        self.externalForceNodeTable.cellChanged.connect(self.on_ext_node_tb_cell_changed)
        self.external_force_node_list = []

        # 其它外力时程结点输入框
        # self.external_force_node_old_text = self.externalForceNodeEnter.toPlainText()
        # self.externalForceNodeEnter.modificationChanged.connect(self.external_force_node_enter)

        # 非线性弹簧表格输入
        self.nonSpringTable.setColumnWidth(0, 140)
        self.nonSpringTable.setColumnWidth(1, 260)
        self.nonSpringTable.setColumnWidth(2, 260)
        self.nonSpringTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        def nsp_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.nonSpringTable, [j], [0, 1, 2])
            table_auto_numbering(self.nonSpringTable)

        def nsp_tb_row_rmv(i, j, k):
            table_auto_numbering(self.nonSpringTable)

        self.nonSpringTable.model().rowsInserted.connect(nsp_tb_row_ist)
        self.nonSpringTable.model().rowsRemoved.connect(nsp_tb_row_rmv)  # 弹簧结点表格中的combo更新任务未在这里绑定
        self.non_spring_dict = {}
        self.nonSpringAdd.clicked.connect(self.non_spring_add)
        self.nonSpringDel.clicked.connect(self.non_spring_del)
        self.nonSpringEdit.clicked.connect(self.non_spring_edit)
        self.nonSpringOrderUp.clicked.connect(self.non_spring_order_up)
        self.nonSpringOrderDown.clicked.connect(self.non_spring_order_down)
        # 非线性弹簧连接结点表格输入
        self.nonSpringNodeTable.verticalHeader().setVisible(False)
        self.nonSpringNodeTable.setColumnWidth(0, 102)  # 142
        self.nonSpringNodeTable.setColumnWidth(1, 105)  # 135
        self.nonSpringNodeTable.setColumnWidth(2, 105)  # 135
        self.nonSpringNodeTable.setColumnWidth(3, 105)  # 135
        self.nonSpringNodeTable.setColumnWidth(4, 265)  # 135
        self.non_spring_node_table_combo_num = 0  # 全局变量：程序执行至今共给这个表格上了几个combo控件（仅用于exec语句中命名及识别）

        def nspn_tb_row_ist(i, j, k):
            # 表格combo增加动作未挂在Add按钮Slot下，而是挂在此处，为的是方便粘贴操作后也能生成按钮
            table_set_align_center_readonly(self.nonSpringNodeTable, [j], [0, 4])
            table_auto_numbering(self.nonSpringNodeTable)
            self.non_spring_node_combo_place(j)

        def nspn_tb_row_rmv(i, j, k):
            # 表格combo删除动作挂在del按钮slot下，方便及时清除内存垃圾（删除combo须在removeRow之前，而此函数所有动作均在其之后）
            table_auto_numbering(self.nonSpringNodeTable)

        self.nonSpringNodeTable.model().rowsInserted.connect(nspn_tb_row_ist)
        self.nonSpringNodeTable.model().rowsRemoved.connect(nspn_tb_row_rmv)
        self.nonSpringNodeAdd.clicked.connect(lambda: table_add_row(self.nonSpringNodeTable))
        self.nonSpringNodeDel.clicked.connect(self.non_spring_node_del)
        self.nonSpringNodeOrderUp.clicked.connect(lambda: table_row_order_up(self, self.nonSpringNodeTable))
        self.nonSpringNodeOrderDown.clicked.connect(lambda: table_row_order_down(self, self.nonSpringNodeTable))

        # 桥梁节点表格信号

        def bn_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.bridgeNodeTable, [j], [0])
            table_auto_numbering(self.bridgeNodeTable)

        def bn_tb_row_rmv(i, j, k):
            table_auto_numbering(self.bridgeNodeTable)

        self.bridgeNodeTable.setRowCount(0)
        self.bridgeNodeTable.model().rowsInserted.connect(bn_tb_row_ist)
        self.bridgeNodeTable.model().rowsRemoved.connect(bn_tb_row_rmv)
        self.briNodeAdd.clicked.connect(lambda: table_add_row(self.bridgeNodeTable, always_to_last=True))
        self.briNodeDel.clicked.connect(lambda: table_delete_row(self.bridgeNodeTable))

        # 结构坐标系选择
        self.on_coord_sel_changed()
        self.coordSel.currentIndexChanged.connect(self.on_coord_sel_changed)

        # 从FEM导入结构坐标信息按钮
        self.nodeLoadFromFEM.clicked.connect(self.load_node_from_fem)

        # 模态文件形式选项
        self.damp_widget_file2_display_flag_equal_sel = False  # 变量初始化，因为页面2最下方几个空间的显示受到2个因素影响，不初始化会导致函数中变量不存在
        self.damp_widget_file3_display_flag_equal_sel = False
        self.mode_file_form_select(self.modeFileFormSel.currentIndex())
        self.modeFileFormSel.currentIndexChanged.connect(self.mode_file_form_select)
        # 浏览结构模态文件，并将结果赋值给相关参数
        # 机理：通过FileDialog获得文件path，并将path赋值给lineText
        self.modeFile1Browse.clicked.connect(self.mode_file1_browse)
        self.modeFile2Browse.clicked.connect(self.mode_file2_browse)
        self.modeFile3Browse.clicked.connect(self.mode_file3_browse)
        # 各阶模态是否采用同一阻尼比选项
        self.equal_damp_file1_select()
        self.equalDampFile1Sel.stateChanged.connect(self.equal_damp_file1_select)
        self.equal_damp_file2_select()
        self.equalDampFile2Sel.stateChanged.connect(self.equal_damp_file2_select)
        self.equal_damp_file3_select()
        self.equalDampFile3Sel.stateChanged.connect(self.equal_damp_file3_select)
        # 行车轨道线位表格输入
        self.railTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.railTable.verticalHeader().setVisible(False)
        self.railTable.setColumnWidth(0, 80)
        self.railTable.setColumnWidth(1, 276)
        self.railTable.setColumnWidth(2, 316)

        def rl_tb_ist(i, j, k):
            table_set_align_center_readonly(self.railTable, [j], range(0, 3))
            table_auto_numbering(self.railTable)

        def rl_tb_rmv(i, j, k):
            table_auto_numbering(self.railTable)

        self.railTable.model().rowsInserted.connect(rl_tb_ist)
        self.railTable.model().rowsRemoved.connect(rl_tb_rmv)

        self.railEdit.clicked.connect(self.rail_edit)
        self.rail_dict = {}  # 轨道线位及控制点数据采用dict按序存储。键：名称；值：控制点list
        self.railAdd.clicked.connect(self.rail_add)
        self.railDel.clicked.connect(self.rail_del)
        self.railOrderUp.clicked.connect(self.rail_order_up)
        self.railOrderDown.clicked.connect(self.rail_order_down)
        # 轨道不平顺参数设置
        self.irrFromSpectrum.setChecked(True)
        self.irr_source_sel()
        self.irrSourceSel.idClicked.connect(self.irr_source_sel)
        self.irrSpectrumSel.clear()
        for i_item in iter(self.irr_spectrum_dict.values()):
            self.irrSpectrumSel.addItem(i_item[0])
        self.irr_spectrum_select(self.irrSpectrumSel.currentIndex())
        self.irrSpectrumSel.currentIndexChanged.connect(self.irr_spectrum_select)
        self.irrRandomSeedSel.setValue(1)
        self.irrSampleTable.setColumnWidth(0, 80)
        self.irrSampleTable.setColumnWidth(1, 80)
        self.irrSampleTable.setColumnWidth(2, 80)
        self.irrPtAdd.clicked.connect(lambda: table_add_row(self.irrSampleTable, always_to_last=True))
        self.irrPtDel.clicked.connect(lambda: table_delete_row(self.irrSampleTable))
        self.irrSampleTable.model().rowsInserted.connect(lambda i, j, k:
                                                         table_set_align_center_readonly(self.irrSampleTable, [j]))
        self.refreshPlot.clicked.connect(self.refresh_irr_sample_plot)

        # 车列定义表格输入
        self.trainTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trainTable.verticalHeader().setVisible(False)
        self.trainTable.setColumnWidth(0, 70)
        self.trainTable.setColumnWidth(1, 290)
        self.trainTable.setColumnWidth(2, 290)

        def tn_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.trainTable, [j], range(0, 3))
            table_auto_numbering(self.trainTable)

        def tn_tb_row_rmv(i, j, k):
            table_auto_numbering(self.trainTable)

        self.trainTable.model().rowsInserted.connect(tn_tb_row_ist)
        self.trainTable.model().rowsRemoved.connect(tn_tb_row_rmv)
        self.trainEdit.clicked.connect(self.train_edit)
        self.train_dict = {}  # 车列名称及编组数据采用dict存储。键：名称；值：编组车辆list
        self.trainAdd.clicked.connect(self.train_add)
        self.trainDel.clicked.connect(self.train_del)

        # 行车工况表格输入
        self.trainOnWayTable.setColumnWidth(0, 100)
        self.trainOnWayTable.setColumnWidth(1, 120)
        self.trainOnWayTable.setColumnWidth(2, 410)
        self.trainOnWayTable.model().rowsInserted.connect(lambda i, j, k:
                                                          table_set_align_center_readonly(self.trainOnWayTable, [j],
                                                                                          [1, 2]))
        self.train_on_way_table_train_combo_num = 0
        self.train_on_way_table_rail_combo_num = 0
        self.train_on_way_data = []  # 三维数组，每个车道的数据是二维：第0行是车道及车列号，之后是每个速度的数据（子窗口传回的格式）
        self.display_speed_summary()
        self.speedNum.valueChanged.connect(self.display_speed_summary)
        self.trainOnWayAdd.clicked.connect(self.train_on_way_add)
        self.trainOnWayDel.clicked.connect(self.train_on_way_del)
        self.trainOperateEdit.clicked.connect(self.train_operate_edit)

        # 风荷载一般参数输入
        self.consider_fluctuating_select()
        self.considerFluctuatingSel.stateChanged.connect(self.consider_fluctuating_select)

        # 桥梁风荷载输入
        self.windForceBriTable.setColumnWidth(0, 140)
        self.windForceBriTable.setColumnWidth(1, 260)
        self.windForceBriTable.setColumnWidth(2, 260)
        self.windForceBriTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        def wfb_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.windForceBriTable, [j], [0, 1, 2])
            table_auto_numbering(self.windForceBriTable)

        def wfb_tb_row_rmv(i, j, k):
            table_auto_numbering(self.windForceBriTable)

        self.windForceBriTable.model().rowsInserted.connect(wfb_tb_row_ist)
        self.windForceBriTable.model().rowsRemoved.connect(wfb_tb_row_rmv)  # 弹簧结点表格中的combo更新任务未在这里绑定
        self.wind_force_bri_dict = {}
        self.windForceBriAdd.clicked.connect(lambda: self.wind_force_add('bri'))
        self.windForceBriDel.clicked.connect(lambda: self.wind_force_del('bri'))
        self.windForceBriEdit.clicked.connect(lambda: self.wind_force_edit('bri'))
        self.windForceBriOrderUp.clicked.connect(lambda: self.wind_force_order_up('bri'))
        self.windForceBriOrderDown.clicked.connect(lambda: self.wind_force_order_down('bri'))

        # 桥梁风力系数分配表格输入
        self.windForceBriAssignTable.model().rowsInserted.connect(
            lambda i, j, k: table_set_align_center_readonly(self.windForceBriAssignTable, [j], [0]))
        # 没有给桥梁风力系数分配表格预留存储list，后面设计了此表与wind_node表格的顺序同步变化，因此在存储时临时抓取list即可

        # 车道沿线风场控制点设置
        # self.wind_field_uniform_select()
        self.windFieldUniformSel.currentIndexChanged.connect(self.wind_field_uniform_select)
        self.wind_field_ctrl_pt_list = []
        self.windFieldCtrlPtEdit.clicked.connect(self.wind_field_ctrl_pt_edit)

        # 车辆风荷载输入
        self.windForceVehTable.setColumnWidth(0, 140)
        self.windForceVehTable.setColumnWidth(1, 260)
        self.windForceVehTable.setColumnWidth(2, 260)
        self.windForceVehTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        def wfb_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.windForceVehTable, [j], [0, 1, 2])
            table_auto_numbering(self.windForceVehTable)

        def wfb_tb_row_rmv(i, j, k):
            table_auto_numbering(self.windForceVehTable)

        self.windForceVehTable.model().rowsInserted.connect(wfb_tb_row_ist)
        self.windForceVehTable.model().rowsRemoved.connect(wfb_tb_row_rmv)  # 弹簧结点表格中的combo更新任务未在这里绑定
        self.wind_force_veh_dict = {}
        self.windForceVehAdd.clicked.connect(lambda: self.wind_force_add('veh'))
        self.windForceVehDel.clicked.connect(lambda: self.wind_force_del('veh'))
        self.windForceVehEdit.clicked.connect(lambda: self.wind_force_edit('veh'))
        self.windForceVehOrderUp.clicked.connect(lambda: self.wind_force_order_up('veh'))
        self.windForceVehOrderDown.clicked.connect(lambda: self.wind_force_order_down('veh'))

        # 车辆风荷载分配表格输入
        self.windForceTrainAssignTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.windForceTrainAssignTable.model().rowsInserted.connect(lambda i, j, k:
                                                                    table_set_align_center_readonly(
                                                                        self.windForceTrainAssignTable, [j], [0, 1, 2]))
        self.wind_force_train_assign_list = []
        self.windForceTrainAssignEdit.clicked.connect(self.wind_force_train_assign_edit)
        self.windForceTrainAssignDel.clicked.connect(self.wind_force_train_assign_del)

        # 其它外力时程输入表格
        self.externalForceTable.setColumnWidth(0, 80)
        self.externalForceTable.setColumnWidth(1, 80)
        self.externalForceTable.setColumnWidth(2, 60)
        self.externalForceTable.setColumnWidth(3, 430)
        self.externalForceTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        def ext_force_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.externalForceTable, [j], range(0, 4))
            table_auto_numbering(self.externalForceTable)
            self.change_save_status()

        def ext_force_tb_row_rmv(i, j, k):
            table_auto_numbering(self.externalForceTable)
            self.change_save_status()

        self.externalForceTable.model().rowsInserted.connect(ext_force_tb_row_ist)
        self.externalForceTable.model().rowsRemoved.connect(ext_force_tb_row_rmv)
        self.external_force_list = []
        self.externalForceAdd.clicked.connect(self.external_force_add)
        self.externalForceDel.clicked.connect(self.external_force_del)
        self.externalForceEdit.clicked.connect(self.external_force_edit)

        # 求解参数输入
        self.integraMethodSel.clear()
        [self.integraMethodSel.addItem(self.integra_method_dict[i][0]) for i in self.integra_method_dict.keys()]
        self.integral_method_select(self.ifPreprocess.currentIndex())
        self.ifPreprocess.currentIndexChanged.connect(self.integral_method_select)
        self.integral_step_enter()
        self.integraStepEnter.valueChanged.connect(self.integral_step_enter)
        self.output_interval_select()
        self.outputIntervalSel.valueChanged.connect(self.output_interval_select)
        # 运行分析按钮及console显示
        self.running_flag = False
        self.runVbc.clicked.connect(self.run_analysis)
        global_ms.new_console_text_ready.connect(self.vbc_console_update)
        self.stopVbc.clicked.connect(self.stop_analysis)
        self.stopVbc.setEnabled(False)

        # 后处理绘图
        self.timeHistPlotTable.setColumnWidth(0, 40)
        self.timeHistPlotTable.setColumnWidth(1, 50)
        self.timeHistPlotTable.setColumnWidth(2, 210)
        self.timeHistPlotTable.setColumnWidth(3, 210)
        self.timeHistPlotTable.setColumnWidth(4, 80)
        self.timeHistPlotTable.setColumnWidth(5, 60)
        self.timeHistPlotTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        def th_tb_row_ist(i, j, k):
            table_set_align_center_readonly(self.timeHistPlotTable, [j], range(0, self.timeHistPlotTable.columnCount()))
            table_auto_numbering(self.timeHistPlotTable)

        def th_tb_row_rmv(i, j, k):
            table_auto_numbering(self.timeHistPlotTable)

        self.timeHistPlotTable.model().rowsInserted.connect(th_tb_row_ist)
        self.timeHistPlotTable.model().rowsRemoved.connect(th_tb_row_rmv)
        self.time_hist_plot_list = []
        self.timeHistPlotAdd.clicked.connect(self.time_hist_plot_add)
        self.timeHistPlotDel.clicked.connect(self.time_hist_plot_del)
        self.timeHistPlotUp.clicked.connect(self.time_hist_plot_up)
        self.timeHistPlotDown.clicked.connect(self.time_hist_plot_down)
        self.timeHistPlotEdit.clicked.connect(self.time_hist_plot_edit)
        self.timeHistPlotShow.clicked.connect(self.show_plot)

        # 后处理制表
        self.postTableFatherPathText.setReadOnly(True)
        self.on_post_table_range_changed()
        self.postTableRangeSel.currentIndexChanged.connect(self.on_post_table_range_changed)
        self.postTableFatherPathBrowse.clicked.connect(self.post_father_path_browse)
        self.addAttend.clicked.connect(self.attend_post_add)
        self.removeAttend.clicked.connect(self.attend_post_remove)
        self.addAllAttend.clicked.connect(self.attend_post_add_all)
        self.removeAllAttend.clicked.connect(self.attned_post_remove_all)
        self.attendUp.clicked.connect(self.attend_post_up)
        self.attendDown.clicked.connect(self.attend_post_down)
        self.addAttendPostNode.clicked.connect(self.attend_post_node_add)
        self.removeAttendPostNode.clicked.connect(self.attend_post_node_remove)
        self.addAllAttendPostNode.clicked.connect(self.attend_post_node_add_all)
        self.removeAllAttendPostNode.clicked.connect(self.attend_post_node_remove_all)
        self.attendPostNodeUp.clicked.connect(self.attend_post_node_up)
        self.attendPostNodeDown.clicked.connect(self.attend_post_node_down)
        self.on_veh_acc_proc_changed()
        self.vehAccDataProcSel.currentIndexChanged.connect(self.on_veh_acc_proc_changed)
        self.on_bri_acc_proc_changed()
        self.briAccDataProcSel.currentIndexChanged.connect(self.on_bri_acc_proc_changed)
        self.on_wheel_force_proc_changed()
        self.wheelForceDataProcSel.currentIndexChanged.connect(self.on_wheel_force_proc_changed)
        self.genPostTable.clicked.connect(self.gen_post_table)


        self.clipboard = QApplication.clipboard()  # 初始化剪贴板

        # 屏蔽粘贴的表格名单
        self.tables_ban_paste = [self.windNodeGroupTable, self.railTable, self.nonSpringTable, self.trainOnWayTable,
                                 self.trainTable, self.windForceBriTable, self.windForceBriAssignTable,
                                 self.windForceVehTable, self.windForceTrainAssignTable,
                                 self.externalForceTable, self.timeHistPlotTable]

        # FEM软件选择slot
        # 功能1：给求解参数赋值；功能2：改变界面中Label、选取文件类型等元素

    def keyPressEvent(self, event):
        monitor_key_press_event(self, event, self.clipboard, self.tables_ban_paste)

    def fem_software_select(self, fem_software_name):
        if fem_software_name == 'Ansys':
            self.ansysGuide.setVisible(True)
        else:
            self.ansysGuide.setVisible(False)
        self.moduleList.setVisible(True)
        # 点击了fem选择按钮之后，直接进入正题，跳转到第一个页面
        init_pg_item = self.moduleList.topLevelItem(0).child(0)
        self.moduleList.setCurrentItem(init_pg_item)
        self.menu.setEnabled(True)
        # 求解参数赋值
        self.fem_software_name = fem_software_name
        self.fem_software_opt = self.fem_software_dict[self.fem_software_name]
        # 改变与FEM软件相关的元素
        if self.fem_software_opt == 1:
            # 改变与FEM软件相关的Label
            self.model_file_ext = "(*.mct)"
            self.mode_file_ext = "(*.dat)"
            # 改变与FEM软件相关的文件类型
            """
            预留，暂未完成
            """
            # 改变模态文件生成向导的内容
            """
            预留，暂未完成
            """
            # 改变与FEM软件相关的其它控件的默认选项
            self.coordSel.setCurrentIndex(1)
        elif self.fem_software_opt == 0:
            self.model_file_ext = "(*.rst)"
            self.mode_file_ext = "(*.dat)"
            self.coordSel.setCurrentIndex(0)

    def ansys_guide(self):
        spring_reply = QMessageBox.information(self, '注意', '请确认您已经定义好所需的非线性弹簧/阻尼。', QMessageBox.Ok | QMessageBox.Cancel,
                                               QMessageBox.Cancel)
        if spring_reply == QMessageBox.Ok:
            pass

    # 侧边栏绑定页面
    def display_module(self, i, j):
        if self.moduleList.currentItem().text(0) in self.tree_index_dict:
            new_page_idx = self.tree_index_dict[self.moduleList.currentItem().text(0)]
            self.moduleStack.setCurrentIndex(new_page_idx)

    # 模型中包含轨道slot
    # 功能：设置“模拟轨道弹性”控件的可用性及默认值
    def model_have_rail_select(self, i):
        if self.modelHaveRailSel.itemText(i) == "否":
            self.simRailElasticSel.setVisible(True)
            self.simRailElasticLabel.setVisible(True)
            self.simRailElasticSel.setCurrentText("是")
        elif self.modelHaveRailSel.itemText(i) == "是":
            self.simRailElasticSel.setVisible(False)
            self.simRailElasticLabel.setVisible(False)
            self.simRailElasticSel.setCurrentText("否")

    # 模态文件形式选择slot
    # 功能1：给MSB参数赋值；功能2：控制页面控件的显示
    def mode_file_form_select(self, i):
        if self.modeFileFormSel.itemText(i) == "列于同一个文件":
            self.mode_file_num = 1
            self.damp_widget_file2_display_flag_file_form = False
            self.damp_widget_file3_display_flag_file_form = False
        elif self.modeFileFormSel.itemText(i) == "分列于两个文件":
            self.mode_file_num = 2
            self.damp_widget_file2_display_flag_file_form = True
            self.damp_widget_file3_display_flag_file_form = False
        elif self.modeFileFormSel.itemText(i) == "分列于三个文件":
            self.mode_file_num = 3
            self.damp_widget_file2_display_flag_file_form = True
            self.damp_widget_file3_display_flag_file_form = True

        self.modeFile2Group.setVisible(self.damp_widget_file2_display_flag_file_form)
        # self.modeFile2Label.setVisible(self.damp_widget_file2_display_flag_file_form),,
        # self.modeFile2Path.setVisible(self.damp_widget_file2_display_flag_file_form)
        # self.modeFile2Browse.setVisible(self.damp_widget_file2_display_flag_file_form)
        # self.includeModeNumFile2Label.setVisible(self.damp_widget_file2_display_flag_file_form)
        # self.includeModeNumFile2Sel.setVisible(self.damp_widget_file2_display_flag_file_form)
        # self.equalDampFile2Sel.setVisible(self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode1DampFile2Label.setVisible(True and self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode1DampFile2Enter.setVisible(True and self.damp_widget_file2_display_flag_file_form)
        # self.ctrlMode1FreqFile2Label.setVisible(self.damp_widget_file2_display_flag_equal_sel and
        #                                         self.damp_widget_file2_display_flag_file_form)
        # self.ctrlMode1FreqFile2Sel.setVisible(self.damp_widget_file2_display_flag_equal_sel and
        #                                       self.damp_widget_file2_display_flag_file_form)
        # self.ctrlMode2DampFile2Label.setVisible(self.damp_widget_file2_display_flag_equal_sel and
        #                                         self.damp_widget_file2_display_flag_file_form)
        # self.ctrlMode2DampFile2Enter.setVisible(self.damp_widget_file2_display_flag_equal_sel and
        #                                         self.damp_widget_file2_display_flag_file_form)
        # self.ctrlMode2FreqFile2Label.setVisible(self.damp_widget_file2_display_flag_equal_sel and
        #                                         self.damp_widget_file2_display_flag_file_form)
        # self.ctrlMode2FreqFile2Sel.setVisible(self.damp_widget_file2_display_flag_equal_sel and
        #                                       self.damp_widget_file2_display_flag_file_form)

        self.modeFile3Group.setVisible(self.damp_widget_file3_display_flag_file_form)
        # self.modeFile3Label.setVisible(self.damp_widget_file3_display_flag_file_form),,
        # self.modeFile3Path.setVisible(self.damp_widget_file3_display_flag_file_form)
        # self.modeFile3Browse.setVisible(self.damp_widget_file3_display_flag_file_form)
        # self.includeModeNumFile3Label.setVisible(self.damp_widget_file3_display_flag_file_form)
        # self.includeModeNumFile3Sel.setVisible(self.damp_widget_file3_display_flag_file_form)
        # self.equalDampFile3Sel.setVisible(self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode1DampFile3Label.setVisible(True and self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode1DampFile3Enter.setVisible(True and self.damp_widget_file3_display_flag_file_form)
        # self.ctrlMode1FreqFile3Label.setVisible(self.damp_widget_file3_display_flag_equal_sel and
        #                                         self.damp_widget_file3_display_flag_file_form)
        # self.ctrlMode1FreqFile3Sel.setVisible(self.damp_widget_file3_display_flag_equal_sel and
        #                                       self.damp_widget_file3_display_flag_file_form)
        # self.ctrlMode2DampFile3Label.setVisible(self.damp_widget_file3_display_flag_equal_sel and
        #                                         self.damp_widget_file3_display_flag_file_form)
        # self.ctrlMode2DampFile3Enter.setVisible(self.damp_widget_file3_display_flag_equal_sel and
        #                                         self.damp_widget_file3_display_flag_file_form)
        # self.ctrlMode2FreqFile3Label.setVisible(self.damp_widget_file3_display_flag_equal_sel and
        #                                         self.damp_widget_file3_display_flag_file_form)
        # self.ctrlMode2FreqFile3Sel.setVisible(self.damp_widget_file3_display_flag_equal_sel and
        #                                       self.damp_widget_file3_display_flag_file_form)

    # 各阶模态采用同一阻尼比slot
    # 第一个和第二个模态文件的选项分开，其中第一个文件兼作共用模态文件
    # 功能：设定尽可能简单的“控制模态阶数及阻尼比”的ui布局——勾选时隐藏不必要的控件，并给隐藏掉的控件自动赋值
    def equal_damp_file1_select(self):
        if self.equalDampFile1Sel.checkState() == 2:
            self.damp_widget_file1_display_flag_equal_sel = False
            self.ctrlMode1DampFile1Label.setText("模态阻尼比")
            self.ctrlMode2FreqFile1Sel.setValue(self.ctrlMode1FreqFile1Sel.value())
            self.ctrlMode2DampFile1Enter.setValue(self.ctrlMode1DampFile1Enter.value())
        elif self.equalDampFile1Sel.checkState() == 0:
            self.damp_widget_file1_display_flag_equal_sel = True
            self.ctrlMode1DampFile1Label.setText("控制阻尼比1")
        self.ctrlMode1DampFile1Label.setVisible(True)
        self.ctrlMode1DampFile1Enter.setVisible(True)
        self.ctrlMode1FreqFile1Label.setVisible(self.damp_widget_file1_display_flag_equal_sel)
        self.ctrlMode1FreqFile1Sel.setVisible(self.damp_widget_file1_display_flag_equal_sel)
        self.ctrlMode2DampFile1Label.setVisible(self.damp_widget_file1_display_flag_equal_sel)
        self.ctrlMode2DampFile1Enter.setVisible(self.damp_widget_file1_display_flag_equal_sel)
        self.ctrlMode2FreqFile1Label.setVisible(self.damp_widget_file1_display_flag_equal_sel)
        self.ctrlMode2FreqFile1Sel.setVisible(self.damp_widget_file1_display_flag_equal_sel)

    def equal_damp_file2_select(self):
        if self.equalDampFile2Sel.checkState() == 2:
            self.damp_widget_file2_display_flag_equal_sel = False
            self.ctrlMode1DampFile2Label.setText("模态阻尼比")
            self.ctrlMode2FreqFile2Sel.setValue(self.ctrlMode1FreqFile2Sel.value())
            self.ctrlMode2DampFile2Enter.setValue(self.ctrlMode1DampFile2Enter.value())
        elif self.equalDampFile2Sel.checkState() == 0:
            self.damp_widget_file2_display_flag_equal_sel = True
            self.ctrlMode1DampFile2Label.setText("控制阻尼比1")
        self.ctrlMode1DampFile2Label.setVisible(True and self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode1DampFile2Enter.setVisible(True and self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode1FreqFile2Label.setVisible(self.damp_widget_file2_display_flag_equal_sel and
                                                self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode1FreqFile2Sel.setVisible(self.damp_widget_file2_display_flag_equal_sel and
                                              self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode2DampFile2Label.setVisible(self.damp_widget_file2_display_flag_equal_sel and
                                                self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode2DampFile2Enter.setVisible(self.damp_widget_file2_display_flag_equal_sel and
                                                self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode2FreqFile2Label.setVisible(self.damp_widget_file2_display_flag_equal_sel and
                                                self.damp_widget_file2_display_flag_file_form)
        self.ctrlMode2FreqFile2Sel.setVisible(self.damp_widget_file2_display_flag_equal_sel and
                                              self.damp_widget_file2_display_flag_file_form)

    def equal_damp_file3_select(self):
        if self.equalDampFile3Sel.checkState() == 2:
            self.damp_widget_file3_display_flag_equal_sel = False
            self.ctrlMode1DampFile3Label.setText("模态阻尼比")
            self.ctrlMode2FreqFile3Sel.setValue(self.ctrlMode1FreqFile3Sel.value())
            self.ctrlMode2DampFile3Enter.setValue(self.ctrlMode1DampFile3Enter.value())
        elif self.equalDampFile3Sel.checkState() == 0:
            self.damp_widget_file3_display_flag_equal_sel = True
            self.ctrlMode1DampFile3Label.setText("控制阻尼比1")
        self.ctrlMode1DampFile3Label.setVisible(True and self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode1DampFile3Enter.setVisible(True and self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode1FreqFile3Label.setVisible(self.damp_widget_file3_display_flag_equal_sel and
                                                self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode1FreqFile3Sel.setVisible(self.damp_widget_file3_display_flag_equal_sel and
                                              self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode2DampFile3Label.setVisible(self.damp_widget_file3_display_flag_equal_sel and
                                                self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode2DampFile3Enter.setVisible(self.damp_widget_file3_display_flag_equal_sel and
                                                self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode2FreqFile3Label.setVisible(self.damp_widget_file3_display_flag_equal_sel and
                                                self.damp_widget_file3_display_flag_file_form)
        self.ctrlMode2FreqFile3Sel.setVisible(self.damp_widget_file3_display_flag_equal_sel and
                                              self.damp_widget_file3_display_flag_file_form)

    # 浏览模型文件
    def model_file_browse(self):
        target_file_type = self.fem_software_name + '模型命令文件 ' + self.model_file_ext
        dialog_title = "绑定" + self.fem_software_name + "模型命令文件"
        # if self.save_path:
        #     browse_path = self.save_path
        # else:
        #     browse_path = './'
        model_file_path = QFileDialog.getOpenFileName(self, dialog_title, self.browse_path, target_file_type)
        if model_file_path[0]:
            self.browse_path = get_dir_name(model_file_path[0])
        model_file_path = model_file_path[0].replace('/', '\\')
        return model_file_path

    # 根据结构坐标系的变化，变换风向示意图
    def on_coord_sel_changed(self):
        if self.coordSel.currentIndex() == 1:
            self.windDirectImage.setPixmap(QtGui.QPixmap("wind-z-up.png"))
        else:
            self.windDirectImage.setPixmap(QtGui.QPixmap("wind-y-up.png"))

    # 从FEM导入桥梁节点坐标信息
    def load_node_from_fem(self):
        # 1.求各个结点组的并集，需要try，因为此时未进行检查操作，不能保证所有表格数据均合法
        error_text = ''
        error_num = 0
        # 1.1 轨道节点
        try:
            id_rail_nodes = get_num_list_from_text(self.railNodeEnter.toPlainText())
        except:
            error_num += 1
            error_text = error_text + str(error_num) + '.轨道节点表格存在非法输入。\n'
        # 1.2 后处理节点
        try:
            id_post_nodes = []
            for i_row in range(self.postNodeTable.rowCount()):
                if self.postNodeTable.item(i_row, 0).text():
                    id2append = int(self.postNodeTable.item(i_row, 0).text())
                    if id2append in id_post_nodes:
                        raise ValueError
                    else:
                        id_post_nodes.append(id2append)
        except:
            error_num += 1
            error_text = error_text + str(error_num) + '.后处理节点表格存在非法输入或重复节点号。\n'
        # 1.3 非线性节点
        try:
            id_nonlinear_spring_nodes = []
            for i_row in range(0, self.nonSpringNodeTable.rowCount()):
                id_nonlinear_spring_nodes.append(int(self.nonSpringNodeTable.item(i_row, 1).text()))
                id_nonlinear_spring_nodes.append(int(self.nonSpringNodeTable.item(i_row, 2).text()))
        except:
            error_num += 1
            error_text = error_text + str(error_num) + '.非线性弹簧表格存在非法输入。\n'
        # 1.4 风荷载节点，这个表格特殊，只要有内容就不会出错，不用try
        id_wind_nodes = []
        for i_row in range(0, len(self.wind_node_group_dict)):
            id_wind_nodes += list(self.wind_node_group_dict.values())[i_row]
        # 1.5 其它外力时程荷载节点
        try:
            id_ext_force_nodes = []
            for i_row in range(self.externalForceNodeTable.rowCount()):
                if self.externalForceNodeTable.item(i_row, 1).text():
                    id2append = int(self.externalForceNodeTable.item(i_row, 1).text())
                    if id2append in id_ext_force_nodes:
                        raise ValueError
                    else:
                        id_ext_force_nodes.append(id2append)
        except:
            error_num += 1
            error_text = error_text + str(error_num) + '.其它外力节点表格存在非法输入或重复节点号。\n'

        # 1.6 检查
        if error_num:
            QMessageBox.warning(self, '警告', error_text + '请更正后重新导入。')
            return
        nodes_id_to_load = list(set(id_rail_nodes)
                                .union(set(id_post_nodes))
                                .union(set(id_nonlinear_spring_nodes))
                                .union(set(id_wind_nodes))
                                .union(set(id_ext_force_nodes)))

        # 2.从fem文件中读取坐标
        fem_file_path = self.model_file_browse()
        try:
            bridge_nodes_info, bridge_nodes_id = SubBri.get_node_info_from_midas(fem_file_path, nodes_id_to_load)
        except:
            if fem_file_path:  # 如果在弹窗中选择了文件，才有必要警告
                QMessageBox.warning(self, '警告', '存在越界结点号或选择了错误的文件。')
            return
        # 3.把读到的坐标写进表格
        self.bridgeNodeTable.setRowCount(0)
        for i_row in range(0, len(bridge_nodes_info)):
            self.bridgeNodeTable.insertRow(i_row)
            i_id = bridge_nodes_info[i_row][0]
            i_x = bridge_nodes_info[i_row][1]
            i_y = bridge_nodes_info[i_row][2]
            i_z = bridge_nodes_info[i_row][3]
            self.bridgeNodeTable.item(i_row, 1).setText(str(i_id))
            self.bridgeNodeTable.item(i_row, 2).setText(str(i_x))
            self.bridgeNodeTable.item(i_row, 3).setText(str(i_y))
            self.bridgeNodeTable.item(i_row, 4).setText(str(i_z))

    # 浏览模态文件
    def mode_file1_browse(self):
        target_file_type = '模型命令文件 ' + self.mode_file_ext
        dialog_title = "绑定结构模态文件1"
        # if self.save_path:
        #     browse_path = self.save_path
        # else:
        #     browse_path = './'
        self.mode_file1_path = QFileDialog.getOpenFileName(self, dialog_title, self.browse_path, target_file_type)
        if self.mode_file1_path[0]:
            self.browse_path = get_dir_name(self.mode_file1_path[0])
        self.mode_file1_path = self.mode_file1_path[0].replace('/', '\\')
        if self.mode_file1_path:
            self.modeFile1Path.setText(self.mode_file1_path)

    def mode_file2_browse(self):
        target_file_type = '模型命令文件 ' + self.mode_file_ext
        dialog_title = "绑定结构模态文件2"
        # if self.save_path:
        #     browse_path = self.save_path
        # else:
        #     browse_path = './'
        self.mode_file2_path = QFileDialog.getOpenFileName(self, dialog_title, self.browse_path, target_file_type)
        if self.mode_file2_path[0]:
            self.browse_path = get_dir_name(self.mode_file2_path[0])
        self.mode_file2_path = self.mode_file2_path[0].replace('/', '\\')
        if self.mode_file2_path:
            self.modeFile2Path.setText(self.mode_file2_path)

    def mode_file3_browse(self):
        target_file_type = '模型命令文件 ' + self.mode_file_ext
        dialog_title = "绑定结构模态文件3"
        # if self.save_path:
        #     browse_path = self.save_path
        # else:
        #     browse_path = './'
        self.mode_file3_path = QFileDialog.getOpenFileName(self, dialog_title, self.browse_path, target_file_type)
        if self.mode_file3_path[0]:
            self.browse_path = get_dir_name(self.mode_file3_path[0])
        self.mode_file3_path = self.mode_file3_path[0].replace('/', '\\')
        if self.mode_file3_path:
            self.modeFile3Path.setText(self.mode_file3_path)

    # 风荷载结点组表格的概况栏更新：读取指定行的名称，再根据dict中的信息更新概况
    def wind_node_table_summary_update(self, row_to_update=None):
        if not row_to_update:
            row_to_update = range(0, self.windNodeGroupTable.rowCount())
        if type(row_to_update) == int:
            row_to_update = [row_to_update]
        for i_row in row_to_update:
            i_name = self.windNodeGroupTable.item(i_row, 1).text()
            i_group_summary_str = '共%d个结点' % (len(self.wind_node_group_dict[i_name]))
            self.windNodeGroupTable.item(i_row, 2).setText(i_group_summary_str)

    # 增加风荷载作用结点组
    def wind_node_group_add(self):
        table_obj = self.windNodeGroupTable  # 保证编辑的是按钮所绑定的表格里的行
        wind_node_group_name_exist = self.wind_node_group_dict.keys()
        self.windNodeGroupDia = GuideWindNodeGroupDefDialog("风荷载作用结点组", wind_node_group_name_exist, [])
        self.windNodeGroupDia.exec_()
        if self.windNodeGroupDia.save_flag:
            table_obj.insertRow(table_obj.rowCount())
            current_group_name = self.windNodeGroupDia.group_name
            self.wind_node_group_dict[current_group_name] = self.windNodeGroupDia.wind_node_list
            table_obj.item(table_obj.rowCount() - 1, 1).setText(current_group_name)
            # 将子窗口保存的参数显示在表格的概览中
            self.wind_node_table_summary_update(table_obj.rowCount() - 1)
            self.wind_force_bri_assign_table_add_row()

    # 编辑风荷载作用结点组
    def wind_node_group_edit(self):
        table_obj = self.windNodeGroupTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中单元。")
            return
        current_group_name = table_obj.item(top, 1).text()
        group_already_defined = self.wind_node_group_dict[current_group_name]
        old_data = self.wind_node_group_dict.copy()
        wind_node_group_dict_except_current = self.wind_node_group_dict.copy()
        del wind_node_group_dict_except_current[current_group_name]
        group_name_exist = wind_node_group_dict_except_current.keys()
        self.windNodeGroupDia = GuideWindNodeGroupDefDialog(current_group_name, group_name_exist, group_already_defined)
        self.windNodeGroupDia.exec_()
        if self.windNodeGroupDia.save_flag:
            # 考虑到更名的可能性，操作流程统一为：删除原先的键值对，再将窗口最后返回的名称和控制点信息新建
            new_group_name = self.windNodeGroupDia.group_name
            self.wind_node_group_dict = wind_node_group_dict_except_current.copy()
            self.wind_node_group_dict[new_group_name] = self.windNodeGroupDia.wind_node_list
            if old_data != self.wind_node_group_dict:
                self.change_save_status()
            table_obj.item(top, 1).setText(new_group_name)
            self.wind_node_table_summary_update(top)
            self.wind_force_bri_assign_table_modify_row(top, new_group_name)

    # 删除风荷载作用结点组
    def wind_node_group_del(self):
        table_obj = self.windNodeGroupTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "此表不支持同时删除多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中弹簧单元。")
            return
        current_group_name = table_obj.item(top, 1).text()
        del self.wind_node_group_dict[current_group_name]
        table_obj.removeRow(top)
        self.wind_force_bri_assign_table_del_row(top)

    # 选中风荷载作用结点组上移(风荷载分配表格跟着上移)
    def wind_node_group_order_up(self):
        top, left, bottom, right = table_select_range(self.windNodeGroupTable)
        order_ok = table_row_order_up(self, self.windNodeGroupTable)
        if order_ok:
            table_row_order_up(self, self.windForceBriAssignTable, top)

    # 选中风荷载作用结点组下移(风荷载分配表格跟着下移)
    def wind_node_group_order_down(self):
        top, left, bottom, right = table_select_range(self.windNodeGroupTable)
        order_ok = table_row_order_down(self, self.windNodeGroupTable)
        if order_ok:
            table_row_order_down(self, self.windForceBriAssignTable, top)

    def on_ext_node_tb_cell_changed(self, row=None, col=None):
        self.external_force_node_list = []
        illegal_flag = False
        for i_row in range(0, self.externalForceNodeTable.rowCount()):
            if self.externalForceNodeTable.item(i_row, 1).text():
                try:
                    i_ext_node = int(self.externalForceNodeTable.item(i_row, 1).text())
                    self.external_force_node_list.append(i_ext_node)
                except:
                    illegal_flag = True
                    self.externalForceNodeTable.cellChanged.disconnect()
                    self.externalForceNodeTable.item(i_row, 1).setText('')
                    self.externalForceNodeTable.cellChanged.connect(self.on_ext_node_tb_cell_changed)
                    self.externalForceNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        if illegal_flag:
            QMessageBox.warning(self, '警告', '存在非法输入，相关单元格已被清空。')
        self.external_force_table_combo_update()

    def external_force_node_add(self):
        self.externalForceNodeTable.cellChanged.disconnect()
        table_add_row(self.externalForceNodeTable, always_to_last=True)
        self.externalForceNodeTable.cellChanged.connect(self.on_ext_node_tb_cell_changed)
        self.externalForceNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())

    def external_force_node_del(self):
        self.externalForceNodeTable.cellChanged.disconnect()
        table_delete_row(self.externalForceNodeTable)
        self.external_force_table_combo_update()
        self.externalForceNodeTable.cellChanged.connect(self.on_ext_node_tb_cell_changed)
        self.externalForceNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.on_ext_node_tb_cell_changed()

    def external_force_node_up(self):
        self.externalForceNodeTable.cellChanged.disconnect()
        table_row_order_up(self, self.externalForceNodeTable)
        self.externalForceNodeTable.cellChanged.connect(self.on_ext_node_tb_cell_changed)
        self.externalForceNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.on_ext_node_tb_cell_changed()

    def external_force_node_down(self):
        self.externalForceNodeTable.cellChanged.disconnect()
        table_row_order_down(self, self.externalForceNodeTable)
        self.externalForceNodeTable.cellChanged.connect(self.on_ext_node_tb_cell_changed)
        self.externalForceNodeTable.cellChanged.connect(lambda i, j: self.change_save_status())
        self.on_ext_node_tb_cell_changed()

    # def external_force_node_enter(self):
    #     try:
    #         self.external_force_node_list = get_num_list_from_text(self.externalForceNodeEnter.toPlainText())
    #         self.external_force_node_old_text = self.externalForceNodeEnter.toPlainText()
    #         self.externalForceNodeEnter.setStyleSheet("background-color: rgb(240, 254, 245)")
    #         """
    #         更新外荷载表格的节点combo列表
    #         """
    #         self.externalForceNodeEnter.modi(True)
    #     except:
    #         self.externalForceNodeEnter.setStyleSheet("background-color: rgb(254, 240, 245)")

    def non_spring_add(self):
        table_obj = self.nonSpringTable  # 保证编辑的是按钮所绑定的表格里的行
        spring_names_exist = self.non_spring_dict.keys()
        self.nonSpringDialog = GuideNonSpringDefDialog("新弹簧/阻尼单元", spring_names_exist, self.non_spring_class_dict,
                                                       [])
        self.nonSpringDialog.exec_()
        if self.nonSpringDialog.save_flag:
            table_obj.insertRow(table_obj.rowCount())
            current_spring_name = self.nonSpringDialog.spring_name
            self.non_spring_dict[current_spring_name] = self.nonSpringDialog.non_spring_paras
            table_obj.item(table_obj.rowCount() - 1, 1).setText(current_spring_name)
            # 将子窗口保存的参数显示在表格的概览中
            spring_idx_vbc = [list(self.non_spring_class_dict.values())[i][1] for i in
                              self.non_spring_class_dict.keys()]  # 当前自由度所采用的本构在VBC中的代号
            para_summary_str = ''
            for i_dof in range(1, 7):
                if self.non_spring_dict[current_spring_name][i_dof - 1]:
                    current_combo_idx = spring_idx_vbc.index(self.non_spring_dict[current_spring_name][i_dof - 1][0])
                    i_str1 = self.dof_dict[i_dof] + ':'
                    i_str2 = self.non_spring_class_dict[current_combo_idx][0] + ' '
                    i_para_summary_str = i_str1 + i_str2
                    para_summary_str = para_summary_str + i_para_summary_str
            table_obj.item(table_obj.rowCount() - 1, 2).setText(para_summary_str)
            self.non_spring_node_combo_update()

    # 编辑非线性弹簧单元参数
    def non_spring_edit(self):
        table_obj = self.nonSpringTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中单元。")
            return
        current_spring_name = self.nonSpringTable.item(top, 1).text()
        paras_already_defined = self.non_spring_dict[current_spring_name]
        old_data = self.non_spring_dict.copy()
        non_spring_dict_except_current = self.non_spring_dict.copy()
        del non_spring_dict_except_current[current_spring_name]
        spring_name_exist = non_spring_dict_except_current.keys()
        self.nonSpringDialog = GuideNonSpringDefDialog(current_spring_name, spring_name_exist,
                                                       self.non_spring_class_dict, paras_already_defined)
        self.nonSpringDialog.exec_()
        if self.nonSpringDialog.save_flag:
            # 考虑到更名的可能性，操作流程统一为：删除原先的键值对，再将窗口最后返回的名称和控制点信息新建
            new_spring_name = self.nonSpringDialog.spring_name
            self.non_spring_dict = non_spring_dict_except_current.copy()
            self.non_spring_dict[new_spring_name] = self.nonSpringDialog.non_spring_paras
            # 检查参数是否有变，如有，更新主窗口保存戳记
            if self.non_spring_dict != old_data:
                self.change_save_status()
            spring_idx_vbc = [list(self.non_spring_class_dict.values())[i][1] for i in
                              self.non_spring_class_dict.keys()]  # 当前自由度所采用的本构在VBC中的代号
            para_summary_str = ''
            for i_dof in range(1, 7):
                if self.non_spring_dict[new_spring_name][i_dof - 1]:
                    new_combo_idx = spring_idx_vbc.index(self.non_spring_dict[new_spring_name][i_dof - 1][0])
                    i_str1 = self.dof_dict[i_dof] + ':'
                    i_str2 = self.non_spring_class_dict[new_combo_idx][0] + ' '
                    i_para_summary_str = i_str1 + i_str2
                    para_summary_str = para_summary_str + i_para_summary_str
            self.nonSpringTable.item(top, 2).setText(para_summary_str)
            table_obj.item(top, 1).setText(new_spring_name)
            self.non_spring_node_combo_update()

    # 删除非线性弹簧单元
    def non_spring_del(self):
        table_obj = self.nonSpringTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "此表不支持同时删除多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中弹簧单元。")
            return
        current_spring_name = table_obj.item(top, 1).text()
        del self.non_spring_dict[current_spring_name]
        table_obj.removeRow(top)
        self.non_spring_node_combo_update()

    # 选中弹簧上移
    def non_spring_order_up(self):
        order_ok = table_row_order_up(self, self.nonSpringTable)
        if order_ok:
            self.non_spring_node_combo_update()

    # 选中弹簧下移
    def non_spring_order_down(self):
        order_ok = table_row_order_down(self, self.nonSpringTable)
        if order_ok:
            self.non_spring_node_combo_update()

    def non_spring_node_del(self):
        top, left, bottom, right = table_select_range(self.nonSpringNodeTable)
        if top != -1:
            for i_row in range(bottom, top - 1, -1):
                self.non_spring_node_combo_del(i_row)
                self.nonSpringNodeTable.removeRow(i_row)

    # 安置非线性弹簧连接结点表格中的控件（在每个新增行动作之后执行，每次仅动作单行）
    def non_spring_node_combo_place(self, row_to_place_new):
        # 第一部分：新增行中放新控件
        self.non_spring_node_table_combo_num += 1
        # self.simRailElasticSel.currentIndexChanged.connect(self.change_save_status)
        new_combo = QComboBox()
        new_combo.addItem('请选择')
        for i_row in range(0, self.nonSpringTable.rowCount()):
            new_combo.addItem(self.nonSpringTable.item(i_row, 1).text())
        new_combo.currentIndexChanged.connect(self.change_save_status)
        self.nonSpringNodeTable.setCellWidget(row_to_place_new, 4, new_combo)

    # 删除非线性弹簧连接结点表格中的控件（在每个删除动作之前执行）
    def non_spring_node_combo_del(self, row_to_del_old):
        # 第二部分：被删除的行中去除旧控件
        self.nonSpringNodeTable.removeCellWidget(row_to_del_old, 4)

    # 更新非线性弹簧连接结点表格中的的控件选项内容
    # 暂时用的是笨方法：上表一有风吹草动，下表立刻全部清空再全部重新加载，须重选
    def non_spring_node_combo_update(self):
        # 遍历各行，更新combo中的选项
        for i_row in range(0, self.nonSpringNodeTable.rowCount()):
            old_text = self.nonSpringNodeTable.cellWidget(i_row, 4).currentText()
            old_index = self.nonSpringNodeTable.cellWidget(i_row, 4).currentIndex()
            self.nonSpringNodeTable.cellWidget(i_row, 4).clear()
            self.nonSpringNodeTable.cellWidget(i_row, 4).addItem('请选择')
            for j_row in range(0, self.nonSpringTable.rowCount()):
                self.nonSpringNodeTable.cellWidget(i_row, 4).addItem(self.nonSpringTable.item(j_row, 1).text())
            new_index_of_old_text = self.nonSpringNodeTable.cellWidget(i_row, 4).findText(old_text)
            if new_index_of_old_text != -1:
                self.nonSpringNodeTable.cellWidget(i_row, 4).setCurrentIndex(new_index_of_old_text)
            else:
                self.nonSpringNodeTable.cellWidget(i_row, 4).setCurrentIndex(old_index)

    # 增加轨道
    def rail_add(self):
        table_obj = self.railTable  # 保证编辑的是按钮所绑定的表格里的行
        rail_names_exist = self.rail_dict.keys()
        self.railCtrlPtDialog = GuideRailLocDefDialog("新轨道", rail_names_exist, [])
        self.railCtrlPtDialog.exec_()
        if self.railCtrlPtDialog.save_flag:
            table_obj.insertRow(table_obj.rowCount())
            current_rail_name = self.railCtrlPtDialog.rail_name
            self.rail_dict[current_rail_name] = self.railCtrlPtDialog.rail_ctrl_pts
            table_obj.item(table_obj.rowCount() - 1, 1).setText(current_rail_name)
            ctrl_pt_num = len(self.rail_dict[current_rail_name]) - 1
            track_width = self.rail_dict[current_rail_name][0]
            x_start = self.rail_dict[current_rail_name][1][0]
            x_end = self.rail_dict[current_rail_name][ctrl_pt_num][0]
            rail_summary_info = "轨距%.3fm; %d控制点; X:%.3fm->%.3fm" % (track_width, ctrl_pt_num, x_start, x_end)
            table_obj.item(table_obj.rowCount() - 1, 2).setText(rail_summary_info)
            self.train_on_way_rail_combo_update()

    # 编辑轨道
    def rail_edit(self):
        table_obj = self.railTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "请先选中一条轨道。")
            return
        if not self.railTable.item(top, 1).text():
            QMessageBox.warning(self, "警告", "编辑前请先命名。")
            return
        current_rail_name = self.railTable.item(top, 1).text()
        rail_pts_already_defined = self.rail_dict[current_rail_name]
        old_data = self.rail_dict.copy()
        rail_dict_except_current = self.rail_dict.copy()
        del rail_dict_except_current[current_rail_name]
        rail_names_exist = rail_dict_except_current.keys()
        self.railCtrlPtDialog = GuideRailLocDefDialog(current_rail_name, rail_names_exist, rail_pts_already_defined)
        self.railCtrlPtDialog.exec_()
        # 考虑到更名的可能性，操作流程统一为：删除原先的键值对，再将窗口最后返回的名称和控制点信息新建
        if self.railCtrlPtDialog.save_flag:
            self.rail_dict = rail_dict_except_current.copy()
            new_rail_name = self.railCtrlPtDialog.rail_name
            self.rail_dict[new_rail_name] = self.railCtrlPtDialog.rail_ctrl_pts
            if old_data != self.rail_dict:
                self.change_save_status()
            table_obj.item(top, 1).setText(new_rail_name)
            ctrl_pt_num = len(self.rail_dict[new_rail_name]) - 1
            track_width = self.rail_dict[new_rail_name][0]
            x_start = self.rail_dict[new_rail_name][1][0]
            x_end = self.rail_dict[new_rail_name][ctrl_pt_num][0]
            rail_summary_info = "轨距%.3fm; %d控制点; X:%.3fm->%.3fm" % (track_width, ctrl_pt_num, x_start, x_end)
            table_obj.item(top, 2).setText(rail_summary_info)
            self.train_on_way_rail_combo_update()

    # 删除轨道
    def rail_del(self):
        table_obj = self.railTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时删除多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中单元。")
            return
        if not self.railTable.item(top, 1).text():
            QMessageBox.warning(self, "警告", "编辑前请先命名。")
            return
        current_rail_name = self.railTable.item(top, 1).text()
        del self.rail_dict[current_rail_name]
        table_obj.removeRow(top)
        self.train_on_way_rail_combo_update()

    # 选中轨道上移
    def rail_order_up(self):
        order_ok = table_row_order_up(self, self.railTable)
        if order_ok:
            self.train_on_way_rail_combo_update()

    # 选中轨道下移
    def rail_order_down(self):
        order_ok = table_row_order_down(self, self.railTable)
        if order_ok:
            self.train_on_way_rail_combo_update()

    # 计算所用轨道的总长度(控制点 + 预振 + 余振)
    def get_rail_total_length(self):
        total_length_ctrl_pt = 0
        for i_rail in self.rail_dict.keys():
            i_ctrl_pts_start = self.rail_dict[i_rail][1][5]
            i_ctrl_pts_end = self.rail_dict[i_rail][-1][5]
            i_length_ctrl_pt = abs(i_ctrl_pts_end - i_ctrl_pts_start)
            total_length_ctrl_pt += i_length_ctrl_pt
        total_length_extra = 0
        for j_rail in self.train_on_way_data:
            k_extra_lengths = []
            for k_speed in range(1, len(j_rail)):
                k_extra_length = j_rail[k_speed][1] + j_rail[k_speed][2]
                k_extra_lengths.append(k_extra_length)
            total_length_extra += max(k_extra_lengths)
        rail_total_length = total_length_ctrl_pt + total_length_extra
        n = 1
        while n:
            n += 1
            if 2 ** n > rail_total_length:
                break
        return 2 ** n

    # 轨道不平顺来源选项
    def irr_source_sel(self):
        if self.irrFromSpectrum.isChecked():
            flag = True
        else:
            flag = False
        self.irrSpectrumSel.setEnabled(flag)
        self.irrRandomSeedSel.setEnabled(flag)
        self.irrWavelengthMinSel.setEnabled(flag)
        self.irrWavelengthMaxSel.setEnabled(flag)
        self.irrSmoothLengthSel.setEnabled(flag)
        # self.irrCoeVertical.setEnabled(flag)
        # self.irrCoeDirectional.setEnabled(flag)
        # self.irrCoeHorizontal.setEnabled(flag)
        self.irrPtIntervalEnter.setEnabled(not flag)
        self.irrPtAdd.setEnabled(not flag)
        self.irrPtDel.setEnabled(not flag)
        self.irrPtDel.setEnabled(not flag)
        self.refreshPlot.setEnabled(not flag)
        self.irrSampleTable.setEnabled(not flag)

    # 轨道不平顺谱参数选项
    def irr_spectrum_select(self, i):
        if i:
            visible_flag = True
        else:
            visible_flag = False
        self.irrRandomSeedSel.setVisible(visible_flag)
        self.irrWavelengthMinSel.setVisible(visible_flag)
        self.irrWavelengthMaxSel.setVisible(visible_flag)
        self.irrSmoothLengthSel.setVisible(visible_flag)
        self.irrRandomSeedLabel.setVisible(visible_flag)
        self.irrWaveLengthLabel_1.setVisible(visible_flag)
        self.irrWaveLengthLabel_2.setVisible(visible_flag)
        self.irrWaveLengthLabel_3.setVisible(visible_flag)
        self.irrSmoothLengthLabel_1.setVisible(visible_flag)
        self.irrSmoothLengthLabel_2.setVisible(visible_flag)

        self.irrWavelengthMinSel.setValue(self.irr_spectrum_dict[i][2][0])
        self.irrWavelengthMaxSel.setValue(self.irr_spectrum_dict[i][2][1])


    # 更新轨道不平顺图像
    def refresh_irr_sample_plot(self):
        plot_x = []
        plot_y = [[], [], []]
        # try:
        for i_row in range(0, self.irrSampleTable.rowCount()):
            if (not self.irrSampleTable.item(i_row, 0).text()) and (not self.irrSampleTable.item(i_row, 1).text()) and (not self.irrSampleTable.item(i_row, 2).text()):
                continue
            i_vertical = float(self.irrSampleTable.item(i_row, 0).text()) * 1000.0
            i_directional = float(self.irrSampleTable.item(i_row, 1).text()) * 1000.0
            i_horizontal = float(self.irrSampleTable.item(i_row, 2).text()) * 1000.0
            plot_y[0].append(i_vertical)
            plot_y[1].append(i_directional)
            plot_y[2].append(i_horizontal)
        plot_x = [[i*self.irrPtIntervalEnter.value() for i in range(len(plot_y[0]))]] * 3
        self.irrSamplePlot.mpl.clear_static_plot()
        self.irrSamplePlot.mpl.start_static_plot(x=plot_x, y=plot_y, plot_title='不平顺样本',
                                                 x_label='距离(m)', y_label='不平顺(mm)',
                                                 line_styles=['-', '-', '-'], colors=['k', 'r', 'b'],
                                                 legends=['高低', '轨向', '水平'])
        self.irrSamplePlot.mpl.draw()
        # except:
        #     QMessageBox.warning(self, '警告', '表中存在不完整或非法输入。')
        #     self.irrSamplePlot.mpl.clear_static_plot()
        #     self.irrSamplePlot.mpl.draw()
        #     return

    # 增加车列
    def train_add(self):
        table_obj = self.trainTable  # 保证编辑的是按钮所绑定的表格里的行
        train_names_exist = self.train_dict.keys()
        self.trainDefDialog = GuideTrainDefDialog("新车列", train_names_exist, self.vehicle_type_dict,
                                                  self.common_train_dict, [])
        self.trainDefDialog.exec_()
        if self.trainDefDialog.save_flag:
            table_obj.insertRow(table_obj.rowCount())
            current_train_name = self.trainDefDialog.train_name
            self.train_dict[current_train_name] = self.trainDefDialog.train_vehicles
            table_obj.item(table_obj.rowCount() - 1, 1).setText(current_train_name)
            vehicle_num = len(self.train_dict[current_train_name])
            train_summary_info = "共%d辆车" % vehicle_num
            table_obj.item(table_obj.rowCount() - 1, 2).setText(train_summary_info)
            self.train_on_way_train_combo_update()

    # 编辑车列
    def train_edit(self):
        table_obj = self.trainTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中单元。")
            return
        if not table_obj.item(top, 1).text():
            QMessageBox.warning(self, "警告", "编辑前请先命名。")
            return
        current_train_name = table_obj.item(top, 1).text()
        train_vehicles_already_defined = self.train_dict[current_train_name]
        old_data = self.train_dict.copy()
        train_dict_except_current = self.train_dict.copy()
        del train_dict_except_current[current_train_name]
        train_names_exist = train_dict_except_current.keys()
        self.trainDefDialog = GuideTrainDefDialog(current_train_name, train_names_exist, self.vehicle_type_dict,
                                                  self.common_train_dict, train_vehicles_already_defined)
        self.trainDefDialog.exec_()
        # 考虑到更名的可能性，操作流程统一为：删除原先的键值对，再将窗口最后返回的名称和控制点信息新建
        if self.trainDefDialog.save_flag:
            self.train_dict = train_dict_except_current.copy()
            new_train_name = self.trainDefDialog.train_name
            self.train_dict[new_train_name] = self.trainDefDialog.train_vehicles
            if old_data != self.train_dict:
                self.change_save_status()
            table_obj.item(top, 1).setText(new_train_name)
            vehicle_num = len(self.train_dict[new_train_name])
            train_summary_info = "共%d辆车" % vehicle_num
            table_obj.item(table_obj.rowCount() - 1, 2).setText(train_summary_info)
            self.train_on_way_train_combo_update()

    # 删除车列
    def train_del(self):
        table_obj = self.trainTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时删除多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中单元。")
            return
        if not table_obj.item(top, 1).text():
            QMessageBox.warning(self, "警告", "编辑前请先命名。")
            return
        current_train_name = self.trainTable.item(top, 1).text()
        del self.train_dict[current_train_name]
        table_obj.removeRow(top)
        self.train_on_way_train_combo_update()

    # 检查行车速度工况数是否存在矛盾
    def display_speed_summary(self):
        if len(self.train_on_way_data):
            for i_rail in range(0, len(self.train_on_way_data)):
                speeds = []
                for i_speed in range(1, len(self.train_on_way_data[i_rail])):
                    speeds.append(str(self.train_on_way_data[i_rail][i_speed][0]) + 'km/h')
                # 显示运行工况概览
                summary_str = ''
                if len(speeds):
                    summary_str = ','.join(speeds)
                speed_num_this_rail = len(self.train_on_way_data[i_rail]) - 1
                if self.speedNum.value() != speed_num_this_rail:
                    summary_str = summary_str + '[速度档位数不匹配]'
                    self.trainOnWayTable.item(i_rail, 2).setForeground(QBrush(QColor(255, 0, 0)))
                else:
                    self.trainOnWayTable.item(i_rail, 2).setForeground(QBrush(QColor(0, 0, 0)))
                self.trainOnWayTable.item(i_rail, 2).setText(summary_str)

    # 增加上道车
    def train_on_way_add(self):
        table_obj = self.trainOnWayTable
        row_to_insert = table_obj.rowCount()
        table_obj.insertRow(row_to_insert)
        self.train_on_way_combo_place(row_to_insert)
        table_auto_numbering(table_obj)
        self.train_on_way_data.insert(row_to_insert, [[0, 0]])  # 车道和上道车列默认都是未选中的状态
        table_obj.item(row_to_insert, 2).setText('[尚未定义运行工况]')
        table_obj.item(row_to_insert, 2).setForeground(QBrush(QColor(255, 0, 0)))
        self.wind_force_train_assign_table_add_row()

    # 删除上道车
    def train_on_way_del(self):
        table_obj = self.trainOnWayTable  # 保证删除的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != -1:
            for i_row in range(bottom, top - 1, -1):
                self.train_on_way_combo_del(i_row)
                table_obj.removeRow(i_row)
                del self.train_on_way_data[i_row]
                self.windForceTrainAssignTable.removeRow(i_row)
                del self.wind_force_train_assign_list[i_row]

    # 编辑上道车运行工况
    def train_operate_edit(self):
        table_obj = self.trainOnWayTable  # 保证编辑的是按钮所绑定的表格里的行
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "未选中单元。")
            return
        current_rail_name = table_obj.cellWidget(top, 0).currentText()
        if len(self.train_on_way_data[top]) > 1:
            veh_opera_already_defined = self.train_on_way_data[top][1:len(self.train_on_way_data[top])]
        else:
            veh_opera_already_defined = []
        old_data = self.train_on_way_data.copy()
        self.train_on_way_dialog = GuideVehOperaDialog(current_rail_name, self.speedNum.value(),
                                                       veh_opera_already_defined)
        self.train_on_way_dialog.exec()
        if self.train_on_way_dialog.save_flag:
            speeds = []
            if len(self.train_on_way_data[top]) > 1:
                del self.train_on_way_data[top][1:len(self.train_on_way_data[top])]
            for i_speed in range(0, len(self.train_on_way_dialog.veh_opera_data)):
                self.train_on_way_data[top].append(self.train_on_way_dialog.veh_opera_data[i_speed])
                speeds.append(str(self.train_on_way_dialog.veh_opera_data[i_speed][0]) + 'km/h')
            # 显示运行工况概览
            self.display_speed_summary()
            # 保存戳记
            if old_data != self.train_on_way_data:
                self.change_save_status()

    # 安置行车工况表格中的控件（在每个新增行动作之后执行）
    def train_on_way_combo_place(self, row_to_place_new):
        # 第一部分：轨道单元格控件
        self.train_on_way_table_rail_combo_num += 1
        new_combo = QComboBox()
        new_combo.addItem('请选择')
        for i_row in range(0, self.railTable.rowCount()):
            new_combo.addItem(self.railTable.item(i_row, 1).text())
        new_combo.currentIndexChanged.connect(self.on_train_on_way_combo_idx_changed)
        self.trainOnWayTable.setCellWidget(row_to_place_new, 0, new_combo)
        # 第二部分：上道车列单元格控件
        self.train_on_way_table_train_combo_num += 1
        new_combo = QComboBox()
        new_combo.addItem('请选择')
        for i_row in range(0, self.trainTable.rowCount()):
            new_combo.addItem(self.trainTable.item(i_row, 1).text())
        new_combo.currentIndexChanged.connect(self.on_train_on_way_combo_idx_changed)
        self.trainOnWayTable.setCellWidget(row_to_place_new, 1, new_combo)

    def on_train_on_way_combo_idx_changed(self):
        # 1.检查新旧上道车的车辆数是否一致，进行相应处理，防止风荷载乱套(trainTable编辑后的检查，放在子窗口中进行)
        """
        2.23遗留问题：此slot无法定位到具体的表格行列，不知道是具体哪个combo发生了变化，可能需要用笨方法检查全表
        且currentItem change后不知道旧的item是哪个（可以从已分配的风荷载表格中得到，但这样写代码有点脏，暂不考虑此法；可考虑在trainOnWay表格中widget下方的item中放不可见的text）
        """
        i_row_to_del_train_wind = None
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            i_old_train_name = self.trainOnWayTable.item(i_row, 1).text()
            try:
                i_old_veh_num = len(self.train_dict[i_old_train_name])
            except:
                i_old_veh_num = 0
            i_new_train_name = self.trainOnWayTable.cellWidget(i_row, 1).currentText()
            if i_new_train_name == '请选择':
                i_new_veh_num = 0
            else:
                i_new_veh_num = len(self.train_dict[i_new_train_name])
            try:  # 读取既有dat文件时也会用到这个slot，由于读取逻辑和窗口直接写并不一样，此处会出越界错，因此这里try一下
                if i_old_veh_num != i_new_veh_num and self.wind_force_train_assign_list[i_row]:
                    reply = QMessageBox.warning(self, '注意', '新选择的车列与现有的车辆数不同，\n现有车列已定义的风荷载将被清空。\n是否继续？',
                                                QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                    if reply == QMessageBox.Cancel:
                        self.trainOnWayTable.cellWidget(i_row, 1).currentIndexChanged.disconnect()
                        self.trainOnWayTable.cellWidget(i_row, 1).setCurrentText(i_old_train_name)
                        self.trainOnWayTable.cellWidget(i_row, 1).currentIndexChanged.connect(
                            self.on_train_on_way_combo_idx_changed)
                        return
                    else:
                        i_row_to_del_train_wind = i_row
                        break
            except:
                pass
        # 2.进行后续操作
        self.change_save_status()
        self.wind_force_train_assign_table_row_update(i_row_to_del_train_wind)
        # 3.一个trick：在每个车列combo下放置item，用于存储combo的text
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            item_text = self.trainOnWayTable.cellWidget(i_row, 1).currentText()
            self.trainOnWayTable.item(i_row, 1).setText(item_text)

    # 删除行车工况表格中的控件（在每个删除动作之前执行）
    def train_on_way_combo_del(self, row_to_del_old):
        # self.trainOnWayTable.removeCellWidget(row_to_del_old, 0)
        # self.trainOnWayTable.removeCellWidget(row_to_del_old, 1)
        # self.trainOnWayTable.cellWidget(row_to_del_old, 0).disconnect()
        # self.trainOnWayTable.cellWidget(row_to_del_old, 1).disconnect()
        sip.delete(self.trainOnWayTable.cellWidget(row_to_del_old, 0))
        sip.delete(self.trainOnWayTable.cellWidget(row_to_del_old, 1))

    # 更新行车工况表格中的的轨道单元格控件选项内容
    # 暂时用的是笨方法：上表一有风吹草动，下表立刻全部清空再全部重新加载，须重选
    def train_on_way_rail_combo_update(self):
        # 遍历各行，更新combo中的选项
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            old_text = self.trainOnWayTable.cellWidget(i_row, 0).currentText()
            old_idx_in_combo = self.trainOnWayTable.cellWidget(i_row, 0).findText(old_text)
            self.trainOnWayTable.cellWidget(i_row, 0).clear()
            self.trainOnWayTable.cellWidget(i_row, 0).addItem('请选择')
            for j_row in range(0, self.railTable.rowCount()):
                self.trainOnWayTable.cellWidget(i_row, 0).addItem(self.railTable.item(j_row, 1).text())
            new_index_of_old_text = self.trainOnWayTable.cellWidget(i_row, 0).findText(old_text)
            if new_index_of_old_text != -1:
                self.trainOnWayTable.cellWidget(i_row, 0).setCurrentIndex(new_index_of_old_text)
            else:
                self.trainOnWayTable.cellWidget(i_row, 0).setCurrentIndex(0)

    # 更新行车工况表格中的的上道车单元格控件选项内容
    def train_on_way_train_combo_update(self):
        # 遍历各行，更新combo中的选项
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            i_train_combo = self.trainOnWayTable.cellWidget(i_row, 1)
            i_train_combo.currentIndexChanged.disconnect()
            old_text = self.trainOnWayTable.cellWidget(i_row, 1).currentText()
            old_idx_in_combo = self.trainOnWayTable.cellWidget(i_row, 1).findText(old_text)
            self.trainOnWayTable.cellWidget(i_row, 1).clear()
            self.trainOnWayTable.cellWidget(i_row, 1).addItem('请选择')
            for j_row in range(0, self.trainTable.rowCount()):
                self.trainOnWayTable.cellWidget(i_row, 1).addItem(self.trainTable.item(j_row, 1).text())
            # self.trainOnWayTable.cellWidget(i_row, 1).setCurrentIndex(old_idx_in_combo)
            self.wind_force_train_assign_table_row_update()
            new_index_of_old_text = self.trainOnWayTable.cellWidget(i_row, 1).findText(old_text)
            if new_index_of_old_text != -1:
                self.trainOnWayTable.cellWidget(i_row, 1).setCurrentIndex(new_index_of_old_text)
            else:
                self.trainOnWayTable.cellWidget(i_row, 1).setCurrentIndex(0)
            i_train_combo.currentIndexChanged.connect(self.on_train_on_way_combo_idx_changed)

    def consider_fluctuating_select(self):
        if self.considerFluctuatingSel.checkState() == 2:
            visible_flag = True
            self.consider_fluctuating = 1
        else:
            visible_flag = False
            self.consider_fluctuating = 0
        self.roughnessLabel.setEnabled(visible_flag)
        self.roughnessEnter.setEnabled(visible_flag)
        self.referenceAltitudeLabel.setEnabled(visible_flag)
        self.referenceAltitudeEnter.setEnabled(visible_flag)
        self.deckAltitudeLabel.setEnabled(visible_flag)
        self.deckAltitudeEnter.setEnabled(visible_flag)
        self.spacePtNumLabel.setEnabled(visible_flag)
        self.spacePtNumEnter.setEnabled(visible_flag)
        self.maxFreqLabel.setEnabled(visible_flag)
        self.maxFreqEnter.setEnabled(visible_flag)
        self.randomSeedWindLabel.setEnabled(visible_flag)
        self.randomSeedWindEnter.setEnabled(visible_flag)
        self.lastTimeLabel.setEnabled(visible_flag)
        self.lastTimeEnter.setEnabled(visible_flag)
        self.smoothDistWindLabel.setEnabled(visible_flag)
        self.smoothDistWindEnter.setEnabled(visible_flag)
        self.smoothTimeWindLabel.setEnabled(visible_flag)
        self.smoothTimeWindEnter.setEnabled(visible_flag)

    # 风荷载表格内容更新：每次执行都读取表中指定行的既有名称，并根据该名称与dict信息，重写概览一栏
    def wind_force_table_summary_update(self, bri_or_veh, row_to_update=None):
        if bri_or_veh == 'bri':
            table_obj = self.windForceBriTable
            target_dict = self.wind_force_bri_dict
        else:
            table_obj = self.windForceVehTable
            target_dict = self.wind_force_veh_dict
        if not row_to_update:
            row_to_update = range(0, table_obj.rowCount())
        if type(row_to_update) == int:
            row_to_update = [row_to_update]
        for i_row in row_to_update:
            i_name = table_obj.item(i_row, 1).text()
            num_valid_dof = 0
            max_order = 0
            for i_dof in range(0, 6):
                if len(target_dict[i_name][i_dof + 1]) > 1 or \
                        target_dict[i_name][i_dof + 1][0] != 0:
                    num_valid_dof += 1
                    max_order = max(max_order, len(target_dict[i_name][i_dof + 1]))
            para_summary_str = '共%d个分力系数；最高%d阶展开' % (num_valid_dof, max_order)
            table_obj.item(i_row, 2).setText(para_summary_str)

    # 新增车/桥风力系数组
    def wind_force_add(self, bri_or_veh):
        if bri_or_veh == 'bri':
            table_obj = self.windForceBriTable
            target_dict = self.wind_force_bri_dict
            default_name = '结构风力系数组'
        else:
            table_obj = self.windForceVehTable
            target_dict = self.wind_force_veh_dict
            default_name = '车辆风力系数组'
        wind_force_names_exist = target_dict.keys()
        self.WindForceDefDia = GuideWindForceDefDialog(bri_or_veh, default_name, wind_force_names_exist, [])
        self.WindForceDefDia.exec_()
        if self.WindForceDefDia.save_flag:
            table_obj.insertRow(table_obj.rowCount())
            current_wind_force_name = self.WindForceDefDia.wind_force_name
            target_dict[current_wind_force_name] = self.WindForceDefDia.wind_force_list
            table_obj.item(table_obj.rowCount() - 1, 1).setText(current_wind_force_name)
            # 将子窗口保存的参数显示在表格的概览中
            self.wind_force_table_summary_update(bri_or_veh, table_obj.rowCount() - 1)
            # num_valid_dof = 0
            # max_order = 0
            # for i_dof in range(0, 6):
            #     if len(self.WindForceDefDia.wind_force_list[i_dof + 1]) > 1 or \
            #             self.WindForceDefDia.wind_force_list[i_dof + 1][0] != 0:
            #         num_valid_dof += 1
            #         max_order = max(max_order, len(self.WindForceDefDia.wind_force_list[i_dof + 1]))
            # para_summary_str = '共%d个分力系数；最高%d阶展开' % (num_valid_dof, max_order)
            # table_obj.item(table_obj.rowCount() - 1, 2).setText(para_summary_str)
            if bri_or_veh == 'bri':
                self.wind_force_bri_assign_table_update_combo()

    # 编辑车/桥风力系数参数
    def wind_force_edit(self, bri_or_veh):
        if bri_or_veh == 'bri':
            table_obj = self.windForceBriTable
            target_dict = self.wind_force_bri_dict
        else:
            table_obj = self.windForceVehTable
            target_dict = self.wind_force_veh_dict
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "请先选中一行。")
            return
        current_wind_force_name = table_obj.item(top, 1).text()
        force_already_defined = target_dict[current_wind_force_name]
        old_data = target_dict.copy()
        wind_force_dict_except_current = target_dict.copy()
        del wind_force_dict_except_current[current_wind_force_name]
        wind_force_name_exist = wind_force_dict_except_current.keys()
        self.WindForceDefDia = GuideWindForceDefDialog(bri_or_veh, current_wind_force_name, wind_force_name_exist,
                                                       force_already_defined)
        self.WindForceDefDia.exec_()
        if self.WindForceDefDia.save_flag:
            new_wind_force_name = self.WindForceDefDia.wind_force_name
            target_dict.clear()
            target_dict.update(wind_force_dict_except_current)
            target_dict[new_wind_force_name] = self.WindForceDefDia.wind_force_list
            table_obj.item(top, 1).setText(new_wind_force_name)
            # 考虑到更名的可能性，操作流程统一为：删除原先的键值对，再将窗口最后返回的名称和控制点信息新建
            self.wind_force_table_summary_update(bri_or_veh, top)
            if bri_or_veh == 'bri':
                self.wind_force_bri_assign_table_update_combo()
            else:
                self.replace_assigned_veh_wind_forces(current_wind_force_name, new_wind_force_name)
                self.wind_force_train_assign_table_summary_update()
            if old_data != target_dict:
                self.change_save_status()

    # 删除车/桥风力系数组
    def wind_force_del(self, bri_or_veh):
        if bri_or_veh == 'bri':
            table_obj = self.windForceBriTable
            target_dict = self.wind_force_bri_dict
        else:
            table_obj = self.windForceVehTable
            target_dict = self.wind_force_veh_dict
        top, left, bottom, right = table_select_range(table_obj)
        if top != bottom:
            QMessageBox.warning(self, "警告", "此表不支持同时删除多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "请先选中一行。")
            return
        reply = QMessageBox.warning(self, '警告', '若此风力系数已被分配，则删除此风力系数后将为相关结构结点/车辆分配默认风力系数。\n是否确认删除？',
                                    QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            current_wind_force_name = table_obj.item(top, 1).text()
            del target_dict[current_wind_force_name]
            table_obj.removeRow(top)
            if bri_or_veh == 'bri':
                self.wind_force_bri_assign_table_update_combo()
            else:
                self.replace_assigned_veh_wind_forces(current_wind_force_name, '无风荷载')
                self.wind_force_train_assign_table_summary_update()
        else:
            return

    # 替换已分配的车风力系数
    def replace_assigned_veh_wind_forces(self, old_wind_force_name, new_wind_force_name):
        for i_train in range(0, len(self.wind_force_train_assign_list)):
            for j_veh in range(0, len(self.wind_force_train_assign_list[i_train])):
                for k_ctrl_pt in range(0, len(self.wind_force_train_assign_list[i_train][j_veh])):
                    if self.wind_force_train_assign_list[i_train][j_veh][k_ctrl_pt] == old_wind_force_name:
                        self.wind_force_train_assign_list[i_train][j_veh][k_ctrl_pt] = new_wind_force_name

    # 选中风力系数组上移
    def wind_force_order_up(self, bri_or_veh):
        if bri_or_veh == 'bri':
            order_ok = table_row_order_up(self, self.windForceBriTable)
            if order_ok:
                self.wind_force_bri_assign_table_update_combo()
        else:
            order_ok = table_row_order_up(self, self.windForceVehTable)
            if order_ok:
                pass

    # 选中风力系数组下移
    def wind_force_order_down(self, bri_or_veh):
        if bri_or_veh == 'bri':
            order_ok = table_row_order_down(self, self.windForceBriTable)
            if order_ok:
                self.wind_force_bri_assign_table_update_combo()
        else:
            order_ok = table_row_order_down(self, self.windForceVehTable)
            if order_ok:
                pass

    # 风荷载结点组表格中新增一行时，执行此slot，给风荷载分配表格中增加一行，同时初始化combo
    def wind_force_bri_assign_table_add_row(self):
        # 在风荷载结点组表格发生变化时（按钮的slot中）调用，不用信号
        self.windForceBriAssignTable.insertRow(self.windForceBriAssignTable.rowCount())
        str_to_put = self.windNodeGroupTable.item(self.windNodeGroupTable.rowCount() - 1, 1).text()
        self.windForceBriAssignTable.item(self.windForceBriAssignTable.rowCount() - 1, 0).setText(str_to_put)
        self.wind_force_bri_assign_table_setup_combo(self.windForceBriAssignTable.rowCount() - 1)

    # 风荷载结点组表格中删除一行时，执行此slot，给风荷载分配表格中删除对应行，同时拆掉对应行的combo
    def wind_force_bri_assign_table_del_row(self, row_to_del):
        self.windForceBriAssignTable.removeCellWidget(row_to_del, 1)
        self.windForceBriAssignTable.removeRow(row_to_del)

    # 风荷载结点组表格中修改一行的名称时，执行此slot，给风荷载分配表中对应的行名称进行修改，combo不动
    def wind_force_bri_assign_table_modify_row(self, row_to_modify, new_name):
        self.windForceBriAssignTable.item(row_to_modify, 0).setText(new_name)

    # 风荷载分配表中combo的初始化
    def wind_force_bri_assign_table_setup_combo(self, row_to_setup):
        new_combo = QComboBox()
        new_combo.addItem('无风荷载')
        for i_row in range(0, self.windForceBriTable.rowCount()):
            item_str = self.windForceBriTable.item(i_row, 1).text()
            new_combo.addItem(item_str)
        self.windForceBriAssignTable.setCellWidget(row_to_setup, 1, new_combo)

    # 风力系数表格中发生新增、删除、修改操作时，执行此slot，给风荷载分配表中对应的combo的item进行更新，同时尽可能保持原来的currentItem
    def wind_force_bri_assign_table_update_combo(self):
        for i_row in range(0, self.windForceBriAssignTable.rowCount()):
            old_selected_item_str = self.windForceBriAssignTable.cellWidget(i_row, 1).currentText()
            self.windForceBriAssignTable.cellWidget(i_row, 1).clear()
            self.wind_force_bri_assign_table_setup_combo(i_row)
            new_index_of_old_text = self.windForceBriAssignTable.cellWidget(i_row, 1).findText(old_selected_item_str)
            if new_index_of_old_text != -1:
                self.windForceBriAssignTable.cellWidget(i_row, 1).setCurrentIndex(new_index_of_old_text)
            else:
                self.windForceBriAssignTable.cellWidget(i_row, 1).setCurrentIndex(0)

    def wind_field_uniform_select(self):  # 要改成对称的if else：不管选了均匀还是不均匀都要弹窗
        if self.windFieldUniformSel.currentText() == '均匀':
            reply = QMessageBox.warning(self, '警告', '已定义的风场控制点坐标及风力系数分配数据将被清空，确定要继续吗？',
                                        QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                self.windFieldUniformSel.currentIndexChanged.disconnect()
                self.windFieldUniformSel.setCurrentText('不均匀')
                self.windFieldUniformSel.currentIndexChanged.connect(self.wind_field_uniform_select)
                return
            visible_flag = False
            self.wind_field_ctrl_pt_list = [0]  # VBC中以单个控制点表示均匀风场；不均匀风场子窗口已经不允许单个控制点，可避免范围交叉
            for i_row in range(0, len(self.wind_force_train_assign_list)):
                self.wind_force_train_assign_list[i_row] = []
            self.wind_force_train_assign_table_summary_update()
        else:
            reply = QMessageBox.warning(self, '警告', '已定义的风力系数分配数据将被清空，确定要继续吗？',
                                        QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                self.windFieldUniformSel.currentIndexChanged.disconnect()
                self.windFieldUniformSel.setCurrentText('均匀')
                self.windFieldUniformSel.currentIndexChanged.connect(self.wind_field_uniform_select)
                return
            visible_flag = True
            self.wind_field_ctrl_pt_list = []
            for i_row in range(0, len(self.wind_force_train_assign_list)):
                self.wind_force_train_assign_list[i_row] = []
            self.wind_force_train_assign_table_summary_update()
        self.windFieldCtrlPtEdit.setVisible(visible_flag)

    def wind_field_ctrl_pt_edit(self):
        old_list = self.wind_field_ctrl_pt_list
        self.wind_field_ctrl_pt_def_dia = GuideWindFieldCtrlPtDefDialog(self.wind_field_ctrl_pt_list)
        self.wind_field_ctrl_pt_def_dia.exec_()
        if self.wind_field_ctrl_pt_def_dia.save_flag:
            old_ctrl_pt_num = len(self.wind_field_ctrl_pt_list)
            self.wind_field_ctrl_pt_list = self.wind_field_ctrl_pt_def_dia.ctrl_pt_list
            new_ctrl_pt_num = len(self.wind_field_ctrl_pt_list)
            # 控制点增减操作会导致风力系数列表对应关系发生改变，须作相关处理以保持对应；该操作的弹窗确认在子窗口中进行
            # 如果控制点增加，就在已经定义了风荷载的车辆中append默认风力系数
            if new_ctrl_pt_num > old_ctrl_pt_num != 0:
                for j_train_wind_forces in self.wind_force_train_assign_list:
                    if j_train_wind_forces:
                        for k_veh_wind_forces in j_train_wind_forces:
                            [k_veh_wind_forces.append('无风荷载') for i in range(0, new_ctrl_pt_num - old_ctrl_pt_num)]
            # 如果控制点减少，就把已经定义了风荷载的车辆的末尾风力系数删掉
            if new_ctrl_pt_num < old_ctrl_pt_num:
                for j_train_wind_forces in self.wind_force_train_assign_list:
                    if j_train_wind_forces:
                        for k_veh_wind_forces in j_train_wind_forces:
                            del k_veh_wind_forces[-1:-(old_ctrl_pt_num - new_ctrl_pt_num + 1)]
            # 如果控制点列表发生了变化，需要变动主窗口的保存戳记
            if old_list != self.wind_field_ctrl_pt_list:
                self.change_save_status()

    def wind_force_train_assign_table_add_row(self):
        self.windForceTrainAssignTable.insertRow(self.windForceTrainAssignTable.rowCount())
        self.wind_force_train_assign_list.append([])
        str1 = self.trainOnWayTable.cellWidget(self.trainOnWayTable.rowCount() - 1, 0).currentText()
        self.windForceTrainAssignTable.item(self.windForceTrainAssignTable.rowCount() - 1, 0).setText(str1)
        str2 = self.trainOnWayTable.cellWidget(self.trainOnWayTable.rowCount() - 1, 1).currentText()
        self.windForceTrainAssignTable.item(self.windForceTrainAssignTable.rowCount() - 1, 1).setText(str2)
        self.wind_force_train_assign_table_summary_update(self.windForceTrainAssignTable.rowCount() - 1)

    def wind_force_train_assign_table_row_update(self, i_row_to_del_wind=None):
        # 上道车安排发生变化时(先用笨方法，检查全表)
        for i_row in range(0, self.windForceTrainAssignTable.rowCount()):
            # 1.车辆风力荷载分配表格的前两列text更新
            str1 = self.trainOnWayTable.cellWidget(i_row, 0).currentText()
            self.windForceTrainAssignTable.item(i_row, 0).setText(str1)
            str2 = self.trainOnWayTable.cellWidget(i_row, 1).currentText()
            self.windForceTrainAssignTable.item(i_row, 1).setText(str2)
        # 2.原来的车列如果已经分配了风荷载，且变化后的车列中车辆数有变，则需要对已经分配好的风荷载进行更新(在末尾删多余的or添默认的)
        # 相应的车辆数检查及弹窗二次确认，在前面的上道车combo_place中由其他slot进行
        if i_row_to_del_wind:
            self.wind_force_train_assign_list[i_row_to_del_wind] = []
            self.wind_force_train_assign_table_summary_update(i_row_to_del_wind)

    def wind_force_train_assign_table_summary_update(self, rows_to_update=None):
        if rows_to_update is None:
            rows_to_update = range(0, self.windForceTrainAssignTable.rowCount())
        if type(rows_to_update) == int:
            rows_to_update = [rows_to_update]
        for i_row in rows_to_update:
            if not self.wind_force_train_assign_list[i_row]:
                self.windForceTrainAssignTable.item(i_row, 2).setText('[无风荷载]')
                self.windForceTrainAssignTable.item(i_row, 2).setForeground(QBrush(QColor(255, 0, 0)))
            else:
                applied_wind_forces = []
                for j_veh_wind in self.wind_force_train_assign_list[i_row]:
                    applied_wind_forces = list(set(applied_wind_forces).union(set(j_veh_wind)))
                    summary_text = ','.join(applied_wind_forces)
                    self.windForceTrainAssignTable.item(i_row, 2).setText(summary_text)
                    self.windForceTrainAssignTable.item(i_row, 2).setForeground(QBrush(QColor(0, 0, 0)))

    def wind_force_train_assign_edit(self):
        top, left, bottom, right = table_select_range(self.windForceTrainAssignTable)
        if top != bottom:
            QMessageBox.warning(self, '警告', '不支持同时编辑多行。')
            return
        if top == -1:
            QMessageBox.warning(self, '警告', '请先选中一行。')
            return
        rail_name = self.windForceTrainAssignTable.item(top, 0).text()
        train_name = self.windForceTrainAssignTable.item(top, 1).text()
        train_and_way_name = rail_name + train_name
        if rail_name == '请选择' or train_name == '请选择':
            QMessageBox.warning(self, '警告', '选中的行车工况无效，请先完成行车工况的定义！')
            return
        veh_list = self.train_dict[train_name]
        veh_name_list = [self.vehicle_type_dict[i][0] for i in veh_list]
        ctrl_pt_num = len(self.wind_field_ctrl_pt_list)
        if ctrl_pt_num == 0:
            QMessageBox.warning(self, '警告', '请先定义车道沿线风场。')
            return
        wind_force_veh_name_list = [self.windForceVehTable.item(i, 1).text()
                                    for i in range(0, self.windForceVehTable.rowCount())]
        if self.wind_force_train_assign_list[top]:
            wind_force_already_defined = self.wind_force_train_assign_list[top]
        else:
            wind_force_already_defined = []
        old_data = self.wind_force_train_assign_list.copy()
        self.windForceVehAssignDialog = GuideWindForceVehAssign(train_and_way_name, veh_name_list, ctrl_pt_num,
                                                                wind_force_veh_name_list, wind_force_already_defined)
        self.windForceVehAssignDialog.exec_()
        if self.windForceVehAssignDialog.save_flag:
            self.wind_force_train_assign_list[top] = self.windForceVehAssignDialog.wind_force_veh_list
            self.wind_force_train_assign_table_summary_update(top)
            if old_data != self.wind_force_train_assign_list:
                self.change_save_status()

    def wind_force_train_assign_del(self):
        top, left, bottom, right = table_select_range(self.windForceTrainAssignTable)
        if top != bottom:
            QMessageBox.warning(self, '警告', '不支持同时编辑多行。')
            return
        if top == -1:
            QMessageBox.warning(self, '警告', '请先选中一行。')
            return
        self.wind_force_train_assign_list[top] = []
        self.wind_force_train_assign_table_summary_update(top)

    def external_force_table_combo_place(self, row_to_place):
        new_combo_node = QComboBox()
        new_combo_node.addItem('请选择')
        new_combo_node.currentIndexChanged.connect(self.change_save_status)
        for i_node in self.external_force_node_list:
            new_combo_node.addItem(str(i_node))
        self.externalForceTable.setCellWidget(row_to_place, 1, new_combo_node)

        new_combo_dof = QComboBox()
        new_combo_dof.addItems(['请选择', 'X', 'Y', 'Z', 'ROTX', 'ROTY', 'ROTZ'])
        new_combo_dof.currentIndexChanged.connect(self.change_save_status)
        self.externalForceTable.setCellWidget(row_to_place, 2, new_combo_dof)

    def external_force_table_combo_update(self):
        for i_row in range(0, self.externalForceTable.rowCount()):
            i_old_text = self.externalForceTable.cellWidget(i_row, 1).currentText()
            self.externalForceTable.cellWidget(i_row, 1).clear()
            self.externalForceTable.cellWidget(i_row, 1).addItem('请选择')
            new_items = [str(i) for i in self.external_force_node_list]
            self.externalForceTable.cellWidget(i_row, 1).addItems(new_items)
            new_index_of_old_text = self.externalForceTable.cellWidget(i_row, 1).findText(i_old_text)
            if new_index_of_old_text != -1:
                self.externalForceTable.cellWidget(i_row, 1).setCurrentIndex(new_index_of_old_text)
            else:
                self.externalForceTable.cellWidget(i_row, 1).setCurrentIndex(0)

    def external_force_add(self):
        table_obj = self.externalForceTable
        table_add_row(table_obj, always_to_last=True)
        self.external_force_table_combo_place(table_obj.rowCount() - 1)
        self.external_force_list.append([])
        self.external_force_table_summary_update(row=table_obj.rowCount() - 1)

    def external_force_del(self, top=None):
        if top is None:
            top, left, bottom, right = table_select_range(self.externalForceTable)
            if top != bottom:
                QMessageBox.warning(self, "警告", "此表不支持同时删除多行。")
                return
            if top == -1:
                QMessageBox.warning(self, "警告", "请先选中一行。")
                return
        self.externalForceTable.removeCellWidget(top, 1)
        self.externalForceTable.removeCellWidget(top, 2)
        self.externalForceTable.removeRow(top)
        del self.external_force_list[top]

    def external_force_edit(self):
        top, left, bottom, right = table_select_range(self.externalForceTable)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "请先选中一行。")
            return
        node_id_text = self.externalForceTable.cellWidget(top, 1).currentText()
        dof_name = self.externalForceTable.cellWidget(top, 2).currentText()
        if node_id_text == '请选择' or dof_name == '请选择':
            QMessageBox.warning(self, '警告', '请先选定外荷载作用的结点号及自由度。')
            return
        time_hist_already_defined = self.external_force_list[top]
        old_data = self.external_force_list.copy()
        self.ext_force_def_dia = GuideExtForceTimeHistDef(node_id_text, dof_name, time_hist_already_defined)
        self.ext_force_def_dia.exec_()
        if self.ext_force_def_dia.save_flag:
            self.external_force_list[top] = self.ext_force_def_dia.external_force_time_history
        self.external_force_table_summary_update(row=top)
        if old_data != self.external_force_list:
            self.change_save_status()

    def external_force_table_summary_update(self, row=None):
        if not row:
            row = range(0, self.externalForceTable.rowCount())
        if type(row) == int:
            row = [row]
        for i_row in row:
            i_data = self.external_force_list[i_row]
            i_length = len(i_data)
            if i_length:
                i_time = i_data[-1][0] - i_data[0][0]
                i_forces = [j[1] for j in i_data]
                i_max_force = max(i_forces)
                i_min_force = min(i_forces)
                summary_text = '%d个时刻; 时长%.3fs; 力范围 [%.3e, %.3e] N(·m)' % (i_length, i_time, i_min_force, i_max_force)
            else:
                summary_text = '尚未定义外荷载时程'
            self.externalForceTable.item(i_row, 3).setText(summary_text)

    # 数值积分方法选项
    def integral_method_select(self, i):
        if i == 0:
            self.integraMethodSel.setEnabled(True)
        else:
            self.integraMethodSel.setEnabled(False)
        if self.saved_flag:
            self.save_action()

    # 数值积分步长
    def integral_step_enter(self):
        self.dt_integration = self.integraStepEnter.value()

    # 输出间隔
    def output_interval_select(self):
        self.step_num_each_output = self.outputIntervalSel.value()

    # 风吹草动就改变保存戳记
    def change_save_status(self):
        self.saved_flag = False
        current_title = self.windowTitle()
        if current_title[-1] != '*':
            self.setWindowTitle(current_title + '*')

    def check_action(self):
        error_num, check_result = self.check_ui_data()
        if error_num:
            # self.er = GuideErrorReminder(check_result)
            # self.er.show()
            QMessageBox.information(self, '输入合法性检查', check_result)
        else:
            QMessageBox.information(self, '输入合法性检查', '未发现非法输入。')

    def save_action(self):
        if self.running_flag:
            QMessageBox.information(self, '运算正在进行', '请在运算结束后再保存.')
            return
        error_num, check_result = self.check_ui_data()
        if error_num:
            # self.er = GuideErrorReminder(check_result)
            # self.er.show()
            QMessageBox.warning(self, '警告', check_result)
            return
        if not self.save_path:
            save_path = QFileDialog.getExistingDirectory(self, '选择项目保存位置(不存在的目录请先在下方新建)', self.browse_path)
            self.save_path = save_path
            if save_path:
                self.browse_path = save_path
            else:
                return
        files = os.listdir(self.save_path)
        if ('Res_Modal_Coordinate_Results_Bridge.bin' in files) and (not self.saved_flag):
            reply_existing_file = QMessageBox.warning(self, '警告', '在此保存将删除既有结果文件。'
                                                                  '\n是否仍要在此保存？',
                                                      QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply_existing_file == QMessageBox.Yes:
                for i_file in files:
                    if i_file[-1:-4:-1] == 'nib':
                        os.remove(path_verify(self.save_path) + i_file)
            if reply_existing_file == QMessageBox.Cancel:
                return
        if self.save_path:  # 其实这句没必要，被上面拦住了，但留着也以防万一吧先
            permission_ok = self.check_file_permissions(self.save_path)
            if permission_ok:
                self.generate_dat_files(self.save_path)
                self.saved_flag = True
                title_path_text = self.save_path.replace('/', '\\')
                self.setWindowTitle('VBC Guide - ' + title_path_text)
                self.runVbc.setEnabled(True)
                self.time_hist_plot_list = []
                self.timeHistPlotTable.setRowCount(0)
                self.on_post_table_range_changed()

    def save_as_action(self):
        if self.running_flag:
            QMessageBox.information(self, '运算正在进行', '请在运算结束后再保存。')
            return
        error_num, check_result = self.check_ui_data()
        if error_num:
            # self.er = GuideErrorReminder(check_result)
            # self.er.show()
            QMessageBox.warning(self, '警告', check_result)
            return
        # if self.save_path:
        #     browse_path = self.save_path
        # else:
        #     browse_path = './'
        save_path = QFileDialog.getExistingDirectory(self, '选择项目保存位置(不存在的目录请先在下方新建)', self.browse_path)
        if save_path:
            self.browse_path = save_path
            files = os.listdir(save_path)
            if 'Res_Modal_Coordinate_Results_Bridge.bin' in files:
                reply_existing_file = QMessageBox.warning(self, '警告', '在此保存将删除已有结果文件。'
                                                                      '\n是否仍要在此保存？',
                                                          QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply_existing_file == QMessageBox.Yes:
                    for i_file in files:
                        if i_file[-1:-4:-1] == 'nib':
                            os.remove(path_verify(save_path) + i_file)
                if reply_existing_file == QMessageBox.Cancel:
                    return
            self.save_path = save_path
            permission_ok = self.check_file_permissions(self.save_path)
            if permission_ok:
                self.generate_dat_files(self.save_path)
                self.saved_flag = True
                title_path_text = self.save_path.replace('/', '\\')
                self.setWindowTitle('VBC Guide - ' + title_path_text)
                self.runVbc.setEnabled(True)
                self.time_hist_plot_list = []
                self.timeHistPlotTable.setRowCount(0)
                self.on_post_table_range_changed()

    def load_action(self):
        if self.running_flag:
            QMessageBox.information(self, '运算正在进行', '请在运算结束后再读取.')
            return
        reply = QMessageBox.warning(self, '警告', '加载操作将覆盖现有窗口中的所有数据。\n确定继续吗？', QMessageBox.Yes | QMessageBox.Cancel,
                                    QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            load_path = QFileDialog.getExistingDirectory(self, '选择既有项目所在目录', self.browse_path)
            if load_path:
                self.browse_path = load_path
                self.load_path = load_path
                permission_ok = self.check_file_permissions(self.load_path)
                if permission_ok:
                    load_res = self.load_dat_files(load_path)
                    self.save_path = load_path
                    title_path_text = self.save_path.replace('/', '\\')
                    self.setWindowTitle('VBC Guide - ' + title_path_text + '*')
                    if not load_res:
                        self.setWindowTitle('VBC Guide - ' + title_path_text)
                        self.saved_flag = True
                        self.runVbc.setEnabled(True)
                        self.on_post_table_range_changed()

    @staticmethod
    def about_action():
        about_dialog = GuideAboutDia()
        about_dialog.exec_()

    def samples_action(self):
        try:
            start_directory = 'samples'
            os.startfile(start_directory)
        except:
            QMessageBox.warning(self, '警告', '算例目录打开失败，可能已经丢失。')

    def ansys_action(self):
        try:
            start_directory = 'Ansys data transfer'
            os.startfile(start_directory)
        except:
            QMessageBox.warning(self, '警告', 'Ansys数据转换脚本目录打开失败，可能已经丢失。')

    def closeEvent(self, QCloseEvent):
        if self.running_flag:
            reply = QMessageBox.question(self, '运算进行中', '运算进行中，确认退出吗？', QMessageBox.Yes | QMessageBox.Cancel,
                                         QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.res.terminate()
                self.running_flag = False
                QCloseEvent.accept()
            else:
                QCloseEvent.ignore()
                return
        if self.saved_flag:
            message_title = '是否确认退出'
            message_text = '是否确认退出程序？'
        else:
            message_title = '项目尚未保存'
            message_text = '您的项目尚未保存，\n是否放弃未保存的内容退出程序？'
        reply = QMessageBox.question(self, message_title, message_text, QMessageBox.Yes | QMessageBox.Cancel,
                                     QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()
            return

    # 根据完整的文件路径，得到文件所在目录的路径和文件名
    @staticmethod
    def split_file_path_and_name(text):
        text1 = text[::-1]
        text2 = text1.split('\\', 1)
        text2 = text2[::-1]
        text3 = []
        [text3.append(i[::-1]) for i in text2]
        return text3[0], text3[1]

    def check_ui_data(self):
        check_result = ''
        error_num = 0

        # 承轨结点号是否为空、是否输入非法(在本函数稍后位置检查是否不在模型中)
        if not self.railNodeEnter.toPlainText():
            error_num += 1
            check_result += (str(error_num) + ".未输入承轨结点号。\n")
        try:
            rail_nodes_list = get_num_list_from_text(self.railNodeEnter.toPlainText())
            rail_nodes_set = set(get_num_list_from_text(self.railNodeEnter.toPlainText()))
            if len(rail_nodes_list) != len(rail_nodes_set):
                raise ValueError
            rail_nodes_ok = True
        except:
            error_num += 1
            check_result += (str(error_num) + ".承轨结点号输入格式错误或存在重复。请尤其留意小写字母、英文标点、空格的使用。\n")
            rail_nodes_ok = False

        # 后处理结点表格是否为空、是否输入非法(第一列应为int)、是否存在残缺行(在本函数稍后位置检查是否不在模型中)
        post_nodes_ok = True
        post_rows_not_empty = []
        for i_row in range(0, self.postNodeTable.rowCount()):
            for i_col in range(0, self.postNodeTable.columnCount()):
                if self.postNodeTable.item(i_row, i_col).text():
                    post_rows_not_empty.append(i_row)
                    break
        post_nodes_list = []
        for i_row in post_rows_not_empty:
            if not self.postNodeTable.item(i_row, 0).text().isdigit():
                post_nodes_ok = False
            if not self.postNodeTable.item(i_row, 1).text():
                post_nodes_ok = False
            try:
                post_nodes_list.append(int(self.postNodeTable.item(i_row, 0).text()))
            except:
                post_nodes_ok = False
            if not post_nodes_ok:
                break
        if post_nodes_ok:
            post_nodes_set = set(post_nodes_list)
            if len(post_nodes_set) != len(post_nodes_list):
                post_nodes_ok = False
        if not post_nodes_ok:
            error_num += 1
            check_result += (str(error_num) + ".后处理结点表格存在不完整数据或非法输入或重复。\n")

        # 页面3
        # 非线性弹簧连接结点表格是否完整、结点号是否非法
        non_spring_nodes_ok = True
        non_spring_nodes_list = []
        for i_row in range(0, self.nonSpringNodeTable.rowCount()):
            for i_col in range(1, 4):
                if not self.nonSpringNodeTable.item(i_row, i_col).text().isdigit():
                    non_spring_nodes_ok = False
                    break
            if not self.nonSpringNodeTable.cellWidget(i_row, 4).currentIndex():
                non_spring_nodes_ok = False
                break
            try:
                non_spring_nodes_list.append(int(self.nonSpringNodeTable.item(i_row, 1).text()))
                non_spring_nodes_list.append(int(self.nonSpringNodeTable.item(i_row, 2).text()))
                if int(self.nonSpringNodeTable.item(i_row, 3).text()):
                    non_spring_nodes_list.append(int(self.nonSpringNodeTable.item(i_row, 3).text()))
            except:
                non_spring_nodes_ok = False
                break
        if non_spring_nodes_ok:
            non_spring_nodes_set = set(non_spring_nodes_list)
        #     if len(non_spring_nodes_list) != len(non_spring_nodes_set):
        #         non_spring_nodes_ok = False
        # ↑ 非线性弹簧节点没有必要查重复
        if not non_spring_nodes_ok:
            error_num += 1
            check_result += (str(error_num) + ".非线性结点表格不完整或输入非法或重复。\n")

        # 结点坐标信息表格是否存在非法或不完整输入或重复输入
        rows_not_empty = []
        nodes_info_ok = True
        nodes_id_list = []
        for i_row in range(0, self.bridgeNodeTable.rowCount()):
            for i_col in range(1, self.bridgeNodeTable.columnCount()):
                if self.bridgeNodeTable.item(i_row, i_col).text():
                    rows_not_empty.append(i_row)
                    break
        for i_row in rows_not_empty:
            if not self.bridgeNodeTable.item(i_row, 1).text().isdigit():
                nodes_info_ok = False
                break
            try:
                nodes_id_list.append(int(self.bridgeNodeTable.item(i_row, 1).text()))
            except:
                nodes_info_ok = False
                break
            for i_col in range(2, self.bridgeNodeTable.columnCount()):
                try:
                    float(self.bridgeNodeTable.item(i_row, i_col).text())
                except:
                    nodes_info_ok = False
                    break
        if nodes_info_ok:
            nodes_id_set = set(nodes_id_list)
            if len(nodes_id_set) != len(nodes_id_list):
                nodes_info_ok = False
        if not nodes_info_ok:
            error_num += 1
            check_result += (str(error_num) + ".结点坐标信息表格不完整或输入非法或重复。\n")

        # 求风荷载节点集合：风荷载节点在子窗口中检查，只要存在就一定不非法
        wind_nodes_set = set([])
        for i_wind_node_group in self.wind_node_group_dict.values():
            wind_nodes_set = wind_nodes_set.union(set(i_wind_node_group))

        # 求其它外力时程作用结点集合：合法性已经由信号机制实时检查，只要存在就一定不非法
        ext_force_nodes_set = set(self.external_force_node_list)

        # 各个子集中是否存在未定义坐标的结点(如果子集的填写存在非法，这步就跳过不检查了)
        if rail_nodes_ok and post_nodes_ok and non_spring_nodes_ok and nodes_info_ok:
            if not (rail_nodes_set.union(post_nodes_set).union(wind_nodes_set).union(non_spring_nodes_set).union(
                    ext_force_nodes_set)) \
                    .issubset(nodes_id_set):
                error_num += 1
                check_result += (str(error_num) + ".存在未填录坐标的结点。\n")

        # 页面2
        # 绑定的模态文件是否存在
        try:
            same_file_flag = False
            f = open(self.modeFile1Path.text(), 'r')
            f.close()
            if self.modeFileFormSel.currentIndex() == 1:
                if self.modeFile1Path.text() == self.modeFile2Path.text():
                    same_file_flag = True
                    raise ValueError
                f2 = open(self.modeFile2Path.text(), 'r')
                f2.close()
            if self.modeFileFormSel.currentIndex() == 2:
                if (self.modeFile1Path.text() == self.modeFile2Path.text()) \
                or (self.modeFile1Path.text() == self.modeFile3Path.text()) \
                or (self.modeFile2Path.text() == self.modeFile3Path.text()):
                    same_file_flag = True
                    raise ValueError
                f2 = open(self.modeFile2Path.text(), 'r')
                f2.close()
                f3 = open(self.modeFile3Path.text(), 'r')
                f3.close()
        except:
            error_num += 1
            if same_file_flag:
                error_str = '.绑定的模态文件存在重复。\n'
            else:
                error_str = '.绑定的模态文件不存在，其路径或已变动。\n'
            check_result += (str(error_num) + error_str)

        # 页面4
        # 轨道表格是否为空
        if not self.railTable.rowCount():
            error_num += 1
            check_result += (str(error_num) + ".未定义行车轨道。\n")

        # 页面5
        # 车列表格是否为空
        if not self.trainTable.rowCount():
            error_num += 1
            check_result += (str(error_num) + ".未定义车列。\n")
        # 行车工况表格是否为空
        if not self.trainOnWayTable.rowCount():
            error_num += 1
            check_result += (str(error_num) + ".未定义行车工况。\n")
        # 行车工况表格是否输入完整、行车速度工况数是否匹配
        current_row_valid_flag = True
        current_row_speed_num_ok = True
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            if not self.trainOnWayTable.cellWidget(i_row, 0).currentIndex():
                current_row_valid_flag = False
                break
            if not self.trainOnWayTable.cellWidget(i_row, 1).currentIndex():
                current_row_valid_flag = False
                break
            if '[' in self.trainOnWayTable.item(i_row, 2).text():
                current_row_speed_num_ok = False
        if not current_row_valid_flag:
            error_num += 1
            check_result += (str(error_num) + ".行车工况表格输入不完整。\n")
        if not current_row_speed_num_ok:
            error_num += 1
            check_result += (str(error_num) + ".行车工况表格的速度工况数不匹配。\n")

        if len(self.wind_node_group_dict):
            if self.windFieldStartEnter.value() >= self.windFieldEndEnter.value():
                error_num += 1
                check_result += (str(error_num) + ".风场起始点坐标应小于终点。\n")
            for i_wind_coe_bri in self.wind_force_bri_dict.keys():
                if i_wind_coe_bri in self.wind_force_veh_dict.keys():
                    error_num += 1
                    check_result += (str(error_num) + ".车辆与桥梁风力系数组存在重名。\n")
                    break

        # 外荷载时程表格是否存在未指定的节点和自由度
        ext_force_dof_ok = True
        for i_row in range(0, self.externalForceTable.rowCount()):
            if (self.externalForceTable.cellWidget(i_row, 1).currentText() == '请选择') \
                    or (self.externalForceTable.cellWidget(i_row, 2).currentText() == '请选择'):
                ext_force_dof_ok = False
                break
        if not ext_force_dof_ok:
            error_num += 1
            check_result += (str(error_num) + ".外荷载时程表格存在未指定的结点或自由度。\n")

        # 外荷载时程表格是否存在未定义的荷载时程
        ext_force_ok = True
        for i_ext_force in self.external_force_list:
            if not i_ext_force:
                ext_force_ok = False
                break
        if not ext_force_ok:
            error_num += 1
            check_result += (str(error_num) + ".外荷载时程表格存在未定义的荷载时程。\n")

        return error_num, check_result

    # 检查文件权限是否齐全
    def check_file_permissions(self, check_path):
        ok_flag = True
        try:
            files = os.listdir(check_path)
            for i_file in files:
                if i_file == '$RECYCLE.BIN' or i_file == 'System Volume Information' or os.path.isdir(i_file):
                    continue
                i_path = check_path + '/' + i_file
                i_f = open(i_path, 'r')
                i_f.close()
                i_f = open(i_path, 'a')
                i_f.close()
        except:
            QMessageBox.warning(self, '文件权限错误', '当前工况目录中文件权限不足或正在被占用，请检查后重试。')
            ok_flag = False
        return  ok_flag


    # 整合dat文件
    def generate_dat_files(self, save_path):
        # 1.非线性弹簧
        i_step = 0
        ns_define_ok = True
        try:
            self.ns = NonSpring(self.non_spring_class_dict)
            i_step += 1
            non_spring_list = []
            non_spring_name_vec = []
            for i_spring in self.non_spring_dict.keys():
                i_step += 1
                non_spring_list.append(self.non_spring_dict[i_spring])
                non_spring_name_vec.append(i_spring)
            self.ns.define(non_spring_list, non_spring_name_vec)
            i_step += 1

        except:
            QMessageBox.warning(self, '警告', '写弹簧遇到错误' + str(i_step))
            ns_define_ok = False

        # 2.桥梁子系统文件
        i_step = 0
        msb_define_ok = True
        try:
            self.msb = SubBri()
            i_step += 1
            bridge_nodes_info = []
            for i_row in range(0, self.bridgeNodeTable.rowCount()):
                i_all_empty_flag = True  # 1-4列每个格子都空
                for j_col in range(1, 5):
                    if self.bridgeNodeTable.item(i_row, j_col).text():
                        i_all_empty_flag = False
                if i_all_empty_flag:
                    continue
                i_id = int(self.bridgeNodeTable.item(i_row, 1).text())
                i_x = float(self.bridgeNodeTable.item(i_row, 2).text())
                i_y = float(self.bridgeNodeTable.item(i_row, 3).text())
                i_z = float(self.bridgeNodeTable.item(i_row, 4).text())
                i_node_info = [i_id, i_x, i_y, i_z]
                bridge_nodes_info.append(i_node_info)

            id_rail_nodes = get_num_list_from_text(self.railNodeEnter.toPlainText())
            post_nodes = []  # 格式：[[int, str], [int, str], [int, str]...]
            id_post_nodes = []
            for i_row in range(self.postNodeTable.rowCount()):
                if self.postNodeTable.item(i_row, 0).text():
                    list2append = [int(self.postNodeTable.item(i_row, 0).text()),
                                   self.postNodeTable.item(i_row, 1).text()]
                    post_nodes.append(list2append)
                    id2append = int(self.postNodeTable.item(i_row, 0).text())
                    if id2append in id_post_nodes:
                        QMessageBox.warning(self, '警告', '整理桥梁子系统信息时出错。\n后处理结点号存在重复。')
                        return
                    else:
                        id_post_nodes.append(id2append)
            i_step += 1
            # 给表中的非线性弹簧的编号，要避开车辆弹簧(处理方法：利用非线性弹簧类读取到的内置车辆弹簧数量，据此给桥梁弹簧编号)
            non_spring_dict_for_name_and_id = {}
            i_step += 1
            for i_row in range(0, self.nonSpringTable.rowCount()):
                i_spring_id = i_row + 1
                i_spring_name = self.nonSpringTable.item(i_row, 1).text()
                non_spring_dict_for_name_and_id[i_spring_name] = i_spring_id
            nonlinear_springs = []
            for i_row in range(0, self.nonSpringNodeTable.rowCount()):
                i_list = [int(self.nonSpringNodeTable.item(i_row, 1).text()),
                          int(self.nonSpringNodeTable.item(i_row, 2).text()),
                          int(self.nonSpringNodeTable.item(i_row, 3).text()),
                          non_spring_dict_for_name_and_id[self.nonSpringNodeTable.cellWidget(i_row, 4).currentText()]]
                nonlinear_springs.append(i_list)
            sync_output_dofs = []  # 屏蔽同步输出结果的功能
            i_step += 1
            if self.mode_file_num == 1:
                bri_rail_mode_num = self.includeModeNumFile1Sel.value()
                path, name = self.split_file_path_and_name(self.modeFile1Path.text())
                mode_files_path = [path]  # 还得拆了名字
                mode_files_name = [name]
                modes_in_each_file = [self.includeModeNumFile1Sel.value()]
                damps_in_each_file = [[self.ctrlMode1FreqFile1Sel.value(), self.ctrlMode2FreqFile1Sel.value(),
                                       self.ctrlMode1DampFile1Enter.value(), self.ctrlMode2DampFile1Enter.value()]]
            elif self.mode_file_num == 2:
                bri_rail_mode_num = self.includeModeNumFile1Sel.value() + self.includeModeNumFile2Sel.value()
                path1, name1 = self.split_file_path_and_name(self.modeFile1Path.text())
                path2, name2 = self.split_file_path_and_name(self.modeFile2Path.text())
                mode_files_path = [path1, path2]
                mode_files_name = [name1, name2]
                modes_in_each_file = [self.includeModeNumFile1Sel.value(), self.includeModeNumFile2Sel.value()]
                damps_in_each_file = [[self.ctrlMode1FreqFile1Sel.value(), self.ctrlMode2FreqFile1Sel.value(),
                                       self.ctrlMode1DampFile1Enter.value(), self.ctrlMode2DampFile1Enter.value()],
                                      [self.ctrlMode1FreqFile2Sel.value(), self.ctrlMode2FreqFile2Sel.value(),
                                       self.ctrlMode1DampFile2Enter.value(), self.ctrlMode2DampFile2Enter.value()]]
            elif self.mode_file_num == 3:
                bri_rail_mode_num = self.includeModeNumFile1Sel.value() + self.includeModeNumFile2Sel.value() \
                                    + self.includeModeNumFile3Sel.value()
                path1, name1 = self.split_file_path_and_name(self.modeFile1Path.text())
                path2, name2 = self.split_file_path_and_name(self.modeFile2Path.text())
                path3, name3 = self.split_file_path_and_name(self.modeFile3Path.text())
                mode_files_path = [path1, path2, path3]
                mode_files_name = [name1, name2, name3]
                modes_in_each_file = [self.includeModeNumFile1Sel.value(), self.includeModeNumFile2Sel.value(),
                                      self.includeModeNumFile3Sel.value()]
                damps_in_each_file = [[self.ctrlMode1FreqFile1Sel.value(), self.ctrlMode2FreqFile1Sel.value(),
                                       self.ctrlMode1DampFile1Enter.value(), self.ctrlMode2DampFile1Enter.value()],
                                      [self.ctrlMode1FreqFile2Sel.value(), self.ctrlMode2FreqFile2Sel.value(),
                                       self.ctrlMode1DampFile2Enter.value(), self.ctrlMode2DampFile2Enter.value()],
                                      [self.ctrlMode1FreqFile3Sel.value(), self.ctrlMode2FreqFile3Sel.value(),
                                       self.ctrlMode1DampFile3Enter.value(), self.ctrlMode2DampFile3Enter.value()]]
            i_step += 1
            excluded_modes = []  # 屏蔽"计算中排除部分模态"的功能
            try:
                self.msb.define(bridge_nodes_info, id_rail_nodes, post_nodes,
                                nonlinear_springs, sync_output_dofs, bri_rail_mode_num,
                                excluded_modes, mode_files_path, mode_files_name, modes_in_each_file,
                                damps_in_each_file)
                i_step += 1
            except:
                QMessageBox.warning(self, '警告', '整理桥梁子系统信息时出错。\n请检查承轨、后处理、非线性弹簧结点号是否越界。')
                return
        except:
            msb_define_ok = False
            QMessageBox.warning(self, '警告', '写msb遇到错误' + str(i_step))
        if ns_define_ok and msb_define_ok:
            self.ns.write_dat(save_path)
            self.msb.write_dat(save_path)


        # 3.求解参数
        try:
            self.sp = SolPara()
            if self.ifPreprocess.currentText() == '前处理+后处理':
                integral_method = self.integra_method_dict[self.integraMethodSel.currentIndex()][1]
            else:
                integral_method = -1
            dt_integration = self.dt_integration
            step_num_each_output = self.step_num_each_output
            w_r_contact_opt = 1  # 默认考虑空间效应
            bridge_coord_opt = self.coordSel.currentIndex()
            if self.simRailElasticSel.currentText() == '是':
                rail_elastic_opt = 1
            else:
                rail_elastic_opt = 0
            rail_vertical_stiff = 0.600000E+08
            rail_vertical_damp = 0.800000E+05
            self.sp.define(integral_method, dt_integration, step_num_each_output, w_r_contact_opt,
                           bridge_coord_opt, rail_elastic_opt, rail_vertical_stiff, rail_vertical_damp)
            self.sp.write_dat(save_path)
        except:
            QMessageBox.warning(self, '警告', '写求解参数遇到错误')

        # 4.轨道线位
        try:
            self.rl = RailsLoc()
            rail_names = list(self.rail_dict.keys())
            rail_dict_for_name_and_id = {}
            rail_matrix = []
            track_width_name_vec = []
            for i_rail in range(0, len(rail_names)):
                rail_dict_for_name_and_id[rail_names[i_rail]] = i_rail + 1
                track_width_name_vec.append([self.rail_dict[rail_names[i_rail]][0], rail_names[i_rail]])
                rail_matrix.append(self.rail_dict[rail_names[i_rail]][1::])
            interpolation_interval = 0.2  # 暂定的
            if self.considerVertCurveSel.checkState() == 2:
                consider_vertical_curve = 1
            elif self.considerVertCurveSel.checkState() == 0:
                consider_vertical_curve = 0
            interpolation_method = 0  # 插值方法就这么一个，直接写死
            self.rl.define(rail_matrix,
                           track_width_name_vec,
                           interpolation_interval,
                           consider_vertical_curve,
                           interpolation_method)
            self.rl.write_dat(save_path)
        except:
            QMessageBox.warning(self, '警告', '写轨道线位遇到错误')

        # 5.轨道不平顺
        # try:
        self.ir = Irregularity()
        sample_pt_list = []
        spectrum_level = self.irr_spectrum_dict[self.irrSpectrumSel.currentIndex()][1]
        if spectrum_level:
            spectrum_level = spectrum_level
            ratio1 = self.irrCoeVertical.value()
            ratio2 = self.irrCoeDirectional.value()
            ratio3 = self.irrCoeHorizontal.value()
        else:
            spectrum_level = 7
            ratio1, ratio2, ratio3 = 0, 0, 0
        random_seed = self.irrRandomSeedSel.value()
        wave_length_min = self.irrWavelengthMinSel.value()
        wave_length_max = self.irrWavelengthMaxSel.value()
        sample_length = self.get_rail_total_length()

        wave_length_filter = 0.0
        smooth_distance = self.irrSmoothLengthSel.value()
        if self.irrFromSpectrum.isChecked():
            sample_source = 1
            interval = 0.25 * wave_length_min
        else:
            sample_source = 0
            for i_row in range(self.irrSampleTable.rowCount()):
                if (not self.irrSampleTable.item(i_row, 0).text()) and (not self.irrSampleTable.item(i_row, 1).text()) and (not self.irrSampleTable.item(i_row, 2).text()):
                    continue
                i_vertical = float(self.irrSampleTable.item(i_row, 0).text())
                i_directional = float(self.irrSampleTable.item(i_row, 1).text())
                i_horizontal = float(self.irrSampleTable.item(i_row, 2).text())
                sample_pt_list.append([i_vertical, i_directional, i_horizontal])
            interval = self.irrPtIntervalEnter.value()
        self.ir.define(spectrum_level, random_seed, wave_length_min, wave_length_max, sample_length, interval,
                       wave_length_filter, sample_source, smooth_distance, ratio1, ratio2, ratio3, sample_pt_list)
        self.ir.write_dat(save_path)
        # except:
        #     QMessageBox.warning(self, '警告', '写不平顺遇到错误')

        # 6.上道车运行组织
        try:
            self.vo = VehOrg()
            veh_matrix = []
            train_name_vec = []
            for i_row in range(0, self.trainOnWayTable.rowCount()):
                i_rail_id = self.trainOnWayTable.cellWidget(i_row, 0).currentIndex()
                i_train_id = self.trainOnWayTable.cellWidget(i_row, 1).currentIndex()
                self.train_on_way_data[i_row][0] = [i_train_id, i_rail_id]
            for i_train in self.train_dict.keys():
                veh_matrix.append(self.train_dict[i_train])
                train_name_vec.append(i_train)
            org_matrix = self.train_on_way_data
            self.vo.define(veh_matrix, train_name_vec, org_matrix)
            self.vo.write_dat(save_path)
        except:
            QMessageBox.warning(self, '警告', '写运行组织遇到问题')

        # 7.车型
        try:
            self.msv = SubVeh()
            self.msv.write_dat(save_path)
        except:
            QMessageBox.warning(self, '警告', '写车型文件遇到问题')

        # 8.风荷载
        try:
            self.wind_coe = WindCoe()
            air_dens = self.airDensEnter.value()
            ave_wind_speed = self.aveWindSpeedEnter.value()
            wind_direction_in_rad = self.windDirectionEnter.value()  #  / 180.0 * 3.141592653589793
            wind_field_start_x = self.windFieldStartEnter.value()
            space_length = self.windFieldEndEnter.value() - self.windFieldStartEnter.value()
            consider_fluctuating = self.consider_fluctuating
            roughness = self.roughnessEnter.value()
            reference_altitude = self.referenceAltitudeEnter.value()
            deck_altitude = self.deckAltitudeEnter.value()
            space_pt_num = self.spacePtNumEnter.value()
            max_freq = self.maxFreqEnter.value()
            random_seed_fluctuating = self.randomSeedWindEnter.value()
            last_time = self.lastTimeEnter.value()
            smooth_dist = self.smoothDistWindEnter.value()
            smooth_time = self.smoothTimeWindEnter.value()
            wind_coe_dict_bri = self.wind_force_bri_dict
            wind_node_group_dict = self.wind_node_group_dict
            wind_load_assign_list_bri = [self.windForceBriAssignTable.cellWidget(i, 1).currentText()
                                         for i in range(0, self.windForceBriAssignTable.rowCount())]
            wind_coe_dict_veh = self.wind_force_veh_dict
            wind_field_ctrl_pt_list = self.wind_field_ctrl_pt_list
            wind_load_assign_list_veh = self.wind_force_train_assign_list
            if wind_field_ctrl_pt_list:
                for i_train_ow in range(0, len(wind_load_assign_list_veh)):
                    if not wind_load_assign_list_veh[i_train_ow]:
                        i_train_name = self.windForceTrainAssignTable.item(i_train_ow, 1).text()
                        i_veh_num = len(self.train_dict[i_train_name])
                        i_veh_coe_list = ['无风荷载' for j in wind_field_ctrl_pt_list]
                        wind_load_assign_list_veh[i_train_ow] = [i_veh_coe_list for j in range(0, i_veh_num)]
            self.wind_coe.define(air_dens, ave_wind_speed, wind_direction_in_rad, wind_field_start_x,
                                 consider_fluctuating, roughness, reference_altitude, deck_altitude,
                                 space_pt_num, space_length,
                                 max_freq, random_seed_fluctuating, last_time, smooth_dist, smooth_time,
                                 wind_coe_dict_bri, wind_node_group_dict, wind_load_assign_list_bri,
                                 wind_coe_dict_veh, wind_field_ctrl_pt_list, wind_load_assign_list_veh)
            self.wind_coe.write_dat(save_path)
        except:
            QMessageBox.warning(self, '警告', '写风荷载文件遇到问题')

        # 9.其它外力时程
        try:
            self.ext_force = ExtForce()
            node_dof_list = []
            for i_row in range(0, self.externalForceTable.rowCount()):
                i_node = int(self.externalForceTable.cellWidget(i_row, 1).currentText())
                i_dof = self.externalForceTable.cellWidget(i_row, 2).currentIndex()
                node_dof_list.append([i_node, i_dof])
            force_time_hist_list = self.external_force_list
            self.ext_force.define(node_dof_list, force_time_hist_list)
            self.ext_force.write_dat(save_path)
        except:
            QMessageBox.warning(self, '警告', '写其它外力时程文件遇到问题')

    def load_dat_files(self, load_path):
        fail_file_names = ''
        fail_file_num = 0
        i_step = 2
        self.non_spring_read_err_flag = False
        self.nonSpringTable.setRowCount(0)
        self.postNodeTable.setRowCount(0)
        self.nonSpringNodeTable.setRowCount(0)
        self.bridgeNodeTable.setRowCount(0)
        self.railTable.setRowCount(0)
        self.trainTable.setRowCount(0)
        self.irrSampleTable.setRowCount(0)
        self.irrSamplePlot.mpl.clear_static_plot()
        self.irrSamplePlot.mpl.draw()
        self.trainOnWayTable.setRowCount(0)
        self.windForceBriTable.setRowCount(0)
        self.windNodeGroupTable.setRowCount(0)
        self.windForceBriAssignTable.setRowCount(0)
        self.windForceVehTable.setRowCount(0)
        self.windForceTrainAssignTable.setRowCount(0)
        self.wind_force_bri_dict = {}
        self.wind_node_group_dict = {}
        self.wind_force_train_assign_list = []
        self.railNodeEnter.clear()
        self.modeFile1Path.clear()
        self.modeFile2Path.clear()
        self.externalForceNodeTable.setRowCount(0)
        while self.externalForceTable.rowCount():
            self.external_force_del(top=0)
        self.vbcConsole.clear()
        self.timeHistPlotTable.setRowCount(0)
        self.time_hist_plot_list = []

        try:
            self.ns = NonSpring(self.non_spring_class_dict)
            i_step += 1
            self.ns.read_dat(load_path)
            i_step += 1
            self.non_spring_dict = {}
            i_step += 1
            i_same_name = 1

            i_step += 1
            for i_spring in range(0, len(self.ns.bri_spring_list)):
                i_step += 1
                current_spring_name = self.ns.non_spring_name_vec[i_spring]
                if current_spring_name in self.non_spring_dict:
                    i_same_name += 1
                    current_spring_name += ('(' + str(i_same_name) + ')')
                self.non_spring_dict[current_spring_name] = self.ns.bri_spring_list[i_spring]
                self.nonSpringTable.insertRow(self.nonSpringTable.rowCount())

                self.nonSpringTable.item(i_spring, 1).setText(current_spring_name)

                para_summary_str = ''
                for i_dof in range(1, 7):
                    if self.non_spring_dict[current_spring_name][i_dof - 1]:
                        i_str1 = self.dof_dict[i_dof] + ':'
                        i_str2 = self.non_spring_class_dict[self.non_spring_dict[current_spring_name][i_dof - 1][0]][
                                     0] + ' '
                        i_para_summary_str = i_str1 + i_str2
                        para_summary_str = para_summary_str + i_para_summary_str
                self.nonSpringTable.item(i_spring, 2).setText(para_summary_str)
        except:
            self.non_spring_read_err_flag = True

        try:
            self.msb = SubBri()
            self.msb.read_dat(load_path)
            for i_row in range(0, len(self.msb.bridge_nodes_info)):
                self.bridgeNodeTable.insertRow(i_row)
                i_id = self.msb.bridge_nodes_info[i_row][0]
                i_x = self.msb.bridge_nodes_info[i_row][1]
                i_y = self.msb.bridge_nodes_info[i_row][2]
                i_z = self.msb.bridge_nodes_info[i_row][3]
                self.bridgeNodeTable.item(i_row, 1).setText(str(i_id))
                self.bridgeNodeTable.item(i_row, 2).setText(str(i_x))
                self.bridgeNodeTable.item(i_row, 3).setText(str(i_y))
                self.bridgeNodeTable.item(i_row, 4).setText(str(i_z))
            id_rail_nodes_str = ', '.join(list(map(str, self.msb.id_rail_nodes)))
            self.railNodeEnter.setPlainText(id_rail_nodes_str)

            for i_row in range(0, len(self.msb.id_post_nodes)):
                self.postNodeTable.insertRow(i_row)
                self.postNodeTable.item(i_row, 0).setText(str(self.msb.id_post_nodes[i_row]))
                self.postNodeTable.item(i_row, 1).setText(self.msb.name_post_nodes[i_row])

            for i_row in range(0, self.msb.num_nonlinear_springs):
                self.nonSpringNodeTable.insertRow(i_row)
                self.nonSpringNodeTable.item(i_row, 1).setText(str(self.msb.nonlinear_springs[i_row][0]))
                self.nonSpringNodeTable.item(i_row, 2).setText(str(self.msb.nonlinear_springs[i_row][1]))
                self.nonSpringNodeTable.item(i_row, 3).setText(str(self.msb.nonlinear_springs[i_row][2]))
                if not self.non_spring_read_err_flag:
                    try:
                        # 找出msb中指定的弹簧是ns中已经定义的弹簧的第几个，再把表中combo翻到对应位置(注意跳过"请选择")
                        spring_id_in_bri_file = self.ns.non_spring_id_in_dat.index(
                            self.msb.nonlinear_springs[i_row][3]) + 1
                        self.nonSpringNodeTable.cellWidget(i_row, 4).setCurrentIndex(spring_id_in_bri_file)
                    except:
                        self.nonSpringNodeTable.cellWidget(i_row, 4).setCurrentIndex(0)
                else:
                    self.nonSpringNodeTable.cellWidget(i_row, 4).setCurrentIndex(0)

            if len(self.msb.mode_files_name) == 1:
                self.modeFileFormSel.setCurrentIndex(0)
                self.modeFile1Path.setText(self.msb.mode_files_path[0] + '\\' + self.msb.mode_files_name[0])
                self.includeModeNumFile1Sel.setValue(self.msb.modes_in_each_file[0])
                self.ctrlMode1DampFile1Enter.setValue(self.msb.damps_in_each_file[0][2])
                self.ctrlMode2DampFile1Enter.setValue(self.msb.damps_in_each_file[0][3])
                self.ctrlMode1FreqFile1Sel.setValue(self.msb.damps_in_each_file[0][0])
                self.ctrlMode2FreqFile1Sel.setValue(self.msb.damps_in_each_file[0][1])
                if self.ctrlMode1FreqFile1Sel.value() == self.ctrlMode2FreqFile1Sel.value():
                    self.equalDampFile1Sel.setCheckState(2)
                else:
                    self.equalDampFile1Sel.setCheckState(0)
            elif len(self.msb.mode_files_name) == 2:
                self.modeFileFormSel.setCurrentIndex(1)
                self.modeFile1Path.setText(self.msb.mode_files_path[0] + '\\' + self.msb.mode_files_name[0])
                self.modeFile2Path.setText(self.msb.mode_files_path[1] + '\\' + self.msb.mode_files_name[1])
                self.includeModeNumFile1Sel.setValue(self.msb.modes_in_each_file[0])
                self.includeModeNumFile2Sel.setValue(self.msb.modes_in_each_file[1])
                self.ctrlMode1DampFile1Enter.setValue(self.msb.damps_in_each_file[0][2])
                self.ctrlMode2DampFile1Enter.setValue(self.msb.damps_in_each_file[0][3])
                self.ctrlMode1FreqFile1Sel.setValue(self.msb.damps_in_each_file[0][0])
                self.ctrlMode2FreqFile1Sel.setValue(self.msb.damps_in_each_file[0][1])
                if self.ctrlMode1FreqFile1Sel.value() == self.ctrlMode2FreqFile1Sel.value():
                    self.equalDampFile1Sel.setCheckState(2)
                else:
                    self.equalDampFile1Sel.setCheckState(0)
                self.ctrlMode1DampFile2Enter.setValue(self.msb.damps_in_each_file[1][2])
                self.ctrlMode2DampFile2Enter.setValue(self.msb.damps_in_each_file[1][3])
                self.ctrlMode1FreqFile2Sel.setValue(self.msb.damps_in_each_file[1][0])
                self.ctrlMode2FreqFile2Sel.setValue(self.msb.damps_in_each_file[1][1])
                if self.ctrlMode1FreqFile2Sel.value() == self.ctrlMode2FreqFile2Sel.value():
                    self.equalDampFile2Sel.setCheckState(2)
                else:
                    self.equalDampFile2Sel.setCheckState(0)
            elif len(self.msb.mode_files_name) == 3:
                self.modeFileFormSel.setCurrentIndex(2)
                self.modeFile1Path.setText(self.msb.mode_files_path[0] + '\\' + self.msb.mode_files_name[0])
                self.modeFile2Path.setText(self.msb.mode_files_path[1] + '\\' + self.msb.mode_files_name[1])
                self.modeFile3Path.setText(self.msb.mode_files_path[2] + '\\' + self.msb.mode_files_name[2])
                self.includeModeNumFile1Sel.setValue(self.msb.modes_in_each_file[0])
                self.includeModeNumFile2Sel.setValue(self.msb.modes_in_each_file[1])
                self.includeModeNumFile3Sel.setValue(self.msb.modes_in_each_file[2])
                self.ctrlMode1DampFile1Enter.setValue(self.msb.damps_in_each_file[0][2])
                self.ctrlMode2DampFile1Enter.setValue(self.msb.damps_in_each_file[0][3])
                self.ctrlMode1FreqFile1Sel.setValue(self.msb.damps_in_each_file[0][0])
                self.ctrlMode2FreqFile1Sel.setValue(self.msb.damps_in_each_file[0][1])
                if self.ctrlMode1FreqFile1Sel.value() == self.ctrlMode2FreqFile1Sel.value():
                    self.equalDampFile1Sel.setCheckState(2)
                else:
                    self.equalDampFile1Sel.setCheckState(0)
                self.ctrlMode1DampFile2Enter.setValue(self.msb.damps_in_each_file[1][2])
                self.ctrlMode2DampFile2Enter.setValue(self.msb.damps_in_each_file[1][3])
                self.ctrlMode1FreqFile2Sel.setValue(self.msb.damps_in_each_file[1][0])
                self.ctrlMode2FreqFile2Sel.setValue(self.msb.damps_in_each_file[1][1])
                if self.ctrlMode1FreqFile2Sel.value() == self.ctrlMode2FreqFile2Sel.value():
                    self.equalDampFile2Sel.setCheckState(2)
                else:
                    self.equalDampFile2Sel.setCheckState(0)
                self.ctrlMode1DampFile3Enter.setValue(self.msb.damps_in_each_file[2][2])
                self.ctrlMode2DampFile3Enter.setValue(self.msb.damps_in_each_file[2][3])
                self.ctrlMode1FreqFile3Sel.setValue(self.msb.damps_in_each_file[2][0])
                self.ctrlMode2FreqFile3Sel.setValue(self.msb.damps_in_each_file[2][1])
                if self.ctrlMode1FreqFile3Sel.value() == self.ctrlMode2FreqFile3Sel.value():
                    self.equalDampFile3Sel.setCheckState(2)
                else:
                    self.equalDampFile3Sel.setCheckState(0)
        except:
            if self.nonSpringNodeTable.rowCount() and (
                    not self.railNodeEnter.toPlainText()) and self.non_spring_read_err_flag:
                fail_file_num += 1
                fail_file_names += (str(fail_file_num) + '.''NonlinearSpringParameters_bridge.dat' + str(i_step) + '\n')
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''Modal_Substructure_bridge.dat\n')

        try:
            self.sp = SolPara()
            self.sp.read_dat(load_path)
            if self.sp.integral_method == -1:
                self.ifPreprocess.setCurrentIndex(1)
            else:
                self.ifPreprocess.setCurrentIndex(0)
                found_flag = False
                for i in self.integra_method_dict.keys():
                    if self.integra_method_dict[i][1] == self.sp.integral_method:
                        self.integraMethodSel.setCurrentIndex(i)
                        found_flag = True
                        break
                if not found_flag:
                    raise ValueError
            self.integraStepEnter.setValue(self.sp.dt_integration)
            self.outputIntervalSel.setValue(self.sp.step_num_each_output)
            self.coordSel.setCurrentIndex(self.sp.bridge_coord_opt)
            self.simRailElasticSel.setCurrentIndex(not self.sp.rail_elastic_opt)
        except:
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''SolutionParameters.dat\n')

        try:
            self.rl = RailsLoc()
            self.rl.read_dat(load_path)
            self.rail_dict = {}

            num_of_same_name = 1
            for i_rail in range(0, self.rl.rail_num):
                i_track_width, i_rail_name = self.rl.track_width_name_vec[i_rail][0], \
                                             self.rl.track_width_name_vec[i_rail][1]
                if i_rail_name in self.rail_dict:
                    num_of_same_name += 1
                    i_rail_name += ('(' + str(num_of_same_name) + ')')
                i_rail_matrix = self.rl.rail_matrix_verified[i_rail]
                i_rail_matrix.insert(0, i_track_width)
                self.rail_dict[i_rail_name] = i_rail_matrix
                self.railTable.insertRow(i_rail)
                self.railTable.item(i_rail, 1).setText(i_rail_name)
                ctrl_pt_num = len(self.rail_dict[i_rail_name]) - 1
                track_width = self.rail_dict[i_rail_name][0]
                x_start = self.rail_dict[i_rail_name][1][0]
                x_end = self.rail_dict[i_rail_name][ctrl_pt_num][0]
                rail_summary_info = "轨距%.3fm; %d控制点; X:%.3fm->%.3fm" % (track_width, ctrl_pt_num, x_start, x_end)
                self.railTable.item(i_rail, 2).setText(rail_summary_info)
                self.train_on_way_rail_combo_update()
            table_auto_numbering(self.railTable)
        except:
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''Rails_Location.dat\n')

        try:
            self.ir = Irregularity()
            self.ir.read_dat(load_path)
            found_flag = False
            for i in self.irr_spectrum_dict.keys():
                if self.irr_spectrum_dict[i][1] == self.ir.spectrum_level:
                    found_flag = True
                    self.irrSpectrumSel.setCurrentIndex(i)
                    break
            if not found_flag:
                raise ValueError
            if self.ir.sample_source == 1:
                self.irrFromSpectrum.setChecked(True)
            else:
                self.irrFromUser.setChecked(True)
            self.irr_source_sel()
            self.irrRandomSeedSel.setValue(self.ir.random_seed)
            self.irrWavelengthMinSel.setValue(self.ir.wave_length_min)
            self.irrWavelengthMaxSel.setValue(self.ir.wave_length_max)
            self.irrSmoothLengthSel.setValue(self.ir.smooth_distance)
            self.irrCoeVertical.setValue(self.ir.ratio1)
            self.irrCoeDirectional.setValue(self.ir.ratio2)
            self.irrCoeHorizontal.setValue(self.ir.ratio3)
            self.irrPtIntervalEnter.setValue(self.ir.interval)
            if (self.ir.ratio1, self.ir.ratio2, self.ir.ratio3) == (0.0, 0.0, 0.0):
                self.irrSpectrumSel.setCurrentIndex(0)
            sample_pt_list = self.ir.sample_pt_list
            for i_row in range(0, len(sample_pt_list)):
                self.irrSampleTable.insertRow(i_row)
                self.irrSampleTable.item(i_row, 0).setText(str(sample_pt_list[i_row][0]))
                self.irrSampleTable.item(i_row, 1).setText(str(sample_pt_list[i_row][1]))
                self.irrSampleTable.item(i_row, 2).setText(str(sample_pt_list[i_row][2]))
            self.refresh_irr_sample_plot()
        except:
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''Irregularity.dat\n')

        try:
            self.vo = VehOrg()
            self.vo.read_dat(load_path)

            self.train_dict = {}
            num_of_same_name = 1
            for i_train in range(0, self.vo.train_num):
                self.trainTable.insertRow(i_train)
                i_train_name = self.vo.train_name_vec[i_train]
                if i_train_name in self.train_dict:
                    num_of_same_name += 1
                    i_train_name += ('(' + str(num_of_same_name) + ')')
                self.train_dict[i_train_name] = self.vo.veh_matrix_verified[i_train]
                self.trainTable.item(i_train, 1).setText(i_train_name)
                vehicle_num = len(self.train_dict[i_train_name])
                train_summary_info = "共%d辆车" % vehicle_num
                self.trainTable.item(i_train, 2).setText(train_summary_info)
                self.train_on_way_train_combo_update()
            table_auto_numbering(self.trainTable)
            self.train_on_way_data = self.vo.org_matrix_verified
            # [self.windForceTrainAssignTable.insertRow(0) for i in range(0, self.vo.train_num_on_way)]
            for i_train_ow in range(0, self.vo.train_num_on_way):
                self.windForceTrainAssignTable.insertRow(i_train_ow)  # 由于信号机制的存在，车辆风荷载分配表格须在此处初始化，而表格中的内容更新由程序一开始定义的信号机制自动进行
                self.trainOnWayTable.insertRow(i_train_ow)
                self.train_on_way_combo_place(i_train_ow)
                self.trainOnWayTable.cellWidget(i_train_ow, 0).setCurrentIndex(
                    int(self.train_on_way_data[i_train_ow][0][1]))
                self.trainOnWayTable.cellWidget(i_train_ow, 1).setCurrentIndex(
                    int(self.train_on_way_data[i_train_ow][0][0]))
                speeds = []
                for i_speed in range(0, self.vo.speed_num_on_way):
                    speeds.append(str(self.train_on_way_data[i_train_ow][i_speed + 1][0]) + 'km/h')
            # 小心！这一行必须等trainOnWay表格填好之后再做！因为这个spinbox连接到了实时检查的槽函数，而这个slot是给“先有表再有spin”准备的
            self.speedNum.setValue(self.vo.speed_num_on_way)
            self.display_speed_summary()  # 有可能读入的速度档恰好和原来相同，这时表格中不会自动显示速度概况，这行代码解决这个问题
        except:
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''VehicleOrginazition.dat\n')

        # 7.车型永远从安装目录重新读取

        # 8.风荷载文件
        try:
            self.wind_coe = WindCoe()
            self.wind_coe.read_dat(load_path)
            self.airDensEnter.setValue(self.wind_coe.air_dens)
            self.aveWindSpeedEnter.setValue(self.wind_coe.ave_wind_speed)
            self.windDirectionEnter.setValue(self.wind_coe.wind_direction_in_rad)  #  / 3.141592653589793 * 180.0)
            self.windFieldStartEnter.setValue(self.wind_coe.wind_field_start_x)
            self.windFieldEndEnter.setValue(self.wind_coe.wind_field_start_x + self.wind_coe.space_length)
            if self.wind_coe.consider_fluctuating == 1:
                self.considerFluctuatingSel.setCheckState(2)
            else:
                self.considerFluctuatingSel.setCheckState(0)
            self.roughnessEnter.setValue(self.wind_coe.roughness)
            self.referenceAltitudeEnter.setValue(self.wind_coe.reference_altitude)
            self.deckAltitudeEnter.setValue(self.wind_coe.deck_altitude)
            self.spacePtNumEnter.setValue(self.wind_coe.space_pt_num)
            self.maxFreqEnter.setValue(self.wind_coe.max_freq)
            self.randomSeedWindEnter.setValue(self.wind_coe.random_seed)
            self.lastTimeEnter.setValue(self.wind_coe.last_time)
            self.smoothDistWindEnter.setValue(self.wind_coe.smooth_dist)
            self.smoothTimeWindEnter.setValue(self.wind_coe.smooth_time)

            for i_row in range(0, len(self.wind_coe.wind_coe_dict_bri)):
                self.windForceBriTable.insertRow(i_row)
                i_name = list(self.wind_coe.wind_coe_dict_bri.keys())[i_row]
                self.windForceBriTable.item(i_row, 1).setText(i_name)
            self.wind_force_bri_dict.update(self.wind_coe.wind_coe_dict_bri)
            self.wind_force_table_summary_update('bri')

            for i_row in range(0, len(self.wind_coe.wind_node_group_dict)):
                self.windNodeGroupTable.insertRow(i_row)
                i_name = list(self.wind_coe.wind_node_group_dict.keys())[i_row]
                self.windNodeGroupTable.item(i_row, 1).setText(i_name)
            self.wind_node_group_dict.update(self.wind_coe.wind_node_group_dict)
            self.wind_node_table_summary_update()

            for i_row in range(0, len(self.wind_coe.wind_load_assign_list_bri)):
                self.windForceBriAssignTable.insertRow(i_row)
                i_name = self.windNodeGroupTable.item(i_row, 1).text()
                self.windForceBriAssignTable.item(i_row, 0).setText(i_name)
                self.wind_force_bri_assign_table_setup_combo(i_row)
                current_text = self.wind_coe.wind_load_assign_list_bri[i_row]
                self.windForceBriAssignTable.cellWidget(i_row, 1).setCurrentText(current_text)

            for i_row in range(0, len(self.wind_coe.wind_coe_dict_veh)):
                self.windForceVehTable.insertRow(i_row)
                i_name = list(self.wind_coe.wind_coe_dict_veh.keys())[i_row]
                self.windForceVehTable.item(i_row, 1).setText(i_name)
            self.wind_force_veh_dict.update(self.wind_coe.wind_coe_dict_veh)
            self.wind_force_table_summary_update('veh')

            self.wind_field_ctrl_pt_list = self.wind_coe.wind_field_ctrl_pt
            if len(self.wind_field_ctrl_pt_list) == 1:
                self.windFieldUniformSel.currentIndexChanged.disconnect()
                self.windFieldUniformSel.setCurrentText('均匀')
                self.windFieldCtrlPtEdit.setVisible(False)
                self.windFieldUniformSel.currentIndexChanged.connect(self.wind_field_uniform_select)
            else:
                self.windFieldUniformSel.currentIndexChanged.disconnect()
                self.windFieldUniformSel.setCurrentText('不均匀')
                self.windFieldCtrlPtEdit.setVisible(True)
                self.windFieldUniformSel.currentIndexChanged.connect(self.wind_field_uniform_select)

            # 注意：由于信号机制的存在，车辆风荷载分配表格的轨道及车列text的更新操作，在vehorg的读取过程中进行
            if self.wind_coe.wind_load_assign_list_veh:
                self.wind_force_train_assign_list = self.wind_coe.wind_load_assign_list_veh
            else:
                self.wind_force_train_assign_list = [[] for i in range(0, self.windForceTrainAssignTable.rowCount())]
            self.wind_force_train_assign_table_summary_update()
        except:
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''Wind_Coefficient.dat\n')
            [self.wind_force_train_assign_list.append([]) for i in range(0, self.windForceTrainAssignTable.rowCount())]
            self.wind_force_train_assign_table_summary_update()

        # 9.读取外力时程文件
        try:
            self.ext_force = ExtForce()
            self.ext_force.read_dat(load_path)
            ext_node_list = [i[0] for i in self.ext_force.node_dof_list]
            ext_node_list = list(set(ext_node_list))  # 去重
            for i_node in range(0, len(ext_node_list)):
                self.external_force_node_add()
                self.externalForceNodeTable.item(i_node, 1).setText(str(ext_node_list[i_node]))
            for i_node in range(0, len(self.ext_force.node_dof_list)):
                self.external_force_add()
                i_node_id = self.ext_force.node_dof_list[i_node][0]
                i_dof_num = self.ext_force.node_dof_list[i_node][1]
                self.externalForceTable.cellWidget(i_node, 1).setCurrentText(str(i_node_id))
                self.externalForceTable.cellWidget(i_node, 2).setCurrentIndex(i_dof_num)
            self.external_force_list = self.ext_force.force_time_hist_list
            self.external_force_table_summary_update()
        except:
            fail_file_num += 1
            fail_file_names += (str(fail_file_num) + '.''ExternalForces.dat\n')

        if fail_file_num:
            QMessageBox.warning(self, '读取文件时出现错误', fail_file_names)
            return 1
        else:
            return 0

    def load_irregularity(self):
        self.irrSampleTable.setRowCount(0)
        self.irrSamplePlot.mpl.clear_static_plot()
        self.irrSamplePlot.mpl.draw()
        load_path = self.save_path
        self.ir = Irregularity()
        self.ir.read_dat(load_path)
        if self.ir.sample_source == 1:
            self.irrFromSpectrum.setChecked(True)
        else:
            self.irrFromUser.setChecked(True)
        self.irr_source_sel()
        self.irrRandomSeedSel.setValue(self.ir.random_seed)
        self.irrWavelengthMinSel.setValue(self.ir.wave_length_min)
        self.irrWavelengthMaxSel.setValue(self.ir.wave_length_max)
        self.irrSmoothLengthSel.setValue(self.ir.smooth_distance)
        self.irrCoeVertical.setValue(self.ir.ratio1)
        self.irrCoeDirectional.setValue(self.ir.ratio2)
        self.irrCoeHorizontal.setValue(self.ir.ratio3)
        self.irrPtIntervalEnter.setValue(self.ir.interval)
        if (self.ir.ratio1, self.ir.ratio2, self.ir.ratio3) == (0.0, 0.0, 0.0):
            self.irrSpectrumSel.setCurrentIndex(0)
        sample_pt_list = self.ir.sample_pt_list
        # 多线程作业，主线程中connect的信号可能会滞后于填充数据操作，导致表格未正确初始化！！！！
        # self.irrSampleTable.model().rowsInserted.disconnect()  # 这个信号不能直接disconnect所有，不然表格控件就废了
        self.irrSampleTable.setRowCount(len(sample_pt_list))
        for i_row in range(0, len(sample_pt_list)):
            table_set_align_center_readonly(self.irrSampleTable, [i_row])
            self.irrSampleTable.item(i_row, 0).setText(str(sample_pt_list[i_row][0]))
            self.irrSampleTable.item(i_row, 1).setText(str(sample_pt_list[i_row][1]))
            self.irrSampleTable.item(i_row, 2).setText(str(sample_pt_list[i_row][2]))
        self.refresh_irr_sample_plot()
        # self.irrSampleTable.model().rowsInserted.connect(lambda i, j, k:
        #                                                  table_set_align_center_readonly(self.irrSampleTable, [j]))
        title_path_text = self.save_path.replace('/', '\\')
        self.setWindowTitle('VBC Guide - ' + title_path_text)
        self.saved_flag = True

    # 运行cmd
    def run_analysis(self):
        if self.saved_flag:
            def run_thread():
                # 复制可执行程序到目标目录
                core_files = os.listdir('.\\VBC_Core')
                target_path_core = path_verify(self.save_path) + 'VBC_Core\\'
                if not os.path.exists(target_path_core):
                    # 如果目标路径不存在原文件夹的话就创建
                    os.makedirs(target_path_core, 0o777)
                for i_file in core_files:
                    if i_file == 'VBC.PATH':
                        continue
                    source = '.\\VBC_Core\\%s ' % i_file
                    target = target_path_core
                    shutil.copy(source, target)
                    if i_file[-1:-4:-1] == 'exe':
                        exe_filename = i_file
                # 常用编码
                GBK = 'gbk'
                UTF8 = 'utf-8'
                # 解码方式，一般 py 文件执行为utf-8 ，cmd 命令为 gbk
                current_encoding = GBK
                f_vbc_path = open((target_path_core + 'VBC.PATH'), 'w')
                f_vbc_path.write(self.save_path)
                f_vbc_path.close()
                st = subprocess.STARTUPINFO()
                st.dwFlags = subprocess.STARTF_USESHOWWINDOW
                st.wShowWindow = subprocess.SW_HIDE

                self.res = subprocess.Popen(args=(target_path_core + exe_filename), shell=False,
                                            encoding=current_encoding,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            cwd=target_path_core, universal_newlines=True, bufsize=1, startupinfo=st)
                for line in iter(self.res.stdout.readline, 'r'):
                    line = line.rstrip()  # .decode('utf8')
                    if line:
                        global_ms.new_console_text_ready.emit(line)
                    if self.res.poll() is not None:
                        # if subprocess.Popen.poll(self.res) is not None:
                        if line == "":
                            break
                self.res.stdout.close()
                self.stopVbc.setEnabled(False)
                self.runVbc.setEnabled(True)
                self.running_flag = False
                self.on_post_table_range_changed()
                self.load_irregularity()

            files = os.listdir(self.save_path)
            # if 'Res_Modal_Coordinate_Results_Bridge.bin' in files:
            if '.bin' in ''.join(files):
                reply_existing_file = QMessageBox.warning(self, '警告', '检测到此项目已存在结果文件，运行分析将覆盖已有结果。'
                                                                      '\n是否进行分析？',
                                                          QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply_existing_file == QMessageBox.Yes:
                    allow_exec_calc = True
                else:
                    allow_exec_calc = False
            else:
                allow_exec_calc = True

            if allow_exec_calc:
                self.runVbc.setEnabled(False)
                self.stopVbc.setEnabled(True)
                self.vbcConsole.clear()
                self.thread = Thread(target=run_thread)
                self.thread.start()
                self.running_flag = True
            else:
                return
        else:
            QMessageBox.warning(self, '项目尚未保存', '请先保存项目，再运行分析！')

    def vbc_console_update(self, line):
        self.vbcConsole.appendPlainText(line)
        cursor = self.vbcConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.vbcConsole.setTextCursor(cursor)
        self.vbcConsole.setTextCursor(cursor)
        self.vbcConsole.ensureCursorVisible()

    def stop_analysis(self):
        if self.res.poll() is None:
            self.res.terminate()
            self.vbcConsole.appendPlainText('运算已被用户终止。')
            self.stopVbc.setEnabled(False)
            self.runVbc.setEnabled(True)
            self.running_flag = False

    def time_hist_plot_table_update(self, i_row, bri_post_node_list, train_ow_list, speed_selected, bri_or_veh,
                                    unit_selected, sub_unit_selected, response_selected, response_position_selected,
                                    line_style_selected, line_color_selected, filt_selected):
        speed_text = '档位%d' % (speed_selected+1)
        if filt_selected[0] == 1:
            filt_text = '(%.1f~%.1fHz)' % (filt_selected[1], filt_selected[2])
        elif filt_selected[0] == 2:
            filt_text = '(%.1fm移动平均)' % filt_selected[1]
        else:
            filt_text = '(不滤波)'
        if bri_or_veh == '结构':
            focus_object_text = '结构节点%d(%s)' % (bri_post_node_list[unit_selected][0],
                                                bri_post_node_list[unit_selected][1])
            response_text_list = ['dx', 'ax', 'dy', 'ay', 'dz', 'az', 'rx', 'arx', 'ry', 'ary', 'rz', 'arz']
            response_text = response_text_list[response_selected] + filt_text
        else:
            focus_object_text = '%s-%s-%d车(%s)' % (train_ow_list[unit_selected][0], train_ow_list[unit_selected][1],
                                                   sub_unit_selected+1,
                                                   self.vehicle_type_dict[self.train_dict[train_ow_list[unit_selected][1]][sub_unit_selected]][0])
            response_text_list = ['轮重减载率', '轮轨竖向力', '脱轨系数', '轮轨横向力',
                                  '轮下轨道位移-竖向', '轮下轨道位移-横向', '轮下轨道位移-摇头',
                                  '轮轨相对位移-竖向', '轮轨相对位移-横向', '轮轨相对位移-摇头',
                                  '加速度-横向', '加速度-竖向']
            if response_selected in range(0, 10):
                response_text = '轮对%d' % (response_position_selected+1) + response_text_list[response_selected] + filt_text
            else:
                position_text_list = ['车体前部', '车体后部']
                response_text = position_text_list[response_position_selected] + response_text_list[response_selected] + filt_text
        line_style_text_list = ['实线', '虚线', '点划线', '点线']
        line_color_text_list = ['蓝色', '绿色', '红色', '青色', '品红', '黄色', '黑色']
        line_text = line_color_text_list[line_color_selected] + line_style_text_list[line_style_selected]
        self.timeHistPlotTable.item(i_row, 1).setText(speed_text)
        self.timeHistPlotTable.item(i_row, 2).setText(focus_object_text)
        self.timeHistPlotTable.item(i_row, 3).setText(response_text)
        self.timeHistPlotTable.item(i_row, 4).setText(line_text)

    # 新增后处理图线
    def time_hist_plot_add(self):
        if not self.saved_flag:
            QMessageBox.warning(self, '尚未保存', '请保存后再进行后处理。')
            return
        speed_num = self.speedNum.value()
        bri_post_node_list = []
        for i_row in range(0, self.postNodeTable.rowCount()):
            if self.postNodeTable.item(i_row, 0).text():
                i_node_id = int(self.postNodeTable.item(i_row, 0).text())
                i_node_name = self.postNodeTable.item(i_row, 1).text()
                bri_post_node_list.append([i_node_id, i_node_name])
        train_ow_list = []
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            i_way_name = self.trainOnWayTable.cellWidget(i_row, 0).currentText()
            i_train_name = self.trainOnWayTable.cellWidget(i_row, 1).currentText()
            train_ow_list.append([i_way_name, i_train_name])
        train_dict = self.train_dict
        vehicle_type_dict = self.vehicle_type_dict
        time_hist_plot_def_dia = GuideTimeHistPlotDef(speed_num, bri_post_node_list, train_ow_list, train_dict,
                                                      vehicle_type_dict)
        time_hist_plot_def_dia.exec_()
        if time_hist_plot_def_dia.save_flag:
            table_add_row(self.timeHistPlotTable, always_to_last=True)
            self.time_hist_plot_table_update(self.timeHistPlotTable.rowCount()-1, bri_post_node_list, train_ow_list,
                                             time_hist_plot_def_dia.speed_selected, time_hist_plot_def_dia.bri_or_veh,
                                             time_hist_plot_def_dia.unit_selected, time_hist_plot_def_dia.sub_unit_selected,
                                             time_hist_plot_def_dia.response_selected, time_hist_plot_def_dia.response_position_selected,
                                             time_hist_plot_def_dia.line_style_selected, time_hist_plot_def_dia.line_color_selected,
                                             time_hist_plot_def_dia.filt_selected)
            new_check_box = QCheckBox(text='')
            new_check_box.setCheckState(2)
            self.timeHistPlotTable.setCellWidget(self.timeHistPlotTable.rowCount()-1, 5, new_check_box)
            self.time_hist_plot_list.append([time_hist_plot_def_dia.speed_selected, time_hist_plot_def_dia.bri_or_veh,
                                             time_hist_plot_def_dia.unit_selected, time_hist_plot_def_dia.sub_unit_selected,
                                             time_hist_plot_def_dia.response_selected, time_hist_plot_def_dia.response_position_selected,
                                             time_hist_plot_def_dia.line_style_selected, time_hist_plot_def_dia.line_color_selected,
                                             time_hist_plot_def_dia.filt_selected, time_hist_plot_def_dia.self_def_legend])

    def time_hist_plot_del(self):
        top, left, bottom, right = table_select_range(self.timeHistPlotTable)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时删除多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "请先选中一行。")
            return
        self.timeHistPlotTable.removeCellWidget(top, 5)
        self.timeHistPlotTable.removeRow(top)
        del self.time_hist_plot_list[top]

    def time_hist_plot_up(self):
        top, left, bottom, right = table_select_range(self.timeHistPlotTable)
        order_res = table_row_order_up(self, self.timeHistPlotTable)
        if order_res == 1:
            self.time_hist_plot_list[top], self.time_hist_plot_list[top-1] = self.time_hist_plot_list[top-1], self.time_hist_plot_list[top]

    def time_hist_plot_down(self):
        top, left, bottom, right = table_select_range(self.timeHistPlotTable)
        order_res = table_row_order_down(self, self.timeHistPlotTable)
        if order_res == 1:
            self.time_hist_plot_list[top+1], self.time_hist_plot_list[top] = self.time_hist_plot_list[top], self.time_hist_plot_list[top+1]

    def time_hist_plot_edit(self):
        if not self.saved_flag:
            QMessageBox.warning(self, '尚未保存', '请保存后再进行后处理。')
            return
        top, left, bottom, right = table_select_range(self.timeHistPlotTable)
        if top != bottom:
            QMessageBox.warning(self, "警告", "不支持同时编辑多行。")
            return
        if top == -1:
            QMessageBox.warning(self, "警告", "请先选中一行。")
            return
        speed_num = self.speedNum.value()
        bri_post_node_list = []
        for i_row in range(0, self.postNodeTable.rowCount()):
            if self.postNodeTable.item(i_row, 0).text():
                i_node_id = int(self.postNodeTable.item(i_row, 0).text())
                i_node_name = self.postNodeTable.item(i_row, 1).text()
                bri_post_node_list.append([i_node_id, i_node_name])
        train_ow_list = []
        for i_row in range(0, self.trainOnWayTable.rowCount()):
            i_way_name = self.trainOnWayTable.cellWidget(i_row, 0).currentText()
            i_train_name = self.trainOnWayTable.cellWidget(i_row, 1).currentText()
            train_ow_list.append([i_way_name, i_train_name])
        train_dict = self.train_dict
        vehicle_type_dict = self.vehicle_type_dict
        time_hist_plot_def_dia = GuideTimeHistPlotDef(speed_num, bri_post_node_list, train_ow_list, train_dict,
                                                      vehicle_type_dict, self.time_hist_plot_list[top])
        time_hist_plot_def_dia.exec_()
        if time_hist_plot_def_dia.save_flag:
            self.time_hist_plot_table_update(top, bri_post_node_list, train_ow_list,
                                             time_hist_plot_def_dia.speed_selected, time_hist_plot_def_dia.bri_or_veh,
                                             time_hist_plot_def_dia.unit_selected, time_hist_plot_def_dia.sub_unit_selected,
                                             time_hist_plot_def_dia.response_selected, time_hist_plot_def_dia.response_position_selected,
                                             time_hist_plot_def_dia.line_style_selected, time_hist_plot_def_dia.line_color_selected,
                                             time_hist_plot_def_dia.filt_selected)

            self.time_hist_plot_list[top] = [time_hist_plot_def_dia.speed_selected, time_hist_plot_def_dia.bri_or_veh,
                                             time_hist_plot_def_dia.unit_selected, time_hist_plot_def_dia.sub_unit_selected,
                                             time_hist_plot_def_dia.response_selected, time_hist_plot_def_dia.response_position_selected,
                                             time_hist_plot_def_dia.line_style_selected, time_hist_plot_def_dia.line_color_selected,
                                             time_hist_plot_def_dia.filt_selected, time_hist_plot_def_dia.self_def_legend]

    def show_plot(self):
        if not self.saved_flag:
            QMessageBox.warning(self, '尚未保存', '请保存后再进行后处理。')
            return
        if not self.timeHistPlotTable.rowCount():
            QMessageBox.warning(self, '警告', '未定义图线。')
            return
        # 难点：有些数据不能允许绘制于同一张图
        # 1.把需要的数据取出来整理好
        plot_data_list = []
        dt_list = []
        response_type_list = []  # 用于判断不宜绘制于同一张图的图线，1位移，2加速度，3角位移，4角加速度，5减载率，6脱轨系数，7力
        veh_num_list = []  # 每列车的车辆数量
        wheelset_num_list = []  # 每辆车的轮对数量(一维list)
        legends = []
        line_styles = ['-', '--', '-.', ':']
        line_styles_selected = []
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
        colors_selected = []
        for j_row in range(0, self.trainOnWayTable.rowCount()):
            j_train_name = self.trainOnWayTable.cellWidget(j_row, 1).currentText()
            j_wheelset_num_list = [int(self.vehicle_type_dict[i][1]/2) for i in self.train_dict[j_train_name]]
            wheelset_num_list = wheelset_num_list + j_wheelset_num_list
            j_veh_num = len(self.train_dict[j_train_name])
            veh_num_list.append(j_veh_num)
        for i_plot in range(0, len(self.time_hist_plot_list)):
            if self.timeHistPlotTable.cellWidget(i_plot, 5).checkState() != 2:
                continue
            if self.time_hist_plot_list[i_plot][9][0] == 2:
                i_legend = self.time_hist_plot_list[i_plot][9][1]
            else:
                i_legend = '-'.join([self.timeHistPlotTable.item(i_plot, 2).text(),
                                     self.timeHistPlotTable.item(i_plot, 3).text(),
                                     self.timeHistPlotTable.item(i_plot, 1).text()])
            legends.append(i_legend)
            i_style_selected = line_styles[self.time_hist_plot_list[i_plot][6]]
            line_styles_selected.append(i_style_selected)
            i_color_selected = colors[self.time_hist_plot_list[i_plot][7]]
            colors_selected.append(i_color_selected)
            i_speed_switch = self.time_hist_plot_list[i_plot][0] + 1  # 这里的序号都保留了matlab中从1开始的习惯
            i_unit = self.time_hist_plot_list[i_plot][2] + 1
            i_sub_unit = self.time_hist_plot_list[i_plot][3] + 1
            i_response_position = self.time_hist_plot_list[i_plot][5] + 1
            i_response = self.time_hist_plot_list[i_plot][4] + 1
            if self.time_hist_plot_list[i_plot][1] == '结构':
                bin_file = 'Res_BridgeResponseBulkDate_disacc.bin'
                i_concerned = 12*(i_unit-1) + i_response
                if i_response in [1, 3, 5]:
                    i_response_type = 1
                elif i_response in [2, 4, 6]:
                    i_response_type = 2
                elif i_response in [7, 9, 11]:
                    i_response_type = 3
                elif i_response in [8, 10, 12]:
                    i_response_type = 4
            elif i_response in range(1, 13):  # 车辆响应分散于多个文件
                #第一大类车辆响应：需要考虑每辆车的轮对数
                # 第几列的第几辆->bin中的第几辆->bin中的第几个轮对
                i_veh_in_vbc = sum(veh_num_list[0:i_unit-1]) + i_sub_unit  # bin文件中的unit序号(也就是所有参与计算的第几个veh)，从1开始
                i_speed = self.train_on_way_data[i_unit-1][i_speed_switch][0]
                i_wheelset_in_vbc = sum(wheelset_num_list[0:i_veh_in_vbc-1]) + i_response_position  # bin文件中的轮对序号(也就是所有参与计算的第几个轮对)，从1开始
                if i_response in [1, 2]:
                    bin_file = 'Res_ReductionRation_Vehicles.bin'
                    if i_response == 1:  # 减载率
                        i_concerned = 2 * (i_wheelset_in_vbc-1) + 1
                        i_response_type = 5
                    else:  # 轮轨竖向力
                        i_concerned = 2 * (i_wheelset_in_vbc-1) + 2
                        i_response_type = 7
                if i_response in [3, 4]:
                    bin_file = 'Res_DerailmentFactor_Vehicles.bin'
                    if i_response == 3:
                        i_concerned = 2 * (i_wheelset_in_vbc-1) + 1
                        i_response_type = 6
                    else:
                        i_concerned = 2 * (i_wheelset_in_vbc-1) + 2
                        i_response_type = 7
                if i_response in range(5, 11):
                    bin_file = 'Res_WheelsetirregDisVehilces.bin'
                    if i_response == 5:
                        i_concerned = 6 * (i_wheelset_in_vbc-1) + 1
                        i_response_type = 1
                    elif i_response == 6:
                        i_concerned = 6 * (i_wheelset_in_vbc-1) + 2
                        i_response_type = 1
                    elif i_response == 7:
                        i_concerned = 6 * (i_wheelset_in_vbc-1) + 3
                        i_response_type = 3
                    elif i_response == 8:
                        i_concerned = 6 * (i_wheelset_in_vbc-1) + 4
                        i_response_type = 1
                    elif i_response == 9:
                        i_concerned = 6 * (i_wheelset_in_vbc-1) + 5
                        i_response_type = 1
                    elif i_response == 10:
                        i_concerned = 6 * (i_wheelset_in_vbc-1) + 6
                        i_response_type = 3
                if i_response in [11, 12]:  # 车辆响应分散于多个文件，第二大类车辆响应：不需要考虑每辆车的轮对数
                    bin_file = 'Res_AccResults_Vehicles.bin'
                    i_speed = self.train_on_way_data[i_unit - 1][i_speed_switch][0]
                    i_response_type = 2
                    if i_response == 11:  # 横向加速度(z)
                        if i_response_position == 1:  # 车体前部
                            i_concerned = 6 * (i_veh_in_vbc-1) + 4
                        else:
                            i_concerned = 6 * (i_veh_in_vbc-1) + 6
                    else:  # 横向加速度(y)
                        if i_response_position == 1:  # 车体前部
                            i_concerned = 6 * (i_veh_in_vbc-1) + 1
                        else:
                            i_concerned = 6 * (i_veh_in_vbc-1) + 3
            try:
                f_test = open((path_verify(self.save_path) + bin_file), 'r')
                f_test.close()
                i_data_temp, i_dt, speed_count = vbc_data_read(path=self.save_path, file=bin_file,
                                                               i_concerned=i_concerned, i_speed_switch=i_speed_switch)
            except:
                QMessageBox.warning(self, '警告', '该项目的结果文件不完整。\n若要查看已计算部分的结果，请将图线的行车工况调至较低速度档位后重试。')
                return
            i_data = i_data_temp[0][0]
            if self.time_hist_plot_list[i_plot][8][0] == 1:
                fn = self.time_hist_plot_list[i_plot][8][1:3]
                i_data = vbc_filter(y_raw=i_data, fn=fn, dt=i_dt)
            elif self.time_hist_plot_list[i_plot][8][0] == 2:
                window_length = self.time_hist_plot_list[i_plot][8][1]
                i_data = moving_average(y_raw=i_data, dt=i_dt, speed=i_speed, window_length=window_length)

            plot_data_list.append(i_data)
            dt_list.append(i_dt)
            response_type_list.append(i_response_type)
        if not plot_data_list:
            QMessageBox.warning(self, '警告', '请至少选择一条已定义的图线。')
            return
        # 2.检查选中的数据是否适合绘制于同一张图
        if len(set(response_type_list)) > 1:
            QMessageBox.warning(self, '警告', '不支持将不同类型的指标绘制于同一张图。')
            return
        else:
            response_type = response_type_list[0]
        # 3.绘图
        plot_x = []
        for i_plot in range(0, len(plot_data_list)):
            i_x = [i*dt_list[i_plot] for i in range(0, len(plot_data_list[i_plot]))]
            plot_x.append(i_x)
        time_hist_plot_dia = GuideTimeHistPlot(x=plot_x, y=plot_data_list, dt_list=dt_list,
                                               legends=legends, response_type=response_type,
                                               line_styles=line_styles_selected, colors=colors_selected)
        time_hist_plot_dia.exec_()

    def save_attend_post_table_list_to_list(self):
        self.post_table_dir_list = []
        if self.postTableFatherPathText.text():
            for i_row in range(self.attendSonPathList.count()):
                i_full_path = path_verify(self.postTableFatherPathText.text()) + self.attendSonPathList.item(i_row).text()
                self.post_table_dir_list.append(i_full_path)


    def save_attend_post_node_list_to_list(self):
        def get_id_before_colon(text):
            text_splited = text.split(':')
            return int(text_splited[0])
        self.attend_post_node_list = [get_id_before_colon(self.attendPostNodeList.item(i).text())
                                      for i in range(self.attendPostNodeList.count())]

    def on_post_table_range_changed(self):
        if self.postTableRangeSel.currentIndex() == 0:
            flag = False
            result_file_names = {'Res_ReductionRation_Vehicles.bin', 'Res_AccResults_Vehicles.bin',
                                 'Res_DerailmentFactor_Vehicles.bin', 'Res_WheelsetirregDisVehilces.bin',
                                 'Res_BridgeResponseBulkDate_disacc.bin'}
            try:
                i_file_names = set([i.name for i in os.scandir(self.save_path)])
                if result_file_names.issubset(i_file_names):
                    self.post_table_dir_list = [self.save_path]
                else:
                    self.post_table_dir_list = []
            except:
                self.post_table_dir_list = []
        else:
            flag = True
            self.save_attend_post_table_list_to_list()
        self.postTableFatherPathText.setEnabled(flag)
        self.postTableFatherPathBrowse.setEnabled(flag)
        self.foundSonPathList.setEnabled(flag)
        self.attendSonPathList.setEnabled(flag)
        self.addAttend.setEnabled(flag)
        self.removeAttend.setEnabled(flag)
        self.attendUp.setEnabled(flag)
        self.attendDown.setEnabled(flag)
        self.init_post_node_list_widget()

    def post_father_path_browse(self):
        father_path = QFileDialog.getExistingDirectory(self, '选择子项目所在的上级目录', self.browse_path)
        if father_path:
            self.browse_path = father_path
        self.postTableFatherPathText.setText(path_verify(father_path))
        subfolders = [i_folder for i_folder in os.scandir(father_path) if i_folder.is_dir()]
        subfolders_names = [i.name for i in subfolders]
        subfolders_paths = [i.path for i in subfolders]
        # 逐个文件夹扫描内部结果文件是否齐全
        result_file_names = {'Res_ReductionRation_Vehicles.bin', 'Res_AccResults_Vehicles.bin',
                             'Res_DerailmentFactor_Vehicles.bin', 'Res_WheelsetirregDisVehilces.bin',
                             'Res_BridgeResponseBulkDate_disacc.bin'}
        valid_folder = []
        error_folder = []
        error_flag = False
        for i_folder in subfolders:
            if i_folder.name == 'System Volume Information':
                continue
            try:
                i_file_names = set([i.name for i in os.scandir(i_folder.path)])
                if result_file_names.issubset(i_file_names):
                    valid_folder.append(i_folder)
            except:
                error_folder.append(i_folder)
                error_flag = True
        self.attendSonPathList.clear()
        self.foundSonPathList.clear()
        self.save_attend_post_table_list_to_list()
        self.foundSonPathList.addItems([i.name for i in valid_folder])
        if error_flag:
            QMessageBox.warning(self, '警告', '读取以下子目录时出错：\n%s' % '\n'.join([i.name for i in error_folder]))

    def attend_post_add(self):
        if self.foundSonPathList.currentRow() != -1:
            self.attendSonPathList.addItem(self.foundSonPathList.currentItem().text())
            self.foundSonPathList.takeItem(self.foundSonPathList.currentRow())
        self.save_attend_post_table_list_to_list()
        self.init_post_node_list_widget()

    def attend_post_remove(self):
        if self.attendSonPathList.currentRow() != -1:
            self.foundSonPathList.addItem(self.attendSonPathList.currentItem().text())
            self.attendSonPathList.takeItem(self.attendSonPathList.currentRow())
        self.save_attend_post_table_list_to_list()
        self.init_post_node_list_widget()

    def attend_post_add_all(self):
        while self.foundSonPathList.count() != 0:
            self.attendSonPathList.addItem(self.foundSonPathList.item(0).text())
            self.foundSonPathList.takeItem(0)
        self.save_attend_post_table_list_to_list()
        self.init_post_node_list_widget()

    def attned_post_remove_all(self):
        while self.attendSonPathList.count() != 0:
            self.foundSonPathList.addItem(self.attendSonPathList.item(0).text())
            self.attendSonPathList.takeItem(0)
        self.save_attend_post_table_list_to_list()
        self.init_post_node_list_widget()

    def attend_post_up(self):
        list_widget_order_up(self.attendSonPathList)
        self.save_attend_post_table_list_to_list()

    def attend_post_down(self):
        list_widget_order_down(self.attendSonPathList)
        self.save_attend_post_table_list_to_list()

    def init_post_node_list_widget(self):
        self.definedPostNodeList.clear()
        self.defined_post_node_list = []
        self.attendPostNodeList.clear()
        self.attend_post_node_list = []
        if self.post_table_dir_list:
            baseline_path = self.post_table_dir_list[0]
            msb = SubBri()
            try:
                msb.read_dat(baseline_path)
            except:
                QMessageBox.warning(self, '警告', '读取后处理结点列表失败\n%s中Modal_Substructure_Bridge.dat文件有误。' % baseline_path)
                return
            post_node_id_list = msb.id_post_nodes
            self.post_node_name_list = msb.name_post_nodes
            del msb
            self.defined_post_node_list = post_node_id_list
            self.baseline_post_node_dict_for_table = {}
            post_node_item_list = []
            for i_node in range(0, len(post_node_id_list)):
                self.baseline_post_node_dict_for_table[post_node_id_list[i_node]] = self.post_node_name_list[i_node]
                post_node_item_list.append('%d:%s' % (post_node_id_list[i_node], self.post_node_name_list[i_node]))
            self.definedPostNodeList.addItems(post_node_item_list)

    def attend_post_node_add(self):
        if self.definedPostNodeList.currentRow() != -1:
            self.attendPostNodeList.addItem(self.definedPostNodeList.currentItem().text())
            self.definedPostNodeList.takeItem(self.definedPostNodeList.currentRow())
        self.save_attend_post_node_list_to_list()

    def attend_post_node_remove(self):
        if self.attendPostNodeList.currentRow() != -1:
            self.definedPostNodeList.addItem(self.attendPostNodeList.currentItem().text())
            self.attendPostNodeList.takeItem(self.attendPostNodeList.currentRow())
        self.save_attend_post_node_list_to_list()

    def attend_post_node_add_all(self):
        while self.definedPostNodeList.count() != 0:
            self.attendPostNodeList.addItem(self.definedPostNodeList.item(0).text())
            self.definedPostNodeList.takeItem(0)
        self.save_attend_post_node_list_to_list()

    def attend_post_node_remove_all(self):
        while self.attendPostNodeList.count() != 0:
            self.definedPostNodeList.addItem(self.attendPostNodeList.item(0).text())
            self.attendPostNodeList.takeItem(0)
        self.save_attend_post_node_list_to_list()

    def attend_post_node_up(self):
        list_widget_order_up(self.attendPostNodeList)
        self.save_attend_post_node_list_to_list()

    def attend_post_node_down(self):
        list_widget_order_down(self.attendPostNodeList)
        self.save_attend_post_node_list_to_list()

    def on_veh_acc_proc_changed(self):
        if self.vehAccDataProcSel.currentIndex() == 1:
            self.vehAccMinFreqEnter.setEnabled(True)
            self.vehAccMaxFreqEnter.setEnabled(True)
        else:
            self.vehAccMinFreqEnter.setEnabled(False)
            self.vehAccMaxFreqEnter.setEnabled(False)

    def on_bri_acc_proc_changed(self):
        if self.briAccDataProcSel.currentIndex() == 1:
            self.briAccMinFreqEnter.setEnabled(True)
            self.briAccMaxFreqEnter.setEnabled(True)
        else:
            self.briAccMinFreqEnter.setEnabled(False)
            self.briAccMaxFreqEnter.setEnabled(False)

    def on_wheel_force_proc_changed(self):
        if self.wheelForceDataProcSel.currentIndex() == 1:
            self.wheelForceMinFreqEnter.setEnabled(True)
            self.wheelForceMaxFreqEnter.setEnabled(True)
        else:
            self.wheelForceMinFreqEnter.setEnabled(False)
            self.wheelForceMaxFreqEnter.setEnabled(False)

    # @profile(precision=4, stream=open('memory_profiler.log', 'w+'))
    def gen_post_table_action(self):
        if not self.post_table_dir_list:
            QMessageBox.warning(self, '警告', '选中的子项目文件夹无效。')
            return

        speed_count_list = []
        for h_path in self.post_table_dir_list:
            veh_org = VehOrg()
            try:
                veh_org.read_dat(h_path)
                h_veh_org_matrix = veh_org.org_matrix_verified
                del veh_org
            except:
                QMessageBox.warning(self, '警告', '%sVehicleOrganization.dat文件不存在或存在错误，操作已取消。' % h_path)
                return
            # h_speed_count = len(h_veh_org_matrix[0])-1
            # speed_count_list.append(h_speed_count)
            # if len(set(speed_count_list)) > 1:
            #     QMessageBox(self, '警告', '选取的各个子项目中速度档数不一致，无法一同汇总，\n操作已取消。')
            #     return

        # 根据窗口控件状态，确定信号处理方法
        veh_acc_filt_range = [self.vehAccMinFreqEnter.value(), self.vehAccMaxFreqEnter.value()]  # 不管是否用到，都提前定义这个变量，防止出现未定义的报错
        if self.vehAccDataProcSel.currentIndex() == 0:
            veh_acc_method = 'max'
        else:
            veh_acc_method = 'filt_max'
            if veh_acc_filt_range[0] == veh_acc_filt_range[1]:
                QMessageBox.warning(self, '警告', '车辆加速度滤波范围无效。')
                return
        bri_acc_filt_range = [self.briAccMinFreqEnter.value(), self.briAccMaxFreqEnter.value()]
        if self.briAccDataProcSel.currentIndex() == 0:
            bri_acc_method = 'max'
        else:
            bri_acc_method = 'filt_max'
            if bri_acc_filt_range[0] == bri_acc_filt_range[1]:
                QMessageBox.warning(self, '警告', '结构加速度滤波范围无效。')
                return
        wheel_force_filt_range = [self.wheelForceMinFreqEnter.value(), self.wheelForceMaxFreqEnter.value()]
        if self.wheelForceDataProcSel.currentIndex() == 0:
            wheel_force_method = 'max'
        elif self.wheelForceDataProcSel.currentIndex() == 1:
            wheel_force_method = 'filt_max'
            if wheel_force_filt_range[0] == wheel_force_filt_range[1]:
                QMessageBox.warning(self, '警告', '轮轨力指标滤波范围无效。')
                return
        else:
            wheel_force_method = 'GB5599-2019'

        # 用于给车型分类
        # 更新dict的函数
        def update_h_max_result_dict(sub_dict_obj, veh_type, result_to_compare):
            # 对于每个工况：指定用于比较的指标dict、车型、新结果，与字典中对应车型的既有结果对比，取较大的保存
            # 对于总体：将每个工况dict的结果排列进总体的dict
            if veh_type in sub_dict_obj.keys():
                result_to_save = [max(result_to_compare[i], sub_dict_obj[veh_type][i])
                                  for i in range(0, len(result_to_compare))]
                sub_dict_obj[veh_type] = result_to_save
            else:
                sub_dict_obj[veh_type] = result_to_compare

        def update_total_max_result_dict(total_dict_obj, h_dict_obj):
            # 每个h工况计算结束后执行此函数，将h工况算得的h_dict汇总入total_dict
            veh_list_to_consider = set(total_dict_obj.keys()).union(h_dict_obj.keys())  # 每一步h循环到这里时，total_dict还停留在上一部，而这一步循环可能需要引入新的veh_type
            for x_type in veh_list_to_consider:
                # (1)total_dict数据格式预处理：如果这一步循环引入了新的车型，那么说明之前已经循环过的工况中没有这个车型，就需要给之前的工况补上空列表占位
                if x_type not in total_dict_obj.keys():
                    if len(total_dict_obj):
                        total_dict_obj[x_type] = [[]] * (len(list(total_dict_obj.values())[0])-1)  # -1: 其中一个位置是下面要塞数据的位置，塞数据的时候会append好，这里不能重复开位子
                    else:  # 如果total_dict还是空的，就说明循环刚开始，就不必补空list了，但要把x_type键值的最外层空位留好
                        total_dict_obj[x_type] = []
                # (2)往total_dict里面塞数据
                if x_type in h_dict_obj.keys():
                    total_dict_obj[x_type].append(h_dict_obj[x_type])
                else:
                    total_dict_obj[x_type].append([])

        # 减载率文件
        max_reduction_ration_dict_by_veh_type = {}  # {车型1id: [[车型1工况1速度1, 车型1工况1速度2...], [车型1工况2速度1, 车型1工况2速度2...]]}，未参与的工况留空list
        max_vertical_wheel_force_dict_by_veh_type = {}  # {车型1id: [[车型1工况1速度1, 车型1工况1速度2...], [车型1工况2速度1, 车型1工况2速度2...]]}
        # 脱轨系数文件
        max_derail_factor_dict_by_veh_type = {}
        max_horizontal_wheel_force_dict_by_veh_type = {}
        # 轮下轨道位移、轮轨相对位移文件
        max_dynamic_irr_vertical_dict_by_veh_type = {}  # 同上
        max_dynamic_irr_horizontal_dict_by_veh_type = {}
        max_dynamic_irr_yaw_dict_by_veh_type = {}
        max_wheel_rail_dis_vertical_dict_by_veh_type = {}
        max_wheel_rail_dis_horizontal_dict_by_veh_type = {}
        max_wheel_rail_dis_yaw_dict_by_veh_type = {}
        # 车体加速度文件 & sperling
        max_veh_acc_vertical_front_dict_by_veh_type = {}  # 同上
        max_veh_acc_vertical_rear_dict_by_veh_type = {}
        max_veh_acc_horizontal_front_dict_by_veh_type = {}
        max_veh_acc_horizontal_rear_dict_by_veh_type = {}
        veh_sperling_vertical_front_dict_by_veh_type = {}
        veh_sperling_vertical_rear_dict_by_veh_type = {}
        veh_sperling_horizontal_front_dict_by_veh_type = {}
        veh_sperling_horizontal_rear_dict_by_veh_type = {}
        # 桥梁响应文件
        # [[[工况1结点1速度1, 工况1结点1速度2...], [工况1结点2速度1, 工况1结点2速度2...], ...],
        #  [[工况2结点1速度1, 工况2结点1速度2...], [工况2结点2速度1, 工况2结点2速度2...], ...],
        #  ...]
        max_bri_dx_list = []
        max_bri_dy_list = []
        max_bri_dz_list = []
        max_bri_rx_list = []
        max_bri_ry_list = []
        max_bri_rz_list = []
        max_bri_ax_list = []
        max_bri_ay_list = []
        max_bri_az_list = []
        max_bri_arx_list = []
        max_bri_ary_list = []
        max_bri_arz_list = []
        for h_path in self.post_table_dir_list:
            # 【车】
            # 总体思路：对每个子工况依次提取上道的每辆车的各个指标的最大值(list)->把各个车型的汇总表作出(dict)->再融合车类汇总表获得整体汇总表
            # 预处理：读取编组等信息
            try:
                msv = SubVeh()
                msv.read_dat(h_path)
                h_vehicle_type_dict = msv.vehicle_type_dict  # 永远从窗口安装目录的dat中动态更新，不理睬项目工况文件{vbc代号: 名称}
                del msv
            except:
                QMessageBox.warning(self, '警告', '%sModal_Substructure_Bridge.dat文件不存在或存在错误，操作已取消。' % h_path)
                return
            veh_org = VehOrg()
            veh_org.read_dat(h_path)
            h_veh_matrix = veh_org.veh_matrix_verified
            h_train_name_vec = veh_org.train_name_vec
            h_veh_num_each_train = veh_org.veh_num_each_train
            h_veh_org_matrix = veh_org.org_matrix_verified
            h_train_num_on_way = veh_org.train_num_on_way
            del veh_org
            h_vehicle_list = []
            h_veh_num_list = []
            wheelset_num_list = []
            if_locomotice_list = []
            train_id_in_vbc_res_of_each_veh_of_each_veh = []  # [第1辆车所属上道车列id, 第2辆车所属上道车列id, ...]，id从1开始
            for j_train in range(0, h_train_num_on_way):
                j_train_ow_id_in_vbc = int(h_veh_org_matrix[j_train][0][0])
                j_train_name = h_train_name_vec[j_train_ow_id_in_vbc-1]
                j_vehicle_list = h_veh_matrix[j_train_ow_id_in_vbc-1]
                h_vehicle_list = h_vehicle_list + j_vehicle_list
                h_veh_num_list.append(len(j_vehicle_list))
                j_wheelset_num_list = [int(h_vehicle_type_dict[i][1]/2) for i in j_vehicle_list]
                wheelset_num_list = wheelset_num_list + j_wheelset_num_list
                j_if_locomotive_list = [h_vehicle_type_dict[i][2] for i in j_vehicle_list]
                if_locomotice_list = if_locomotice_list + j_if_locomotive_list
                # vbc结果里的第几辆车，从1开始(针对corner case：定义了2列车，但只上道了第2列，这样结果文件里就只有1列。
                # 如果不引入这个变量，后面读取结果就会读成第2列车，从而越界)
                j_train_id_in_vbc_res = j_train + 1
                train_id_in_vbc_res_of_each_veh_of_each_veh += ([j_train_id_in_vbc_res]*len(j_vehicle_list))

            # 减载率文件
            h_max_reduction_ration_dict_by_veh_type = {}  # {车型id1: [车型1速度1, 车型1速度2...]}
            h_max_vertical_wheel_force_dict_by_veh_type = {}  # {车型id1: [车型1速度1, 车型1速度2...]}
            # 减载率文件
            bin_file_reduct = 'Res_ReductionRation_Vehicles.bin'
            concerned_list_reduct = list(range(1, 2*sum(wheelset_num_list)+1, 2))\
                                    + list(range(2, 2*sum(wheelset_num_list)+1, 2))  # 先读所有轴的减载率，再读所有轴的动轴重
            # data_reduct每个速度档的前半段(0-sum(wheelset_list)-1)是减载率，后半段是动轴重
            data_reduct, dt, speed_count = vbc_data_read(path=h_path, file=bin_file_reduct, i_concerned=concerned_list_reduct)
            # 减载率文件
            h_max_reduction_ration_list = []  # [[第1辆车速度1, 第1辆车速度2, 第1辆车速度3...], [第2辆车速度1, 第2辆车速度2...]]
            h_max_vertical_wheel_force_list = []  # 同上
            for k_veh in range(0, len(h_vehicle_list)):  # k_veh+1相当于show_plot函数中的i_veh_in_vbc
                train_order_of_k_veh = train_id_in_vbc_res_of_each_veh_of_each_veh[k_veh]  # 当前这第k辆车属于第几列车，用于读取这列车速度
                k_wheelset_num = wheelset_num_list[k_veh]
                k_wheelset_range_in_vbc = [sum(wheelset_num_list[0:k_veh])+l_wheelset
                                           for l_wheelset in range(0, k_wheelset_num)]  # 第k辆车在bin文件中的轮对序号范围(也就是所有参与计算的第几个轮对)，从0开始
                # 减载率文件
                k_max_reduction_ration_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车所有轮对的最大减载率
                k_max_vertical_wheel_force_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大动轴重
                for l_wheelset in k_wheelset_range_in_vbc:
                    # 减载率文件
                    l_max_reduction_ration = [get_data_for_table(data_reduct[m][l_wheelset],
                                                                 wheel_force_method, dt, wheel_force_filt_range,
                                                                 h_veh_org_matrix[train_order_of_k_veh-1][m+1][0],
                                                                 abs_for_max=False)
                                              for m in range(len(data_reduct))]  # 一维，各速度档该轮对最大减载率
                    [k_max_reduction_ration_list[i].append(l_max_reduction_ration[i]) for i in range(speed_count)]
                    l_max_vertical_wheel_force_list = [get_data_for_table(data_reduct[m][l_wheelset+sum(wheelset_num_list)],
                                                                          wheel_force_method, dt, wheel_force_filt_range,
                                                                          h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                                       for m in range(len(data_reduct))]
                    [k_max_vertical_wheel_force_list[i].append(l_max_vertical_wheel_force_list[i]) for i in range(speed_count)]
                # 减载率文件
                k_max_reduction_ration = [max(i) for i in k_max_reduction_ration_list]  # 用于存储各速度档下第k辆车的【最大减载率的】最大值
                k_max_vertical_wheel_force = [max(i) for i in k_max_vertical_wheel_force_list]  # 用于存储各速度档下第k辆车的【最大动轴重的】最大值
                h_max_reduction_ration_list.append(k_max_reduction_ration)
                h_max_vertical_wheel_force_list.append(k_max_vertical_wheel_force)
                update_h_max_result_dict(h_max_reduction_ration_dict_by_veh_type,
                                       h_vehicle_list[k_veh], k_max_reduction_ration)
                update_h_max_result_dict(h_max_vertical_wheel_force_dict_by_veh_type,
                                       h_vehicle_list[k_veh], k_max_vertical_wheel_force)
            del data_reduct
            # 减载率文件
            update_total_max_result_dict(max_reduction_ration_dict_by_veh_type, h_max_reduction_ration_dict_by_veh_type)
            update_total_max_result_dict(max_vertical_wheel_force_dict_by_veh_type, h_max_vertical_wheel_force_dict_by_veh_type)

            # 脱轨系数文件
            h_max_derail_factor_dict_by_veh_type = {}
            h_max_horizontal_wheel_force_dict_by_veh_type = {}
            # 脱轨系数文件
            bin_file_derail = 'Res_DerailmentFactor_Vehicles.bin'
            concerned_list_derail = concerned_list_reduct  # 脱轨系数和减载率bin文件格式相同
            data_derail, dt, speed_count = vbc_data_read(path=h_path, file=bin_file_derail, i_concerned=concerned_list_derail)
            # 脱轨系数
            h_max_derail_factor_list = []
            h_max_horizontal_wheel_force_list = []
            for k_veh in range(0, len(h_vehicle_list)):  # k_veh+1相当于show_plot函数中的i_veh_in_vbc
                train_order_of_k_veh = train_id_in_vbc_res_of_each_veh_of_each_veh[k_veh]  # 当前这第k辆车属于第几列车，用于读取这列车速度
                k_wheelset_num = wheelset_num_list[k_veh]
                k_wheelset_range_in_vbc = [sum(wheelset_num_list[0:k_veh])+l_wheelset
                                           for l_wheelset in range(0, k_wheelset_num)]  # 第k辆车在bin文件中的轮对序号范围(也就是所有参与计算的第几个轮对)，从0开始
                # 脱轨系数文件
                k_max_derail_factor_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车所有轮对的最大脱轨系数
                k_max_horizontal_wheel_force_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大轮轨横向力
                for l_wheelset in k_wheelset_range_in_vbc:
                    # 脱轨系数文件
                    l_max_derail_factor = [get_data_for_table(data_derail[m][l_wheelset],
                                                              wheel_force_method, dt, wheel_force_filt_range,
                                                              h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                           for m in range(len(data_derail))]  # 一维，各速度档该轮对最大脱轨系数
                    [k_max_derail_factor_list[i].append(l_max_derail_factor[i]) for i in range(speed_count)]
                    l_max_horizontal_wheel_force_list = [get_data_for_table(data_derail[m][l_wheelset+sum(wheelset_num_list)],
                                                                            wheel_force_method, dt, wheel_force_filt_range,
                                                                            h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                                         for m in range(len(data_derail))]
                    [k_max_horizontal_wheel_force_list[i].append(l_max_horizontal_wheel_force_list[i]) for i in range(speed_count)]
                # 脱轨系数文件
                k_max_derail_factor = [max(i) for i in k_max_derail_factor_list]  # 用于存储各速度档下第k辆车的【最大脱轨系数的】最大值
                k_max_horizontal_wheel_force = [max(i) for i in k_max_horizontal_wheel_force_list]  # 用于存储各速度档下第k辆车的【最大横向轮轨力的】最大值
                h_max_derail_factor_list.append(k_max_derail_factor)
                h_max_horizontal_wheel_force_list.append(k_max_horizontal_wheel_force)
                update_h_max_result_dict(h_max_derail_factor_dict_by_veh_type,
                                       h_vehicle_list[k_veh], k_max_derail_factor)
                update_h_max_result_dict(h_max_horizontal_wheel_force_dict_by_veh_type,
                                       h_vehicle_list[k_veh], k_max_horizontal_wheel_force)
            del data_derail
            # 脱轨系数文件
            update_total_max_result_dict(max_derail_factor_dict_by_veh_type, h_max_derail_factor_dict_by_veh_type)
            update_total_max_result_dict(max_horizontal_wheel_force_dict_by_veh_type, h_max_horizontal_wheel_force_dict_by_veh_type)

            # 轮下轨道位移、轮轨相对位移文件
            h_max_dynamic_irr_vertical_dict_by_veh_type = {}  # 同上
            h_max_dynamic_irr_horizontal_dict_by_veh_type = {}
            h_max_dynamic_irr_yaw_dict_by_veh_type = {}
            h_max_wheel_rail_dis_vertical_dict_by_veh_type = {}
            h_max_wheel_rail_dis_horizontal_dict_by_veh_type = {}
            h_max_wheel_rail_dis_yaw_dict_by_veh_type = {}
            # 轮下轨道位移、轮轨相对位移文件
            bin_file_wheelset = 'Res_WheelsetirregDisVehilces.bin'
            concerned_list_wheelset = list(range(1, 6*sum(wheelset_num_list)+1, 6))\
                                      + list(range(2, 6*sum(wheelset_num_list)+1, 6))\
                                      + list(range(3, 6*sum(wheelset_num_list)+1, 6))\
                                      + list(range(4, 6*sum(wheelset_num_list)+1, 6))\
                                      + list(range(5, 6*sum(wheelset_num_list)+1, 6))\
                                      + list(range(6, 6*sum(wheelset_num_list)+1, 6))  # 依次读取所有轴的6项指标：动态不平顺(3项，竖、横、摇)，轮轨相对位移(3项，竖、横、摇)
            data_wheelset, dt, speed_count = vbc_data_read(path=h_path, file=bin_file_wheelset, i_concerned=concerned_list_wheelset)
            # 轮下轨道位移、轮轨相对位移文件
            h_max_dynamic_irr_vertical_list = []  # 同上
            h_max_dynamic_irr_horizontal_list = []
            h_max_dynamic_irr_yaw_list = []
            h_max_wheel_rail_dis_vertical_list = []
            h_max_wheel_rail_dis_horizontal_list = []
            h_max_wheel_rail_dis_yaw_list = []
            for k_veh in range(0, len(h_vehicle_list)):  # k_veh+1相当于show_plot函数中的i_veh_in_vbc
                train_order_of_k_veh = train_id_in_vbc_res_of_each_veh_of_each_veh[k_veh]  # 当前这第k辆车属于第几列车，用于读取这列车速度
                k_if_locomotive = if_locomotice_list[k_veh]
                k_wheelset_num = wheelset_num_list[k_veh]
                k_wheelset_range_in_vbc = [sum(wheelset_num_list[0:k_veh])+l_wheelset
                                           for l_wheelset in range(0, k_wheelset_num)]  # 第k辆车在bin文件中的轮对序号范围(也就是所有参与计算的第几个轮对)，从0开始
                # 轮下轨道位移、轮轨相对位移文件
                k_max_dynamic_irr_vertical_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大动态竖向不平顺
                k_max_dynamic_irr_horizontal_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大动态横向不平顺
                k_max_dynamic_irr_yaw_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大动态摇头不平顺
                k_max_wheel_rail_dis_vertical_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大轮轨竖向相对位移
                k_max_wheel_rail_dis_horizontal_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大轮轨横向相对位移
                k_max_wheel_rail_dis_yaw_list = [[] for i in range(speed_count)]  # 用于存储各速度档下第k辆车各轮对的最大轮轨摇头相对位移
                for l_wheelset in k_wheelset_range_in_vbc:
                    # 轮下轨道位移、轮轨相对位移文件
                    l_max_dynamic_irr_vertical_list = [max(m_data[l_wheelset]) for m_data in data_wheelset]  # 一维，各速度档该轮对最大动态竖向不平顺
                    [k_max_dynamic_irr_vertical_list[i].append(l_max_dynamic_irr_vertical_list[i]) for i in range(speed_count)]
                    l_max_dynamic_irr_horizontal_list = [max(m_data[l_wheelset+sum(wheelset_num_list)]) for m_data in data_wheelset]  # 一维，各速度档该轮对最大动态横向不平顺
                    [k_max_dynamic_irr_horizontal_list[i].append(l_max_dynamic_irr_horizontal_list[i]) for i in range(speed_count)]
                    l_max_dynamic_irr_yaw_list = [max(m_data[l_wheelset+sum(wheelset_num_list)*2]) for m_data in data_wheelset]  # 一维，各速度档该轮对最大动态摇头不平顺
                    [k_max_dynamic_irr_yaw_list[i].append(l_max_dynamic_irr_yaw_list[i]) for i in range(speed_count)]
                    l_max_wheel_rail_dis_vertical_list = [max(m_data[l_wheelset+sum(wheelset_num_list)*3]) for m_data in data_wheelset]  # 一维，各速度档该轮对最大轮轨竖向相对位移
                    [k_max_wheel_rail_dis_vertical_list[i].append(l_max_wheel_rail_dis_vertical_list[i]) for i in range(speed_count)]
                    l_max_wheel_rail_dis_horizontal_list = [max(m_data[l_wheelset+sum(wheelset_num_list)*4]) for m_data in data_wheelset]  # 一维，各速度档该轮对最大轮轨横向相对位移
                    [k_max_wheel_rail_dis_horizontal_list[i].append(l_max_wheel_rail_dis_horizontal_list[i]) for i in range(speed_count)]
                    l_max_wheel_rail_dis_yaw_list = [max(m_data[l_wheelset+sum(wheelset_num_list)*5]) for m_data in data_wheelset]  # 一维，各速度档该轮对最大轮轨摇头相对位移
                    [k_max_wheel_rail_dis_yaw_list[i].append(l_max_wheel_rail_dis_yaw_list[i]) for i in range(speed_count)]
                # 轮下轨道位移、轮轨相对位移文件
                k_max_dynamic_irr_vertical = [max(i) for i in k_max_dynamic_irr_vertical_list]  # 用于存储各速度档下第k辆车的【最大动态竖向不平顺的】最大值
                k_max_dynamic_irr_horizontal = [max(i) for i in k_max_dynamic_irr_horizontal_list]  # 用于存储各速度档下第k辆车的【最大动态横向不平顺的】最大值
                k_max_dynamic_irr_yaw = [max(i) for i in k_max_dynamic_irr_yaw_list]  # 用于存储各速度档下第k辆车的【最大动态摇头不平顺的】最大值
                k_max_wheel_rail_dis_vertical = [max(i) for i in k_max_wheel_rail_dis_vertical_list]  # 用于存储各速度档下第k辆车的【最大轮轨竖向相对位移的】最大值
                k_max_wheel_rail_dis_horizontal = [max(i) for i in k_max_wheel_rail_dis_horizontal_list]  # 用于存储各速度档下第k辆车的【最大轮轨横向相对位移的】最大值
                k_max_wheel_rail_dis_yaw = [max(i) for i in k_max_wheel_rail_dis_yaw_list]  # 用于存储各速度档下第k辆车的【最大轮轨摇头相对位移的】最大值
                h_max_dynamic_irr_vertical_list.append(k_max_dynamic_irr_vertical)
                h_max_dynamic_irr_horizontal_list.append(k_max_dynamic_irr_horizontal)
                h_max_dynamic_irr_yaw_list.append(k_max_dynamic_irr_yaw)
                h_max_wheel_rail_dis_vertical_list.append(k_max_wheel_rail_dis_vertical)
                h_max_wheel_rail_dis_horizontal_list.append(k_max_wheel_rail_dis_horizontal)
                h_max_wheel_rail_dis_yaw_list.append(k_max_wheel_rail_dis_yaw)
                update_h_max_result_dict(h_max_dynamic_irr_vertical_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_dynamic_irr_vertical)
                update_h_max_result_dict(h_max_dynamic_irr_horizontal_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_dynamic_irr_horizontal)
                update_h_max_result_dict(h_max_dynamic_irr_yaw_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_dynamic_irr_yaw)
                update_h_max_result_dict(h_max_wheel_rail_dis_vertical_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_wheel_rail_dis_vertical)
                update_h_max_result_dict(h_max_wheel_rail_dis_horizontal_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_wheel_rail_dis_horizontal)
                update_h_max_result_dict(h_max_wheel_rail_dis_yaw_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_wheel_rail_dis_yaw)
            del data_wheelset
            # 轮下轨道位移、轮轨相对位移文件
            update_total_max_result_dict(max_dynamic_irr_vertical_dict_by_veh_type, h_max_dynamic_irr_vertical_dict_by_veh_type)
            update_total_max_result_dict(max_dynamic_irr_horizontal_dict_by_veh_type, h_max_dynamic_irr_horizontal_dict_by_veh_type)
            update_total_max_result_dict(max_dynamic_irr_yaw_dict_by_veh_type, h_max_dynamic_irr_yaw_dict_by_veh_type)
            update_total_max_result_dict(max_wheel_rail_dis_vertical_dict_by_veh_type, h_max_wheel_rail_dis_vertical_dict_by_veh_type)
            update_total_max_result_dict(max_wheel_rail_dis_horizontal_dict_by_veh_type, h_max_wheel_rail_dis_horizontal_dict_by_veh_type)
            update_total_max_result_dict(max_wheel_rail_dis_yaw_dict_by_veh_type, h_max_wheel_rail_dis_yaw_dict_by_veh_type)

            # 车体加速度文件 & sperling
            h_max_veh_acc_vertical_front_dict_by_veh_type = {}  # 同上
            h_max_veh_acc_vertical_rear_dict_by_veh_type = {}
            h_max_veh_acc_horizontal_front_dict_by_veh_type = {}
            h_max_veh_acc_horizontal_rear_dict_by_veh_type = {}
            h_veh_sperling_vertical_front_dict_by_veh_type = {}  # 同上
            h_veh_sperling_vertical_rear_dict_by_veh_type = {}
            h_veh_sperling_horizontal_front_dict_by_veh_type = {}
            h_veh_sperling_horizontal_rear_dict_by_veh_type = {}
            # 车体加速度文件
            bin_file_veh_acc = 'Res_AccResults_Vehicles.bin'
            concerned_list_veh_acc = list(range(1, 6*sum(h_veh_num_list)+1, 6))\
                                     + list(range(3, 6*sum(h_veh_num_list)+1, 6))\
                                     + list(range(4, 6*sum(h_veh_num_list)+1, 6))\
                                     + list(range(6, 6*sum(h_veh_num_list)+1, 6))  # 依次读取所有车体的4项指标：竖acc前，竖acc后，横acc前，横acc后
            data_veh_acc, dt, speed_count = vbc_data_read(path=h_path, file=bin_file_veh_acc, i_concerned=concerned_list_veh_acc)
            # 车体加速度文件 & sperling
            h_max_veh_acc_vertical_front_list = []  # 同上
            h_max_veh_acc_vertical_rear_list = []
            h_max_veh_acc_horizontal_front_list = []
            h_max_veh_acc_horizontal_rear_list = []
            h_veh_sperling_vertical_front_list = []
            h_veh_sperling_vertical_rear_list = []
            h_veh_sperling_horizontal_front_list = []
            h_veh_sperling_horizontal_rear_list = []
            for k_veh in range(0, len(h_vehicle_list)):  # k_veh+1相当于show_plot函数中的i_veh_in_vbc
                train_order_of_k_veh = train_id_in_vbc_res_of_each_veh_of_each_veh[k_veh]  # 当前这第k辆车属于第几列车，用于读取这列车速度
                k_if_locomotive = if_locomotice_list[k_veh]
                # 车体加速度文件
                h_vehicle_count = sum(h_veh_num_list)
                k_max_veh_acc_vertical_front = [get_data_for_table(data_veh_acc[m][0*h_vehicle_count+k_veh],
                                                                   veh_acc_method, dt, veh_acc_filt_range,
                                                                   h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                                for m in range(len(data_veh_acc))]  # 一维，各速度档第k车厢前部竖向acc最大值
                k_max_veh_acc_vertical_rear = [get_data_for_table(data_veh_acc[m][1*h_vehicle_count+k_veh],
                                                                  veh_acc_method, dt, veh_acc_filt_range,
                                                                  h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                               for m in range(len(data_veh_acc))]
                k_max_veh_acc_horizontal_front = [get_data_for_table(data_veh_acc[m][2*h_vehicle_count+k_veh],
                                                                     veh_acc_method, dt, veh_acc_filt_range,
                                                                     h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                                  for m in range(len(data_veh_acc))]
                k_max_veh_acc_horizontal_rear = [get_data_for_table(data_veh_acc[m][3*h_vehicle_count+k_veh],
                                                                    veh_acc_method, dt, veh_acc_filt_range,
                                                                    h_veh_org_matrix[train_order_of_k_veh-1][m+1][0])
                                                 for m in range(len(data_veh_acc))]
                k_veh_sperling_vertical_front = [sperling(data_veh_acc[m][0 * h_vehicle_count + k_veh], True, dt)
                                                 for m in range(len(data_veh_acc))]  # 一维，各速度档第k车厢前部竖向sperling
                k_veh_sperling_vertical_rear = [sperling(data_veh_acc[m][1 * h_vehicle_count + k_veh], True, dt)
                                                for m in range(len(data_veh_acc))]
                k_veh_sperling_horizontal_front = [sperling(data_veh_acc[m][2 * h_vehicle_count + k_veh], False, dt)
                                                   for m in range(len(data_veh_acc))]
                k_veh_sperling_horizontal_rear = [sperling(data_veh_acc[m][3 * h_vehicle_count + k_veh], False, dt)
                                                  for m in range(len(data_veh_acc))]
                h_max_veh_acc_vertical_front_list.append(k_max_veh_acc_vertical_front)
                h_max_veh_acc_vertical_rear_list.append(k_max_veh_acc_vertical_rear)
                h_max_veh_acc_horizontal_front_list.append(k_max_veh_acc_horizontal_front)
                h_max_veh_acc_horizontal_rear_list.append(k_max_veh_acc_horizontal_rear)
                h_veh_sperling_vertical_front_list.append(k_veh_sperling_vertical_front)
                h_veh_sperling_vertical_rear_list.append(k_veh_sperling_vertical_rear)
                h_veh_sperling_horizontal_front_list.append(k_veh_sperling_horizontal_front)
                h_veh_sperling_horizontal_rear_list.append(k_veh_sperling_horizontal_rear)
                update_h_max_result_dict(h_max_veh_acc_vertical_front_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_veh_acc_vertical_front)
                update_h_max_result_dict(h_max_veh_acc_vertical_rear_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_veh_acc_vertical_rear)
                update_h_max_result_dict(h_max_veh_acc_horizontal_front_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_veh_acc_horizontal_front)
                update_h_max_result_dict(h_max_veh_acc_horizontal_rear_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_max_veh_acc_horizontal_rear)
                update_h_max_result_dict(h_veh_sperling_vertical_front_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_veh_sperling_vertical_front)
                update_h_max_result_dict(h_veh_sperling_vertical_rear_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_veh_sperling_vertical_rear)
                update_h_max_result_dict(h_veh_sperling_horizontal_front_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_veh_sperling_horizontal_front)
                update_h_max_result_dict(h_veh_sperling_horizontal_rear_dict_by_veh_type,
                                         h_vehicle_list[k_veh], k_veh_sperling_horizontal_rear)
            del data_veh_acc
            # 车体加速度文件 & sperling
            update_total_max_result_dict(max_veh_acc_vertical_front_dict_by_veh_type, h_max_veh_acc_vertical_front_dict_by_veh_type)
            update_total_max_result_dict(max_veh_acc_vertical_rear_dict_by_veh_type, h_max_veh_acc_vertical_rear_dict_by_veh_type)
            update_total_max_result_dict(max_veh_acc_horizontal_front_dict_by_veh_type, h_max_veh_acc_horizontal_front_dict_by_veh_type)
            update_total_max_result_dict(max_veh_acc_horizontal_rear_dict_by_veh_type, h_max_veh_acc_horizontal_rear_dict_by_veh_type)
            update_total_max_result_dict(veh_sperling_vertical_front_dict_by_veh_type, h_veh_sperling_vertical_front_dict_by_veh_type)
            update_total_max_result_dict(veh_sperling_vertical_rear_dict_by_veh_type, h_veh_sperling_vertical_rear_dict_by_veh_type)
            update_total_max_result_dict(veh_sperling_horizontal_front_dict_by_veh_type, h_veh_sperling_horizontal_front_dict_by_veh_type)
            update_total_max_result_dict(veh_sperling_horizontal_rear_dict_by_veh_type, h_veh_sperling_horizontal_rear_dict_by_veh_type)

            # 【桥】
            msb = SubBri()
            try:
                msb.read_dat(h_path)
            except:
                QMessageBox.warning(self, '警告', '%s中Modal_Substructure_Bridge.dat文件有误。' % h_path)
                return
            h_post_node_id_list = msb.id_post_nodes
            del msb
            h_post_node_count = len(h_post_node_id_list)
            # 检查后处理节点list中是否有此目录未定义的节点
            for k_node in self.attend_post_node_list:
                if k_node not in h_post_node_id_list:
                    QMessageBox.warning(self, '警告', '项目%s中未定义后处理结点%d。' % (h_path, k_node))
                    return
            bin_file_bri = 'Res_BridgeResponseBulkDate_disacc.bin'
            concerned_list_bri = list(range(1, 12*h_post_node_count+1, 12))\
                                 + list(range(3, 12*h_post_node_count+1, 12))\
                                 + list(range(5, 12*h_post_node_count+1, 12))\
                                 + list(range(7, 12*h_post_node_count+1, 12))\
                                 + list(range(9, 12*h_post_node_count+1, 12))\
                                 + list(range(11, 12*h_post_node_count+1, 12))\
                                 + list(range(2, 12*h_post_node_count+1, 12))\
                                 + list(range(4, 12*h_post_node_count+1, 12))\
                                 + list(range(6, 12*h_post_node_count+1, 12))\
                                 + list(range(8, 12*h_post_node_count+1, 12))\
                                 + list(range(10, 12*h_post_node_count+1, 12))\
                                 + list(range(12, 12*h_post_node_count+1, 12))
            data_bri, dt, speed_count = vbc_data_read(path=h_path, file=bin_file_bri, i_concerned=concerned_list_bri)
            h_max_bri_dx_list = []  # [[第1Post结点速度1, 第1post结点速度2...], [第2Post结点速度1, 第2post结点速度2...], ...]
            h_max_bri_dy_list = []
            h_max_bri_dz_list = []
            h_max_bri_rx_list = []
            h_max_bri_ry_list = []
            h_max_bri_rz_list = []
            h_max_bri_ax_list = []
            h_max_bri_ay_list = []
            h_max_bri_az_list = []
            h_max_bri_arx_list = []
            h_max_bri_ary_list = []
            h_max_bri_arz_list = []
            for k_node in self.attend_post_node_list:
                # l_max_reduction_ration = [get_data_for_table(data_bri[m][l_wheelset],
                #                                              bri_acc_method, dt, bri_acc_filt_range,
                #                                              h_speed_list[m])
                #                           for m in range(len(data_bri))]  # 一维，各速度档该轮对最大减载率
                k_idx_in_vbc = h_post_node_id_list.index(k_node) + 1  # 当前处理的后处理结点，在此项目中是第几个post，从1开始
                k_max_bri_dx = [get_data_for_table(data_bri[m][0*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]  # 一维，各速度档该结点的最大dx，下同
                k_max_bri_dy = [get_data_for_table(data_bri[m][1*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_dz = [get_data_for_table(data_bri[m][2*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_rx = [get_data_for_table(data_bri[m][3*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_ry = [get_data_for_table(data_bri[m][4*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_rz = [get_data_for_table(data_bri[m][5*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_ax = [get_data_for_table(data_bri[m][6*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]  # 一维，各速度档该结点的最大ax，下同
                k_max_bri_ay = [get_data_for_table(data_bri[m][7*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_az = [get_data_for_table(data_bri[m][8*h_post_node_count+(k_idx_in_vbc-1)],
                                                   bri_acc_method, dt, bri_acc_filt_range)
                                for m in range(len(data_bri))]
                k_max_bri_arx = [get_data_for_table(data_bri[m][9*h_post_node_count+(k_idx_in_vbc-1)],
                                                    bri_acc_method, dt, bri_acc_filt_range)
                                 for m in range(len(data_bri))]
                k_max_bri_ary = [get_data_for_table(data_bri[m][10*h_post_node_count+(k_idx_in_vbc-1)],
                                                    bri_acc_method, dt, bri_acc_filt_range)
                                 for m in range(len(data_bri))]
                k_max_bri_arz = [get_data_for_table(data_bri[m][11*h_post_node_count+(k_idx_in_vbc-1)],
                                                    bri_acc_method, dt, bri_acc_filt_range)
                                 for m in range(len(data_bri))]
                h_max_bri_dx_list.append(k_max_bri_dx)
                h_max_bri_dy_list.append(k_max_bri_dy)
                h_max_bri_dz_list.append(k_max_bri_dz)
                h_max_bri_rx_list.append(k_max_bri_rx)
                h_max_bri_ry_list.append(k_max_bri_ry)
                h_max_bri_rz_list.append(k_max_bri_rz)
                h_max_bri_ax_list.append(k_max_bri_ax)
                h_max_bri_ay_list.append(k_max_bri_ay)
                h_max_bri_az_list.append(k_max_bri_az)
                h_max_bri_arx_list.append(k_max_bri_arx)
                h_max_bri_ary_list.append(k_max_bri_ary)
                h_max_bri_arz_list.append(k_max_bri_arz)
            del data_bri
            max_bri_dx_list.append(h_max_bri_dx_list)
            max_bri_dy_list.append(h_max_bri_dy_list)
            max_bri_dz_list.append(h_max_bri_dz_list)
            max_bri_rx_list.append(h_max_bri_rx_list)
            max_bri_ry_list.append(h_max_bri_ry_list)
            max_bri_rz_list.append(h_max_bri_rz_list)
            max_bri_ax_list.append(h_max_bri_ax_list)
            max_bri_ay_list.append(h_max_bri_ay_list)
            max_bri_az_list.append(h_max_bri_az_list)
            max_bri_arx_list.append(h_max_bri_arx_list)
            max_bri_ary_list.append(h_max_bri_ary_list)
            max_bri_arz_list.append(h_max_bri_arz_list)

        if self.postTableRangeSel.currentIndex() == 0:
            condition_name_list = ['当前工况']
        else:
            condition_name_list = [self.attendSonPathList.item(i_row).text()
                                   for i_row in range(self.attendSonPathList.count())]
        # speed_num = speed_count_list[0]
        post_tb_show_dia = GuidePostTableShowDialog(condition_name_list, self.vehicle_type_dict,
                                                    veh_acc_method, bri_acc_method, wheel_force_method,
                                                    veh_acc_filt_range, bri_acc_filt_range, wheel_force_filt_range,
                                                    self.attend_post_node_list, self.baseline_post_node_dict_for_table,
                                                    max_reduction_ration_dict_by_veh_type, max_vertical_wheel_force_dict_by_veh_type,
                                                    max_derail_factor_dict_by_veh_type, max_horizontal_wheel_force_dict_by_veh_type,
                                                    max_dynamic_irr_vertical_dict_by_veh_type, max_dynamic_irr_horizontal_dict_by_veh_type,
                                                    max_dynamic_irr_yaw_dict_by_veh_type, max_wheel_rail_dis_vertical_dict_by_veh_type,
                                                    max_wheel_rail_dis_horizontal_dict_by_veh_type, max_wheel_rail_dis_yaw_dict_by_veh_type,
                                                    max_veh_acc_vertical_front_dict_by_veh_type, max_veh_acc_vertical_rear_dict_by_veh_type,
                                                    max_veh_acc_horizontal_front_dict_by_veh_type, max_veh_acc_horizontal_rear_dict_by_veh_type,
                                                    veh_sperling_vertical_front_dict_by_veh_type, veh_sperling_vertical_rear_dict_by_veh_type,
                                                    veh_sperling_horizontal_front_dict_by_veh_type, veh_sperling_horizontal_rear_dict_by_veh_type,
                                                    max_bri_dx_list, max_bri_dy_list, max_bri_dz_list, max_bri_rx_list,
                                                    max_bri_ry_list, max_bri_rz_list, max_bri_ax_list, max_bri_ay_list,
                                                    max_bri_az_list, max_bri_arx_list, max_bri_ary_list, max_bri_arz_list)
        post_tb_show_dia.exec_()

    def gen_post_table(self):
        try:  # 偷懒做法，其实应该在action函数的读取文件部分try
            self.gen_post_table_action()
        except:
            QMessageBox.warning(self, '制表失败', '计算结果文件可能不完整，请检查或重新运行分析。\n若要查看已计算的部分结果，可尝试查看时程图。')
            return


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_EnableHighDpiScaling)
main_window = GuideMainWindow()

allow_run = True
try:
    f = open('NonlinearSpringParameters_Vehicletypes.dat', 'r')
    f.close()
    f = open('Modal_Substructure_Vehicletypes.dat', 'r')
    f.close()
except:
    QMessageBox.critical(main_window, '错误', '缺少车辆弹簧参数文件。')
    allow_run = False
if allow_run:
    main_window.show()
    sys.exit(app.exec_())

# pyinstaller ui_MainWindow.py --noconsole --workpath d:\vbcguide0630  --distpath d:\vbcguide0630\dist --icon="VBC.ico" --upx-dir=D:\VBC_Guide\upx\upx.exe
