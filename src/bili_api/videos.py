import asyncio
import threading
from datetime import datetime
from typing import cast

import requests
from bilibili_api import sync
from bilibili_api.user import User
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.config import VIDEO_DIR, cfg
from src.song_list import SongList
from src.utils.file import load_extend
from src.utils.text import contain_text

from .common import get_credential

remove_urls_index = []


def resolve_url_to_info(url, words_set=None):
    """解析视频url并转换为详细信息(title,author,date)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")
        if not (h1 := soup.find("h1", class_="video-title special-text-indent")):
            return

        # 获取标题
        video_title = str(cast(Tag, h1).get("data-title"))
        # 获取作者(联合投稿可能失败)
        video_author = soup.find("a", class_="up-name")
        if video_author is not None:
            video_author = video_author.getText()  # 调用 getText 方法获取实际文本
            video_author = video_author.strip()
        else:
            logger.debug(f"未找到作者名: {url}")
            video_author = "Unknown"
        # 获取发布时间
        video_date = soup.find("div", class_="pubdate-ip-text")
        if video_date is not None:
            video_date = video_date.getText()  # 调用 getText 方法获取实际文本
        else:
            logger.debug(f"未找到发布日期: {url}")
            video_date = "Unknown"

        if words_set is None or contain_text(words_set, video_title):
            return {"title": video_title, "author": video_author, "date": video_date}
        else:
            logger.debug(f"未识别到关键词: {url}")
            return None

    except Exception:
        logger.exception("提取信息时出错")
        return None


async def get_user_videos(user_id: int, words_set: list[str] | None = None, page: int = 1):
    """获取指定用户的视频信息"""
    user = User(user_id, credential=get_credential())
    info = await user.get_user_info()
    data = await user.get_videos(pn=page)

    videos = SongList()
    for item in data["list"]["vlist"]:
        if words_set is not None and not contain_text(words_set, item["title"]):
            continue

        song_info = {
            "title": item["title"],
            "author": item["author"],
            "date": datetime.fromtimestamp(item["created"]).strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"https://www.bilibili.com/video/{item['bvid']}/",
            "bv": item["bvid"],
        }
        videos.append_info(song_info)

    file_path = VIDEO_DIR / f"{user_id}_data.json"
    old_data = SongList(file_path)
    videos.append_list(old_data)
    logger.info(f"{info['name']}({user_id}) 作者歌回记录数量从 {len(old_data)} 更新到 {len(videos)} ")
    videos.save_list(file_path)


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


def get_up_name(user_id: int) -> str:
    try:
        res = sync(User(user_id, credential=get_credential()).get_user_info())
        return res["name"]
    except Exception:
        logger.exception(f"获取UP主 {user_id} 名称失败")
        return f"Unknown({user_id})"


def get_up_names(user_ids: list[int]) -> dict[int, str]:
    """获取多个UP主的名称"""
    up_names = {}

    async def task(user_id: int):
        try:
            res = await User(user_id, credential=get_credential()).get_user_info()
            up_names[user_id] = res["name"]
        except Exception:
            logger.exception(f"获取UP主 {user_id} 名称失败")
            up_names[user_id] = f"Unknown({user_id})"

    async def fetch_all():
        await asyncio.gather(*[task(user_id) for user_id in user_ids])

    sync(fetch_all())
    return up_names
