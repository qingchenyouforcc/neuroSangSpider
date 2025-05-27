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
    count = 0
    for ch in text:
        if '\u4e00'<text<'\u9fa5' in ch:
            count += 1
    return count
