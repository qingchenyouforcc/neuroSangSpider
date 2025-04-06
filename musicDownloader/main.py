import asyncio
import os
from re import search

from musicDownloader.downloader import download_music
from utils.bili_tools import url2bv
from utils.fileManager import create_dir
from utils.string_tools import contain_text, remove_text_after_char, fileName_process

find_flag = False
create_dir("music")
search_result = []

def download_main(bv, output_fileName):
    """下载器主进程"""
    print(f"你选择了第{index + 1}个，开始下载歌曲")
    print(f"BVID:{bv}")
    print(f"title:{output_fileName}")

    # 运行下载器(异步函数)
    os.chdir("musicDownloader/music")
    asyncio.run(download_music(bv, output_fileName))


if __name__ == '__main__':
    os.chdir("..")
    file_name = 'crawlerCore/data/videos_list.txt'

    print("请输入你要查找的视频:")
    search_content = input()

    # 查找内容
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            find_line = line.lower()
            if search_content in find_line:
                search_result.append(line)
                find_flag = True

    if find_flag:
        search_seq = 1
        for result in search_result:
            print(f"{search_seq}.{result}")
            search_seq += 1
        print(f"找到{len(search_result)}个结果，请选择第几个(请输入数字)")

        # 处理信息
        index = int(input()) - 1
        bvid = url2bv(search_result[int(index)])
        title = fileName_process(remove_text_after_char(search_result[int(index)], ':')).replace(' ', '').replace('_',
                                                                                                                  '', 1)
        download_main(bvid, title)
    else:
        print(f"没有找到包含{search_content}的歌曲")
