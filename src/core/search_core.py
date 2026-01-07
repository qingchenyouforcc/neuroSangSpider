from __future__ import annotations

from datetime import datetime

from bilibili_api import sync
from loguru import logger

from src.bili_api import search_on_bilibili, search_song_list, search_bvid_on_bilibili
from src.core.song_list import SongList
from src.utils.text import format_date_str


_LAST_SEARCH_ERROR: str | None = None


def get_last_search_error() -> str | None:
    """获取最近一次搜索的错误信息（如有）。"""
    return _LAST_SEARCH_ERROR


def parse_date(dt_str: str) -> datetime:
    """尽力解析日期字符串为 datetime，用于排序。失败返回最小时间。"""
    try:
        if not dt_str:
            return datetime.min
        # 尝试完整时间戳格式
        if " " in dt_str:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        # 退化为仅日期，先规范化显示格式再解析
        norm = format_date_str(dt_str)
        return datetime.strptime(norm, "%Y-%m-%d")
    except Exception:
        return datetime.min


def sort_song_list_by_date_desc(slist: SongList) -> None:
    """将 SongList 按 date 从新到旧排序（原地）。"""
    try:
        data = slist.get_data()
        data.sort(key=lambda x: parse_date(str(x.get("date", ""))), reverse=True)
    except Exception:
        logger.exception("排序列表时出错")


def compute_relevance(item: dict, query: str) -> float:
    """基于标题与作者的简单相关性评分。"""
    try:
        q = (query or "").strip().lower()
        if not q:
            return 0.0
        tokens = [tok for tok in q.split() if tok]
        title = str(item.get("title", "")).lower()
        author = str(item.get("author", "")).lower()

        score = 0.0
        # 短语匹配加权
        if q in title:
            score += 5.0
        # 首词前缀
        if tokens and title.startswith(tokens[0]):
            score += 2.0
        # 逐词匹配
        for tok in tokens:
            if tok in title:
                score += 1.0
                # 多次出现的轻微加成
                occ = title.count(tok)
                if occ > 1:
                    score += min(occ - 1, 3) * 0.3
            if tok in author:
                score += 0.3

        # 轻微长度规范化（更短标题略占优）
        tl = len(title)
        if tl > 0:
            score += max(0.0, 1.5 - tl / 80.0)

        return score
    except Exception:
        logger.exception("计算相关度失败")
        return 0.0


def sort_song_list_by_relevance(slist: SongList, query: str) -> None:
    """按相关度排序；空查询则退化为日期倒序。"""
    q = (query or "").strip()
    try:
        data = slist.get_data()
        if not q:
            data.sort(key=lambda x: parse_date(str(x.get("date", ""))), reverse=True)
            return
        data.sort(
            key=lambda x: (
                compute_relevance(x, q),
                parse_date(str(x.get("date", ""))),
            ),
            reverse=True,
        )
    except Exception:
        logger.exception("相关度排序失败，退化为日期排序")
        sort_song_list_by_date_desc(slist)


def perform_search(search_content: str, mode: str = "title") -> SongList | None:
    """执行搜索：先查本地，必要时或增量用 bilibili 搜索补充。

    - 返回 SongList 或 None（未找到或出错）。
    - 不做任何 UI 交互，仅记录日志。
    """
    global _LAST_SEARCH_ERROR
    _LAST_SEARCH_ERROR = None

    try:
        # BV 模式是精确唯一匹配：不做“增量追加”，避免重复网络请求与 I/O
        if mode == "bvid":
            main_search_list = search_song_list(search_content, mode)
            if main_search_list is not None:
                return main_search_list

            logger.info("没有在本地列表找到该 BV，正在尝试 bilibili 精确拉取")
            try:
                sync(search_bvid_on_bilibili(search_content))
            except Exception as e:
                logger.exception("bilibili BV 精确拉取失败")
                _LAST_SEARCH_ERROR = str(e)
                return None

            return search_song_list(search_content, mode)

        # 标题模式：保留原有“本地 + bilibili 增量”行为
        main_search_list = search_song_list(search_content, mode)
        if main_search_list is None:
            logger.info("没有在本地列表找到该歌曲，正在尝试 bilibili 搜索")
            try:
                sync(search_on_bilibili(search_content))
                main_search_list = search_song_list(search_content, mode)
            except Exception as e:
                logger.exception("bilibili 搜索失败")
                _LAST_SEARCH_ERROR = str(e)
            else:
                if main_search_list is None:
                    logger.warning("bilibili 搜索结果为空")
            return main_search_list

        logger.info(f"本地获取 {len(main_search_list.get_data())} 个有效视频数据:")
        logger.info(main_search_list.get_data())

        try:
            sync(search_on_bilibili(search_content))
            if more_search_list := search_song_list(search_content, mode):
                delta = len(more_search_list.get_data()) - len(main_search_list.get_data())
                logger.info(f"bilibili 获取增量 {delta} 个有效视频数据:")
                main_search_list.append_list(more_search_list)
        except Exception as e:
            logger.exception("bilibili 搜索失败（增量阶段）")
            _LAST_SEARCH_ERROR = str(e)

        return main_search_list

    except Exception as e:
        logger.exception("执行搜索时发生未知错误")
        _LAST_SEARCH_ERROR = str(e)
        return None
