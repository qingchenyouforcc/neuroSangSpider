import asyncio
import os

from loguru import logger
from qfluentwidgets import MessageBox
from config import cfg
from musicDownloader.downloader import download_music
from text_tools import format_date_str
from utils.file_tools import create_dir, MAIN_PATH, part2all, load_from_all_data
from utils.text_tools import fileName_process

create_dir("music")
search_result = []
bvid = ""
title = ""


def search_song(search_content):
    """从文件中搜索歌曲"""
    os.chdir(MAIN_PATH)
    find_flag = False
    file_name = 'data/videos_list.txt'

    # 查找内容
    global search_result
    search_result = []

    # 重置videos_list.txt
    os.remove(file_name)
    part2all("data", "videos_list.txt")

    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            find_line = line.lower()
            if search_content in find_line:
                search_result.append(line)
                find_flag = True

    if find_flag:
        logger.info("搜索结果:")
        search_seq = 1
        for result in search_result:
            logger.info(f"{search_seq}.{result}")
            search_seq += 1
        # logger.info(f"找到{len(search_result)}个结果，请选择第几个(请输入数字)")

        """
        # 处理信息
        bvid = url2bv(search_result[int(index)])
        title = fileName_process(remove_text_after_char(search_result[int(index)], ':')).replace(' ', '').replace('_',
                                                                                                                  '', 1)
        """

        # run_download(bvid, title, index)
        return search_result

    else:
        logger.info(f"没有找到包含{search_content}的歌曲")
        return None


def search_songList(search_content):
    """重写的搜索方法,读取json文件搜索,存储search_result并返回标题列表"""
    # 切换路径
    os.chdir(MAIN_PATH)

    total_data = load_from_all_data("data")
    global search_result
    search_result = []
    str_result = []
    filter_list = ["neuro", "歌", "手书", "切片", "熟肉", "[evil", "社区", "21"]
    black_list = ["李19"]

    search_resultlist = total_data
    search_resultlist.search_by_title(search_content)

    if len(search_resultlist.getData()) == 0:
        return None

    search_resultlist.unique_by_bv()
    search_result = search_resultlist.getData()
    for item in search_result:
        if any(blackWord in item['author'].lower() for blackWord in black_list):
            continue
        else:
            if any(filterWord in item['title'].lower() for filterWord in filter_list):
                tmp_str = [item['title'], item['author'].replace('\n', ''), format_date_str(item['date']), item['bv']]
                str_result.append(tmp_str)

    return str_result


def run_download(index, fileType=""):
    """运行下载器"""
    bv = search_result[int(index)]["bv"]
    output_fileName = fileName_process(search_result[int(index)]["title"]).replace(' ', '').replace(
        '_', '', 1)
    logger.info(f"你选择了第{index + 1}个，开始下载歌曲")
    logger.info(f"BVID:{bv}")
    logger.info(f"title:{output_fileName}")

    # 运行下载器(异步函数)
    os.chdir(MAIN_PATH)
    os.chdir("music")
    
    # 检查文件是否已经存在
    if fileType:
        file_exists = os.path.exists(f"{output_fileName}.{fileType}")
    else:
        file_exists = os.path.exists(f"{output_fileName}.mp3")
    
    # 如果文件存在，弹出提示窗口
    if file_exists:
        w = MessageBox(
            '文件已存在',
            f"文件 '{output_fileName}.{fileType or 'mp3'}' 已存在。是否覆盖？",
            cfg.MAIN_WINDOW
        )

        w.setClosableOnMaskClicked(True)
        w.setDraggable(True)

        if not w.exec():
            logger.info("用户取消下载。")
            return
    
    if fileType:
        asyncio.run(download_music(bv, output_fileName, fileType))
    else:
        asyncio.run(download_music(bv, output_fileName, "mp3"))
