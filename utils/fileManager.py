import os

def create_dir(dir_name):
    try:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
            print(f"目录 '{dir_name}' 已创建 (os.mkdir)")
        else:
            print(f"目录 '{dir_name}' 已存在 (os.mkdir)")
    except OSError as e:
        print(f"创建目录 '{dir_name}' 失败: {e}")
