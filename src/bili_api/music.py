import contextlib
import subprocess
import uuid
from pathlib import Path

from PyQt6.QtCore import Qt
from bilibili_api import HEADERS, get_client, sync, video
from loguru import logger
from qfluentwidgets import InfoBar, InfoBarPosition, MessageBox

from src.app_context import app_context
from src.config import CACHE_DIR, FFMPEG_PATH, MAIN_PATH, MUSIC_DIR, VIDEO_DIR, DATA_DIR, cfg, subprocess_options
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
    filter_list = cfg.filter_list.value if cfg.enable_filter.value else []
    black_author_list = cfg.black_author_list.value

    search_result_list = total_data
    search_result_list.search_by_title(search_content)

    search_result_list.unique_by_bv()
    search_result_list.remove_blacklist(black_author_list, 1)
    if cfg.enable_filter.value:
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

    # 如果文件存在，执行覆盖操作
    if output_file.exists():
        logger.info(f"文件 {output_file} 已存在，执行覆盖操作。")

    try:
        sync(download_music(bv, output_file))
        return True
    except Exception:
        logger.exception(f"下载失败: {bv}")
        InfoBar.error(
            title="错误",
            content=f"下载失败: {title}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=app_context.main_window,
        )
        return False


def _get_video_title_by_bvid(bvid: str) -> str:
    """通过 bvid 获取视频标题，失败时回退为 bvid"""
    try:
        v = video.Video(bvid, credential=get_credential())
        info = sync(v.get_info())
        # 兼容不同结构
        title = info.get("title") if isinstance(info, dict) else None
        if not title and isinstance(info, dict) and "View" in info:
            title = info["View"].get("title")
        return title or bvid
    except Exception:
        logger.exception(f"获取标题失败: {bvid}")
        return bvid


def run_music_download_by_bvid(bvid: str, file_type: str = "mp3") -> bool:
    """直接根据 BV 号下载音频"""
    try:
        title = _get_video_title_by_bvid(bvid)
        safe_title = fix_filename(title).replace(" ", "").replace("_", "", 1)
        output_file = MUSIC_DIR / f"{safe_title}.{file_type}"

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

        sync(download_music(bvid, output_file))
        return True
    except Exception:
        logger.exception(f"下载失败: {bvid}")
        return False


def import_custom_songs_and_download(directory: Path | None = None, file_type: str = "mp3") -> None:
    """读取 custom_songs 文件夹中的文本文件，逐行 BV 号下载音频"""
    from pathlib import Path as _Path
    import re

    try:
        base_dir = directory or (DATA_DIR / "custom_songs")
        base_dir = _Path(base_dir)
        if not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)
            InfoBar.info(
                "已创建目录",
                f"已创建 {base_dir}，请放入包含 BV 的 txt 文件后重试",
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=2500,
            )
            logger.info(f"已创建 custom_songs 目录: {base_dir}")
            return

        bv_pattern = re.compile(r"^BV[0-9A-Za-z]+$", re.IGNORECASE)
        bv_set: set[str] = set()

        for fp in base_dir.iterdir():
            if not fp.is_file() or fp.suffix.lower() != ".txt":
                continue
            try:
                for line in fp.read_text(encoding="utf-8").splitlines():
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    # 仅接受 BV，其他跳过
                    if bv_pattern.match(s):
                        # 统一大小写
                        if not s.startswith("BV"):
                            s = "BV" + s[2:]
                        bv_set.add(s)
                    else:
                        logger.debug(f"跳过无效行: {s}")
            except UnicodeDecodeError:
                logger.info(f"跳过非 UTF-8 文本文件: {fp}")
            except Exception:
                logger.exception(f"读取文件失败: {fp}")

        if not bv_set:
            InfoBar.info(
                "没有可下载的 BV",
                "未在任何 txt 中找到有效 BV 号",
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=2000,
            )
            return

        success, failed = 0, 0
        for bv in sorted(bv_set):
            ok = run_music_download_by_bvid(bv, file_type=file_type)
            if ok:
                success += 1
            else:
                failed += 1

        InfoBar.success(
            "下载完成",
            f"成功 {success} 个，失败 {failed} 个",
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=app_context.main_window,
            duration=3000,
        )
    except Exception:
        logger.exception("处理 custom_songs 失败")
        InfoBar.error(
            "处理失败",
            "读取或下载过程中发生错误",
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=app_context.main_window,
            duration=2000,
        )
