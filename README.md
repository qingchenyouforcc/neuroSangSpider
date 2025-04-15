# NeuroSongSpider

## 项目简介

这是一个基于 `Python 3.13` 开发的爬虫程序，用于从 Bilibili（哔哩哔哩）爬取 **Neuro/Evil** 的歌曲的视频内容。

~~(当然也可以通过自定义 **UP 主列表** 和 **关键词**，灵活调整爬取目标)~~ 

程序计划实现 **本地下载** 和 **播放** 功能，但目前 GUI 界面仍在开发中，核心爬虫逻辑已基本完成。

**请注意，该爬虫目前仅支持爬取每个up的最新的前30个视频（也就是第一页，不过后续可能会增加爬取范围设置）** 

---

## 特性概述
### ✅ 已实现功能
- 获取歌回列表，支持按设置的 UP 主和关键词筛选目标视频
- 支持搜索歌曲，下载指定歌回
- 使用 `PyQt6` 构建 GUI 基础框架
- 调用bilibili搜索补全歌曲列表（开发中）

### 🚧 正在计划中
- 升级 GUI 界面，提供可视化交互（如进度条、筛选设置面板）
- 支持播放歌曲，基础播放界面（可能需要外接）

---

## 安装步骤

打开NeuroSongSpider.exe既可

第一次运行一定要点击“获取视频列表”!!!

## 扩展包

(扩展包是用来扩展一些二创视频的，文本格式是`name_extend.txt`)

项目中的扩展包全都在`ExtendPack`文件夹下

安装方法：下载扩展包(extend.zip)后，解压到data文件夹中

**一定记得要加扩展包口牙**

## 数据包

(数据包中是发行版本时的视频列表，文本格式是`time_videos_list.txt`)

安装方法：下载(datatime.zip)数据包后，解压到data文件夹中

## 构建步骤

首先你需要将目录中的ffmpeg.zip解压到ffmpeg文件夹，因为这个软件需要ffmpeg

```bash
# 克隆仓库
git clone https://github.com/qingchenyouforcc/neuroSangSpider

# 进入目录
cd neuroSangSpider

# 初始化虚拟环境（推荐）
python3.13 -m venv venv
venv\\Scripts\\activate

# 安装依赖
pip install -r requirements.txt
pip install bilibili-api-python

# 运行
python main.py
```

---

## 开发扩展包

扩展包实际上是由多个txt文件组成的

txt文件里面的格式是一行一个 `title:url` 

也就是 `视频/文件名:标准Bilibili_BV_URL`

标准Bilibili_BV_URL:`https://www.bilibili.com/video/BV号/`

按照这个格式编写xxx_extend.txt文件即可(最好不要有中文)

**一定记得在最后一项后面加一个回车！**

(实在看不懂可以去data文件里面看看)

---

## 感谢名单

### 感谢Stazer提供的加载动画授权

- 稳定器stz https://space.bilibili.com/125198191

### 感谢以下up主对Neuro/Evil歌回的贡献，没有你们就不会有这个项目的出现

- _环戊烷多氢菲_ https://space.bilibili.com/351692111
- Neuro21烤肉组 https://space.bilibili.com/1880487363
- 绅士羊OuO https://space.bilibili.com/22535350
- NSC987 https://space.bilibili.com/3546612622166788
- 西街Westreet https://space.bilibili.com/5971855
- BulletFX https://space.bilibili.com/483178955
- ASDFHGV https://space.bilibili.com/690857494
- 意念艾特感叹号 https://space.bilibili.com/390418501

以及感谢所有切Neuro/Evil歌回和做二创的UP主们

