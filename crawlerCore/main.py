from crawlerCore.videosList import show_video_list

# UP主列表 和 爬取视频需包含词
up_list = [351692111, 1880487363, 22535350, 3546612622166788, 5971855, 483178955]
words_set = ["合唱", "歌回"]

for up in up_list:
    show_video_list(up, words_set)

print("爬取完成")