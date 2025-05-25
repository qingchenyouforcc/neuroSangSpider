import json

"""用于保存歌曲列表"""
class songList(object):
    def __init__(self,dirPath:str=""):
        """创建空列表"""
        self.jsonInfo = json.dumps({})
        self.dictInfo ={"data":[]}
        if dirPath != "":
            self.loadList(dirPath)

    def syncJson(self):
        """将map的手动更改同步到json变量"""
        self.jsonInfo = json.dumps(self.dictInfo)

    def appendInfo(self, songInfo:dict):
        """插入一条歌曲dict信息"""
        self.dictInfo["data"].append(songInfo)
        self.syncJson()

    def appendList(self, slist):
        """插入一组songList信息"""
        tmplist=slist.getData()
        for songInfo in tmplist:
            self.appendInfo(songInfo)


    def selectInfo(self,index:int):
        """
        选择index对应的歌曲信息
        """
        if index < len(self.dictInfo["data"]):
            songMapInfo = self.dictInfo["data"][index]
            return songMapInfo
        else:
            return None

    def saveList(self,dirPath:str):
        """保存文件到指定的路径和文件名下"""
        try:
            with open(dirPath,'w',encoding='utf-8') as f:
                f.write(json.dumps(self.dictInfo, ensure_ascii=False, indent=4))
        except Exception as e:
            print(e)

    def loadList(self,dirPath:str):
        """从指定的路径和文件名下载入文件"""
        try:
            with open(dirPath,'r',encoding='utf-8') as f:
                self.dictInfo = json.load(f)
            self.jsonInfo = json.dumps(self.dictInfo)
        except Exception as e:
            print("json文件读取错误:",e)

    def uniqueByBV(self):
        """对内容根据bv号进行去重"""
        try:
            resultlist=[]
            bvChecker=[]
            for songInfo in self.getData():
                if songInfo["bv"] not in bvChecker:
                    bvChecker.append(songInfo["bv"])
                    resultlist.append(songInfo)
            self.dictInfo={"data":resultlist}
            self.syncJson()
        except Exception as e:
            print("去重模块错误:",e)

    def searchByTitle(self,title:str):
        """仅保留包含关键字的video项"""
        resultList=[]
        for songInfo in self.dictInfo["data"]:
            if songInfo["title"].lower().find(title) != -1:
                resultList.append(songInfo)
        self.dictInfo={"data":resultList}
        self.syncJson()

    def getData(self):
        """获取歌曲信息dict的列表"""
        return self.dictInfo["data"]