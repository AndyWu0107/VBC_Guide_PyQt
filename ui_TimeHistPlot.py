from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from UITimeHistPlot import *
from VBCPostFunctions import fft_for_plot


class GuideTimeHistPlot(QDialog, Ui_TimeHistPlot):
    def __init__(self, x, y, dt_list, legends, response_type, line_styles, colors):
        super(GuideTimeHistPlot, self).__init__()
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)

        x_label = '时间(s)'
        # 1位移，2加速度，3角位移，4角加速度，5减载率，6脱轨系数，7力
        if response_type == 1:
            y_label = '位移(mm)'
            unit_ratio = 1000.0
        elif response_type == 2:
            y_label = '加速度(m/$s^2$)'
            unit_ratio = 1.0
        elif response_type == 3:
            y_label = '转角(‰ rad)'
            unit_ratio = 1000.0
        elif response_type == 4:
            y_label = '角加速度(rad/$s^2$)'
            unit_ratio = 1.0
        elif response_type == 5:
            y_label = '轮重减载率'
            unit_ratio = 1.0
        elif response_type == 6:
            y_label = '脱轨系数'
            unit_ratio = 1.0
        elif response_type == 7:
            y_label = '力(kN)'
            unit_ratio = 0.001
        for i_plot in range(0, len(y)):
            y[i_plot] = [j*unit_ratio for j in y[i_plot]]
        self.timeHistPlot.mpl.start_static_plot(x=x, y=y, plot_title='', x_label=x_label, y_label=y_label,
                                                legends=legends, line_styles=line_styles, colors=colors)

        f = []
        af = []
        for i_plot in range(0, len(y)):
            i_f, i_af = fft_for_plot(y[i_plot], dt_list[i_plot])
            f.append(i_f)
            af.append(i_af)
        self.fftPlot.mpl.start_static_plot(x=f, y=af, plot_title='', x_label='频率(Hz)', y_label=y_label, xlim=[0, 50],
                                           legends=legends, line_styles=line_styles, colors=colors)

