import contextlib
import subprocess
import uuid
from pathlib import Path

from PyQt6.QtCore import Qt
from bilibili_api import HEADERS, get_client, sync, video
from loguru import logger
from qfluentwidgets import InfoBar, InfoBarPosition, MessageBox

from src.app_context import app_context
from src.config import CACHE_DIR, FFMPEG_PATH, MAIN_PATH, MUSIC_DIR, VIDEO_DIR, cfg, subprocess_options
from src.core.song_list import SongList
from src.core.data_io import load_from_all_data
from src.utils.text import fix_filename

from .common import get_credential


@contextlib.asynccontextmanager
async def download(url: str, ext: str, intro: str):
    logger.info(f"Using ffmpeg: {FFMPEG_PATH}")
    client = get_client()
    dwn_id = await client.download_create(url, HEADERS)
    current = 0
    total = client.download_content_length(dwn_id)

    cache_file = CACHE_DIR / f"{uuid.uuid4()}{ext}"
    with open(cache_file, "wb") as temp_file:
        logger.info(f"临时文件: {temp_file.name}")
        while True:
            current += temp_file.write(await client.download_chunk(dwn_id))
            print(f"{intro} - {ext} [{current} / {total}]", end="\r")
            if current == total:
                break

    try:
        yield cache_file
    finally:
        cache_file.unlink(missing_ok=True)


async def download_music(bvid: str, output_file: Path) -> None:
    # 实例化 Video 类
    v = video.Video(bvid, credential=get_credential())
    # 获取视频下载链接
    download_url_data = await v.get_download_url(0)
    # 解析视频下载信息
    detecter = video.VideoDownloadURLDataDetecter(data=download_url_data)
    streams = detecter.detect_best_streams()
    # 有 MP4 流 / FLV 流两种可能
    async with (
        download(streams[0].url, ".flv", "下载 FLV 音视频流")
        if detecter.check_flv_mp4_stream()
        else download(streams[1].url, ".m4s", "下载音频流")
    ) as temp_file:
        # 转换文件格式
        subprocess.run(
            [
                str(FFMPEG_PATH),
                "-y",
                "-i",
                str(temp_file),
                str(output_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **subprocess_options(),
        ).check_returncode()

    logger.info(f"已下载为：{output_file}")


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


def run_music_download(index: int, search_list: SongList, file_type: str = "mp3") -> bool:
    """运行下载器"""
    info = search_list.select_info(index)
    if info is None:
        InfoBar.error(
            "错误",
            "索引超出范围或信息不存在",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
            parent=app_context.main_window,
        )
        return False

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
            app_context.main_window,
        )

        w.setClosableOnMaskClicked(True)
        w.setDraggable(True)

        if not w.exec():
            logger.info("用户取消下载。")
            return False

    sync(download_music(bv, output_file))
    return True
