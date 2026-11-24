# -*- coding: utf-8 -*-
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from pydantic import BaseModel

from .database import get_db, init_db
from .models import Question, Theme, GameStats, QuestionStats, User, UserStats, UserSeenQuestion
from .curriculum import (
    get_curriculum,
    validate_grade_and_theme,
    grade_has_themes,
    is_valid_grade,
    generate_unique_slug,
)
from .websocket import socket_app

# FastAPI uygulaması
app = FastAPI(
    title="TarihTöz API",
    description="Tarih ve Sosyal Bilgiler eğitici multiplayer bilgi oyunu",
    version="2.1.0"
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
    unacceptable_answers: Optional[str] = None
    grade: str
    theme: Optional[str] = None
    # Geriye dönük uyumluluk için opsiyonel alanlar
    acceptable_answers: Optional[str] = None
    category: Optional[str] = None
    difficulty: str = "medium"


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    correct_answer: str
    unacceptable_answers: Optional[str] = None
    acceptable_answers: Optional[str] = None
    grade: Optional[str] = None
    theme: Optional[str] = None
    category: Optional[str] = None
    difficulty: str
    is_active: bool

    class Config:
        from_attributes = True


class ThemeCreate(BaseModel):
    grade: str
    name: str


class ThemeUpdate(BaseModel):
    name: str


class ThemeMove(BaseModel):
    direction: str  # "up" | "down"


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
        "message": "TarihTöz API'ye hoş geldiniz!",
        "version": "2.1.0",
        "endpoints": {
            "health": "/health",
            "curriculum": "/api/curriculum",
            "questions": "/api/questions",
            "socket": "/socket.io/"
        }
    }


@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    return {"status": "healthy", "service": "tarihtoz"}


@app.get("/api/curriculum")
async def get_curriculum_with_counts(db: Session = Depends(get_db)):
    """Sınıf, tema ve Dünyanın Enleri yapısını soru sayılarıyla birlikte döndür"""
    sections = get_curriculum(db)

    # Toplam ve aktif soru sayılarını tek sorguda topla
    counts_rows = (
        db.query(
            Question.grade,
            Question.theme,
            Question.is_active,
            func.count(Question.id)
        )
        .group_by(Question.grade, Question.theme, Question.is_active)
        .all()
    )

    total_by_grade = {}
    active_by_grade = {}
    total_by_theme = {}
    active_by_theme = {}
    uncategorized_total = 0

    for grade, theme, is_active, count in counts_rows:
        if not grade:
            uncategorized_total += count
            continue
        total_by_grade[grade] = total_by_grade.get(grade, 0) + count
        if is_active:
            active_by_grade[grade] = active_by_grade.get(grade, 0) + count

        key = (grade, theme)
        total_by_theme[key] = total_by_theme.get(key, 0) + count
        if is_active:
            active_by_theme[key] = active_by_theme.get(key, 0) + count

    for section in sections:
        g_id = section["id"]
        section["total_questions"] = total_by_grade.get(g_id, 0)
        section["active_questions"] = active_by_grade.get(g_id, 0)

        for theme_obj in section["themes"]:
            key = (g_id, theme_obj["id"])
            theme_obj["total_questions"] = total_by_theme.get(key, 0)
            theme_obj["active_questions"] = active_by_theme.get(key, 0)

    return {
        "sections": sections,
        "uncategorized_questions": uncategorized_total
    }


def _resequence_grade_themes(db: Session, grade: str):
    """Ensure display_order values for a grade are contiguous 1..N."""
    remaining = (
        db.query(Theme)
        .filter(Theme.grade == grade)
        .order_by(Theme.display_order.asc(), Theme.id.asc())
        .all()
    )
    for idx, t in enumerate(remaining, start=1):
        t.display_order = idx


@app.post("/api/themes", status_code=201)
async def create_theme(payload: ThemeCreate, db: Session = Depends(get_db)):
    """Bir sınıf altına yeni tema ekle"""
    if not is_valid_grade(payload.grade) or not grade_has_themes(payload.grade):
        raise HTTPException(status_code=400, detail="Bu bölüm altına tema eklenemez!")

    clean_name = " ".join(payload.name.strip().split())
    if not clean_name:
        raise HTTPException(status_code=400, detail="Tema adı zorunludur!")

    existing_same = (
        db.query(Theme)
        .filter(Theme.grade == payload.grade, func.lower(Theme.name) == clean_name.lower())
        .first()
    )
    if existing_same:
        raise HTTPException(status_code=400, detail="Bu sınıfta aynı isimde bir tema zaten var!")

    max_order = (
        db.query(func.max(Theme.display_order))
        .filter(Theme.grade == payload.grade)
        .scalar()
        or 0
    )
    slug = generate_unique_slug(db, payload.grade, clean_name)

    db_theme = Theme(
        grade=payload.grade,
        slug=slug,
        name=clean_name,
        display_order=max_order + 1,
    )
    db.add(db_theme)
    db.commit()
    db.refresh(db_theme)

    return {
        "db_id": db_theme.id,
        "id": db_theme.slug,
        "grade": db_theme.grade,
        "order": db_theme.display_order,
        "name": db_theme.name,
        "full_name": f"{db_theme.display_order}. {db_theme.name}",
    }


@app.put("/api/themes/{theme_id}")
async def update_theme(theme_id: int, payload: ThemeUpdate, db: Session = Depends(get_db)):
    """Tema adını güncelle"""
    db_theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not db_theme:
        raise HTTPException(status_code=404, detail="Tema bulunamadı!")

    clean_name = " ".join(payload.name.strip().split())
    if not clean_name:
        raise HTTPException(status_code=400, detail="Tema adı zorunludur!")

    existing_same = (
        db.query(Theme)
        .filter(
            Theme.grade == db_theme.grade,
            Theme.id != theme_id,
            func.lower(Theme.name) == clean_name.lower(),
        )
        .first()
    )
    if existing_same:
        raise HTTPException(status_code=400, detail="Bu sınıfta aynı isimde başka bir tema zaten var!")

    db_theme.name = clean_name
    db.commit()
    db.refresh(db_theme)

    return {
        "db_id": db_theme.id,
        "id": db_theme.slug,
        "grade": db_theme.grade,
        "order": db_theme.display_order,
        "name": db_theme.name,
        "full_name": f"{db_theme.display_order}. {db_theme.name}",
    }


@app.patch("/api/themes/{theme_id}/move")
async def move_theme(theme_id: int, payload: ThemeMove, db: Session = Depends(get_db)):
    """Temanın sırasını yukarı/aşağı taşı"""
    if payload.direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Geçersiz yön!")

    db_theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not db_theme:
        raise HTTPException(status_code=404, detail="Tema bulunamadı!")

    siblings = (
        db.query(Theme)
        .filter(Theme.grade == db_theme.grade)
        .order_by(Theme.display_order.asc(), Theme.id.asc())
        .all()
    )
    idx = next((i for i, t in enumerate(siblings) if t.id == theme_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Tema bulunamadı!")

    swap_idx = idx - 1 if payload.direction == "up" else idx + 1
    if 0 <= swap_idx < len(siblings):
        siblings[idx], siblings[swap_idx] = siblings[swap_idx], siblings[idx]
        for new_order, t in enumerate(siblings, start=1):
            t.display_order = new_order
        db.commit()

    return {"message": "Tema sırası güncellendi"}


@app.delete("/api/themes/{theme_id}")
async def delete_theme(theme_id: int, db: Session = Depends(get_db)):
    """Temayı ve altındaki soruları kalıcı olarak sil"""
    db_theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not db_theme:
        raise HTTPException(status_code=404, detail="Tema bulunamadı!")

    grade = db_theme.grade
    slug = db_theme.slug

    # Temaya ait soruları ve istatistiklerini temizle
    theme_questions = (
        db.query(Question.id)
        .filter(Question.grade == grade, Question.theme == slug)
        .all()
    )
    q_ids = [row[0] for row in theme_questions]
    if q_ids:
        db.query(UserSeenQuestion).filter(UserSeenQuestion.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(QuestionStats).filter(QuestionStats.question_id.in_(q_ids)).delete(synchronize_session=False)
        db.query(Question).filter(Question.id.in_(q_ids)).delete(synchronize_session=False)

    db.delete(db_theme)
    db.flush()
    _resequence_grade_themes(db, grade)
    db.commit()

    return {
        "message": "Tema silindi",
        "id": theme_id,
        "deleted_questions": len(q_ids),
    }


@app.get("/api/questions")
async def get_questions(
    skip: int = 0,
    limit: Optional[int] = None,
    grade: Optional[str] = None,
    theme: Optional[str] = None,
    category: Optional[str] = None,
    uncategorized: bool = False,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Soruları sınıf/tema filtresi ve istatistiklerle birlikte listele"""
    query = db.query(Question)

    if not include_inactive:
        query = query.filter(Question.is_active == True)

    if uncategorized:
        query = query.filter(Question.grade.is_(None))
    elif grade:
        query = query.filter(Question.grade == grade)
        if grade_has_themes(grade):
            if theme:
                query = query.filter(Question.theme == theme)
        else:
            query = query.filter((Question.theme.is_(None)) | (Question.theme == ""))
    elif theme:
        query = query.filter(Question.theme == theme)

    if category:
        query = query.filter(Question.category == category)

    query = query.order_by(Question.id.desc()).offset(skip)
    if limit:
        query = query.limit(limit)

    questions = query.all()

    result = []
    for q in questions:
        unacceptable = q.unacceptable_answers if q.unacceptable_answers is not None else q.acceptable_answers
        q_dict = {
            'id': q.id,
            'question_text': q.question_text,
            'correct_answer': q.correct_answer,
            'unacceptable_answers': unacceptable,
            'acceptable_answers': unacceptable,
            'grade': q.grade,
            'theme': q.theme,
            'category': q.category,
            'difficulty': q.difficulty,
            'is_active': q.is_active,
            'stats': None
        }

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
    q_text = question.question_text.strip()
    c_answer = question.correct_answer.strip()

    if not q_text or not c_answer:
        raise HTTPException(status_code=400, detail="Soru ve doğru cevap alanları zorunludur!")

    try:
        valid_grade, valid_theme = validate_grade_and_theme(question.grade, question.theme, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    raw_unacceptable = (
        question.unacceptable_answers
        if question.unacceptable_answers is not None
        else question.acceptable_answers
    )
    cleaned_unacceptable = raw_unacceptable.strip() if raw_unacceptable and raw_unacceptable.strip() else None

    db_question = Question(
        question_text=q_text,
        correct_answer=c_answer,
        unacceptable_answers=cleaned_unacceptable,
        acceptable_answers=cleaned_unacceptable,
        grade=valid_grade,
        theme=valid_theme,
        category=question.category,
        difficulty=question.difficulty or "medium",
        is_active=True
    )
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

    q_text = question.question_text.strip()
    c_answer = question.correct_answer.strip()
    if not q_text or not c_answer:
        raise HTTPException(status_code=400, detail="Soru ve doğru cevap alanları zorunludur!")

    try:
        valid_grade, valid_theme = validate_grade_and_theme(question.grade, question.theme, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    raw_unacceptable = (
        question.unacceptable_answers
        if question.unacceptable_answers is not None
        else question.acceptable_answers
    )
    cleaned_unacceptable = raw_unacceptable.strip() if raw_unacceptable and raw_unacceptable.strip() else None

    db_question.question_text = q_text
    db_question.correct_answer = c_answer
    db_question.unacceptable_answers = cleaned_unacceptable
    db_question.acceptable_answers = cleaned_unacceptable
    db_question.grade = valid_grade
    db_question.theme = valid_theme
    if question.category is not None:
        db_question.category = question.category
    if question.difficulty:
        db_question.difficulty = question.difficulty

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

    # İlişkili istatistik ve görülme kayıtlarını sil (FK kısıtı)
    db.query(UserSeenQuestion).filter(
        UserSeenQuestion.question_id == question_id
    ).delete()
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


@app.post("/api/rooms/{room_code}/reset")
async def reset_room(room_code: str):
    """Admin: Odayı zorla sıfırla (tüm oyuncuları çıkar ve odayı temizle)"""
    from .game_manager import game_manager
    from .websocket import sio, socket_rooms, cancel_all_room_tasks

    room = game_manager.get_room(room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")

    # Asılı task'ları iptal et
    cancel_all_room_tasks(room_code)

    # Odadaki oyunculara bildir (odadan çıkarmadan önce!)
    await sio.emit('room_reset', {
        'message': 'Oda admin tarafından sıfırlandı. Ana sayfaya yönlendiriliyorsunuz...'
    }, room=room_code)

    # Socket tracking'den oyuncuları temizle
    players_to_remove = [sid for sid, code in socket_rooms.items() if code == room_code]
    for player_sid in players_to_remove:
        await sio.leave_room(player_sid, room_code)
        del socket_rooms[player_sid]

    # Odayı sıfırla
    game_manager.reset_room(room_code)

    return {"message": "Oda sıfırlandı", "room_code": room_code}


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


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Tek bir kullanıcıyı ve puan/istatistik/görülen soru geçmişini kalıcı olarak sil"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    db.query(UserSeenQuestion).filter(UserSeenQuestion.user_id == user_id).delete()
    db.query(UserStats).filter(UserStats.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    # Aktif socket eşleşmesi varsa temizle
    from .websocket import socket_users
    for sid in [s for s, uid in socket_users.items() if uid == user_id]:
        del socket_users[sid]

    return {"message": "Kullanıcı kalıcı olarak silindi", "user_id": user_id}


@app.delete("/api/users")
async def delete_all_users(db: Session = Depends(get_db)):
    """Tüm kullanıcıları, puan/istatistiklerini ve liderlik tablosunu sıfırla (sorulara dokunulmaz)"""
    deleted_count = db.query(User).count()
    db.query(UserSeenQuestion).delete()
    db.query(UserStats).delete()
    db.query(User).delete()

    stats = db.query(GameStats).first()
    if stats:
        stats.total_players = 0
        stats.total_sessions = 0
        stats.completed_sessions = 0
        stats.total_questions_answered = 0
        stats.total_correct_answers = 0
        stats.total_wrong_answers = 0

    db.commit()

    from .websocket import socket_users
    socket_users.clear()

    return {"message": f"{deleted_count} kullanıcı ve tüm liderlik istatistikleri silindi", "deleted_count": deleted_count}


# Socket.IO'yu FastAPI'ye mount et
app.mount("/socket.io", socket_app)


@app.get("/api/stats", response_model=GameStatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """İstatistikleri getir"""
    stats = db.query(GameStats).first()
    if not stats:
        stats = GameStats()
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


@app.on_event("startup")
async def startup_event():
    print("TarihToz sunucusu baslatiliyor...")
    init_db()
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
