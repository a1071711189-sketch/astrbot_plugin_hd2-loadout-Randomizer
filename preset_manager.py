"""
用户预设存储模块
每个用户（以 sid/QQ号 识别）可保存自定义过滤预设，
每次随机时自动应用。
"""
import json
import os
from pathlib import Path

PRESETS_DIR = Path(__file__).parent / "presets"


def _ensure_dir():
    PRESETS_DIR.mkdir(exist_ok=True)


def _user_file(user_id: str) -> Path:
    return PRESETS_DIR / f"{user_id}.json"


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


def list_presets() -> list:
    _ensure_dir()
    return [p.stem for p in PRESETS_DIR.glob("*.json")]


def apply_preset(user_id: str) -> dict:
    """
    返回用户的过滤参数，供 randomizer 使用。
    返回格式: {"exclude_warbond_ids": [...], "exclude_items": [...], "locked_slots": {}}
    """
    preset = load_preset(user_id)
    result = {}
    if preset.get("exclude_warbond_ids"):
        result["exclude_warbond_ids"] = preset["exclude_warbond_ids"]
    if preset.get("exclude_items"):
        result["exclude_items"] = {"all": preset["exclude_items"]}
    if preset.get("locked_slots"):
        result["locked_slots"] = preset["locked_slots"]
    return result
