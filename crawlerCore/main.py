import threading

from SongList import SongList
from config import cfg
from crawlerCore.videosList import get_video_list, resolve_url_to_info
from utils.file_tools import create_dir, load_extend


def create_video_list_file():
    """获得视频列表文件(多线程)"""
    # UP主列表 和 爬取视频需包含词
    up_list = cfg.up_list
    words_set = ["合唱", "歌回", "金曲"]
    threads = []
    bv_list = []
    create_dir("data")

    # 启动多线程爬取程序内建的up主近期视频
    for up in up_list:
        t = threading.Thread(target=get_video_list, args=(up, words_set))
        t.start()
        threads.append(t)

    # 获取扩展包数据
    extend_data = load_extend("data")
    if extend_data is not None:
        bv_list.extend(extend_data["bv"])
    song_list = SongList()

    for bv in bv_list:
        song_url = f"https://www.bilibili.com/video/{bv}/"
        song_info = resolve_url_to_info(song_url)
        if song_info is not None:
            song_info["url"] = song_url
            song_info["bv"] = bv
            song_list.append_info(song_info)

    song_list.unique_by_bv()
    # 将所有扩展包内视频爬取的信息写入文件
    if song_list is not None:
        song_list.save_list("data/extend_video_data.json")

    for t in threads:
        t.join()
