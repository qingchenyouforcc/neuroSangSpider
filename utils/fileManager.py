import os
from pathlib import Path

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
        with open(output_file_path, 'w', encoding='utf-8') as f:
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
