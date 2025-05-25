import threading

from crawlerCore.videosList import get_video_list
from utils.fileManager import create_dir, part2all,loadFromAllJson


def create_video_list_file():
    """获得视频列表文件(多线程)"""
    # UP主列表 和 爬取视频需包含词
    # up_list = [351692111]
    up_list = [351692111, 1880487363, 22535350, 3546612622166788, 5971855, 483178955, 690857494]
    words_set = ["合唱", "歌回", "金曲"]
    threads = []

    create_dir("data")

    for up in up_list:
        t = threading.Thread(target=get_video_list, args=(up, words_set))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # 合成完整的视频列表
    loadFromAllJson("data",["videoList.json"]).saveList("data/videoList.json")
