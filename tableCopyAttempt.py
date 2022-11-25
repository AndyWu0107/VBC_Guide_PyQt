import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem
from itertools import product
# import pyperclip


class Demo(QWidget):
    def __init__(self):
        self.clipboard = QApplication.clipboard()
        # self.text = str()
        # self.topRow = int()
        # self.bottomRow = int()
        # self.leftColumn = int()
        # self.rightColumn = int()

        super(Demo, self).__init__()
        self.resize(650, 250)
        self.table = QTableWidget(self)
        self.table.setRowCount(6)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([('{}'.format(i)) for i in range(6)])  # 列表解析式   # 5
        self.table.setVerticalHeaderLabels([('{}'.format(i)) for i in range(6)])
        self.table.clicked.connect(self.selected)

        hbox = QHBoxLayout(self)
        hbox.addWidget(self.table)
        self.setLayout(hbox)

    def selected(self, index):  # 获取选中单元格的索引
        self.index_row = index.row()
        self.index_column = index.column()

    def keyPressEvent(self, event):
        # print(event.key())
        if self.focusWidget().__class__.__name__ == "QTableWidget" and (event.key() == Qt.Key_C) \
                and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # 按键事件，ctrl+c时触发，复制。
            # print(self.focusWidget().__class__.__name__ == "QTableWidget")
            self.table_copy()
            self.clipboard.setText(self.STR)
            self.STR = str()  # 字符串归零
        else:
            pass
        if self.focusWidget().__class__.__name__ == "QTableWidget" and (event.key() == Qt.Key_V) \
                and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # ctrl+v粘贴
            self.table_paste()
        else:
            pass

    def table_copy(self):
        select_rect = self.table.selectedRanges()
        for r in select_rect:  # 获取范围边界
            self.top = r.topRow()
            self.left = r.leftColumn()
            self.bottom = r.bottomRow()
            self.right = r.rightColumn()
            print(self.top, self.left, self.bottom, self.right)
        self.column_n = 0
        self.number = 0
        self.row_n = 0
        self.column_n = self.right - self.left + 1
        self.row_n = self.bottom - self.top + 1
        self.number = self.row_n * self.column_n
        self.c = []
        for i in range(self.number):
            self.c.append(' \t')  # 注意，是空格+\t
            if (i % self.column_n) == (self.column_n - 1):
                # self.c.pop()  # 去除每行最后一个\t
                self.c.append('\n')
            else:
                pass
            # 这里生成了一个列表，大小是：行X（列+1），换行符占了一列。
            # 默认情况下，列表中全部是空格
        # print(self.c)
        self.c.pop()  # 删去最后多余的换行符

        range1 = range(self.top, self.bottom + 1)
        range2 = range(self.left, self.right + 1)
        for row, column in product(range1, range2):
            try:
                # 计算出单元格的位置，替换掉原来的空格；每行最后一个\t省略
                data = self.table.item(row, column).text()
                number2 = (row - self.top) * (self.column_n + 1) + (column - self.left)
                if column != range2[-1]:
                    self.c[number2] = data + '\t'
                else:
                    self.c[number2] = data
            except:
                pass
        self.STR = str()
        # print(self.c)
        for s in self.c:
            self.STR = self.STR + s

    def table_paste(self):
        try:  # 有时会误触ctrl+v，避免报错，所以就try了
            i = self.index_row
            j = self.index_column
            # content = self.table.item(i, j).text()  # 可能有误，应该是剪贴板内容
            data = self.clipboard.mimeData()
            if data.hasText():
                content = data.text()
            else:
                content = ''
            # print(content)
            b = str()
            for a in content:
                if a != '\n':
                    if a != '\t':
                        b = b + a
                    else:
                        item = QTableWidgetItem(b)
                        self.table.setItem(i, j, item)
                        b = ''
                        j += 1
                else:
                    item = QTableWidgetItem(b)
                    self.table.setItem(i, j, item)
                    b = ''
                    i += 1
                    j = self.index_column
                item = QTableWidgetItem(b)
                self.table.setItem(i, j, item)
        except:
            pass


# if __name__=="__main__":
app = QApplication(sys.argv)
demo = Demo()
demo.show()
sys.exit(app.exec_())

# ————————————————
# 原文作者：Firecelyyyy
# 转自链接：https://learnku.com/articles/46980
# 版权声明：著作权归作者所有。商业转载请联系作者获得授权，非商业转载请保留以上作者信息和原文链接。
