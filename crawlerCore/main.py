import os

from crawlerCore.videosList import get_video_list

import threading

from utils.fileManager import create_dir, part2all

# UP主列表 和 爬取视频需包含词
# up_list = [351692111]
up_list = [351692111, 1880487363, 22535350, 3546612622166788, 5971855, 483178955, 690857494]
words_set = ["合唱", "歌回", "金曲"]

videos_temp_list = []
videos_list = []
videos_num = 0
threads = []

create_dir("data")

def create_video_list_file():
    """获得视频列表文件(多线程)"""
    for up in up_list:
        t = threading.Thread(target=get_video_list, args=(up, words_set))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # 合成完整的视频列表
    part2all("data", "videos_list.txt")

