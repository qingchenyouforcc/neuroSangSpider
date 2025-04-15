import json
import os

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

from fileManager import MAIN_PATH
from utils.string_tools import contain_text

import time
import requests
from bs4 import BeautifulSoup

remove_urls_index = []


def get_video_url(user_id):
    """获取视频url"""
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    url = f'https://space.bilibili.com/{user_id}/video'
    page_count = 1
    max_pages = 10  # 设置一个最大翻页次数，防止无限循环

    driver.get(url)
    video_list = []

    try:
        # 处理弹窗的代码
        try:
            driver.maximize_window()
            popup_wait = WebDriverWait(driver, 5)  # 等待弹窗最多 5 秒 (时间可调整)

            # 定位
            avatar_locator = (By.CSS_SELECTOR, 'div.go-login-btn')

            # print("等待头像元素出现...")
            wait = WebDriverWait(driver, 10)  # 等待头像最多10秒
            avatar_element = wait.until(EC.visibility_of_element_located(avatar_locator))
            # print("头像元素已找到。")

            # 执行鼠标悬停操作
            # print("执行鼠标悬停到头像的操作...")
            actions = ActionChains(driver)
            actions.move_to_element(avatar_element).perform()
            # print("鼠标悬停操作完成。")

            time.sleep(1)  # 短暂固定等待，可以根据实际情况调整或移除

            try:
                # print("执行鼠标移开 '登录' 按钮区域的操作 (移动到 body)...")
                body_element = driver.find_element(By.TAG_NAME, 'body')
                actions_move_to_body = ActionChains(driver)
                actions_move_to_body.move_to_element(body_element)
                actions_move_to_body.perform()
            except NoSuchElementException:
                print("警告：未找到 body 元素，无法执行移动到 body 的操作。")

            # 使用 CSS Selector
            close_button_locator = (By.CSS_SELECTOR, "div.close")

            # print("检查并等待 'div.close' 关闭按钮...")
            close_button = popup_wait.until(EC.element_to_be_clickable(close_button_locator))
            # print("找到 'div.close' 关闭按钮，尝试关闭...")
            close_button.click()
            # print("弹窗已关闭。")
            time.sleep(0.5)  # 等待关闭动画

        except (TimeoutException, NoSuchElementException):
            # 如果在等待时间内找不到按钮，或者按钮不存在，就认为没有弹窗或已关闭
            print("未找到弹窗关闭按钮，或弹窗未出现/已关闭。")
            path = os.path.join(MAIN_PATH, "crawlerCore")
            # try:
            #     screenshot_path = os.path.join(path, "error.png")
            #     driver.save_screenshot(screenshot_path)
            #     print(f"已保存截图: {screenshot_path}")
            # except Exception as img_e:
            #     print(f"保存截图失败: {img_e}")
    except Exception as e:
        print(f"处理弹窗时发生错误: {e}")

    time.sleep(3)

    title_elements = driver.find_elements(By.CLASS_NAME, 'title')

    # 单页爬取
    for title_element in title_elements:
        video_url = title_element.get_attribute('href')
        video_list.append({
            'url': video_url,
            'title': "",
        })

    # # 自动翻页
    # while page_count <= max_pages:
    #
    #     # 爬取页面
    #     print(f"\n--- 正在处理第 {page_count} 页 ---")
    #
    #     time.sleep(3)
    #
    #     title_elements = driver.find_elements(By.CLASS_NAME, 'title')
    #
    #     for title_element in title_elements:
    #         video_url = title_element.get_attribute('href')
    #         video_list.append({
    #             'url': video_url,
    #             'title': "",
    #         })
    #         # print(video_url)
    #     print(f"\n--- 第 {page_count} 页爬取完成 ---")
    #
    #     # 查找下一项
    #     try:
    #         wait = WebDriverWait(driver, 15)  # 使用之前的等待时间
    #
    #         # # 首先检查是否有任何匹配的元素（不用:not筛选）
    #         # all_buttons = driver.find_elements(By.CLASS_NAME,"vui_button.vui_pagenation--btn.vui_pagenation--btn-side")
    #         # print(f"找到 {len(all_buttons)} 个可能的按钮")
    #
    #         # # 检查这些按钮是否可见和可点击
    #         # for i, btn in enumerate(all_buttons):
    #         #     print(f"按钮 {i}:")
    #         #     print(f"  文本: {btn.text}")
    #         #     print(f"  可见: {btn.is_displayed()}")
    #         #     print(f"  启用: {not ('disabled' in btn.get_attribute('class'))}")
    #         #     print(f"  类名: {btn.get_attribute('class')}")
    #
    #         # # 检查拼写是否有问题
    #         # alternative_buttons = driver.find_elements(By.CSS_SELECTOR,"button.vui_button.vui_pagination--btn.vui_pagination--btn-side")
    #         # print(f"使用正确拼写找到 {len(alternative_buttons)} 个可能的按钮")
    #
    #         print("等待 '下一页' 按钮变为可点击...")
    #         next_button = wait.until(EC.element_to_be_clickable(all_buttons))
    #         print("按钮可点击。")
    #
    #         # 步骤 4: 点击按钮 (滚动到视图可能不再严格需要，但保留无害)
    #         # driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", next_button)
    #         # time.sleep(0.5)
    #         print("尝试点击按钮...")
    #         next_button.click()
    #         print("已点击“下一页”。")
    #         page_count += 1
    #
    #         # **关键步骤 5: 等待新页面/内容加载**
    #         time.sleep(3)  # 等待加载
    #
    #
    #     except TimeoutException:
    #         print("\n找不到“下一页”按钮或按钮不可点击 (超时)。可能已到达最后一页。")
    #         try:
    #             screenshot_path = f"timeout_page_{page_count}.png"
    #             driver.save_screenshot(screenshot_path)
    #             # print(f"已保存截图: {screenshot_path}")
    #         except Exception as img_e:
    #             print(f"保存截图失败: {img_e}")
    #         break
    #     except NoSuchElementException:
    #         print("\n找不到“下一页”按钮元素。可能已到达最后一页。")
    #         break
    #     except Exception as e:
    #         print(f"\n点击“下一页”时发生错误: {e}")
    #         break
    #
    #     if page_count > max_pages:
    #         print(f"\n已达到最大翻页次数 ({max_pages})。")

    # --- 清理 ---
    # print("\n爬取（或尝试）完成，关闭浏览器。")
    driver.quit()

    return video_list


def get_video_list(user_id, words_set):
    """处理url返回视频列表"""
    file_path = f"data/{user_id}_data.txt"

    videos = []
    temp_videos = get_video_url(user_id)

    temp_videos.remove(temp_videos[0])
    for i in range(0, int(len(temp_videos) / 2)):
        temp_videos.remove(temp_videos[0])

    # print("origin:")
    for video in temp_videos:
        # print(video['url'])
        video_url = video['url']
        video['title'] = resolve_url_to_title(video_url, words_set)
        # print(video)

    for video in temp_videos:
        video_title = video['title']
        if video_title is not None:
            videos.append(video)

    print("---------------------")
    os.chdir(MAIN_PATH)

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
    """解析视频url并转换为标题"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    video_title = soup.find('h1', class_='video-title special-text-indent').get('data-title')

    if contain_text(words_set, video_title):
        return video_title
