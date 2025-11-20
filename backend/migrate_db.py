#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script - creates User and UserStats tables
"""
from app.database import engine, Base
from app.models import User, UserStats, Question, GameSession, Player, GameStats, QuestionStats

def migrate():
    """Create all tables (only creates new ones, existing tables are not modified)"""
    print("Starting database migration...")
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("✓ Database migration completed successfully!")
    print("\nNew tables added:")
    print("  - users")
    print("  - user_stats")
    print("\nExisting tables preserved:")
    print("  - questions")
    print("  - game_sessions")
    print("  - players")
    print("  - game_stats")
    print("  - question_stats")

if __name__ == '__main__':
    migrate()
