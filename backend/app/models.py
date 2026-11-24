# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import random

Base = declarative_base()


def generate_user_id():
    """Generate a unique 5-digit user ID"""
    return random.randint(10000, 99999)


class Theme(Base):
    """Dynamic theme model for grades 5, 6, 7, 8"""
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(String(50), nullable=False, index=True)  # "5", "6", "7", "8"
    slug = Column(String(100), nullable=False, index=True)  # matches Question.theme
    name = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("grade", "slug", name="uq_themes_grade_slug"),
    )

    def __repr__(self):
        return f"<Theme(id={self.id}, grade='{self.grade}', slug='{self.slug}', name='{self.name}')>"


class Question(Base):
    """Question model"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(String(500), nullable=False)  # Görünür doğru cevap
    unacceptable_answers = Column(Text, nullable=True)  # Virgülle ayrılmış kabul edilmeyecek yanıtlar
    acceptable_answers = Column(Text, nullable=True)  # Geriye dönük uyumluluk için
    grade = Column(String(50), nullable=True, index=True)  # "5", "6", "7", "8", "dunyanin_enleri"
    theme = Column(String(100), nullable=True, index=True)  # Tema ID (Dünyanın Enleri için None)
    category = Column(String(100), nullable=True)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Question(id={self.id}, grade='{self.grade}', theme='{self.theme}', text='{self.question_text[:50]}...')>"


class GameSession(Base):
    """Game session model"""
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(6), unique=True, nullable=False, index=True)
    status = Column(String(20), default="waiting")  # waiting, playing, finished
    current_round = Column(Integer, default=0)
    max_rounds = Column(Integer, default=10)
    created_at = Column(Integer)  # Unix timestamp

    players = relationship("Player", back_populates="game_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GameSession(room_code='{self.room_code}', status='{self.status}')>"


class Player(Base):
    """Player model"""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    player_name = Column(String(50), nullable=False)
    socket_id = Column(String(100), unique=True, nullable=True)
    score = Column(Integer, default=0)
    is_host = Column(Boolean, default=False)

    game_session = relationship("GameSession", back_populates="players")

    def __repr__(self):
        return f"<Player(name='{self.player_name}', score={self.score})>"


class GameStats(Base):
    """Game statistics model"""
    __tablename__ = "game_stats"

    id = Column(Integer, primary_key=True, index=True)
    total_players = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    total_wrong_answers = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GameStats(sessions={self.total_sessions}, players={self.total_players})>"


class QuestionStats(Base):
    """Question-specific statistics model"""
    __tablename__ = "question_stats"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, unique=True, index=True)
    times_asked = Column(Integer, default=0)  # Kaç defa soruldu
    times_correct = Column(Integer, default=0)  # Kaç defa doğru cevaplandı
    times_wrong = Column(Integer, default=0)  # Kaç defa yanlış cevaplandı
    total_players_seen = Column(Integer, default=0)  # Kaç oyuncu gördü
    games_used = Column(Integer, default=0)  # Kaç oyunda kullanıldı
    last_used = Column(DateTime, nullable=True)  # Son kullanım tarihi

    def __repr__(self):
        return f"<QuestionStats(question_id={self.question_id}, asked={self.times_asked})>"


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)  # 5-digit unique ID
    username = Column(String(50), unique=True, nullable=False, index=True)  # Unique username
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    stats = relationship("UserStats", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}')>"


class UserStats(Base):
    """User statistics model"""
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True, index=True)

    # Game statistics
    total_games_played = Column(Integer, default=0)
    total_games_won = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    highest_score = Column(Integer, default=0)

    # Question statistics
    total_questions_answered = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    total_wrong_answers = Column(Integer, default=0)

    # Deception statistics
    total_players_deceived = Column(Integer, default=0)  # Kaç kişiyi kandırdı
    total_times_deceived = Column(Integer, default=0)  # Kaç kere kandırıldı

    # Time statistics
    average_answer_time = Column(Integer, default=0)  # Ortalama cevap süresi (saniye)
    total_play_time = Column(Integer, default=0)  # Toplam oyun süresi (saniye)

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="stats")

    def __repr__(self):
        return f"<UserStats(user_id={self.user_id}, games={self.total_games_played})>"


class UserSeenQuestion(Base):
    """Tracks which questions a registered user has seen in each section/topic"""
    __tablename__ = "user_seen_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    topic_key = Column(String(160), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    seen_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "topic_key", "question_id", name="uq_user_topic_question"),
    )

    def __repr__(self):
        return f"<UserSeenQuestion(user_id={self.user_id}, topic='{self.topic_key}', q={self.question_id})>"


class SystemMigration(Base):
    """Records one-time idempotent data migrations"""
    __tablename__ = "system_migrations"

    key = Column(String(100), primary_key=True)
    applied_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SystemMigration(key='{self.key}')>"
