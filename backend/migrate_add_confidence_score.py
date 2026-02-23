"""
Migration script to add confidence_score column to messages table.

This migration adds the confidence_score column (REAL/Float) to the messages table
to store LLM self-assessed confidence scores (0.0-1.0).

Run this script once to update your existing database:
    python migrate_add_confidence_score.py
"""

import sqlite3
import sys
import os

def run_migration():
    """Add confidence_score column to messages table"""
    
    db_path = "askbase.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        print("   The database will be created automatically when you start the application.")
        print("   No migration needed for a fresh database.")
        return True
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'confidence_score' in column_names:
            print("✅ confidence_score column already exists. No migration needed.")
            conn.close()
            return True
        
        # Add the column
        print("📝 Adding confidence_score column to messages table...")
        cursor.execute("""
            ALTER TABLE messages 
            ADD COLUMN confidence_score REAL
        """)
        
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'confidence_score' in column_names:
            print("✅ Migration successful! confidence_score column added.")
            print(f"   Column type: REAL (Float, nullable)")
            print(f"   Purpose: Stores LLM self-assessed confidence (0.0-1.0)")
        else:
            print("❌ Migration failed. Column was not added.")
            conn.close()
            return False
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add confidence_score to messages table")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    print()
    if success:
        print("Migration complete! You can now start your application.")
        sys.exit(0)
    else:
        print("Migration failed. Please check the errors above.")
        sys.exit(1)
