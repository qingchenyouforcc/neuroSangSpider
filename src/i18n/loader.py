import re
import unicodedata
from pathlib import Path
from typing import Dict
from loguru import logger


class PropertiesLoader:
    """properties格式的翻译文件加载器"""

    # 支持转义字符
    ESCAPE_SEQUENCES = {"\\n": "\n", "\\t": "\t", "\\r": "\r", '\\"': '"', "\\'": "'", "\\\\": "\\"}

    def __init__(self, resources_dir: Path):
        self.resources_dir = resources_dir

    def load_properties(self, file_path: Path) -> Dict[str, str]:
        translations = {}

        if not file_path.exists():
            logger.warning(f"语言文件不存在: {file_path}")
            return translations

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # NOTE:
            # - 不能在分隔符(=/:)后使用 \s*，因为 \s 会匹配 \r/\n，导致空值行把下一行 key 吞进 value。
            # - 仅允许分隔符后跟空格/Tab，不允许跨行。
            pattern = r"^[ \t]*([^=:\s][^=:]*?)\s*[=:][ \t]*(.*?)(?=(?<!\\)\r?\n[ \t]*[^=:\s]|\Z)"
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

            for match in matches:
                key = match.group(1).strip()
                value = match.group(2).strip()

                # 规范化键名，移除不可见控制/格式字符（如 BOM、零宽空格等）
                key = self._normalize_key(key)

                value = self._process_multiline_value(value)
                value = self._unescape(value)

                if key:
                    translations[key] = value

            logger.info(f"成功加载语言文件: {file_path}, 共 {len(translations)} 个词条")

        except Exception as e:
            logger.error(f"加载语言文件失败 {file_path}: {e}")

        return translations

    @staticmethod
    def _normalize_key(key: str) -> str:
        """去除键名中的不可见字符，避免由于 BOM/零宽字符 导致的匹配失败"""
        # NFC 规范化
        k = unicodedata.normalize("NFC", key)
        # 过滤掉控制字符和格式字符（如 ZWSP/ZWJ/ZWNJ/BOM）
        k = "".join(c for c in k if (ord(c) >= 32 and unicodedata.category(c) not in {"Cf"}))
        # 再次去掉首尾空白
        return k.strip()

    def _process_multiline_value(self, value: str) -> str:
        """处理多行值，将续行连接为单行"""
        # 将换行符后跟空格的模式替换为空格，实现多行连接
        # 但保留显式的 \n 转义符
        lines = value.split("\n")
        processed_lines = []

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            # 如果行以反斜杠结束，表示续行
            if stripped_line.endswith("\\") and i < len(lines) - 1:
                # 移除反斜杠，但不移除行尾空格（除非是转义空格）
                processed_line = stripped_line[:-1].rstrip()
                processed_lines.append(processed_line)
            else:
                processed_lines.append(stripped_line)
                if i < len(lines) - 1:  # 不是最后一行，添加换行符
                    processed_lines.append("\n")

        result = "".join(processed_lines)
        # 移除末尾的多余换行符
        return result.rstrip("\n")

    def _unescape(self, value: str) -> str:
        """处理转义字符"""
        for escape, replacement in self.ESCAPE_SEQUENCES.items():
            value = value.replace(escape, replacement)
        return value

    def get_available_languages(self) -> Dict[str, str]:
        languages = {}

        for file_path in self.resources_dir.glob("*.properties"):
            lang_code = file_path.stem  # 去掉扩展名

            # 读取语言名称
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 查找 language.name
                    name_match = re.search(r"^language\.name\s*[=:]\s*(.*)$", content, re.MULTILINE)
                    if name_match:
                        lang_name = name_match.group(1).strip()
                        languages[lang_code] = self._unescape(lang_name)
                    else:
                        languages[lang_code] = lang_code
            except Exception as e:
                logger.warning(f"读取语言名称失败 {file_path}: {e}")
                languages[lang_code] = lang_code

        return languages
