# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Question
import os

# SQLite veritabanı dosya yolu
DATABASE_URL = "sqlite:///./data/lugatoz.db"

# Engine oluştur
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Veritabanı bağlantısı için dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """Mevcut SQLite veritabanına yeni Tarihöz sütunlarını güvenle ekle"""
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(questions)"))
        existing_columns = {row[1] for row in result.fetchall()}

        if "grade" not in existing_columns:
            conn.execute(text("ALTER TABLE questions ADD COLUMN grade VARCHAR(50)"))
            print("Migration: questions.grade eklendi")

        if "theme" not in existing_columns:
            conn.execute(text("ALTER TABLE questions ADD COLUMN theme VARCHAR(100)"))
            print("Migration: questions.theme eklendi")

        if "unacceptable_answers" not in existing_columns:
            conn.execute(text("ALTER TABLE questions ADD COLUMN unacceptable_answers TEXT"))
            # Mevcut acceptable_answers değerlerini geriye dönük koru
            if "acceptable_answers" in existing_columns:
                conn.execute(text(
                    "UPDATE questions SET unacceptable_answers = acceptable_answers "
                    "WHERE acceptable_answers IS NOT NULL AND unacceptable_answers IS NULL"
                ))
            print("Migration: questions.unacceptable_answers eklendi")

        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_questions_grade_theme ON questions (grade, theme)"
        ))


def init_db():
    """Veritabanını başlat, tabloları oluştur ve migrasyonu çalıştır"""
    os.makedirs("./data", exist_ok=True)

    Base.metadata.create_all(bind=engine)
    migrate_db()
    print("Veritabani tablolari hazir")

    # Veritabanı tamamen boşsa başlangıç için örnek Tarihöz soruları ekle
    db = SessionLocal()
    try:
        if db.query(Question).count() == 0:
            sample_questions = [
                # 5. Sınıf - 1. Birlikte Yaşamak
                Question(
                    question_text="Bir kişinin kendini başkasının yerine koyarak onun duygu ve düşüncelerini anlamaya çalışmasına ne denir?",
                    correct_answer="Empati",
                    unacceptable_answers="duygudaşlık, empati kurmak",
                    acceptable_answers="duygudaşlık, empati kurmak",
                    grade="5",
                    theme="birlikte_yasamak",
                ),
                Question(
                    question_text="İnsanların bir arada yaşarken ortak amaçlarla oluşturdukları, kuralları olan en az iki kişilik topluluklara ne ad verilir?",
                    correct_answer="Grup",
                    unacceptable_answers="topluluk",
                    acceptable_answers="topluluk",
                    grade="5",
                    theme="birlikte_yasamak",
                ),
                Question(
                    question_text="Bireyin içinde yer aldığı gruplarda üstlendiği görev ve sorumluluklara ne denir?",
                    correct_answer="Rol",
                    unacceptable_answers="görev, sosyal rol",
                    acceptable_answers="görev, sosyal rol",
                    grade="5",
                    theme="birlikte_yasamak",
                ),
                Question(
                    question_text="Toplumda yardımlaşma ve dayanışma amacıyla gönüllü olarak kurulan kuruluşlara ne ad verilir?",
                    correct_answer="Sivil Toplum Kuruluşu",
                    unacceptable_answers="STK, vakıf, dernek",
                    acceptable_answers="STK, vakıf, dernek",
                    grade="5",
                    theme="birlikte_yasamak",
                ),
                # 8. Sınıf - 1. Bir Kahraman Doğuyor
                Question(
                    question_text="Mustafa Kemal'in 1881 yılında dünyaya geldiği Osmanlı şehri hangisidir?",
                    correct_answer="Selanik",
                    unacceptable_answers="selanik şehri",
                    acceptable_answers="selanik şehri",
                    grade="8",
                    theme="bir_kahraman_doguyor",
                ),
                Question(
                    question_text="Mustafa Kemal'e 'Kemal' adının verildiği okul hangisidir?",
                    correct_answer="Selanik Askerî Rüştiyesi",
                    unacceptable_answers="askeri rüştiye, selanik askeri rüştiyesi",
                    acceptable_answers="askeri rüştiye, selanik askeri rüştiyesi",
                    grade="8",
                    theme="bir_kahraman_doguyor",
                ),
                Question(
                    question_text="Mustafa Kemal'in ilk görev yeri olan ve 5. Ordu'nun bulunduğu şehir hangisidir?",
                    correct_answer="Şam",
                    unacceptable_answers="suriye, şam şehri",
                    acceptable_answers="suriye, şam şehri",
                    grade="8",
                    theme="bir_kahraman_doguyor",
                ),
                Question(
                    question_text="1789 yılında gerçekleşerek milliyetçilik akımının dünyaya yayılmasına yol açan büyük tarihî olay hangisidir?",
                    correct_answer="Fransız İhtilali",
                    unacceptable_answers="fransız devrimi",
                    acceptable_answers="fransız devrimi",
                    grade="8",
                    theme="bir_kahraman_doguyor",
                ),
                # Dünyanın Enleri
                Question(
                    question_text="Dünyanın yüz ölçümü bakımından en büyük okyanusu hangisidir?",
                    correct_answer="Pasifik Okyanusu",
                    unacceptable_answers="Büyük Okyanus, pasifik",
                    acceptable_answers="Büyük Okyanus, pasifik",
                    grade="dunyanin_enleri",
                    theme=None,
                ),
                Question(
                    question_text="Dünyanın deniz seviyesinden en yüksek dağı hangisidir?",
                    correct_answer="Everest Dağı",
                    unacceptable_answers="Everest, Everest Tepesi",
                    acceptable_answers="Everest, Everest Tepesi",
                    grade="dunyanin_enleri",
                    theme=None,
                ),
                Question(
                    question_text="Dünyanın yüz ölçümü en büyük kıtası hangisidir?",
                    correct_answer="Asya",
                    unacceptable_answers="Asya Kıtası",
                    acceptable_answers="Asya Kıtası",
                    grade="dunyanin_enleri",
                    theme=None,
                ),
                Question(
                    question_text="Dünyanın en büyük sıcak çölü hangisidir?",
                    correct_answer="Sahra Çölü",
                    unacceptable_answers="Sahra, Büyük Sahra",
                    acceptable_answers="Sahra, Büyük Sahra",
                    grade="dunyanin_enleri",
                    theme=None,
                ),
            ]
            db.add_all(sample_questions)
            db.commit()
            print(f"{len(sample_questions)} ornek Tarihoz sorusu eklendi")
    finally:
        db.close()
