from enum import IntEnum
from typing import Any, List


class CardType(IntEnum):
    """Card types in the game"""

    MEMBER = 0
    LIVE = 1
    ENERGY = 2


class HeartColor(IntEnum):
    """Heart/color types (6 colors + any + rainbow)"""

    PINK = 0
    RED = 1
    YELLOW = 2
    GREEN = 3
    BLUE = 4
    PURPLE = 5
    ANY = 6  # Colorless requirement
    RAINBOW = 7  # Can be any color


class Area(IntEnum):
    """Member areas on stage"""

    LEFT = 0
    CENTER = 1
    RIGHT = 2


class Group(IntEnum):
    """Card Groups (Series/Schools)"""

    MUSE = 0
    AQOURS = 1
    NIJIGASAKI = 2
    LIELLA = 3
    HASUNOSORA = 4
    ARISE = 10
    SAINT_SNOW = 11
    SUNNY_PASSION = 12
    MUSICAL = 13
    AQOURS_OR_SAINT_SNOW = 101
    LIVE = 98
    OTHER = 99
    NONE = 100

    @classmethod
    def from_japanese_name(cls, name: str) -> "Group":
        name = name.strip()
        name_lower = name.lower()
        if "ラブライブ！" == name or "μ's" in name or "muse" in name_lower:
            return cls.MUSE
        if "サンシャイン" in name or "aqours" in name_lower:
            return cls.AQOURS
        if "虹ヶ咲" in name or "nijigasaki" in name_lower:
            return cls.NIJIGASAKI
        if "スーパースター" in name or "liella" in name_lower:
            return cls.LIELLA
        if "蓮ノ空" in name or "hasunosora" in name_lower:
            return cls.HASUNOSORA
        if "a-rise" in name_lower or "arise" in name_lower:
            return cls.ARISE
        if "saint snow" in name_lower or "saintsnow" in name_lower:
            return cls.SAINT_SNOW
        if "sunny passion" in name_lower or "sunnypassion" in name_lower:
            return cls.SUNNY_PASSION
        if "スクールアイドルミュージカル" in name:
            return cls.MUSICAL
        if "aqours_or_saint_snow" in name_lower or ("aqours" in name_lower and "saint" in name_lower):
            return cls.AQOURS_OR_SAINT_SNOW
        return cls.OTHER


class Unit(IntEnum):
    """Card Units"""

    PRINTEMPS = 0
    LILY_WHITE = 1
    BIBI = 2
    CYARON = 3
    AZALEA = 4
    GUILTY_KISS = 5
    DIVER_DIVA = 6
    A_ZU_NA = 7
    QU4RTZ = 8
    R3BIRTH = 9
    CATCHU = 10
    KALEIDOSCORE = 11
    SYNCRISE = 12
    CERISE_BOUQUET = 13
    DOLLCHESTRA = 14
    MIRA_CRA_PARK = 15
    EDEL_NOTE = 16
    AISCREAM = 17
    OTHER = 99

    @classmethod
    def from_japanese_name(cls, name: str) -> "Unit":
        name = name.strip()
        name_lower = name.lower()
        if "printemps" in name_lower:
            return cls.PRINTEMPS
        if "lily white" in name_lower or "lilywhite" in name_lower:
            return cls.LILY_WHITE
        if "bibi" in name_lower:
            return cls.BIBI
        if "cyaron" in name_lower or "cyaron！" in name_lower:
            return cls.CYARON
        if "azalea" in name_lower:
            return cls.AZALEA
        if "guilty kiss" in name_lower or "guiltykiss" in name_lower:
            return cls.GUILTY_KISS
        if "diverdiva" in name_lower:
            return cls.DIVER_DIVA
        if "azuna" in name_lower or "a・zu・na" in name_lower:
            return cls.A_ZU_NA
        if "qu4rtz" in name_lower:
            return cls.QU4RTZ
        if "r3birth" in name_lower:
            return cls.R3BIRTH
        if "catchu" in name_lower:
            return cls.CATCHU
        if "kaleidoscore" in name_lower:
            return cls.KALEIDOSCORE
        if "5yncri5e" in name_lower or "syncrise" in name_lower:
            return cls.SYNCRISE
        if "スリーズブーケ" in name or "cerise" in name_lower or "hasu" in name_lower:
            # Note: "Hasu" maps to Cerise if it's a unit, but usually it's a group.
            return cls.CERISE_BOUQUET
        if "dollchestra" in name_lower or "doll" in name_lower:
            return cls.DOLLCHESTRA
        if "みらくらぱーく" in name or "mira-cra" in name_lower or "mirakura" in name_lower:
            return cls.MIRA_CRA_PARK
        if "edelnote" in name_lower or "edel_note" in name_lower:
            return cls.EDEL_NOTE
        if "aiscream" in name_lower:
            return cls.AISCREAM
        if not name:
            return cls.NONE
        return cls.OTHER


def ensure_group_list(v: Any) -> List[Group]:
    """Validator to convert string/single Group to List[Group]"""
    if isinstance(v, list):
        return [
            g if isinstance(g, Group) else Group(g) if isinstance(g, int) else Group.from_japanese_name(str(g))
            for g in v
        ]
    if isinstance(v, Group):
        return [v]
    if isinstance(v, int):
        return [Group(v)]
    if isinstance(v, str):
        if not v:
            return []
        parts = [p.strip() for p in v.split("\n") if p.strip()]
        return [Group.from_japanese_name(p) for p in parts]
    return []


def ensure_unit_list(v: Any) -> List[Unit]:
    """Validator to convert string/single Unit to List[Unit]"""
    if isinstance(v, list):
        return [
            u if isinstance(u, Unit) else Unit(u) if isinstance(u, int) else Unit.from_japanese_name(str(u)) for u in v
        ]
    if isinstance(v, Unit):
        return [v]
    if isinstance(v, int):
        return [Unit(v)]
    if isinstance(v, str):
        if not v:
            return []
        parts = [p.strip() for p in v.split("\n") if p.strip()]
        return [Unit.from_japanese_name(p) for p in parts]
    return []


# Character ID Map (Used for Filter Logic)
CHAR_MAP = {
    "高坂穂乃果": 1,
    "絢瀬絵里": 2,
    "南ことり": 3,
    "園田海未": 4,
    "星空凛": 5,
    "西木野真姫": 6,
    "東條希": 7,
    "小泉花陽": 8,
    "矢澤にこ": 9,
    "高海千歌": 11,
    "桜内梨子": 12,
    "松浦果南": 13,
    "黒澤ダイヤ": 14,
    "渡辺曜": 15,
    "津島善子": 16,
    "国木田花丸": 17,
    "小原鞠莉": 18,
    "黒澤ルビィ": 19,
    "上原歩夢": 21,
    "中須かすみ": 22,
    "桜坂しずく": 23,
    "朝香果林": 24,
    "宮下愛": 25,
    "近江彼方": 26,
    "優木せつ菜": 27,
    "エマ・ヴェルデ": 28,
    "天王寺璃奈": 29,
    "三船栞子": 30,
    "ミア・テイラー": 31,
    "鐘嵐珠": 32,
    "高咲侑": 33,
    "澁谷かのん": 41,
    "唐可可": 42,
    "嵐千砂都": 43,
    "平安名すみれ": 44,
    "葉月恋": 45,
    "桜小路きな子": 46,
    "米女メイ": 47,
    "若菜四季": 48,
    "鬼塚夏美": 49,
    "ウィーン・マルガレーテ": 50,
    "鬼塚冬毬": 51,
    "日野下花帆": 61,
    "村野さやか": 62,
    "乙宗梢": 63,
    "夕霧綴理": 64,
    "大沢瑠璃乃": 65,
    "藤島慈": 66,
    "百生吟子": 67,
    "徒町小鈴": 68,
    "安養寺姫芽": 69,
    "綺羅ツバサ": 71,
    "統堂英玲奈": 72,
    "優木あんじゅ": 73,
    "聖澤悠奈": 74,
    "柊摩央": 75,
    "鹿角聖良": 76,
    "鹿角理亞": 77,
}
