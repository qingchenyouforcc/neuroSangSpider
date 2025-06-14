from bilibili_api import sync
from loguru import logger
from qfluentwidgets import MessageBox

from src.config import MAIN_PATH, MUSIC_DIR, VIDEO_DIR, cfg
from src.song_list import SongList
from src.utils.file import load_from_all_data
from src.utils.text import fix_filename

from .downloader import download_music


def search_song_list(search_content: str) -> SongList | None:
    """
    重写的搜索方法

    参数:
        search_result(str):搜索的关键字

    返回:
        search_result_list:
            (SongList):搜索结果
            (None):未搜索到结果,返回空
    """

    total_data = load_from_all_data(VIDEO_DIR)
    if total_data is None:
        return None
    filter_list = cfg.filter_list.value
    black_author_list = cfg.black_author_list.value

    search_result_list = total_data
    search_result_list.search_by_title(search_content)

    search_result_list.unique_by_bv()
    search_result_list.remove_blacklist(black_author_list, 1)
    search_result_list.filter_data(filter_list, 0)

    if len(search_result_list.get_data()) == 0:
        return None

    return search_result_list


def run_download(index, search_list: SongList, file_type: str = "mp3") -> None:
    """运行下载器"""
    info = search_list.select_info(index)
    assert info is not None, "索引超出范围或信息不存在"

    bv = info["bv"]
    file_name = info["title"]
    title = fix_filename(file_name).replace(" ", "").replace("_", "", 1)
    output_file = MUSIC_DIR / f"{title}.{file_type}"
    logger.info(f"选择第 {index + 1} 个，开始下载歌曲")
    logger.info(f"  BVID: {bv}")
    logger.info(f"  title: {title}")
    logger.info(f"  输出文件: {output_file}")

    # 如果文件存在，弹出提示窗口
    if output_file.exists():
        w = MessageBox(
            "文件已存在",
            f"文件 '{output_file.relative_to(MAIN_PATH)}' 已存在。是否覆盖？",
            cfg.main_window,
        )

        w.setClosableOnMaskClicked(True)
        w.setDraggable(True)

        if not w.exec():
            logger.info("用户取消下载。")
            return

    sync(download_music(bv, output_file))


__all__ = ["run_download", "search_song_list"]
