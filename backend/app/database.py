# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
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


def init_db():
    """Veritabanını başlat ve tabloları oluştur"""
    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)

    Base.metadata.create_all(bind=engine)
    print("Veritabani tablolari olusturuldu")

    # Örnek sorular ekle (eğer veritabanı boşsa)
    db = SessionLocal()
    try:
        if db.query(Question).count() == 0:
            sample_questions = [
                Question(
                    question_text="Türkiye'nin başkenti neresidir?",
                    correct_answer="Ankara",
                    category="Coğrafya",
                    difficulty="easy"
                ),
                Question(
                    question_text="Dünyanın en büyük okyanusu hangisidir?",
                    correct_answer="Pasifik Okyanusu",
                    category="Coğrafya",
                    difficulty="easy"
                ),
                Question(
                    question_text="Işık hızı yaklaşık kaç km/s'dir?",
                    correct_answer="300000",
                    category="Fizik",
                    difficulty="medium"
                ),
                Question(
                    question_text="İlk bilgisayar programcısı olarak kabul edilen kişi kimdir?",
                    correct_answer="Ada Lovelace",
                    category="Tarih",
                    difficulty="medium"
                ),
                Question(
                    question_text="DNA'nın açılımı nedir?",
                    correct_answer="Deoksiribonükleik Asit",
                    category="Biyoloji",
                    difficulty="medium"
                ),
                Question(
                    question_text="İnsanlık tarihinde ilk yazı hangi medeniyette bulunmuştur?",
                    correct_answer="Sümer",
                    category="Tarih",
                    difficulty="hard"
                ),
                Question(
                    question_text="Osmanlı İmparatorluğu kaç yıl sürmüştür?",
                    correct_answer="623",
                    category="Tarih",
                    difficulty="hard"
                ),
                Question(
                    question_text="Periyodik tabloda altın elementinin sembolü nedir?",
                    correct_answer="Au",
                    category="Kimya",
                    difficulty="medium"
                ),
                Question(
                    question_text="Python programlama dili hangi yıl yaratılmıştır?",
                    correct_answer="1991",
                    category="Teknoloji",
                    difficulty="medium"
                ),
                Question(
                    question_text="Dünyada en çok konuşulan dil hangisidir?",
                    correct_answer="Mandarin Çincesi",
                    category="Dil",
                    difficulty="medium"
                ),
                Question(
                    question_text="Fotosentez olayı bitkilerin hangi organelinde gerçekleşir?",
                    correct_answer="Kloroplast",
                    category="Biyoloji",
                    difficulty="hard"
                ),
                Question(
                    question_text="Shakespeare'in kaç tane oyunu vardır?",
                    correct_answer="37",
                    category="Edebiyat",
                    difficulty="hard"
                ),
            ]
            db.add_all(sample_questions)
            db.commit()
            print(f"{len(sample_questions)} ornek soru eklendi")
    finally:
        db.close()
