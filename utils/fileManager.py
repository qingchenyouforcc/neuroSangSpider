import os
import json
from pathlib import Path
from infoManager.SongList import SongList
from utils.bili_tools import url2bv

MAIN_PATH = Path.cwd()


def create_dir(dir_name):
    """创建目录"""
    try:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
            print(f"目录 '{dir_name}' 已创建 (os.mkdir)")
        else:
            print(f"目录 '{dir_name}' 已存在 (os.mkdir)")
    except OSError as e:
        print(f"创建目录 '{dir_name}' 失败: {e}")


def part2all(input_folder, output_file):
    """将多个txt文件合并为一个文件(不包括子目录文件)"""
    # 构建输出文件路径
    output_file_path = os.path.join(input_folder, output_file)
    try:
        with open(output_file_path, 'w', encoding='utf-8'):
            # 只是创建/清空文件
            pass
    except IOError as e:
        print(f"写入文件时发生错误: {e}")

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
                print(f"跳过非文本文件: {filename}")
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")

    print(f"所有文件内容已合并到 {output_file_path}")


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
            print(f"处理文件 {filename} 时出错: {str(e)}")
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
            print(f"处理扩展包 {filename} 时出错: {str(e)}")
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
            print(f"处理文件 {filename} 时出错: {str(e)}")
            return None
    return None


if __name__ == "__main__":
    # """将data文件夹内的txt扩展包转换为新格式"""
    # convert_old2new("../data")
    pass
