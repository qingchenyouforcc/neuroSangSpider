from math import expm1

from PyQt6 import QtWidgets

from crawlerCore.main import create_video_list_file
from fileManager import MAIN_PATH

from musicDownloader.main import search_song, run_download

import sys
from PyQt6.QtWidgets import QMainWindow, QMessageBox

from ui.main_windows import Ui_NeuroSongSpider

# if __name__ == '__main__':
#     print("")
#     create_video_list_file()
#
#     download_main()

class mainWindow(QMainWindow, Ui_NeuroSongSpider):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)
        self.setupUi(self)
        self.GetVideoBtn.clicked.connect(lambda: create_video_list_file())
        self.SearchBtn.clicked.connect(lambda: self.search_btn())
        self.DownloadBtn.clicked.connect(lambda: self.Download_btn())


    def search_btn(self):
        self.listWidget.clear()
        search_content = self.search_line.text()
        main_search_list = search_song(search_content)
        try:
            main_search_list = search_song(search_content)
            for item in main_search_list:
                self.listWidget.addItem(item)
        except TypeError:
            messageBox = QMessageBox()
            QMessageBox.about(messageBox, "提示","没有找到该歌曲！")
        except Exception as e:
            print(f"错误:{e}")

    def Download_btn(self):
        index = self.listWidget.currentRow()
        run_download(index)


if __name__ == '__main__':
    print(MAIN_PATH)
    app = QtWidgets.QApplication(sys.argv)
    main = mainWindow()
    main.show()
    sys.exit(app.exec())
