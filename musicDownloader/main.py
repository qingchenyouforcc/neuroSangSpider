import asyncio
import os

from musicDownloader.downloader import download_music, download_music_ogg
from utils.bili_tools import url2bv
from utils.fileManager import create_dir, MAIN_PATH, part2all,load_from_all_data
from utils.string_tools import remove_text_after_char, fileName_process

from infoManager.SongList import SongList


create_dir("music")
search_result = []
bvid = ""
title = ""


def search_song(search_content):
    '''从文件中搜索歌曲'''
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
        print("搜索结果:")
        search_seq = 1
        for result in search_result:
            print(f"{search_seq}.{result}")
            search_seq += 1
        # print(f"找到{len(search_result)}个结果，请选择第几个(请输入数字)")

        """
        # 处理信息
        bvid = url2bv(search_result[int(index)])
        title = fileName_process(remove_text_after_char(search_result[int(index)], ':')).replace(' ', '').replace('_',
                                                                                                                  '', 1)
        """

        # run_download(bvid, title, index)
        return search_result

    else:
        print(f"没有找到包含{search_content}的歌曲")

def search_songList(search_content):
    """重写的搜索方法,读取json文件搜索,存储search_result并返回标题列表"""
    total_data=load_from_all_data("data")
    global search_result
    search_result = []
    str_result = []

    search_resultlist=total_data
    search_resultlist.search_by_title(search_content)

    if len(search_resultlist.getData()) == 0:
        return None

    search_resultlist.unique_by_bv()
    search_result=search_resultlist.getData()
    for item in search_result:
        #作者名中文对齐
        tmp_str=f"{item['title']}\n\tup:{item['author']:{chr(12288)}<15}{item['bv']:<15}{item['date']:<20}"
        str_result.append(tmp_str)

    return str_result


def run_download(index, fileType=""):
    """运行下载器"""
    bv = search_result[int(index)]["bv"]
    output_fileName = fileName_process(search_result[int(index)]["title"]).replace(' ', '').replace(
        '_', '', 1)
    print(f"你选择了第{index + 1}个，开始下载歌曲")
    print(f"BVID:{bv}")
    print(f"title:{output_fileName}")

    # 运行下载器(异步函数)
    os.chdir(MAIN_PATH)
    os.chdir("music")
    if fileType == "ogg":
        asyncio.run(download_music_ogg(bv, output_fileName))
    else:
        asyncio.run(download_music(bv, output_fileName))
