from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd


# CRITICAL: exact README constants.
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900.0, "origin_x": -370.0, "origin_z": -473.0},
    "GrandRift": {"scale": 581.0, "origin_x": -290.0, "origin_z": -290.0},
    "Lockdown": {"scale": 1000.0, "origin_x": -500.0, "origin_z": -500.0},
}

MINIMAP_IMAGE_PATHS = {
    "AmbroseValley": Path("player_data/minimaps/AmbroseValley_Minimap.png"),
    "GrandRift": Path("player_data/minimaps/GrandRift_Minimap.png"),
    "Lockdown": Path("player_data/minimaps/Lockdown_Minimap.jpg"),
}


def _decode_event_value(value: object) -> object:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def get_pixel_coords(x: float, z: float, map_id: str) -> tuple[float, float]:
    """
    README formula (2D minimap uses x and z only; y is elevation):
      u = (x - origin_x)/scale
      v = (z - origin_z)/scale
      pixel_x = u * 1024
      pixel_y = (1 - v) * 1024
    """
    if map_id not in MAP_CONFIG:
        supported = ", ".join(sorted(MAP_CONFIG.keys()))
        raise ValueError(f"Unknown map_id '{map_id}'. Supported maps: {supported}")

    cfg = MAP_CONFIG[map_id]
    u = (float(x) - cfg["origin_x"]) / cfg["scale"]
    v = (float(z) - cfg["origin_z"]) / cfg["scale"]
    pixel_x = u * 1024.0
    pixel_y = (1.0 - v) * 1024.0
    # Keep rendered points in minimap bounds.
    pixel_x = min(1024.0, max(0.0, pixel_x))
    pixel_y = min(1024.0, max(0.0, pixel_y))
    return pixel_x, pixel_y


def get_map_image_path(map_id: str) -> str:
    if map_id not in MINIMAP_IMAGE_PATHS:
        supported = ", ".join(sorted(MINIMAP_IMAGE_PATHS.keys()))
        raise ValueError(f"Unknown map_id '{map_id}'. Supported maps: {supported}")
    return str(MINIMAP_IMAGE_PATHS[map_id])


def _iter_parquet_like_files(data_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in data_root.rglob("*"):
        if not path.is_file():
            continue
        if "minimaps" in path.parts:
            continue
        if path.suffix.lower() == ".md":
            continue
        files.append(path)
    return files


@lru_cache(maxsize=4)
def _load_all_data_cached(data_root_str: str) -> pd.DataFrame:
    """
    Disk-read cache:
    same data_root path => no second disk scan/read.
    """
    data_root = Path(data_root_str)
    frames: list[pd.DataFrame] = []

    for file_path in _iter_parquet_like_files(data_root):
        try:
            # Use pyarrow engine for stable/parquet-optimized reads.
            df = pd.read_parquet(file_path, engine="pyarrow")
        except Exception:
            continue

        if df.empty:
            continue

        if "event" in df.columns:
            df["event"] = df["event"].map(_decode_event_value)

        if "user_id" in df.columns:
            # Requested rule: UUIDs contain hyphens; bot IDs are numeric/no hyphen.
            user_as_str = df["user_id"].astype("string")
            df["is_bot"] = ~user_as_str.str.contains("-", regex=False, na=False)
        else:
            df["is_bot"] = False

        rel_parts = file_path.relative_to(data_root).parts
        df["date"] = rel_parts[0] if len(rel_parts) > 1 else "unknown"

        # Extract leading 4-digit HHMM prefix from filename, e.g. "1405_matchid.nakama-0" → 1405.
        # Files without this prefix (UUID-only names) get -1.
        hhmm_match = re.match(r"^(\d{4})_", file_path.name)
        df["file_hhmm"] = int(hhmm_match.group(1)) if hhmm_match else -1

        frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


@dataclass
class DataManager:
    data_root: str | Path = "player_data"

    def __post_init__(self) -> None:
        self.data_root = Path(self.data_root)

    def load_all_data(self, force_reload: bool = False) -> pd.DataFrame:
        if force_reload:
            _load_all_data_cached.cache_clear()
        return _load_all_data_cached(str(self.data_root.resolve()))

