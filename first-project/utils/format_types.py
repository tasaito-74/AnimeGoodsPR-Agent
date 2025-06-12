from enum import Enum
from dataclasses import dataclass
from typing import Optional

class StoreType(Enum):
    """店舗タイプ"""
    NORMAL = "normal"  # 通常の店舗
    A3 = "a3"         # 株式会社A3
    TSUTAYA = "tsutaya"  # TSUTAYA

class IllustrationType(Enum):
    """イラストタイプ"""
    ORIGINAL = "original"  # 描き下ろしイラスト
    ANIME = "anime"       # アニメビジュアル

@dataclass
class StoreInfo:
    """店舗情報"""
    name: str
    type: StoreType
    illustration_type: IllustrationType
    start_date: str
    end_date: str
    location: str
    google_maps_url: str
    official_url: str
    contact_url: str
    twitter_url: Optional[str] = None
    category_url: Optional[str] = None

@dataclass
class NoveltyInfo:
    """ノベルティ情報"""
    price: int
    name: str
    total_types: int
    is_random: bool = True
    is_original: bool = False

@dataclass
class ArticleInfo:
    """記事情報"""
    title: str
    author: str
    anime_name: str
    maker_name: str
    store_info: StoreInfo
    novelty_info: NoveltyInfo
    character_names: Optional[list[str]] = None 