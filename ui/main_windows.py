# Form implementation generated from reading ui file 'main_windows.ui'
#
# Created by: PyQt6 UI code generator 6.8.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_NeuroSongSpider(object):
    def setupUi(self, NeuroSongSpider):
        NeuroSongSpider.setObjectName("NeuroSongSpider")
        NeuroSongSpider.resize(680, 544)
        NeuroSongSpider.setWindowTitle("NeuroSongSpider")
        NeuroSongSpider.setIconSize(QtCore.QSize(32, 32))
        self.centralwidget = QtWidgets.QWidget(parent=NeuroSongSpider)
        self.centralwidget.setObjectName("centralwidget")
        self.DownloadBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.DownloadBtn.setGeometry(QtCore.QRect(610, 10, 61, 24))
        self.DownloadBtn.setObjectName("DownloadBtn")
        self.search_line = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.search_line.setGeometry(QtCore.QRect(110, 10, 201, 20))
        self.search_line.setObjectName("search_line")
        self.GetVideoBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.GetVideoBtn.setGeometry(QtCore.QRect(10, 10, 91, 24))
        self.GetVideoBtn.setObjectName("GetVideoBtn")
        self.SearchBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.SearchBtn.setGeometry(QtCore.QRect(320, 10, 81, 24))
        self.SearchBtn.setObjectName("SearchBtn")
        self.listWidget = QtWidgets.QListWidget(parent=self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(10, 40, 661, 471))
        self.listWidget.setObjectName("listWidget")
        self.openPlayerBTN = QtWidgets.QPushButton(parent=self.centralwidget)
        self.openPlayerBTN.setGeometry(QtCore.QRect(410, 10, 101, 24))
        self.openPlayerBTN.setObjectName("openPlayerBTN")
        self.DownloadBtn_ogg = QtWidgets.QPushButton(parent=self.centralwidget)
        self.DownloadBtn_ogg.setGeometry(QtCore.QRect(520, 10, 81, 24))
        self.DownloadBtn_ogg.setObjectName("DownloadBtn_ogg")
        NeuroSongSpider.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=NeuroSongSpider)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 680, 22))
        self.menubar.setObjectName("menubar")
        NeuroSongSpider.setMenuBar(self.menubar)

        self.retranslateUi(NeuroSongSpider)
        QtCore.QMetaObject.connectSlotsByName(NeuroSongSpider)

    def retranslateUi(self, NeuroSongSpider):
        _translate = QtCore.QCoreApplication.translate
        self.DownloadBtn.setText(_translate("NeuroSongSpider", "下载"))
        self.GetVideoBtn.setText(_translate("NeuroSongSpider", "获取视频列表"))
        self.SearchBtn.setText(_translate("NeuroSongSpider", "搜索"))
        self.openPlayerBTN.setText(_translate("NeuroSongSpider", "打开内置播放器"))
        self.DownloadBtn_ogg.setText(_translate("NeuroSongSpider", "下载ogg"))
