import json
from pathlib import Path
from loguru import logger
from core.song_list import SongList


def load_from_all_data(input_folder: Path, exclude_file: list[str] | None = None):
    """读取所有的data.json文件,并在去重后返回"""
    if exclude_file is None:
        exclude_file = []

    total_list = SongList()

    for fp in input_folder.iterdir():
        # 跳过非data.json和已排除的文件
        if not fp.name.endswith("data.json") or fp.name in exclude_file:
            continue
        try:
            total_list.append_list(SongList(fp))
        except Exception:
            logger.exception(f"处理文件 {fp} 时出错")
            return None
    total_list.unique_by_bv()
    return total_list

def load_extend(input_folder: Path):
    """读取所有的扩展包,返回bv号列表和up主id列表"""
    bv_list = []
    for fp in input_folder.iterdir():
        # 跳过非extend.json和已排除的文件
        if not fp.name.endswith("extend.json"):
            continue

        try:
            with fp.open("r", encoding="utf-8") as f:
                dict_info = json.load(f)
            for video in dict_info["video"]:
                bv_list.append(video["bv"])
        except Exception:
            logger.exception(f"处理扩展包 {fp} 时出错")
            return None
    return {"bv": bv_list}