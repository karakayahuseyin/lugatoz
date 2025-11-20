# -*- coding: utf-8 -*-
"""User authentication and management"""
from sqlalchemy.orm import Session
from .models import User, UserStats, generate_user_id
from datetime import datetime
from typing import Optional, Dict


def create_user(db: Session, username: str) -> Optional[User]:
    """Create a new user with unique ID and username"""
    # Check if username already exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return None

    # Generate unique user_id
    max_attempts = 100
    for _ in range(max_attempts):
        user_id = generate_user_id()
        if not db.query(User).filter(User.user_id == user_id).first():
            break
    else:
        # Failed to generate unique ID after max attempts
        return None

    # Create user
    user = User(
        user_id=user_id,
        username=username,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    db.add(user)

    # Create user stats
    stats = UserStats(user_id=user_id)
    db.add(stats)

    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by user_id"""
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def update_username(db: Session, user_id: int, new_username: str) -> bool:
    """Update user's username"""
    # Check if new username is taken
    existing = db.query(User).filter(User.username == new_username).first()
    if existing and existing.user_id != user_id:
        return False

    user = get_user_by_id(db, user_id)
    if not user:
        return False

    user.username = new_username
    db.commit()
    return True


def update_last_login(db: Session, user_id: int):
    """Update user's last login time"""
    user = get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.utcnow()
        db.commit()


def get_user_stats(db: Session, user_id: int) -> Optional[UserStats]:
    """Get user statistics - creates if doesn't exist"""
    stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()

    # If stats don't exist, create them (for users created before stats feature)
    if not stats:
        # Verify user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            stats = UserStats(user_id=user_id)
            db.add(stats)
            db.commit()
            db.refresh(stats)

    return stats


def get_leaderboard(db: Session, limit: int = 100) -> list:
    """Get global leaderboard sorted by total score"""
    users = db.query(User).join(UserStats).order_by(UserStats.total_score.desc()).limit(limit).all()

    leaderboard = []
    for user in users:
        leaderboard.append({
            'user_id': user.user_id,
            'username': user.username,
            'total_score': user.stats.total_score,
            'games_played': user.stats.total_games_played,
            'games_won': user.stats.total_games_won,
            'highest_score': user.stats.highest_score,
            'correct_answers': user.stats.total_correct_answers,
            'total_questions': user.stats.total_questions_answered
        })

    return leaderboard


def update_user_stats_after_game(db: Session, user_id: int, game_data: Dict):
    """Update user stats after a game completes"""
    stats = get_user_stats(db, user_id)
    if not stats:
        return

    # Update game statistics
    stats.total_games_played += 1
    if game_data.get('won', False):
        stats.total_games_won += 1

    score = game_data.get('score', 0)
    stats.total_score += score
    if score > stats.highest_score:
        stats.highest_score = score

    # Update question statistics
    correct = game_data.get('correct_answers', 0)
    wrong = game_data.get('wrong_answers', 0)
    stats.total_correct_answers += correct
    stats.total_wrong_answers += wrong
    stats.total_questions_answered += (correct + wrong)

    # Update deception statistics
    stats.total_players_deceived += game_data.get('players_deceived', 0)
    stats.total_times_deceived += game_data.get('times_deceived', 0)

    stats.last_updated = datetime.utcnow()
    db.commit()
