from PyQt5.QtWidgets import QWidget, QApplication

from UIErrorReminder import Ui_ErrorReminder


class GuideErrorReminder(QWidget, Ui_ErrorReminder):
    def __init__(self, error_text):
        super(GuideErrorReminder, self).__init__()
        # 初始化ui
        self.setupUi(self)
        self.errorText.setPlainText(error_text)


if __name__ == '__main__':

    app = QApplication([])
    er = GuideErrorReminder('hhhh')
    er.show()
    app.exec_()
