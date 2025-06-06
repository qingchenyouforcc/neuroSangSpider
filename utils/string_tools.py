import re
import time

def contain_text(words_set, text):
    """检测是否包含内容"""
    for word in words_set:
        if word in text:
            return True
    return False


def remove_text_after_char(text, after_char):
    """删除字符后的文本"""
    index = text.find(after_char)
    if index != -1:
        text = text[:index]
    return text


def fileName_process(filename):
    """文件名处理，防止文件名导致的各种问题"""
    chars_to_remove = ['>', '<', '\\', '/', '*', '|', '?', '\"', '&', ';']
    for char in filename:
        if char in chars_to_remove: filename = filename.replace(char, '_')
    return filename

def count_cn_char(text):
    """计算中文字符数"""
    count = 0
    for ch in text:
        if '\u4e00'<text<'\u9fa5' in ch:
            count += 1
    return count

def format_date_str(date):
    """将爬取的时间格式转换为统一格式(YYYY-MM-DD)"""
    try:
        res = re.search("([0-9]*)-([0-9]*)-([0-9]*)", date)
        if res is None:
            localtime = time.localtime(time.time())
            res = re.search("([0-9]*)-([0-9]*)", date)
            if res is None:
                if "昨天" in date:
                    localtime = time.localtime(time.time()-3600*24)
                    res=f"{localtime.tm_year}-{localtime.tm_mon}-{localtime.tm_mday}"
                elif "前天" in date:
                    localtime = time.localtime(time.time()-3600*24*2)
                    res=f"{localtime.tm_year}-{localtime.tm_mon}-{localtime.tm_mday}"
                else:
                    localtime = time.localtime(time.time())
                    res=f"{localtime.tm_year}-{localtime.tm_mon}-{localtime.tm_mday}"
            else:
                res = res.group(1, 2)
                res = f"{localtime.tm_year}-{int(res[0])}-{int(res[1])}"
        else:
            res = res.group(1, 2, 3)
            res = f"{res[0]}-{int(res[1])}-{int(res[2])}"
        # print(res)
        return res
    except Exception as search_e:
        print(f"日期格式化错误: {search_e}")
        return date