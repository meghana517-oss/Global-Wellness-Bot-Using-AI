"""Utility script to normalize chat_logs emails and migrate legacy messages into chat_logs.
Run with: python scripts/fix_chat_history.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'wellness.db'

def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Ensure chat_logs table exists
    cur.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='chat_logs'""")
    if not cur.fetchone():
        print("chat_logs table does not exist. Nothing to fix.")
        return

    # 2. Normalize email casing
    cur.execute("UPDATE chat_logs SET user_id = lower(user_id) WHERE user_id != lower(user_id)")
    normalized = conn.total_changes

    # 3. Count pre-migration
    cur.execute("SELECT COUNT(*) FROM chat_logs")
    pre_count = cur.fetchone()[0]

    # 4. Migrate legacy messages table if present
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
    if cur.fetchone():
        # Insert rows not already present within 2 seconds window
        migration_sql = """
            INSERT INTO chat_logs (user_id, role, message, response, feedback, timestamp)
            SELECT m.email, 'user', m.user_text, m.bot_response, NULL, m.timestamp
            FROM messages m
            WHERE NOT EXISTS (
                SELECT 1 FROM chat_logs c
                WHERE c.user_id = lower(m.email)
                  AND c.message = m.user_text
                  AND ABS(strftime('%s', c.timestamp) - strftime('%s', m.timestamp)) <= 2
            )
        """
        cur.execute(migration_sql)
    conn.commit()

    # 5. Count post-migration
    cur.execute("SELECT COUNT(*) FROM chat_logs")
    post_count = cur.fetchone()[0]

    print({
        'normalized_rows': normalized,
        'pre_count': pre_count,
        'post_count': post_count,
        'migrated_new_rows': post_count - pre_count
    })

if __name__ == '__main__':
    main()
