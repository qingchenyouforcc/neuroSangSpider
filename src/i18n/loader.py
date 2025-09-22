import re
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


class PropertiesLoader:
    """properties格式的翻译文件加载器"""

    # 支持转义字符
    ESCAPE_SEQUENCES = {
        '\\n': '\n',
        '\\t': '\t',
        '\\r': '\r',
        '\\"': '"',
        "\\'": "'",
        '\\\\': '\\'
    }

    def __init__(self, resources_dir: Path):
        self.resources_dir = resources_dir

    def load_properties(self, file_path: Path) -> Dict[str, str]:
        translations = {}

        if not file_path.exists():
            logger.warning(f"语言文件不存在: {file_path}")
            return translations

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # 跳过空行和注释
                    if not line or line.startswith('#') or line.startswith('!'):
                        continue

                    # 解析键值对
                    key, value = self._parse_line(line, line_num, file_path)
                    if key:
                        translations[key] = value

            logger.info(f"成功加载语言文件: {file_path}, 共 {len(translations)} 个词条")

        except Exception as e:
            logger.error(f"加载语言文件失败 {file_path}: {e}")

        return translations

    def _parse_line(self, line: str, line_num: int, file_path: Path) -> Optional[tuple]:
        """解析单行属性"""
        try:
            # 匹配等号和冒号
            match = re.match(r'^\s*([^=:]+?)\s*[=:]\s*(.*?)\s*$', line)
            if not match:
                logger.warning(f"无效的行格式 {file_path}:{line_num}: {line}")
                return None

            key = match.group(1).strip()
            value = match.group(2).strip()

            # 处理转义字符
            value = self._unescape(value)

            return key, value

        except Exception as e:
            logger.error(f"解析行失败 {file_path}:{line_num}: {e}")
            return None

    def _unescape(self, value: str) -> str:
        """处理转义字符"""
        for escape, replacement in self.ESCAPE_SEQUENCES.items():
            value = value.replace(escape, replacement)
        return value

    def get_available_languages(self) -> Dict[str, str]:
        languages = {}

        for file_path in self.resources_dir.glob("*.properties"):
            lang_code = file_path.stem  # 去掉扩展名

            # 从文件内容读取语言名称
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('language.name='):
                            lang_name = line.split('=', 1)[1].strip()
                            languages[lang_code] = self._unescape(lang_name)
                            break
                # 如果没有找到语言名称，使用代码作为名称
                if lang_code not in languages:
                    languages[lang_code] = lang_code
            except Exception as e:
                logger.warning(f"读取语言名称失败 {file_path}: {e}")
                languages[lang_code] = lang_code

        return languages