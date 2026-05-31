import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL").replace("Tvijay@1098", "Tvijay%401098")

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    # Drop foreign keys first to allow type change
    cur.execute("ALTER TABLE user_settings DROP CONSTRAINT IF EXISTS user_settings_user_id_fkey;")
    cur.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_user_id_fkey;")
    cur.execute("ALTER TABLE chat_history DROP CONSTRAINT IF EXISTS chat_history_user_id_fkey;")
    cur.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey;")
    
    # Change columns to VARCHAR(255)
    cur.execute("ALTER TABLE users ALTER COLUMN id TYPE VARCHAR(255);")
    # Also change id sequence dependency
    cur.execute("ALTER TABLE users ALTER COLUMN id DROP DEFAULT;")
    
    cur.execute("ALTER TABLE user_settings ALTER COLUMN user_id TYPE VARCHAR(255);")
    cur.execute("ALTER TABLE documents ALTER COLUMN user_id TYPE VARCHAR(255);")
    cur.execute("ALTER TABLE chat_history ALTER COLUMN user_id TYPE VARCHAR(255);")
    cur.execute("ALTER TABLE notifications ALTER COLUMN user_id TYPE VARCHAR(255);")
    
    # Re-add foreign keys
    cur.execute("ALTER TABLE user_settings ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE documents ADD CONSTRAINT documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE chat_history ADD CONSTRAINT chat_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE notifications ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    
    conn.commit()
    print("Successfully altered user_id columns to VARCHAR(255)")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
