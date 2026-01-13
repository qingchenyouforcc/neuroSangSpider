#!/usr/bin/env python3
"""
自动生成PyInstaller版本信息文件
从src/config.py中读取VERSION并生成version_info.txt
同时维护构建次数并生成src/build_info.py
"""

import re
import os
import json
import datetime
import subprocess
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


def _run_git(args: list[str]) -> str | None:
    """运行 git 命令并返回 stdout；失败则返回 None。"""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=True,
        )
        return (result.stdout or "").strip()
    except Exception:
        return None


def get_build_number(version: str) -> tuple[int, str | None, str]:
    """获取构建号。

    规则：
    1) 优先使用 git commit count（同一提交在不同机器上得到一致的 build 号，且不会产生仓库文件变更）；
    2) 若不在 git 仓库/没有 git，则使用本机 LocalAppData 的计数文件自增。
    """
    override = os.getenv("NEUROSONGSPIDER_BUILD_NUMBER")
    if override and override.isdigit():
        return int(override) % 65536, _run_git(["rev-parse", "--short", "HEAD"]), "env"

    commit_count = _run_git(["rev-list", "--count", "HEAD"])
    if commit_count and commit_count.isdigit():
        git_hash = _run_git(["rev-parse", "--short", "HEAD"])
        return int(commit_count) % 65536, git_hash, "git"

    # fallback: per-user counter outside the repo to avoid PR conflicts
    base_dir = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    stats_file = Path(base_dir) / "NeuroSongSpider" / "build_stats.json"
    stats_file.parent.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {}
    if stats_file.exists():
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f) or {}
        except Exception:
            stats = {}

    current_count = int(stats.get(version, 0) or 0)
    new_count = (current_count + 1) % 65536
    stats[version] = new_count

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)

    return new_count, None, "local"


def write_build_info_module(version: str, build_number: int, git_hash: str | None, source: str):
    """生成src/build_info.py供程序调用"""
    content = f'''"""
自动生成的构建信息文件
请勿手动修改
"""
BUILD_VERSION = "{version}"
BUILD_NUMBER = {build_number}
BUILD_GIT_HASH = {repr(git_hash)}
BUILD_SOURCE = "{source}"
BUILD_TIME = "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
'''
    with open("src/build_info.py", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"构建信息模块已生成: src/build_info.py (Build {build_number}, source={source})")


def parse_version(version_str, build_number=0):
    """解析版本字符串为四位数字元组"""
    parts = version_str.split(".")
    # 确保有3位数字 (Major.Minor.Patch)
    while len(parts) < 3:
        parts.append("0")

    # 取前3位
    parts = parts[:3]

    # 第4位使用构建次数
    parts.append(str(build_number))

    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        raise ValueError(f"无效的版本号格式: {version_str}")


def generate_version_info(version_str, build_number):
    """生成版本信息文件内容"""
    version_tuple = parse_version(version_str, build_number)
    full_version_str = f"{version_str}.{build_number}"

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
        StringStruct(u'FileVersion', u'{full_version_str}'),
        StringStruct(u'InternalName', u'NeuroSongSpider'),
        StringStruct(u'LegalCopyright', u'Copyright © 2026 qingchenyouforcc. Licensed under AGPL-3.0'),
        StringStruct(u'OriginalFilename', u'NeuroSongSpider.exe'),
        StringStruct(u'ProductName', u'NeuroSongSpider'),
        StringStruct(u'ProductVersion', u'{full_version_str}')])
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

        # 获取构建号（优先 git 派生；否则本机自增）
        build_number, git_hash, source = get_build_number(version)

        # 生成Python模块
        write_build_info_module(version, build_number, git_hash, source)

        # 生成版本信息文件
        version_info_content = generate_version_info(version, build_number)

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
