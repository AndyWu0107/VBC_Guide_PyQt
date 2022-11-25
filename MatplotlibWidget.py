import sys
import random
import matplotlib
import numpy as np

matplotlib.use("Qt5Agg")
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最终的父类其实是QWidget。"""

    def __init__(self, parent=None, width=5, height=4, dpi=300):
        # 配置中文显示
        plt.rcParams['font.family'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

        self.fig = Figure(figsize=(width, height), dpi=dpi)  # 新建一个figure
        self.axes = self.fig.add_subplot(111)  # 建立一个子图，如果要建立复合图，可以在这里修改

        # self.axes.hold(False)  # 每次绘图的时候不保留上一次绘图的结果  # 新版matplotlib已经没hold了

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''定义FigureCanvas的尺寸策略，这部分的意思是设置FigureCanvas，使之尽可能的向外填充空间。'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    '''绘制静态图，可以在这里定义自己的绘图逻辑'''

    def start_static_plot(self, x, y, plot_title='title', x_label='x', y_label='y', xlim=None, ylim=None, legends=None, line_styles=None, colors=None):
        # x, y支持多组
        self.fig.suptitle(plot_title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)

        if type(x[0]) != list:
            x = [x]
        if type(y[0]) != list:
            y = [y]

        show_legends = True
        if not legends:
            show_legends = False
            legends = [None for i in range(0, len(x))]
        elif type(legends) != list:
            legends = [legends]

        if not line_styles:
            line_styles = [None for i in range(0, len(x))]
        elif type(line_styles) != list:
            line_styles = [line_styles]

        if not colors:
            colors = [None for i in range(0, len(x))]
        elif type(colors) != list:
            colors = [colors]

        for i_plot in range(0, len(x)):
            self.axes.plot(x[i_plot], y[i_plot], color=colors[i_plot], linewidth=1.0, linestyle=line_styles[i_plot],
                           label=legends[i_plot])
        if show_legends:
            self.axes.legend()
        if xlim:
            self.axes.set_xlim(xlim[0], xlim[1])
        if ylim:
            self.axes.set_ylim(ylim[0], ylim[1])
        # self.axes.grid(True)

    def clear_static_plot(self):
        self.axes.cla()

    '''启动绘制动态图'''

    def start_dynamic_plot(self, *args, **kwargs):
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)  # 每隔一段时间就会触发一次update_figure函数。
        timer.start(1000)  # 触发的时间间隔为1秒。

    '''动态图的绘图逻辑可以在这里修改'''

    def update_figure(self):
        self.fig.suptitle('测试动态图')
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.axes.set_ylabel('动态图：Y轴')
        self.axes.set_xlabel('动态图：X轴')
        self.axes.grid(True)
        self.draw()


class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)
        self.initUi()

    def initUi(self):
        self.layout = QVBoxLayout(self)
        self.mpl = MyMplCanvas(self, width=5, height=4, dpi=100)
        # self.mpl.start_static_plot() # 如果你想要初始化的时候就呈现静态图，请把这行注释去掉
        # self.mpl.start_dynamic_plot() # 如果你想要初始化的时候就呈现动态图，请把这行注释去掉
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 添加完整的 toolbar

        self.layout.addWidget(self.mpl_ntb)
        self.layout.addWidget(self.mpl)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MatplotlibWidget()
    x = []
    y = []
    x0 = list(np.linspace(-3, 3, 50))
    y0 = list(sin(x0))
    x.append(x0)
    y.append(y0)
    print(x)
    x1 = list(np.linspace(-4, 4, 80))
    y1 = list(2*sin(x1)**2)
    x.append(x1)
    y.append(y1)
    ui.mpl.start_static_plot(x=x, y=y, x_label='i am x', y_label='i am y', legends=['test line1', 'test line2'], line_styles=[':', '--'])  # 测试静态图效果
    # ui.mpl.clear_static_plot()
    # ui.mpl.start_static_plot(x=x, y=y, x_label='i am x', y_label='i am y', legends=['test line3', 'test line4'], line_styles=['-.', '--'])  # 测试静态图效果
    # ui.mpl.start_dynamic_plot() # 测试动态图效果

    ui.show()
    sys.exit(app.exec_())
