# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Question(Base):
    """Question model"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(String(500), nullable=False)
    category = Column(String(100), nullable=True)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Question(id={self.id}, text='{self.question_text[:50]}...')>"


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
