import os
import json
from src.utils.logger import setup_logger

logger = setup_logger("i18n")

_translations = {}
_current_lang = "zh"


def load_translations(lang="zh"):
    global _translations, _current_lang
    _current_lang = lang

    i18n_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(i18n_dir, f"{lang}.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            _translations = json.load(f)
    except FileNotFoundError:
        logger.warning(f"语言文件不存在: {file_path}")
        _translations = {}
    except Exception as e:
        logger.error(f"加载语言文件失败: {str(e)}")
        _translations = {}


def t(key, default=None):
    if key in _translations:
        return _translations[key]
    if default is not None:
        return default
    return key


def get_current_lang():
    return _current_lang


def get_available_languages():
    i18n_dir = os.path.dirname(os.path.abspath(__file__))
    langs = []
    for f in os.listdir(i18n_dir):
        if f.endswith(".json"):
            langs.append(f.replace(".json", ""))
    return sorted(langs)


load_translations("zh")