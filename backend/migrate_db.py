#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script to add acceptable_answers column to questions table
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'ozbilig.db')

def migrate():
    """Add acceptable_answers column if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(questions)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'acceptable_answers' not in columns:
            print("Adding acceptable_answers column...")
            cursor.execute("""
                ALTER TABLE questions
                ADD COLUMN acceptable_answers TEXT
            """)
            conn.commit()
            print("✓ Migration completed successfully!")
        else:
            print("✓ acceptable_answers column already exists. No migration needed.")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starting database migration...")
    migrate()
