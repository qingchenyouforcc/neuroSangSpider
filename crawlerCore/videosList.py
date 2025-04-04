from time import sleep
from urllib.parse import urlencode

# noinspection PyUnresolvedReferences
from selenium import webdriver
# noinspection PyUnresolvedReferences
from selenium.webdriver.common.by import By
# noinspection PyUnresolvedReferences
from selenium.webdriver.chrome.options import Options

import time
import math
import requests
from bs4 import BeautifulSoup

remove_urls_index = []

def get_video_list(user_id):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    url = f'https://space.bilibili.com/{user_id}/video'
    driver.get(url)

    # 等待页面加载
    time.sleep(3)

    video_list = []
    title_elements = driver.find_elements(By.CLASS_NAME, 'title')

    for title_element in title_elements:
        video_url = title_element.get_attribute('href')
        video_list.append({
            'url': video_url,
            'title': "",
        })

    driver.quit()

    return video_list


def w_video_list(user_id, words_set):
    file_path = f"data/{user_id}_data.txt"

    videos = []
    temp_videos = get_video_list(user_id)

    temp_videos.remove(temp_videos[0])
    for i in range(0, int(len(temp_videos)/2)):
        temp_videos.remove(temp_videos[0])

    print("origin:")
    for video in temp_videos:
        # print(video['url'])
        video_url = video['url']
        video['title'] = resolve_url_to_title(video_url, words_set)
        print(video)

    for video in temp_videos:
        video_title = video['title']
        if video_title is not None:
            videos.append(video)


    print("---------------------")

    for video in videos:
        print(video)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in videos:
                f.write(f"{item['title']}:{item['url']}" + "\n")
        print(f"列表数据已写入到: {file_path}")
    except IOError as e:
        print(f"写入文件时发生错误: {e}")



def resolve_url_to_title(url, words_set):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    video_title = soup.find('h1', class_='video-title special-text-indent').get('data-title')

    if contain_text(words_set, video_title):
        return video_title


def contain_text(words_set, text):
    for word in words_set:
        if word in text:
            return True
    return False
