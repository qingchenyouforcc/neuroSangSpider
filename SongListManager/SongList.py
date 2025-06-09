import json

"""用于保存歌曲列表"""


class SongList(object):
    def __init__(self, dir_path: str = ""):
        """创建空列表"""
        self.jsonInfo = json.dumps({})
        self.dictInfo = {"data": []}
        if dir_path != "":
            self.load_list(dir_path)

    def __len__(self):
        """返回数据长度"""
        return len(self.dictInfo["data"])

    def clear(self):
        """清除列表"""
        self.dictInfo = {"data": []}
        self.sync_json()

    def sync_json(self):
        """将map的手动更改同步到json变量"""
        # 过滤掉值为方法的条目
        clean_dict = {k: v for k, v in self.dictInfo.items() if not callable(v)}
        # 创建一个新的字典，仅包含可序列化的项
        serializable_dict = {k: v for k, v in clean_dict.items() if isinstance(v, (str, int, float, bool, type(None)))}
        self.jsonInfo = json.dumps(serializable_dict)

    def append_info(self, song_info: dict):
        """插入一条歌曲dict信息"""
        # 过滤掉值为方法的条目
        clean_song_info = {k: v for k, v in song_info.items() if not callable(v)}
        self.dictInfo["data"].append(clean_song_info)
        self.sync_json()

    def append_list(self, slist: 'SongList'):
        """插入一组songList信息"""
        if not isinstance(slist, SongList):
            raise TypeError("列表插入失败:", type(slist))
        tmp_list = slist.get_data()
        for songInfo in tmp_list:
            self.append_info(songInfo)
        self.unique_by_bv()

    def select_info(self, index: int):
        """
        选择index对应的歌曲信息

        参数:
            index(int):指定项目的下标

        返回:
            (dict):包含url,bv,date,author,title的dict
        """
        if index < len(self.dictInfo["data"]):
            song_map_info = self.dictInfo["data"][index]
            return song_map_info
        else:
            return None

    def save_list(self, dir_path: str):
        """保存文件到指定的路径和文件名下"""
        try:
            with open(dir_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.dictInfo, ensure_ascii=False, indent=4))
        except Exception as e:
            print("json文件保存错误:", e)

    def load_list(self, dir_path: str):
        """从指定的路径和文件名下载入文件"""
        try:
            with open(dir_path, 'r', encoding='utf-8') as f:
                self.dictInfo = json.load(f)
            self.jsonInfo = json.dumps(self.dictInfo)
        except Exception as e:
            print("json文件读取错误:", e)

    def unique_by_bv(self):
        """根据bv号进行去重"""
        try:
            result_list = []
            bv_checker = []
            for songInfo in self.get_data():
                if songInfo["bv"] not in bv_checker:
                    bv_checker.append(songInfo["bv"])
                    result_list.append(songInfo)
            self.dictInfo = {"data": result_list}
            self.sync_json()
        except Exception as e:
            print("去重模块错误:", e)

    def search_by_title(self, title: str):
        """仅保留标题包含关键字的video项"""
        result_list = []
        for songInfo in self.dictInfo["data"]:
            if songInfo["title"].lower().find(title.lower()) != -1:
                result_list.append(songInfo)
        self.dictInfo = {"data": result_list}
        self.sync_json()

    def get_data(self):
        """获取歌曲信息dict的列表,列表项为"""
        return self.dictInfo["data"]

    def remove_blacklist(self, words, types=0):
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
        try:
            result_list = []
            if isinstance(words, list):
                for songInfo in self.dictInfo["data"]:
                    for word in words:
                        if not isinstance(word, str):
                            raise TypeError(f"words参数错误,出错的word:{word}")
                        word = word.lower()
                        if types == 0:
                            if word in songInfo["title"].lower():
                                continue
                        elif types == 1:
                            if word in songInfo["author"].lower():
                                continue
                        else:
                            raise TypeError("types参数范围错误")
                    result_list.append(songInfo)
            elif isinstance(words, str):
                for songInfo in self.dictInfo["data"]:
                    word = words.lower()
                    if types == 0:
                        if word in songInfo["title"].lower():
                            continue
                    elif types == 1:
                        if word in songInfo["author"].lower():
                            continue
                    else:
                        raise TypeError("types参数范围错误")
                    result_list.append(songInfo)
            else:
                raise TypeError(f"words参数类型错误:{type(words)}")
            # noinspection PyUnreachableCode
            self.dictInfo = {"data": result_list}
            self.sync_json()
            return 0
        except Exception as e:
            print("排除模块错误:", e)
            return 1

    def filter_data(self, words, types=0):
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
        try:
            result_list = []
            if isinstance(words, list):
                for songInfo in self.dictInfo["data"]:
                    for word in words:
                        if not isinstance(word, str):
                            raise TypeError(f"words参数错误,出错的word:{word}")
                        word = word.lower()
                        if types == 0:
                            if word in songInfo["title"].lower():
                                result_list.append(songInfo)
                                break
                        elif types == 1:
                            if word in songInfo["author"].lower():
                                result_list.append(songInfo)
                                break
                        else:
                            raise TypeError("types参数范围错误")
            elif isinstance(words, str):
                for songInfo in self.dictInfo["data"]:
                    word = words.lower()
                    if types == 0:
                        if word in songInfo["title"].lower():
                            result_list.append(songInfo)
                            continue
                    elif types == 1:
                        if word in songInfo["author"].lower():
                            result_list.append(songInfo)
                            continue
                    else:
                        raise TypeError("types参数范围错误")
            else:
                raise TypeError(f"words参数类型错误:{type(words)}")

            # noinspection PyUnreachableCode
            self.dictInfo = {"data": result_list}
            self.sync_json()
            return 0
        except Exception as e:
            print("过滤模块错误:", e)
            return 1
