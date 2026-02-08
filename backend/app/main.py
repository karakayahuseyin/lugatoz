# -*- coding: utf-8 -*-
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from .database import get_db, init_db
from .models import Question, GameStats, QuestionStats, User, UserStats
from .websocket import socket_app

# FastAPI uygulaması
app = FastAPI(
    title="LügaTöz API",
    description="Eğitici multiplayer aldatma oyunu",
    version="1.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic modelleri
class QuestionCreate(BaseModel):
    question_text: str
    correct_answer: str
    acceptable_answers: str = None
    category: str = None
    difficulty: str = "medium"


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    correct_answer: str
    acceptable_answers: str | None
    category: str | None
    difficulty: str
    is_active: bool

    class Config:
        from_attributes = True


class GameStatsResponse(BaseModel):
    id: int
    total_players: int
    total_sessions: int
    completed_sessions: int
    total_questions_answered: int
    total_correct_answers: int
    total_wrong_answers: int

    class Config:
        from_attributes = True


# API endpoints
@app.get("/")
async def root():
    """Ana endpoint"""
    return {
        "message": "LügaTöz API'ye hoş geldiniz!",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "questions": "/api/questions",
            "socket": "/socket.io/"
        }
    }


@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    return {"status": "healthy", "service": "lugatoz"}


@app.get("/api/questions")
async def get_questions(
    skip: int = 0,
    limit: int = None,
    category: str = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Tüm soruları listele (istatistiklerle birlikte)"""
    query = db.query(Question)

    if not include_inactive:
        query = query.filter(Question.is_active == True)

    if category:
        query = query.filter(Question.category == category)

    query = query.offset(skip)
    if limit:
        query = query.limit(limit)

    questions = query.all()

    # Add statistics to each question
    result = []
    for q in questions:
        q_dict = {
            'id': q.id,
            'question_text': q.question_text,
            'correct_answer': q.correct_answer,
            'acceptable_answers': q.acceptable_answers,
            'category': q.category,
            'difficulty': q.difficulty,
            'is_active': q.is_active,
            'stats': None
        }

        # Get stats for this question
        stats = db.query(QuestionStats).filter(
            QuestionStats.question_id == q.id
        ).first()

        if stats:
            q_dict['stats'] = {
                'times_asked': stats.times_asked,
                'times_correct': stats.times_correct,
                'times_wrong': stats.times_wrong,
                'total_players_seen': stats.total_players_seen,
                'games_used': stats.games_used,
                'success_rate': (stats.times_correct / stats.times_asked * 100) if stats.times_asked > 0 else 0
            }

        result.append(q_dict)

    return result


@app.get("/api/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """Tek bir soru getir"""
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    return question


@app.post("/api/questions", response_model=QuestionResponse, status_code=201)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """Yeni soru oluştur"""
    db_question = Question(**question.model_dump())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@app.put("/api/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    """Soru güncelle"""
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    for key, value in question.model_dump().items():
        setattr(db_question, key, value)

    db.commit()
    db.refresh(db_question)
    return db_question


@app.patch("/api/questions/{question_id}/toggle")
async def toggle_question_active(question_id: int, db: Session = Depends(get_db)):
    """Sorunun aktif/pasif durumunu değiştir"""
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    db_question.is_active = not db_question.is_active
    db.commit()
    db.refresh(db_question)

    return {
        "id": db_question.id,
        "is_active": db_question.is_active,
        "message": f"Soru {'aktif' if db_question.is_active else 'pasif'} yapıldı"
    }


@app.delete("/api/questions/{question_id}")
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """Soru sil (hard delete - veritabanından kalıcı olarak kaldırır)"""
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    # İlişkili istatistikleri sil (FK kısıtı)
    db.query(QuestionStats).filter(
        QuestionStats.question_id == question_id
    ).delete()

    db.delete(db_question)
    db.commit()
    return {"message": "Soru kalıcı olarak silindi", "id": question_id}


@app.get("/api/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Tüm kategorileri listele"""
    categories = db.query(Question.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]


@app.get("/api/rooms")
async def get_rooms():
    """Tüm odaları listele"""
    from .game_manager import game_manager
    return game_manager.get_all_rooms()


@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Tüm kullanıcıları listele (Admin için)"""
    users = db.query(User).join(UserStats).order_by(User.user_id.desc()).all()

    result = []
    for user in users:
        result.append({
            'user_id': user.user_id,
            'username': user.username,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'stats': {
                'total_games_played': user.stats.total_games_played,
                'total_games_won': user.stats.total_games_won,
                'total_score': user.stats.total_score,
                'highest_score': user.stats.highest_score,
                'total_correct_answers': user.stats.total_correct_answers,
                'total_questions_answered': user.stats.total_questions_answered
            } if user.stats else None
        })

    return result


# Socket.IO'yu FastAPI'ye mount et
app.mount("/socket.io", socket_app)


# Başlangıçta veritabanını initialize et
@app.get("/api/stats", response_model=GameStatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """İstatistikleri getir"""
    stats = db.query(GameStats).first()
    if not stats:
        # İlk kez çağrılıyorsa boş stats oluştur
        stats = GameStats()
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


@app.on_event("startup")
async def startup_event():
    print("LugaToz sunucusu baslatiliyor...")
    init_db()
    # Istatistik kaydi olustur
    from .database import SessionLocal
    db = SessionLocal()
    try:
        stats = db.query(GameStats).first()
        if not stats:
            stats = GameStats()
            db.add(stats)
            db.commit()
    finally:
        db.close()
    print("Sunucu hazir!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
