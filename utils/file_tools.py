import os
import json
import subprocess

from PyQt6.QtCore import Qt
from loguru import logger
from qfluentwidgets import InfoBar, InfoBarPosition
from tqdm import tqdm
from pathlib import Path
from mutagen import File

from config import MAIN_PATH, cfg
from infoManager.SongList import SongList
from utils.bili_tools import url2bv


def create_dir(dir_name):
    """创建目录"""
    try:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
            logger.info(f"目录 '{dir_name}' 已创建 (os.mkdir)")
        else:
            logger.info(f"目录 '{dir_name}' 已存在 (os.mkdir)")
    except OSError as e:
        logger.error(f"创建目录 '{dir_name}' 失败: {e}")


def part2all(input_folder, output_file):
    """将多个txt文件合并为一个文件(不包括子目录文件)"""
    # 构建输出文件路径
    output_file_path = os.path.join(input_folder, output_file)
    try:
        with open(output_file_path, 'w', encoding='utf-8'):
            # 只是创建/清空文件
            pass
    except IOError as e:
        logger.error(f"写入文件时发生错误: {e}")

    with open(output_file_path, 'a', encoding='utf-8') as f:
        for filename in os.listdir(input_folder):
            # 跳过输出文件本身
            if filename == output_file:
                continue
            # 构建文件路径
            file_path = os.path.join(input_folder, filename)
            try:
                # 打开并读取每个文件内容
                with open(file_path, 'r', encoding='utf-8') as infile:
                    for line in infile:
                        f.write(line)
            except UnicodeDecodeError:
                logger.info(f"跳过非文本文件: {filename}")
            except Exception as e:
                logger.error(f"处理文件 {filename} 时出错: {str(e)}")

    logger.info(f"所有文件内容已合并到 {output_file_path}")


def load_from_all_data(input_folder, exclude_file=None):
    """读取所有的data.json文件,并在去重后返回"""
    if exclude_file is None:
        exclude_file = []

    total_list = SongList()

    for filename in os.listdir(input_folder):
        # 跳过非data.json和已排除的文件
        if (not filename.endswith("data.json")) or filename in exclude_file:
            continue
        # 构建文件路径
        file_path = os.path.join(input_folder, filename)
        try:
            this_list = SongList(file_path)
            total_list.append_list(this_list)
        except Exception as e:
            logger.error(f"处理文件 {filename} 时出错: {str(e)}")
            return None
    total_list.unique_by_bv()
    return total_list


def load_extend(input_folder):
    """读取所有的扩展包,返回bv号列表和up主id列表"""
    bv_list = []
    for filename in os.listdir(input_folder):
        # 跳过非extend.json和已排除的文件
        if not filename.endswith("extend.json"):
            continue
        # 构建文件路径
        file_path = os.path.join(input_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dict_info = json.load(f)
                for video in dict_info["video"]:
                    bv_list.append(video["bv"])
        except Exception as e:
            logger.error(f"处理扩展包 {filename} 时出错: {str(e)}")
            return None
    return {"bv": bv_list}


def convert_old2new(input_folder):
    """将input_folder文件夹下的 所有 以extend.txt旧扩展包转换为新格式"""
    for filename in os.listdir(input_folder):
        json_dict = {"video": []}
        # 跳过非extend.txt和已排除的文件
        if not filename.endswith("extend.txt"):
            continue
        # 构建文件路径
        file_path = os.path.join(input_folder, filename)
        new_filename = filename.replace(".txt", ".json")
        new_path = os.path.join(input_folder, new_filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as fr:
                data = fr.readline()
                while data:
                    json_dict["video"].append({"title": data.split(':')[0],
                                               "bv": url2bv(data[data.find(":") + 1:])})
                    data = fr.readline()

            with open(new_path, 'w', encoding='utf-8') as fw:
                fw.write(json.dumps(json_dict, ensure_ascii=False, indent=4))
                return None

        except Exception as e:
            logger.error(f"处理文件 {filename} 时出错: {str(e)}")
            return None
    return None


def get_audio_duration(file_path):
    """
    获取音频文件的时长和文件名

    参数:
        file_path (str): 音频文件的完整路径

    返回:
        tuple: (文件名, 时长秒数)

    示例:
        ("example.mp3", 245.3)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        audio = File(file_path)
        # 单位为秒，保留两位小数
        duration = round(audio.info.length, 2)
        filename = os.path.basename(file_path)
        return filename, duration
    except Exception as e:
        raise RuntimeError(f"无法读取音频信息: {e}")


def read_all_audio_info(directory, extensions=None):
    """
    读取指定目录下的所有音频文件信息

    参数:
        directory (str): 要扫描的目录
        extensions (list): 支持的音频扩展名列表

    返回:
        list of tuples: [(文件名, 时长), ...]
    """
    if extensions is None:
        extensions = ['.mp3', '.ogg', '.wav']
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                full_path = os.path.join(root, file)
                try:
                    info = get_audio_duration(full_path)
                    results.append(info)
                except Exception as e:
                    logger.error(f"跳过文件: {full_path} - 原因: {e}")
    return results


def clean_audio_file(input_path, output_path, target_format='mp3'):
    """
    使用 ffmpeg 清理音频文件，去除无效帧和时间戳问题

    参数:
        input_path: 输入音频文件路径
        output_path: 输出文件路径（支持 .mp3/.ogg/.wav/.flac）
        target_format: 输出格式，默认为 mp3
    """
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-c:a', {
            'mp3': 'libmp3lame',
            'ogg': 'libvorbis',
            'wav': 'pcm_s16le',
            'flac': 'flac'
        }[target_format],
        '-vn',  # 忽略视频流（如封面）
        '-af', 'aresample=async=1',  # 同步音频时间戳
        '-nostdin',
        '-y',  # 覆盖已有文件
        str(output_path)
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 处理失败: {input_path}\n错误{e}")
        return False


SUPPORTED_EXTENSIONS = ['.mp3', '.ogg', '.wav', '.flac', '.m4a', '.aac']


def batch_clean_audio_files(directory, target_format='mp3', overwrite=False):
    """
    批量清理指定目录下的音频文件，解决时间戳问题

    参数:
        directory: 目标目录路径
        target_format: 输出格式（mp3/ogg/wav/flac）
        overwrite: 是否覆盖原文件（默认生成新文件）
    """
    cleaned_count = 0
    input_dir = Path(directory)

    # 收集所有需要处理的文件
    files_to_process = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if Path(file).suffix.lower() in SUPPORTED_EXTENSIONS:
                input_file = Path(root) / file
                output_file = input_file.parent / (input_file.stem + f"_fix.{target_format}")

                if input_file == output_file and not overwrite:
                    output_file = input_file.parent / (input_file.stem + f"_cleaned.{target_format}")

                if not output_file.exists():
                    files_to_process.append((input_file, output_file))
                else:
                    logger.info(f"✅ 已存在: {output_file.name}")

    total_count = len(files_to_process)

    if total_count == 0:
        logger.info("✅ 没有需要处理的文件")
        return

    logger.info(f"🔍 共找到 {total_count} 个音频文件，开始清理...\n")

    for input_file, output_file in tqdm(files_to_process, desc="处理中", unit="file"):
        success = clean_audio_file(input_file, output_file, target_format=target_format)
        if success:
            tqdm.write(f"✔️ 已清理: {input_file.name} -> {output_file.name}")
            cleaned_count += 1
            if overwrite:
                input_file.unlink()

    logger.info(f"\n✅ 完成！共清理 {cleaned_count}/{total_count} 个文件")


def on_fix_music():
    music_dir = os.path.join(MAIN_PATH, "music")
    try:
        batch_clean_audio_files(music_dir, target_format='mp3', overwrite=True)
        InfoBar.success(
            "修复完成",
            "修复完成！",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=cfg.MAIN_WINDOW
        )
    except Exception as e:
        logger.error(e)
        InfoBar.error(
            "修复失败",
            "修复失败！",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=cfg.MAIN_WINDOW
        )


if __name__ == "__main__":
    # """将data文件夹内的txt扩展包转换为新格式"""
    # convert_old2new("../data")
    pass
