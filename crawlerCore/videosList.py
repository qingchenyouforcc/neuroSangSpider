import os
import time
import requests

# noinspection PyUnresolvedReferences
from selenium import webdriver
# noinspection PyUnresolvedReferences
from selenium.webdriver.common.by import By
# noinspection PyUnresolvedReferences
from selenium.webdriver.chrome.options import Options
# noinspection PyUnresolvedReferences
from selenium.webdriver.support.ui import WebDriverWait
# noinspection PyUnresolvedReferences
from selenium.webdriver.support import expected_conditions as EC
# noinspection PyUnresolvedReferences
from selenium.common.exceptions import NoSuchElementException, TimeoutException
# noinspection PyUnresolvedReferences
from selenium.webdriver.common.action_chains import ActionChains

from utils.fileManager import MAIN_PATH
from utils.string_tools import contain_text
from utils.bili_tools import url2bv
from bs4 import BeautifulSoup

from infoManager.songList import songList

remove_urls_index = []


def get_video_url(user_id):
    """获取视频url"""
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    url = f'https://space.bilibili.com/{user_id}/video'
    video_list = []

    driver.get(url)
    time.sleep(3)

    title_elements = driver.find_elements(By.CLASS_NAME, 'title')

    # 单页爬取
    for title_element in title_elements:
        video_url = title_element.get_attribute('href')
        video_list.append({
            'url': video_url,
            'title': "",
        })

    driver.quit()

    return video_list


def get_video_list(user_id, words_set):
    """处理url返回视频列表"""
    file_path = f"data/{user_id}_data.json"

    videos = songList()
    temp_videos = get_video_url(user_id)

    temp_videos.remove(temp_videos[0])
    for i in range(0, int(len(temp_videos) / 2)):
        temp_videos.remove(temp_videos[0])

    # print("origin:")
    for video in temp_videos:
        # print(video['url'])
        video_url = video['url']
        video_info=resolve_url_to_info(video_url, words_set)
        if video_info is not None:
            video_dict=video_info
            video_dict['url']=video_url
            video_dict["bv"]=url2bv(video_url)
            videos.appendInfo(video_dict)

    print("---------------------")
    os.chdir(MAIN_PATH)

    videos.saveList(file_path)



def resolve_url_to_title(url, words_set):
    """解析视频url并转换为标题"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    video_title = soup.find('h1', class_='video-title special-text-indent').get('data-title')

    if contain_text(words_set, video_title):
        return video_title

def resolve_url_to_info(url, words_set):
    """解析视频url并转换为详细信息(title,author,date)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')

        video_title = soup.find('h1', class_='video-title special-text-indent').get('data-title')
        video_author = soup.find('a', class_='up-name').getText(strip=True)
        video_date=soup.find('div', class_='pubdate-ip-text').getText(strip=True)
        if contain_text(words_set, video_title):
            return {"title": video_title, "author": video_author, "date": video_date}
        else:
            return None
    except Exception as search_e:
        print(f"提取信息时出错: {search_e}")
        return None
