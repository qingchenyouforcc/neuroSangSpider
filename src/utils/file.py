import json
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger
from mutagen._file import File
from PyQt6.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition
from tqdm import tqdm

from src.config import FFMPEG_PATH, MUSIC_DIR, subprocess_options
from src.app_context import app_context
from src.bili_api.converters import url2bv


def create_dir(dir_name: str) -> None:
    """创建目录"""
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def part2all(input_folder: str, output_file: str):
    """将多个txt文件合并为一个文件(不包括子目录文件)"""
    output_file_path = Path(input_folder) / output_file
    with output_file_path.open("w", encoding="utf-8") as f:
        for path in Path(input_folder).iterdir():
            # 跳过输出文件本身
            if path.name == output_file:
                continue
            try:
                with open(path, "r", encoding="utf-8") as infile:
                    for line in infile:
                        f.write(line)
            except UnicodeDecodeError:
                logger.info(f"跳过非文本文件: {path.name}")
            except Exception:
                logger.exception(f"处理文件 {path.name} 时出错")

    logger.info(f"所有文件内容已合并到 {output_file_path}")


def convert_old2new(input_folder: Path):
    """将input_folder文件夹下的 所有 以extend.txt旧扩展包转换为新格式"""
    for fp in input_folder.glob("*extend.txt"):
        json_dict = {"video": []}
        try:
            with fp.open("r", encoding="utf-8") as fr:
                while data := fr.readline():
                    title, _, url = data.partition(":")
                    json_dict["video"].append({"title": title, "bv": url2bv(url)})

            fp.with_suffix(".json").write_text(
                json.dumps(json_dict, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )
        except Exception:
            logger.exception(f"处理文件 {fp} 时出错")


def get_audio_duration(file_path: Path):
    """
    获取音频文件的时长和文件名

    参数:
        file_path (str): 音频文件的完整路径

    返回:
        tuple: (文件名, 时长秒数)

    示例:
        ("example.mp3", 245.3)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    try:
        audio: Any = File(file_path)
        # 单位为秒，保留两位小数
        duration = round(audio.info.length, 2)
        return file_path.name, duration

    except Exception as e:
        raise RuntimeError(f"无法读取音频信息: {e}") from e


def read_all_audio_info(
    directory: Path,
    extensions: list[str] | None = None,
) -> list[tuple[str, float]]:
    """
    读取指定目录下的所有音频文件信息

    参数:
        directory (str | Path): 要扫描的目录
        extensions (list): 支持的音频扩展名列表，默认为 [".mp3", ".ogg", ".wav"]

    返回:
        list[tuple[str, float]]: [(文件名, 时长), ...]
    """

    if extensions is None:
        extensions = [".mp3", ".ogg", ".wav"]

    results: list[tuple[str, float]] = []

    # 使用 Path.rglob 递归遍历所有文件
    for fp in directory.rglob("*"):
        if fp.is_file() and fp.suffix.lower() in extensions:
            try:
                info = get_audio_duration(fp)
                results.append(info)
            except Exception:
                logger.exception(f"跳过文件: {fp.relative_to(directory)}")

    return results


def clean_audio_file(input_path, output_path, target_format="mp3"):
    """
    使用 ffmpeg 清理音频文件，去除无效帧和时间戳问题

    参数:
        input_path: 输入音频文件路径
        output_path: 输出文件路径（支持 .mp3/.ogg/.wav/.flac）
        target_format: 输出格式，默认为 mp3
    """
    cmd = [
        str(FFMPEG_PATH),
        "-i",
        str(input_path),
        "-c:a",
        {"mp3": "libmp3lame", "ogg": "libvorbis", "wav": "pcm_s16le", "flac": "flac"}[target_format],
        "-vn",  # 忽略视频流（如封面）
        "-af",
        "aresample=async=1",  # 同步音频时间戳
        "-nostdin",
        "-y",  # 覆盖已有文件
        str(output_path),
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            **subprocess_options(),
        )
        return True
    except subprocess.CalledProcessError:
        logger.exception(f"❌ 处理失败: {input_path}")
        return False


SUPPORTED_EXTENSIONS = [".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac"]


def batch_clean_audio_files(
    directory: Path,
    target_format: str = "mp3",
    overwrite: bool = False,
) -> None:
    """
    批量清理指定目录下的音频文件，解决时间戳问题

    参数:
        directory: 目标目录路径
        target_format: 输出格式（mp3/ogg/wav/flac）
        overwrite: 是否覆盖原文件（默认生成新文件）
    """
    cleaned_count = 0

    files_to_process: list[tuple[Path, Path]] = []
    for input_file in directory.rglob("*"):
        if not input_file.is_file() or input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        output_file = input_file.parent / f"{input_file.stem}_fix.{target_format}"
        if input_file == output_file and not overwrite:
            output_file = input_file.parent / f"{input_file.stem}_cleaned.{target_format}"

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
    try:
        batch_clean_audio_files(MUSIC_DIR, target_format="mp3", overwrite=True)
        InfoBar.success(
            "修复完成",
            "修复完成！",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=app_context.main_window,
        )
    except Exception:
        logger.exception("修复音乐文件时发生错误")
        InfoBar.error(
            "修复失败",
            "修复失败！",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=app_context.main_window,
        )


if __name__ == "__main__":
    # """将data文件夹内的txt扩展包转换为新格式"""
    # convert_old2new("../data")
    pass
