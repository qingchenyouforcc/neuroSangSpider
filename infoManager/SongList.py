import json

"""用于保存歌曲列表"""
class SongList(object):
    def __init__(self,dirPath:str=""):
        """创建空列表"""
        self.jsonInfo = json.dumps({})
        self.dictInfo ={"data":[]}
        if dirPath != "":
            self.load_list(dirPath)

    def sync_json(self):
        """将map的手动更改同步到json变量"""
        # 过滤掉值为方法的条目
        clean_dict = {k: v for k, v in self.dictInfo.items() if not callable(v)}
        # 创建一个新的字典，仅包含可序列化的项
        serializable_dict = {k: v for k, v in clean_dict.items() if isinstance(v, (str, int, float, bool, type(None)))}
        self.jsonInfo = json.dumps(serializable_dict)

    def append_info(self, songInfo: dict):
        """插入一条歌曲dict信息"""
        # 过滤掉值为方法的条目
        clean_song_info = {k: v for k, v in songInfo.items() if not callable(v)}
        self.dictInfo["data"].append(clean_song_info)
        self.sync_json()

    def append_list(self, slist):
        """插入一组songList信息"""
        tmplist=slist.getData()
        for songInfo in tmplist:
            self.append_info(songInfo)


    def select_info(self, index:int):
        """
        选择index对应的歌曲信息
        """
        if index < len(self.dictInfo["data"]):
            songMapInfo = self.dictInfo["data"][index]
            return songMapInfo
        else:
            return None

    def save_list(self, dirPath:str):
        """保存文件到指定的路径和文件名下"""
        try:
            with open(dirPath,'w',encoding='utf-8') as f:
                f.write(json.dumps(self.dictInfo, ensure_ascii=False, indent=4))
        except Exception as e:
            print("json文件保存错误:",e)

    def load_list(self, dirPath:str):
        """从指定的路径和文件名下载入文件"""
        try:
            with open(dirPath,'r',encoding='utf-8') as f:
                self.dictInfo = json.load(f)
            self.jsonInfo = json.dumps(self.dictInfo)
        except Exception as e:
            print("json文件读取错误:",e)

    def unique_by_bv(self):
        """对内容根据bv号进行去重"""
        try:
            resultlist=[]
            bvChecker=[]
            for songInfo in self.getData():
                if songInfo["bv"] not in bvChecker:
                    bvChecker.append(songInfo["bv"])
                    resultlist.append(songInfo)
            self.dictInfo={"data":resultlist}
            self.sync_json()
        except Exception as e:
            print("去重模块错误:",e)

    def search_by_title(self, title:str):
        """仅保留包含关键字的video项"""
        resultList=[]
        for songInfo in self.dictInfo["data"]:
            if songInfo["title"].lower().find(title.lower()) != -1:
                resultList.append(songInfo)
        self.dictInfo={"data":resultList}
        self.sync_json()

    def getData(self):
        """获取歌曲信息dict的列表,包含url,bv,date,"""
        return self.dictInfo["data"]