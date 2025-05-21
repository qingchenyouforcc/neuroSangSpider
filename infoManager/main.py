
'''
将获取到的文件信息以json的形式存储,同时实现json和map的互相转换,以简化代码逻辑
也许也可以提高可读性awa
不过我不太会写python项目,希望能轻点喷
'''

from songList import songList

if __name__ == '__main__':
    print("Testing")

    # # test write
    # Info=songInfo("握握手","BV123456","2020/10/10","samuv")
    # print(Info.getItem())
    # totalList=songList()
    # totalList.appendInfo(Info)
    # Info=songInfo("握握手","BV123457","2020/10/09","samuv")
    # totalList.appendInfo(Info)
    # Info=songInfo("握握双手","BV123458","2020/10/08","samuv")
    # totalList.appendInfo(Info)
    # Info=songInfo("握握双手","BV123458","2020/10/08","samuv")
    # totalList.appendInfo(Info)
    # totalList.saveList(r".\data.json")
    # print(totalList.mapInfo)

    # # test read and unique
    # totalList = songList()
    # totalList.loadList(r".\data.json")
    # print(totalList.mapInfo)
    # print(totalList.selectInfo(3).getItem(),len(totalList.mapInfo["data"]))
    # totalList.uniqueByBV()
    # print(len(totalList.mapInfo["data"]))




