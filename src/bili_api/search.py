import asyncio
from datetime import datetime

from bilibili_api.search import SearchObjectType, search_by_type
from bs4 import BeautifulSoup
from loguru import logger

from src.config import VIDEO_DIR, cfg
from src.core.song_list import SongList


async def search_page(search_content: str, page: int) -> list[dict]:
    try:
        page_data = await search_by_type(
            keyword=f"neuro {search_content}",
            search_type=SearchObjectType.VIDEO,
            page=page,
            page_size=10,
        )
    except Exception:
        logger.opt(exception=True).warning(f"搜索 {search_content} 第 {page} 页时发生错误")
        return []

    result = [
        {
            "title": BeautifulSoup(item["title"], "html.parser").get_text(strip=True),
            "author": item["author"],
            "date": datetime.fromtimestamp(item["pubdate"]).strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"https://www.bilibili.com/video/{item['bvid']}/",
            "bv": item["bvid"],
        }
        for item in page_data["result"]
    ]
    logger.info(f"搜索 {search_content} 第 {page} 页成功，找到 {len(result)} 条结果")
    return result


async def search_on_bilibili(search_content: str) -> None:
    songs = SongList()

    try:
        for data in await asyncio.gather(
            *[search_page(search_content, page) for page in range(1, cfg.search_page.value + 1)]
        ):
            for item in data:
                songs.append_info(item)

        songs.append_list(SongList(VIDEO_DIR / "search_data.json"))
        songs.unique_by_bv()
        songs.save_list(VIDEO_DIR / "search_data.json")
    except Exception as e:
        logger.opt(exception=True).error(f"搜索 {search_content} 失败: {e}")
        return
