import re
import time
from collections.abc import Iterable

from loguru import logger

from i18n import t


def contain_text(words_set: Iterable[str], text: str) -> bool:
    """检测是否包含内容"""
    return any(word in text for word in words_set)


def remove_text_after_char(text: str, after_char: str) -> str:
    """删除字符后的文本"""
    index = text.find(after_char)
    if index != -1:
        text = text[:index]
    return text


def fix_filename(filename: str) -> str:
    """文件名处理，防止文件名导致的各种问题"""
    for char in (">", "<", "\\", "/", "*", "|", "?", '"', "&", ";"):
        filename = filename.replace(char, "_")
    return filename


def count_cn_char(text: str) -> int:
    """计算中文字符数"""
    count = 0
    for ch in text:
        if "\u4e00" < text < "\u9fa5" in ch:
            count += 1
    return count


def format_date_str(date: str) -> str:
    """将爬取的时间格式转换为统一格式(YYYY-MM-DD)"""
    try:
        res = re.search("([0-9]*)-([0-9]*)-([0-9]*)", date)
        if res is None:
            localtime = time.localtime(time.time())
            res = re.search("([0-9]*)-([0-9]*)", date)
            if res is None:
                if t("date.yesterday") in date:
                    localtime = time.localtime(time.time() - 3600 * 24)
                    res = f"{localtime.tm_year}-{localtime.tm_mon}-{localtime.tm_mday}"
                elif t("date.day_before_yesterday") in date:
                    localtime = time.localtime(time.time() - 3600 * 24 * 2)
                    res = f"{localtime.tm_year}-{localtime.tm_mon}-{localtime.tm_mday}"
                else:
                    localtime = time.localtime(time.time())
                    res = f"{localtime.tm_year}-{localtime.tm_mon}-{localtime.tm_mday}"
            else:
                res = res.group(1, 2)
                res = f"{localtime.tm_year}-{int(res[0])}-{int(res[1])}"
        else:
            res = res.group(1, 2, 3)
            res = f"{res[0]}-{int(res[1])}-{int(res[2])}"

        return res
    except Exception:
        logger.opt(exception=True).warning(t("utils.date_format_error"))
        return date


def escape_tag(s: str) -> str:
    """用于记录带颜色日志时转义 `<tag>` 类型特殊标签

    参考: [loguru color 标签](https://loguru.readthedocs.io/en/stable/api/logger.html#color)

    参数:
        s: 需要转义的字符串
    """
    return re.sub(r"</?((?:[fb]g\s)?[^<>\s]*)>", r"\\\g<0>", s)