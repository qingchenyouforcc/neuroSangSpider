from crawlerCore.videosList import show_video_list

# UP主列表 和 爬取视频需包含词
up_list = [351692111, 1880487363, 22535350, 3546612622166788, 5971855, 483178955]
words_set = ["合唱", "歌回"]

videos_temp_list = []
videos_list = []
videos_num = 0

for up in up_list:
    videos = show_video_list(up, words_set)
    videos_temp_list.append(videos)

for videos in videos_temp_list:
    for video in videos:
        videos_list.append(video)

for video in videos_list:
    print(video)
    videos_num += 1

print(f"爬取完成，共{videos_num}个视频")