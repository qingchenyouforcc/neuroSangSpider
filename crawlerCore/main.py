from crawlerCore.videosList import w_video_list

import threading

from utils.fileManager import create_dir

# UP主列表 和 爬取视频需包含词
up_list = [351692111]
up_list = [351692111, 1880487363, 22535350, 3546612622166788, 5971855, 483178955]
words_set = ["合唱", "歌回"]

videos_temp_list = []
videos_list = []
videos_num = 0

threads = []

create_dir("data")

for up in up_list:
    t = threading.Thread(target=w_video_list, args=(up, words_set))
    t.start()
    threads.append(t)

for t in threads:
    t.join()


# for video in videos_list:
#     print(video)
#     videos_num += 1

print(f"爬取完成")