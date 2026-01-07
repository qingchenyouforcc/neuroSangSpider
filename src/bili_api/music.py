import contextlib
import subprocess
import uuid
from pathlib import Path

from bilibili_api import HEADERS, get_client, sync, video
from loguru import logger

from src.config import CACHE_DIR, FFMPEG_PATH, MUSIC_DIR, VIDEO_DIR, DATA_DIR, cfg, subprocess_options
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


async def download_music(bvid: str, output_file: Path, page_index: int = 0) -> None:
    # 实例化 Video 类
    v = video.Video(bvid, credential=get_credential())
    # 获取视频下载链接
    download_url_data = await v.get_download_url(page_index)
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


async def get_video_parts(bvid: str) -> list[dict]:
    """获取视频的分P信息

    Args:
        bvid: 视频BV号

    Returns:
        分P信息列表，每个元素包含 'page' (页码) 和 'part' (标题) 字段
        如果只有一个分P，返回空列表
    """
    try:
        v = video.Video(bvid, credential=get_credential())
        info = await v.get_info()

        # 获取分P信息
        pages = info.get("pages", [])

        # 如果只有一个分P，返回空列表
        if len(pages) <= 1:
            return []

        # 返回分P信息
        return [
            {
                "page": page.get("page", idx + 1),
                "part": page.get("part", f"分P {idx + 1}"),
            }
            for idx, page in enumerate(pages)
        ]
    except Exception:
        logger.exception(f"获取视频分P信息失败: {bvid}")
        return []


def get_video_parts_sync(bvid: str) -> list[dict]:
    """同步方式获取视频的分P信息

    Args:
        bvid: 视频BV号

    Returns:
        分P信息列表
    """
    return sync(get_video_parts(bvid))


def search_song_list(search_content: str, mode: str = "title") -> SongList | None:
    """
    重写的搜索方法

    参数:
        search_result(str):搜索的关键字
        mode(str):搜索模式 ('title' or 'bvid')

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

    if mode == "bvid":
        # BV 精确查找：不应用黑名单/关键词过滤，避免把目标视频过滤掉
        search_result_list.filter_by_bv(search_content)
        search_result_list.unique_by_bv()
    else:
        search_result_list.search_by_title(search_content)
        search_result_list.unique_by_bv()
        search_result_list.remove_blacklist(black_author_list, 1)
        if cfg.enable_filter.value:
            search_result_list.filter_data(filter_list, 0)

    if len(search_result_list.get_data()) == 0:
        return None

    return search_result_list


def run_music_download(
    index: int, search_list: SongList, file_type: str = "mp3", parts: list[int] | None = None
) -> bool:
    """运行下载器

    Args:
        index: 歌曲索引
        search_list: 搜索结果列表
        file_type: 文件类型
        parts: 要下载的分P页码列表，None表示下载第一个分P或全部分P

    Returns:
        是否下载成功
    """
    info = search_list.select_info(index)
    if info is None:
        logger.error("索引超出范围或信息不存在")
        return False

    bv = info["bv"]
    file_name = info["title"]
    title = fix_filename(file_name).replace(" ", "").replace("_", "", 1)

    logger.info(f"选择第 {index + 1} 个，开始下载歌曲")
    logger.info(f"  BVID: {bv}")
    logger.info(f"  title: {title}")

    try:
        # 如果没有指定分P，下载第一个分P（索引为0）
        if parts is None:
            output_file = MUSIC_DIR / f"{title}.{file_type}"
            logger.info(f"  输出文件: {output_file}")

            # 如果文件存在，执行覆盖操作
            if output_file.exists():
                logger.info(f"文件 {output_file} 已存在，执行覆盖操作。")

            sync(download_music(bv, output_file, 0))
        else:
            # 下载指定的多个分P，获取分P信息以使用分P标题
            parts_info = get_video_parts_sync(bv)

            for part_num in parts:
                part_index = part_num - 1  # 页码从1开始，索引从0开始

                # 查找对应分P的标题
                part_title = None
                for part_info in parts_info:
                    if part_info["page"] == part_num:
                        part_title = part_info["part"]
                        break

                # 如果找到了分P标题，使用分P标题；否则使用P{num}格式
                if part_title:
                    safe_part_title = fix_filename(part_title).replace(" ", "").replace("_", "", 1)
                    output_file = MUSIC_DIR / f"{title}_{safe_part_title}.{file_type}"
                else:
                    output_file = MUSIC_DIR / f"{title}_P{part_num}.{file_type}"

                logger.info(f"  输出文件: {output_file}")

                # 如果文件存在，执行覆盖操作
                if output_file.exists():
                    logger.info(f"文件 {output_file} 已存在，执行覆盖操作。")

                sync(download_music(bv, output_file, part_index))

        return True
    except Exception:
        logger.exception(f"下载失败: {bv}")
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


def run_music_download_by_bvid(bvid: str, file_type: str = "mp3", check_exists: bool = True) -> bool:
    """直接根据 BV 号下载音频"""
    try:
        title = _get_video_title_by_bvid(bvid)
        safe_title = fix_filename(title).replace(" ", "").replace("_", "", 1)
        output_file = MUSIC_DIR / f"{safe_title}.{file_type}"

        if check_exists and output_file.exists():
            # 在后台线程中无法弹出对话框，默认跳过或覆盖？
            # 这里为了安全起见，如果是后台批量下载，建议跳过或覆盖，而不是阻塞等待用户输入
            # 但由于此函数也被 import_custom_songs_and_download 调用，
            # 而 import_custom_songs_and_download 现在被设计为在后台运行，
            # 所以这里不能有 UI 交互。
            # 暂时策略：如果文件存在，记录日志并跳过下载（返回 True 表示已处理）
            logger.info(f"文件已存在，跳过下载: {output_file}")
            return True

        sync(download_music(bvid, output_file))
        return True
    except Exception:
        logger.exception(f"下载失败: {bvid}")
        return False


def import_custom_songs_and_download(directory: Path | None = None, file_type: str = "mp3") -> dict:
    """读取 custom_songs 文件夹中的文本文件，逐行 BV 号下载音频

    Returns:
        dict: 包含状态和结果信息的字典
        {
            "status": "success" | "error" | "created_dir" | "no_bv",
            "message": 描述信息,
            "data": {"success": int, "failed": int} (仅在 status="success" 时存在)
        }
    """
    from pathlib import Path as _Path
    import re

    try:
        base_dir = directory or (DATA_DIR / "custom_songs")
        base_dir = _Path(base_dir)
        if not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建 custom_songs 目录: {base_dir}")
            return {
                "status": "created_dir",
                "message": f"已创建 {base_dir}，请放入包含 BV 的 txt 文件后重试",
                "path": str(base_dir),
            }

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
            return {"status": "no_bv", "message": "未在任何 txt 中找到有效 BV 号"}

        success, failed = 0, 0
        for bv in sorted(bv_set):
            # 批量下载时不检查文件是否存在（或者默认跳过），避免阻塞
            # 这里调用 run_music_download_by_bvid 时 check_exists=True 会跳过已存在文件
            ok = run_music_download_by_bvid(bv, file_type=file_type, check_exists=True)
            if ok:
                success += 1
            else:
                failed += 1

        return {"status": "success", "message": "下载完成", "data": {"success": success, "failed": failed}}

    except Exception as e:
        logger.exception("处理 custom_songs 失败")
        return {"status": "error", "message": f"读取或下载过程中发生错误: {str(e)}"}
