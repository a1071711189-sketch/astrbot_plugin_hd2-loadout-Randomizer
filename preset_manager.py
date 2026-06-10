"""
用户预设存储模块
数据存储在 AstrBot 的 data/plugin_data 目录下，卸载重装不丢失。
"""
import json
import os
from pathlib import Path

_presets_dir = None


def init_preset_dir(context):
    """
    由插件在 initialize() 中调用，传入 Star 的 context。
    优先使用 AstrBot 提供的持久化数据目录。
    """
    global _presets_dir

    # 尝试从 context 获取 AstrBot data 目录
    candidates = []

    # AstrBot v4 常见路径
    if hasattr(context, "plugin_data_dir"):
        candidates.append(Path(context.plugin_data_dir))
    if hasattr(context, "data_dir"):
        candidates.append(Path(context.data_dir) / "plugin_data")
    if hasattr(context, "get_data_dir"):
        candidates.append(Path(context.get_data_dir()) / "plugin_data")

    # 从 context 的其他属性推断
    if hasattr(context, "config"):
        cfg = context.config
        for attr in ("data_dir", "plugin_data_dir", "storage_dir"):
            if hasattr(cfg, attr):
                candidates.append(Path(getattr(cfg, attr)) / "plugin_data")

    # 回退: AstrBot 根目录下的 data/plugin_data
    candidates.append(Path(os.getcwd()) / "data" / "plugin_data")

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test = candidate / ".write_test"
            test.touch()
            test.unlink()
            _presets_dir = candidate
            return
        except Exception:
            continue

    # 最终回退: 插件自身目录
    _presets_dir = Path(__file__).parent / "data" / "plugin_data"
    _presets_dir.mkdir(parents=True, exist_ok=True)


def _ensure_dir():
    if _presets_dir is None:
        _presets_dir = Path(__file__).parent / "data" / "plugin_data"
    _presets_dir.mkdir(parents=True, exist_ok=True)


def _user_file(user_id: str) -> Path:
    _ensure_dir()
    return _presets_dir / "{}.json".format(user_id)


def load_preset(user_id: str) -> dict:
    _ensure_dir()
    path = _user_file(user_id)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_preset(user_id: str, preset: dict):
    _ensure_dir()
    with open(_user_file(user_id), "w", encoding="utf-8") as f:
        json.dump(preset, f, ensure_ascii=False, indent=2)


def delete_preset(user_id: str):
    _ensure_dir()
    path = _user_file(user_id)
    if path.exists():
        path.unlink()


def apply_preset(user_id: str) -> dict:
    preset = load_preset(user_id)
    result = {}
    if preset.get("exclude_warbond_ids"):
        result["exclude_warbond_ids"] = preset["exclude_warbond_ids"]
    if preset.get("exclude_items"):
        result["exclude_items"] = {"all": preset["exclude_items"]}
    if preset.get("locked_slots"):
        result["locked_slots"] = preset["locked_slots"]
    return result
