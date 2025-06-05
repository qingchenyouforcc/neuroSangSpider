import os

# noinspection PyUnresolvedReferences
from bilibili_api import video, Credential, HEADERS, get_client

from utils.fileManager import MAIN_PATH

SESSDATA = ""
BILI_JCT = ""
BUVID3 = ""

# FFMPEG 路径，查看：http://ffmpeg.org/
FFMPEG_PATH = f"{MAIN_PATH}" + "\\ffmpeg\\bin\\ffmpeg.exe"


async def download(url: str, out: str, intro: str):
    print(FFMPEG_PATH)
    dwn_id = await get_client().download_create(url, HEADERS)
    bts = 0
    tot = get_client().download_content_length(dwn_id)
    # 自动覆盖文件，无需用户确认
    with open(out, "wb") as file:
        while True:
            bts += file.write(await get_client().download_chunk(dwn_id))
            print(f"{intro} - {out} [{bts} / {tot}]", end="\r")
            if bts == tot:
                break
    print()


# noinspection DuplicatedCode
async def download_music(bvid, title, fileType):
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
    if detecter.check_flv_mp4_stream():
        # FLV 流下载
        await download(streams[0].url, "flv_temp.flv", "下载 FLV 音视频流")
        # 转换文件格式
        os.system(f"{FFMPEG_PATH} -y -i flv_temp.flv {title}.{fileType}")
        # 删除临时文件
        os.remove("flv_temp.flv")
    else:
        # MP4 流下载
        await download(streams[1].url, "audio_temp.m4s", "下载音频流")
        os.system(f"{FFMPEG_PATH} -y -i audio_temp.m4s {title}.{fileType}")
        # 删除临时文件
        os.remove("audio_temp.m4s")

    print(f"已下载为：{title}.{fileType}")

