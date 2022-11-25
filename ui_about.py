from UIAbout import *
from PyQt5.QtWidgets import QDialog


class GuideAboutDia(QDialog, Ui_About):
    def __init__(self):
        super(GuideAboutDia, self).__init__()
        self.setupUi(self)
