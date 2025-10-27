# -*- coding: utf-8 -*-
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from .database import get_db, init_db
from .models import Question
from .websocket import socket_app

# FastAPI uygulaması
app = FastAPI(
    title="ÖzBilig API",
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
    category: str = None
    difficulty: str = "medium"


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    correct_answer: str
    category: str | None
    difficulty: str
    is_active: bool

    class Config:
        from_attributes = True


# API endpoints
@app.get("/")
async def root():
    """Ana endpoint"""
    return {
        "message": "ÖzBilig API'ye hoş geldiniz!",
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
    return {"status": "healthy", "service": "ozbilig"}


@app.get("/api/questions", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Tüm soruları listele"""
    query = db.query(Question).filter(Question.is_active == True)

    if category:
        query = query.filter(Question.category == category)

    questions = query.offset(skip).limit(limit).all()
    return questions


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


@app.delete("/api/questions/{question_id}")
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """Soru sil (soft delete)"""
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    db_question.is_active = False
    db.commit()
    return {"message": "Soru silindi", "id": question_id}


@app.get("/api/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Tüm kategorileri listele"""
    categories = db.query(Question.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]


# Socket.IO'yu FastAPI'ye mount et
app.mount("/socket.io", socket_app)


# Başlangıçta veritabanını initialize et
@app.on_event("startup")
async def startup_event():
    print("🚀 ÖzBilig sunucusu başlatılıyor...")
    init_db()
    print("✓ Sunucu hazır!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
