# ![](https://qingchenyou-1301914189.cos.ap-beijing.myqcloud.com/this_32.png)NeuroSongSpider



## 项目简介

这是一个基于 `Python 3.13` 开发的爬虫程序，用于从 Bilibili（哔哩哔哩）爬取 **Neuro/Evil** 的歌曲的视频内容。

~~(当然也可以通过自定义 **UP 主列表** 和 **关键词**，灵活调整爬取目标)~~ 

程序计划实现 **本地下载** 和 **播放** 功能，但目前 GUI 界面仍在开发中，核心爬虫逻辑已基本完成。

**请注意，该爬虫目前仅支持爬取每个up的最新的前30个视频（但是有bilibili搜索功能）** 

---

## 特性概述
### ✅ 已实现功能
- 获取歌回列表，支持按设置的 UP 主和关键词筛选目标视频
- 支持搜索歌曲，下载指定歌回、本地播放歌曲
- 使用 `PyQt6` 构建 GUI 基础框架，实现进度条
- 调用bilibili搜索补全歌曲列表（开发中）
- 升级 GUI 界面，提供可视化交互（设置面板等）

### 🚧 正在计划中
- 支持在线播放，无需下载歌曲

---

## 安装步骤

打开NeuroSongSpider.exe既可

第一次运行一定要点击“获取视频列表”!!!

## 扩展包

(扩展包是用来扩展一些二创视频的，文本格式是`name_extend.json`)

在"获取视频列表"后，扩展包数据会被读取，之后这些扩展包中的视频就能被稳定搜索到了

项目中的扩展包全都在`ExtendPack`文件夹下

安装方法：下载扩展包(extend.zip)后，解压到data文件夹中

**一定记得要加扩展包口牙**

## 数据包

(数据包中是发行版本时的视频列表，文本格式是`time_videos_list.txt`)

安装方法：下载(datatime.zip)数据包后，解压到data文件夹中

## 构建步骤

**请注意，如果你要拉取仓库，请拉取master仓库！如果你要提交代码，请PR到Other仓库！**

首先你需要将目录中的ffmpeg.zip解压到ffmpeg文件夹，因为这个软件需要ffmpeg

```bash
# 克隆仓库
git clone https://github.com/qingchenyouforcc/neuroSangSpider

# 进入目录
cd neuroSangSpider

# 安装依赖
uv sync

# 运行
uv run main.py
```

---

## 开发扩展包

扩展包是data文件夹下所有以`extend.json`结尾的文件，以纯文本方式存储

意思是这些文件可以右键使用记事本或者其他文本编辑器打开

文件内部包含一个`video`数组，数组下的每一个对象代表扩展包加入的一个视频

每个对象需要至少包含一个`bv`属性，内容为视频的BV号，用于程序获取视频，其他属性不会被读入程序

(如果实在看不懂的话，可以参考`ExtendPack/extend`文件夹下的`example_extend.json`，里面有更详细的说明和例子)

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

还有对本项目做出贡献的所有开发者

![](https://qingchenyou-1301914189.cos.ap-beijing.myqcloud.com/681dcdd42da7fc5484c1dd3a9875b54a_324.png)
