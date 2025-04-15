import requests
from bs4 import BeautifulSoup


def get_target(keyword):
    """
    爬取B站视频信息

    参数:
        keyword: 搜索关键词
    """
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

    def is_valid_title(title):
        """检查标题是否有效"""
        if not title or title == "标题提取失败":
            return False
        return True

    def scrape_page(url):
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
                    if not is_valid_title(title):
                        invalid_count += 1
                        continue

                    seen_videos.add(video_url)

                    video_info = {
                        'url': video_url,
                        'title': title,
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

    # 爬取
    first_page_url = f'https://search.bilibili.com/all?keyword={keyword}'
    videos = scrape_page(first_page_url)
    print('已经完成b站搜索视频爬取')
    print(f"总计获取 {len(videos)} 个有效视频数据")

    # 保存结果
    file_path = f"data\\search_data.txt"
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in videos:
                f.write(f"{item['title']}:{item['url']}" + "\n")
        print(f"列表数据已写入到: {file_path}")
    except IOError as e:
        print(f"写入文件时发生错误: {e}")


def search_song_online(search_content):
    """调用联网搜索"""
    get_target("[neuro]歌回" + search_content)
