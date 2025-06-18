import json
from pathlib import Path
from typing import Literal

from loguru import logger


class SongList:
    def __init__(self, dir_path: Path | None = None):
        """创建空列表"""
        self.dictInfo = {"data": []}
        if dir_path is not None:
            self.load_list(dir_path)

    def __len__(self):
        """返回数据长度"""
        return len(self.dictInfo["data"])

    def clear(self):
        """清除列表"""
        self.dictInfo = {"data": []}

    def append_info(self, song_info: dict):
        """插入一条歌曲dict信息"""
        # 过滤掉值为方法的条目
        clean_song_info = {k: v for k, v in song_info.items() if not callable(v)}
        self.dictInfo["data"].append(clean_song_info)

    def append_list(self, slist: "SongList"):
        """插入一组songList信息"""
        tmp_list = slist.get_data()
        for songInfo in tmp_list:
            self.append_info(songInfo)
        self.unique_by_bv()

    def select_info(self, index: int) -> dict | None:
        """
        选择index对应的歌曲信息

        参数:
            index(int):指定项目的下标

        返回:
            (dict):包含url,bv,date,author,title的dict
        """
        if 0 <= index < len(self.dictInfo["data"]):
            return self.dictInfo["data"][index]

    def save_list(self, path: Path):
        """保存文件到指定的路径和文件名下"""
        try:
            path.write_text(json.dumps(self.dictInfo, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.opt(exception=True).warning("json文件保存错误")

    def load_list(self, path: Path):
        """从指定的路径和文件名下载入文件"""
        if not path.exists():
            return

        try:
            self.dictInfo = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.opt(exception=True).warning("json文件读取错误:")

    def unique_by_bv(self):
        """根据bv号进行去重"""
        try:
            result = {songInfo["bv"]: songInfo for songInfo in self.get_data()}
            self.dictInfo = {"data": list(result.values())}
        except Exception:
            logger.opt(exception=True).warning("去重模块错误:")

    def search_by_title(self, title: str):
        """仅保留标题包含关键字的video项"""
        songs = [songInfo for songInfo in self.dictInfo["data"] if title.lower() in songInfo["title"].lower()]
        self.dictInfo = {"data": songs}

    def get_data(self) -> list[dict]:
        """获取歌曲信息dict的列表,列表项为"""
        return self.dictInfo["data"]

    def remove_blacklist(self, words: str | list[str], types: Literal[0, 1] = 0):
        """
        删除所有特定位置带有words的项目

        参数:
            words(str/list): 字符串或字符串列表
            types(int): (0)/1
                0:默认值,在标题中匹配
                1:在作者中匹配

        返回:
            返回0为成功操作对象
            其他值为异常
        """
        words = [words] if not isinstance(words, list) else words
        if any(not isinstance(word, str) for word in words):
            raise TypeError("words参数类型错误")

        key = "author" if types == 1 else "title"
        try:
            result_list = []
            for songInfo in self.dictInfo["data"]:
                if all(word.lower() not in songInfo[key].lower() for word in words):
                    result_list.append(songInfo)
            self.dictInfo = {"data": result_list}
            return 0
        except Exception:
            logger.opt(exception=True).warning("排除模块错误")
            return 1

    def filter_data(self, words: str | list[str], types: Literal[0, 1] = 0):
        """
        仅保留所有特定位置带有words的列表项

        参数:
            words(str/list): 字符串或字符串列表
            types(int): (0)/1
                0:默认值,在标题中匹配
                1:在作者中匹配

        返回:
            返回0为成功操作对象
            其他值为异常
        """
        words = [words] if not isinstance(words, list) else words
        if any(not isinstance(word, str) for word in words):
            raise TypeError("words参数类型错误")
        key = "author" if types == 1 else "title"

        try:
            result_list = []
            for songInfo in self.dictInfo["data"]:
                if any(word.lower() in songInfo[key].lower() for word in words):
                    result_list.append(songInfo)

            self.dictInfo = {"data": result_list}
            return 0
        except Exception:
            logger.opt(exception=True).warning("过滤模块错误")
            return 1
