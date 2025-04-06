# NeuroSangSpider

## 项目简介

这是一个基于 `Python 3.13` 开发的爬虫程序，用于从 Bilibili（哔哩哔哩）爬取 **Neuro/Evil** 的歌曲的视频内容。通过自定义 **UP 主列表** 和 **关键词**，可以灵活调整爬取目标。程序计划实现 **本地下载** 和 **播放** 功能，但目前 GUI 界面仍在开发中，核心爬虫逻辑已基本完成。

**请注意，该爬虫目前仅支持爬取每个up的最新的前30个视频（也就是第一页，不过后续可能会增加爬取范围设置）** 

---

## 特性概述
### ✅ 已实现功能
- 获取歌回列表，支持按设置的 UP 主和关键词筛选目标视频
- 支持搜索歌曲，下载指定歌回（下一阶段目标，开发中）
- 使用 `PyQt6` 构建 GUI 基础框架（开发中）

### 🚧 正在计划中
- 完成 GUI 界面，提供可视化交互（如进度条、筛选设置面板）
- 将爬取的音乐文件下载至本地
- 集成本地音频播放功能

---


## 安装步骤
```bash
# 克隆仓库
git clone https://github.com/qingchenyouforcc/neuroSangSpider

# 初始化虚拟环境（推荐）
python3.13 -m venv venv
source venv/bin/activate    # Linux/macOS 或 venv\Scripts\activate (Windows)

# 安装依赖
pip install -r requirements.txt
