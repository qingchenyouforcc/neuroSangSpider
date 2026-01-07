#!/usr/bin/env python3
"""
自动生成PyInstaller版本信息文件
从src/config.py中读取VERSION并生成version_info.txt
"""

import re
from pathlib import Path


def get_version_from_config():
    """从config.py中获取版本号"""
    config_path = Path("src/config.py")
    if not config_path.exists():
        raise FileNotFoundError("未找到src/config.py文件")

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 使用正则表达式查找VERSION定义
    version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        raise ValueError("在config.py中未找到VERSION定义")

    return version_match.group(1)


def parse_version(version_str):
    """解析版本字符串为四位数字元组"""
    parts = version_str.split(".")
    # 确保有4位数字，不足的补0
    while len(parts) < 4:
        parts.append("0")

    # 只取前4位
    parts = parts[:4]

    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        raise ValueError(f"无效的版本号格式: {version_str}")


def generate_version_info(version_str):
    """生成版本信息文件内容"""
    version_tuple = parse_version(version_str)

    template = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx

VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero.
    filevers={version_tuple},
    prodvers={version_tuple},
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404B0',
        [StringStruct(u'CompanyName', u'qingchenyouforcc'),
        StringStruct(u'FileDescription', u'NeuroSongSpider - 歌回播放软件'),
        StringStruct(u'FileVersion', u'{version_str}'),
        StringStruct(u'InternalName', u'NeuroSongSpider'),
        StringStruct(u'LegalCopyright', u'Copyright © 2026 qingchenyouforcc. Licensed under AGPL-3.0'),
        StringStruct(u'OriginalFilename', u'NeuroSongSpider.exe'),
        StringStruct(u'ProductName', u'NeuroSongSpider'),
        StringStruct(u'ProductVersion', u'{version_str}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)"""
    return template


def main():
    """主函数"""
    try:
        # 获取版本号
        version = get_version_from_config()
        print(f"检测到版本号: {version}")

        # 生成版本信息文件
        version_info_content = generate_version_info(version)

        # 写入文件
        version_info_path = Path("version_info.txt")
        with open(version_info_path, "w", encoding="utf-8") as f:
            f.write(version_info_content)

        print(f"版本信息文件已生成: {version_info_path.absolute()}")

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
