from datetime import datetime
from typing import cast

import requests
from bilibili_api.user import User
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.config import VIDEO_DIR
from src.song_list import SongList
from src.utils.text import contain_text

remove_urls_index = []


# noinspection PyCallingNonCallable
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
            # print("未找到作者名:",url)
            video_author = "Unknown"
        # 获取发布时间
        video_date = soup.find("div", class_="pubdate-ip-text")
        if video_date is not None:
            video_date = video_date.getText()  # 调用 getText 方法获取实际文本
        else:
            # print("未找到发布日期:",url)
            video_date = "Unknown"

        if words_set is None or contain_text(words_set, video_title):
            return {"title": video_title, "author": video_author, "date": video_date}
        else:
            # print("未识别到关键词:",url)
            return None
    except Exception:
        logger.exception("提取信息时出错")
        return None


async def get_user_videos(user_id: int, words_set: list[str] | None = None, page: int = 1):
    """获取指定用户的视频信息"""
    user = User(user_id)
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
