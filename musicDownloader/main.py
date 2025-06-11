import asyncio
import os
import warnings

from loguru import logger
from qfluentwidgets import MessageBox

from SongListManager.SongList import SongList
from config import cfg
from musicDownloader.downloader import download_music
from utils.file_tools import create_dir, MAIN_PATH, part2all, load_from_all_data
from utils.text_tools import fileName_process

create_dir("music")
bvid = ""
title = ""

@warnings.deprecated("被废弃的用法,对应的函数替换为`search_song_list`")
def search_song(search_content):
    """从文件中搜索歌曲"""
    os.chdir(MAIN_PATH)
    find_flag = False
    file_name = 'data/videos_list.txt'

    # 查找内容
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


def search_song_list(search_content):
    """
    重写的搜索方法

    参数:
        search_result(str):搜索的关键字

    返回:
        search_result_list:
            (SongList):搜索结果
            (None):未搜索到结果,返回空
    """
    # 切换路径
    os.chdir(MAIN_PATH)

    total_data = load_from_all_data("data")
    if total_data is None:
        return None
    filter_list = cfg.filter_list
    black_author_list = cfg.black_author_list

    search_result_list = total_data
    search_result_list.search_by_title(search_content)

    search_result_list.unique_by_bv()
    search_result_list.remove_blacklist(black_author_list, 1)
    search_result_list.filter_data(filter_list, 0)

    if len(search_result_list.get_data()) == 0:
        return None

    return search_result_list


def run_download(index, search_list: SongList, file_type=""):
    """运行下载器"""
    bv = search_list.select_info(index)["bv"]
    file_name = search_list.select_info(index)["title"]
    output_file_name = fileName_process(file_name).replace(' ', '').replace(
        '_', '', 1)
    logger.info(f"你选择了第{index + 1}个，开始下载歌曲")
    logger.info(f"BVID:{bv}")
    logger.info(f"title:{output_file_name}")

    # 运行下载器(异步函数)
    os.chdir(MAIN_PATH)
    os.chdir("music")

    # 检查文件是否已经存在
    if file_type:
        file_exists = os.path.exists(f"{output_file_name}.{file_type}")
    else:
        file_exists = os.path.exists(f"{output_file_name}.mp3")

    # 如果文件存在，弹出提示窗口
    if file_exists:
        w = MessageBox(
            '文件已存在',
            f"文件 '{output_file_name}.{file_type or 'mp3'}' 已存在。是否覆盖？",
            cfg.MAIN_WINDOW
        )

        w.setClosableOnMaskClicked(True)
        w.setDraggable(True)

        if not w.exec():
            logger.info("用户取消下载。")
            return

    if file_type:
        asyncio.run(download_music(bv, output_file_name, file_type))
    else:
        asyncio.run(download_music(bv, output_file_name, "mp3"))
