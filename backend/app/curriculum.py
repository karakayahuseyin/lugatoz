# -*- coding: utf-8 -*-
"""TarihTöz müfredat yapısı: Sınıflar, dinamik Temalar, Tüm Temalar (Karışık) ve Dünyanın Enleri"""
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from .models import Theme

ALL_THEMES_SLUG = "__all__"
ALL_THEMES_LABEL = "Tüm Temalar (Karışık)"

DEFAULT_THEMES_5_6_7 = [
    {"slug": "birlikte_yasamak", "order": 1, "name": "Birlikte Yaşamak"},
    {"slug": "evimiz_dunya", "order": 2, "name": "Evimiz Dünya"},
    {"slug": "ortak_mirasimiz", "order": 3, "name": "Ortak Mirasımız"},
    {"slug": "yasayan_demokrasimiz", "order": 4, "name": "Yaşayan Demokrasimiz"},
    {"slug": "hayatimizdaki_ekonomi", "order": 5, "name": "Hayatımızdaki Ekonomi"},
    {"slug": "teknoloji_ve_sosyal_bilimler", "order": 6, "name": "Teknoloji ve Sosyal Bilimler"},
]

DEFAULT_THEMES_8 = [
    {"slug": "bir_kahraman_doguyor", "order": 1, "name": "Bir Kahraman Doğuyor"},
    {"slug": "milli_uyanis", "order": 2, "name": "Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar"},
    {"slug": "milli_bir_destan", "order": 3, "name": "Millî Bir Destan: Ya İstiklal Ya Ölüm!"},
    {"slug": "ataturkculuk_ve_cagdaslasan_turkiye", "order": 4, "name": "Atatürkçülük ve Çağdaşlaşan Türkiye"},
    {"slug": "demokratiklesme_cabalari", "order": 5, "name": "Demokratikleşme Çabaları"},
    {"slug": "ataturk_donemi_turk_dis_politikasi", "order": 6, "name": "Atatürk Dönemi Türk Dış Politikası"},
    {"slug": "ataturkun_olumu_ve_sonrasi", "order": 7, "name": "Atatürk'ün Ölümü ve Sonrası"},
]

SECTIONS: List[Dict] = [
    {"id": "5", "name": "5. Sınıf", "short_name": "5. Sınıf", "has_themes": True},
    {"id": "6", "name": "6. Sınıf", "short_name": "6. Sınıf", "has_themes": True},
    {"id": "7", "name": "7. Sınıf", "short_name": "7. Sınıf", "has_themes": True},
    {"id": "8", "name": "8. Sınıf", "short_name": "8. Sınıf", "has_themes": True},
    {"id": "dunyanin_enleri", "name": "Dünyanın Enleri", "short_name": "Dünyanın Enleri", "has_themes": False},
]

_SECTION_MAP: Dict[str, Dict] = {section["id"]: section for section in SECTIONS}


def make_topic_key(grade: Optional[str], theme: Optional[str]) -> str:
    """Create canonical scope key for seen-question tracking per section/topic."""
    if not grade:
        return ""
    if not grade_has_themes(grade):
        return grade
    return f"{grade}:{theme or ALL_THEMES_SLUG}"


def slugify_turkish(text: str) -> str:
    """Create an ASCII-safe slug from Turkish text."""
    tr_map = {
        'İ': 'i', 'I': 'i', 'ı': 'i', 'î': 'i', 'Î': 'i',
        'Ş': 's', 'ş': 's',
        'Ğ': 'g', 'ğ': 'g',
        'Ü': 'u', 'ü': 'u', 'û': 'u', 'Û': 'u',
        'Ö': 'o', 'ö': 'o',
        'Ç': 'c', 'ç': 'c',
        'â': 'a', 'Â': 'a',
    }
    mapped = ''.join(tr_map.get(ch, ch.lower()) for ch in text.strip())
    slug = re.sub(r'[^a-z0-9]+', '_', mapped).strip('_')
    return (slug[:80] or 'tema')


def generate_unique_slug(db: Session, grade: str, name: str) -> str:
    """Generate a slug unique within the given grade."""
    base = slugify_turkish(name)
    if base == ALL_THEMES_SLUG:
        base = "tema"
    existing = {
        row[0]
        for row in db.query(Theme.slug).filter(Theme.grade == grade).all()
    }
    if base not in existing:
        return base

    suffix = 2
    while f"{base}_{suffix}" in existing:
        suffix += 1
    return f"{base}_{suffix}"


def _with_session(db: Optional[Session]):
    """Return (session, should_close)."""
    if db is not None:
        return db, False
    from .database import SessionLocal
    return SessionLocal(), True


def seed_default_themes(db: Session):
    """Seed initial default themes when the themes table is empty."""
    if db.query(Theme).count() > 0:
        return

    rows: List[Theme] = []
    for grade_id in ("5", "6", "7"):
        for t in DEFAULT_THEMES_5_6_7:
            rows.append(Theme(
                grade=grade_id,
                slug=t["slug"],
                name=t["name"],
                display_order=t["order"],
            ))
    for t in DEFAULT_THEMES_8:
        rows.append(Theme(
            grade="8",
            slug=t["slug"],
            name=t["name"],
            display_order=t["order"],
        ))
    db.add_all(rows)
    db.commit()
    print(f"{len(rows)} varsayilan tema olusturuldu")


def get_curriculum(db: Optional[Session] = None) -> List[Dict]:
    """Return all sections with their live themes from the database."""
    session, should_close = _with_session(db)
    try:
        themes_db = (
            session.query(Theme)
            .order_by(Theme.grade.asc(), Theme.display_order.asc(), Theme.id.asc())
            .all()
        )
        themes_by_grade: Dict[str, List[Dict]] = {}
        for t in themes_db:
            themes_by_grade.setdefault(t.grade, []).append({
                "db_id": t.id,
                "id": t.slug,
                "order": t.display_order,
                "name": t.name,
                "full_name": f"{t.display_order}. {t.name}",
            })

        return [
            {
                **section,
                "themes": themes_by_grade.get(section["id"], []) if section["has_themes"] else [],
            }
            for section in SECTIONS
        ]
    finally:
        if should_close:
            session.close()


def is_valid_grade(grade: Optional[str]) -> bool:
    return bool(grade and grade in _SECTION_MAP)


def grade_has_themes(grade: Optional[str]) -> bool:
    section = _SECTION_MAP.get(grade) if grade else None
    return bool(section and section["has_themes"])


def is_valid_theme(
    grade: Optional[str],
    theme: Optional[str],
    db: Optional[Session] = None,
    allow_all: bool = False
) -> bool:
    if not is_valid_grade(grade):
        return False
    if not grade_has_themes(grade):
        return not theme
    if not theme:
        return False
    if allow_all and theme == ALL_THEMES_SLUG:
        return True

    session, should_close = _with_session(db)
    try:
        exists = (
            session.query(Theme.id)
            .filter(Theme.grade == grade, Theme.slug == theme)
            .first()
        )
        return exists is not None
    finally:
        if should_close:
            session.close()


def validate_grade_and_theme(
    grade: Optional[str],
    theme: Optional[str],
    db: Optional[Session] = None,
    allow_all: bool = False
) -> Tuple[str, Optional[str]]:
    """Validate and normalize (grade, theme) against live database themes."""
    if not grade or not is_valid_grade(grade):
        raise ValueError("Geçersiz bölüm veya sınıf seçimi!")

    if not grade_has_themes(grade):
        return grade, None

    if not theme or not is_valid_theme(grade, theme, db=db, allow_all=allow_all):
        raise ValueError("Seçilen sınıf için geçerli bir tema seçilmelidir!")

    return grade, theme


def get_topic_info(
    grade: Optional[str],
    theme: Optional[str],
    db: Optional[Session] = None
) -> Optional[Dict]:
    """Return human-readable topic metadata using live database themes."""
    if not grade or grade not in _SECTION_MAP:
        return None

    section = _SECTION_MAP[grade]
    if not section["has_themes"]:
        return {
            "grade": section["id"],
            "grade_name": section["name"],
            "theme": None,
            "theme_name": None,
            "topic_key": make_topic_key(section["id"], None),
            "label": section["name"],
        }

    if not theme:
        return {
            "grade": section["id"],
            "grade_name": section["name"],
            "theme": None,
            "theme_name": None,
            "topic_key": make_topic_key(section["id"], None),
            "label": section["name"],
        }

    if theme == ALL_THEMES_SLUG:
        return {
            "grade": section["id"],
            "grade_name": section["name"],
            "theme": ALL_THEMES_SLUG,
            "theme_name": ALL_THEMES_LABEL,
            "topic_key": make_topic_key(section["id"], ALL_THEMES_SLUG),
            "label": f"{section['name']} • {ALL_THEMES_LABEL}",
        }

    session, should_close = _with_session(db)
    try:
        theme_obj = (
            session.query(Theme)
            .filter(Theme.grade == grade, Theme.slug == theme)
            .first()
        )
    finally:
        if should_close:
            session.close()

    if not theme_obj:
        return {
            "grade": section["id"],
            "grade_name": section["name"],
            "theme": theme,
            "theme_name": theme,
            "topic_key": make_topic_key(section["id"], theme),
            "label": f"{section['name']} • {theme}",
        }

    full_name = f"{theme_obj.display_order}. {theme_obj.name}"
    return {
        "grade": section["id"],
        "grade_name": section["name"],
        "theme": theme_obj.slug,
        "theme_name": full_name,
        "topic_key": make_topic_key(section["id"], theme_obj.slug),
        "label": f"{section['name']} • {full_name}",
    }
