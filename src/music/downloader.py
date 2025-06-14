import contextlib
import subprocess
import uuid
from pathlib import Path

from bilibili_api import HEADERS, Credential, get_client, video
from loguru import logger

from src.config import CACHE_DIR, FFMPEG_PATH

SESSDATA = ""
BILI_JCT = ""
BUVID3 = ""


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
    # 实例化 Credential 类
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    # 实例化 Video 类
    v = video.Video(bvid, credential=credential)
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
        ).check_returncode()

    logger.info(f"已下载为：{output_file}")
