import os
import yaml
from src.utils.exceptions import ConfigError

DEFAULT_CONFIG = {
    "output": {
        "default_dir": "",
        "overwrite_mode": "ask",
        "formats": ["epub", "txt"],
    },
    "conversion": {
        "max_workers": 4,
        "preserve_layout": True,
        "detect_chapters": True,
        "image_quality": 90,
        "min_image_size": 10,
    },
    "ocr": {
        "enabled": False,
        "language": "eng",
        "dpi": 300,
    },
    "ui": {
        "theme": "blue",
        "language": "zh",
        "font_family": "Microsoft YaHei",
        "font_size": 11,
        "log_level": "INFO",
    },
    "preview": {
        "max_image_width": 500,
        "temp_dir_cleanup": True,
    },
}

_config_cache = None


def _find_config_path():
    paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "default.yaml"),
        os.path.join(os.path.expanduser("~"), ".pdf2epub", "config.yaml"),
        "config/default.yaml",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config = DEFAULT_CONFIG.copy()
    config_path = _find_config_path()

    if config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
            if user_config:
                _deep_merge(config, user_config)
        except Exception as e:
            raise ConfigError(f"无法加载配置文件: {config_path}\n{str(e)}")

    _config_cache = config
    return config


def save_config(config):
    config_dir = os.path.join(os.path.expanduser("~"), ".pdf2epub")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.yaml")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        raise ConfigError(f"无法保存配置文件: {str(e)}")


def get_config(key=None, default=None):
    config = load_config()
    if key is None:
        return config
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if value is not None else default


def _deep_merge(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value