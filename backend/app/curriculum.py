# -*- coding: utf-8 -*-
"""Tarihöz müfredat yapısı: Sınıflar, Temalar ve Dünyanın Enleri"""
from typing import Dict, List, Optional, Tuple

COMMON_THEMES_5_6_7 = [
    {"id": "birlikte_yasamak", "order": 1, "name": "Birlikte Yaşamak", "full_name": "1. Birlikte Yaşamak"},
    {"id": "evimiz_dunya", "order": 2, "name": "Evimiz Dünya", "full_name": "2. Evimiz Dünya"},
    {"id": "ortak_mirasimiz", "order": 3, "name": "Ortak Mirasımız", "full_name": "3. Ortak Mirasımız"},
    {"id": "yasayan_demokrasimiz", "order": 4, "name": "Yaşayan Demokrasimiz", "full_name": "4. Yaşayan Demokrasimiz"},
    {"id": "hayatimizdaki_ekonomi", "order": 5, "name": "Hayatımızdaki Ekonomi", "full_name": "5. Hayatımızdaki Ekonomi"},
    {"id": "teknoloji_ve_sosyal_bilimler", "order": 6, "name": "Teknoloji ve Sosyal Bilimler", "full_name": "6. Teknoloji ve Sosyal Bilimler"},
]

THEMES_8 = [
    {"id": "bir_kahraman_doguyor", "order": 1, "name": "Bir Kahraman Doğuyor", "full_name": "1. Bir Kahraman Doğuyor"},
    {"id": "milli_uyanis", "order": 2, "name": "Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar", "full_name": "2. Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar"},
    {"id": "milli_bir_destan", "order": 3, "name": "Millî Bir Destan: Ya İstiklal Ya Ölüm!", "full_name": "3. Millî Bir Destan: Ya İstiklal Ya Ölüm!"},
    {"id": "ataturkculuk_ve_cagdaslasan_turkiye", "order": 4, "name": "Atatürkçülük ve Çağdaşlaşan Türkiye", "full_name": "4. Atatürkçülük ve Çağdaşlaşan Türkiye"},
    {"id": "demokratiklesme_cabalari", "order": 5, "name": "Demokratikleşme Çabaları", "full_name": "5. Demokratikleşme Çabaları"},
    {"id": "ataturk_donemi_turk_dis_politikasi", "order": 6, "name": "Atatürk Dönemi Türk Dış Politikası", "full_name": "6. Atatürk Dönemi Türk Dış Politikası"},
    {"id": "ataturkun_olumu_ve_sonrasi", "order": 7, "name": "Atatürk'ün Ölümü ve Sonrası", "full_name": "7. Atatürk'ün Ölümü ve Sonrası"},
]

CURRICULUM: List[Dict] = [
    {
        "id": "5",
        "name": "5. Sınıf",
        "short_name": "5. Sınıf",
        "has_themes": True,
        "themes": [dict(t) for t in COMMON_THEMES_5_6_7],
    },
    {
        "id": "6",
        "name": "6. Sınıf",
        "short_name": "6. Sınıf",
        "has_themes": True,
        "themes": [dict(t) for t in COMMON_THEMES_5_6_7],
    },
    {
        "id": "7",
        "name": "7. Sınıf",
        "short_name": "7. Sınıf",
        "has_themes": True,
        "themes": [dict(t) for t in COMMON_THEMES_5_6_7],
    },
    {
        "id": "8",
        "name": "8. Sınıf",
        "short_name": "8. Sınıf",
        "has_themes": True,
        "themes": [dict(t) for t in THEMES_8],
    },
    {
        "id": "dunyanin_enleri",
        "name": "Dünyanın Enleri",
        "short_name": "Dünyanın Enleri",
        "has_themes": False,
        "themes": [],
    },
]

_SECTION_MAP: Dict[str, Dict] = {section["id"]: section for section in CURRICULUM}
_THEME_MAP: Dict[str, Dict[str, Dict]] = {
    section["id"]: {theme["id"]: theme for theme in section["themes"]}
    for section in CURRICULUM
}


def get_curriculum() -> List[Dict]:
    """Return a copy of the curriculum catalog."""
    return [
        {
            **section,
            "themes": [dict(t) for t in section["themes"]],
        }
        for section in CURRICULUM
    ]


def is_valid_grade(grade: Optional[str]) -> bool:
    return bool(grade and grade in _SECTION_MAP)


def grade_has_themes(grade: Optional[str]) -> bool:
    section = _SECTION_MAP.get(grade) if grade else None
    return bool(section and section["has_themes"])


def is_valid_theme(grade: Optional[str], theme: Optional[str]) -> bool:
    if not is_valid_grade(grade):
        return False
    if not grade_has_themes(grade):
        return not theme
    return bool(theme and theme in _THEME_MAP.get(grade, {}))


def validate_grade_and_theme(grade: Optional[str], theme: Optional[str]) -> Tuple[str, Optional[str]]:
    """Validate and normalize (grade, theme). Raises ValueError if invalid."""
    if not grade or not is_valid_grade(grade):
        raise ValueError("Geçersiz bölüm veya sınıf seçimi!")

    if not grade_has_themes(grade):
        return grade, None

    if not theme or not is_valid_theme(grade, theme):
        raise ValueError("Seçilen sınıf için geçerli bir tema seçilmelidir!")

    return grade, theme


def get_topic_info(grade: Optional[str], theme: Optional[str]) -> Optional[Dict]:
    """Return human-readable topic metadata for a (grade, theme) pair."""
    if not grade or grade not in _SECTION_MAP:
        return None

    section = _SECTION_MAP[grade]
    if not section["has_themes"]:
        return {
            "grade": section["id"],
            "grade_name": section["name"],
            "theme": None,
            "theme_name": None,
            "label": section["name"],
        }

    theme_obj = _THEME_MAP.get(grade, {}).get(theme) if theme else None
    if not theme_obj:
        return {
            "grade": section["id"],
            "grade_name": section["name"],
            "theme": None,
            "theme_name": None,
            "label": section["name"],
        }

    return {
        "grade": section["id"],
        "grade_name": section["name"],
        "theme": theme_obj["id"],
        "theme_name": theme_obj["full_name"],
        "label": f"{section['name']} • {theme_obj['full_name']}",
    }
