#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database migration script for LügaTöz
Adds GameStats and QuestionStats tables to existing database
"""

from app.database import engine, SessionLocal
from app.models import Base, GameStats, QuestionStats
from sqlalchemy import inspect

def migrate():
    """Run database migration"""
    print("🔄 Starting database migration...")

    # Create inspector to check existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print(f"📋 Existing tables: {existing_tables}")

    # Create all tables (will skip existing ones)
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created/verified")

    # Check if GameStats table exists and has data
    db = SessionLocal()
    try:
        stats = db.query(GameStats).first()
        if not stats:
            print("📊 Creating initial GameStats record...")
            stats = GameStats()
            db.add(stats)
            db.commit()
            print("✓ GameStats initialized")
        else:
            print("✓ GameStats already exists")

        # QuestionStats will be created automatically per question when needed
        print("✓ QuestionStats table ready (stats will be created per question)")
    finally:
        db.close()

    print("✅ Migration completed successfully!")
    print("\n📝 New features:")
    print("  - GameStats: Global game statistics")
    print("  - QuestionStats: Per-question statistics")
    print("  - Emoji reactions on answers")
    print("  - Player color coding")

if __name__ == "__main__":
    migrate()
