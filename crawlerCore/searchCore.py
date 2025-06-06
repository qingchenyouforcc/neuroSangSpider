import random
import time

import requests
from bs4 import BeautifulSoup

from infoManager.SongList import SongList
from utils.bili_tools import url2bv


def get_target(keyword, page=3):
    """爬取B站视频信息"""
    seen_videos = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36'
    }

    def get_title(video_item):
        """增强的标题提取函数"""
        try:
            # 尝试多种可能的标题元素选择器
            title_elem = (
                    video_item.find('h3', class_='bili-video-card__info--tit') or
                    video_item.find('a', class_='title') or
                    video_item.find('div', class_='title') or
                    video_item.find('h3', class_='title')
            )

            if title_elem:
                # 优先获取title属性
                title = title_elem.get('title', '')
                if not title:
                    # 如果没有title属性，获取文本内容
                    title = title_elem.get_text(strip=True)
                return title

            # 如果上述方法都失败，尝试直接从链接获取title
            link = video_item.find('a')
            if link:
                return link.get('title', '') or link.get_text(strip=True)

            return "标题提取失败"
        except Exception as search_e:
            print(f"提取标题时出错: {search_e}")
            return "标题提取失败"

    def get_date(video_item):
        """模仿着写的获取日期函数"""
        # print(video_item)
        try:
            date_elem = video_item.find('span', class_='bili-video-card__info--date')

            if date_elem:
                date = date_elem.get_text(strip=True)
                return date
            return None
        except Exception as search_e:
            print(f"提取日期时出错: {search_e}")
            return ""

    def get_author(video_item):
        """模仿着写的获取作者函数"""
        # print(video_item)
        try:
            author_elem = video_item.find('span', class_='bili-video-card__info--author')

            if author_elem:
                author = author_elem.get_text(strip=True)
                return author
            return None
        except Exception as search_e:
            print(f"提取up主名称时出错: {search_e}")
            return ""

    def is_valid_title(title):
        """检查标题是否有效"""
        if not title or title == "标题提取失败":
            return False
        return True

    def crawler_page(url):
        """爬取页面"""
        try:
            html = requests.get(url, headers=headers, timeout=10)
            html.raise_for_status()  # 检查请求是否成功
            bs = BeautifulSoup(html.content, 'html.parser')

            # 多种可能的视频项选择器
            items = (
                # bs.find_all('div', class_='video-list-item') or
                bs.find_all('div', class_='bili-video-card')
                # bs.find_all('li', class_='video-item')
            )

            if not items:
                print(f"警告：在页面 {url} 未找到视频列表")

            page_data = []
            duplicate_count = 0
            invalid_count = 0

            for v_item in items:
                try:
                    if len(page_data) > 10:
                        break

                    video_url = v_item.find('a')['href'].replace("//", "")

                    if video_url in seen_videos:
                        duplicate_count += 1
                        continue

                    title = get_title(v_item)
                    date = get_date(v_item)
                    author = get_author(v_item)

                    # print(title)
                    # print(date)
                    # print(video_url)
                    # print(author)

                    if not is_valid_title(title):
                        invalid_count += 1
                        continue

                    seen_videos.add(video_url)

                    video_info = {
                        'url': video_url,
                        'title': title,
                        'date': date,
                        "author": author,
                        "bv": url2bv(video_url)
                    }
                    page_data.append(video_info)


                except Exception as search_e:
                    print(f"处理视频项时出错: {search_e}")
                    continue

            if duplicate_count > 0:
                print(f"在当前页面发现 {duplicate_count} 个重复视频，已跳过")
            if invalid_count > 0:
                print(f"在当前页面发现 {invalid_count} 个无效标题，已跳过")

            return page_data

        except Exception as search_e:
            print(f"爬取页面时发生错误: {search_e}")
            return None

    # 爬取
    first_page_url = f'https://search.bilibili.com/all?keyword={keyword}'
    videos = crawler_page(first_page_url)
    print(f"已经完成b站第 1 页爬取，本页获取 {len(videos)} 个视频")
    print(videos)

    try:
        for i in range(2, page + 1):
            n_url = f'https://search.bilibili.com/all?keyword={keyword}&page={i}&o={(i - 1) * 30}'
            new_data = crawler_page(n_url)
            videos += new_data
            print(f'已经完成b站第 {i} 页爬取，本页获取 {len(new_data)} 个视频')
            time.sleep(random.uniform(1, 2))

        # 最终去重
        initial_len = len(videos)
        videos = list(dict.fromkeys(videos))
        final_len = len(videos)

        if initial_len != final_len:
            print(f"最终去重移除了 {initial_len - final_len} 条重复数据")

    except TypeError as e:
        print(f"爬取页面时发生错误: {e}")

    print(f"总计获取 {len(videos)} 个有效视频数据")
    print('已经完成b站搜索视频爬取')


    # 返回结果
    return videos


def search_song_online(search_content, page):
    """调用联网搜索,返回songList"""
    result_list = SongList()
    result_list.dictInfo = {"data": get_target("neuro " + search_content, page)}
    # result_list.dictInfo = {"data": get_target("evil" + search_content)}

    # debug
    print(f"搜索结果:{result_list.dictInfo}")

    result_list.sync_json()
    return result_list
