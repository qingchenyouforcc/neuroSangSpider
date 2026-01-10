import asyncio
import re
from datetime import datetime

from bilibili_api.search import SearchObjectType, search_by_type
from bilibili_api.video import Video
from bs4 import BeautifulSoup
from loguru import logger

from src.config import VIDEO_DIR, cfg
from src.core.song_list import SongList
from .common import get_credential, apply_proxy_if_enabled


_BVID_RE = re.compile(r"(BV[0-9A-Za-z]{10})", re.IGNORECASE)


def _extract_bvid(text: str) -> str | None:
    """从输入中提取 BV 号。

    支持：
    - BV1xxxxxxxxxx
    - https://www.bilibili.com/video/BVxxxxxx
    - 其他包含 BV 号的文本
    """
    if not text:
        return None
    m = _BVID_RE.search(text.strip())
    if not m:
        return None
    # 统一成 "BV" 前缀大写
    return "BV" + m.group(1)[2:]


async def search_page(search_content: str, page: int) -> list[dict]:
    apply_proxy_if_enabled()
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
    apply_proxy_if_enabled()
    songs = SongList()

    try:
        results = await asyncio.gather(
            *[search_page(search_content, page) for page in range(1, cfg.search_page.value + 1)],
            return_exceptions=True,
        )

        first_exc: Exception | None = None
        for data in results:
            if isinstance(data, Exception):
                if first_exc is None:
                    first_exc = data
                continue
            if isinstance(data, list):  # Ensure data is iterable
                for item in data:
                    songs.append_info(item)

        # 如果全部页面都失败，则向上抛出，给 UI 展示网络错误
        if len(songs.get_data()) == 0 and first_exc is not None:
            raise first_exc

        songs.append_list(SongList(VIDEO_DIR / "search_data.json"))
        songs.unique_by_bv()
        songs.save_list(VIDEO_DIR / "search_data.json")
    except Exception as e:
        logger.opt(exception=True).error(f"搜索 {search_content} 失败: {e}")
        raise


async def search_bvid_on_bilibili(search_content: str) -> None:
    """通过 BV 号精确拉取视频信息并写入本地 search_data.json。"""
    apply_proxy_if_enabled()
    songs = SongList()
    try:
        bvid = _extract_bvid(search_content)
        if not bvid:
            logger.warning(f"BV号格式不正确: {search_content}")
            return

        v = Video(bvid=bvid, credential=get_credential())
        info = await v.get_info()

        pubdate = info.get("pubdate")
        date_str = ""
        if isinstance(pubdate, (int, float)) and pubdate > 0:
            date_str = datetime.fromtimestamp(int(pubdate)).strftime("%Y-%m-%d %H:%M:%S")

        owner = info.get("owner") or {}
        item = {
            "title": str(info.get("title", "")),
            "author": str(owner.get("name", "")),
            "date": date_str,
            "url": f"https://www.bilibili.com/video/{bvid}/",
            "bv": bvid,
        }

        songs.append_info(item)
        songs.append_list(SongList(VIDEO_DIR / "search_data.json"))
        songs.unique_by_bv()
        songs.save_list(VIDEO_DIR / "search_data.json")
        logger.info(f"Successfully fetched info for {bvid}")

    except Exception as e:
        logger.opt(exception=True).error(f"Failed to fetch BV {search_content}: {e}")
        raise
