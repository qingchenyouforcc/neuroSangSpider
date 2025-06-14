import asyncio
import threading

from bilibili_api import sync

from src.config import VIDEO_DIR, cfg
from src.song_list import SongList
from src.utils.file import load_extend

from .search import search_on_bilibili as search_on_bilibili
from .videos import get_user_videos, resolve_url_to_info


def create_video_list_file() -> None:
    """获得视频列表文件(多线程)"""
    # UP主列表 和 爬取视频需包含词
    up_list = cfg.up_list.value
    words_set = ["合唱", "歌回", "金曲"]
    bv_list = []

    async def fetch_all():
        await asyncio.gather(*[get_user_videos(up, words_set) for up in up_list])

    # 爬取程序内建的up主近期视频
    thread = threading.Thread(target=sync, args=(fetch_all(),))
    thread.start()

    # 获取扩展包数据
    extend_data = load_extend(VIDEO_DIR)
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
        song_list.save_list(VIDEO_DIR / "extend_video_data.json")

    thread.join()


__all__ = ["create_video_list_file", "search_on_bilibili"]
