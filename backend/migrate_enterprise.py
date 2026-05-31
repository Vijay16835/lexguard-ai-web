import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:2004@localhost/lexguard_db")

def run_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Migrating database for enterprise voice and multilingual features...")
        
        # 1. Update user_settings
        print("Checking/adding voice_speed and voice_response_enabled to user_settings...")
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='user_settings' AND column_name='voice_speed') THEN
                    ALTER TABLE user_settings ADD COLUMN voice_speed FLOAT DEFAULT 1.0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='user_settings' AND column_name='voice_response_enabled') THEN
                    ALTER TABLE user_settings ADD COLUMN voice_response_enabled BOOLEAN DEFAULT FALSE;
                END IF;
            END $$;
        """)
        
        # 2. Update chat_history
        print("Checking/adding language to chat_history...")
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='chat_history' AND column_name='language') THEN
                    ALTER TABLE chat_history ADD COLUMN language VARCHAR(50) DEFAULT 'English';
                END IF;
            END $$;
        """)
        
        # 3. Create translated_summaries table
        print("Checking/creating translated_summaries table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS translated_summaries (
                id SERIAL PRIMARY KEY,
                document_id VARCHAR(255) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                language VARCHAR(50) NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_doc_lang UNIQUE(document_id, language)
            );
        """)
        
        # 4. Create index for translated_summaries
        cur.execute("CREATE INDEX IF NOT EXISTS idx_translated_summaries_doc_lang ON translated_summaries(document_id, language);")

        conn.commit()
        print("Migration for enterprise features completed successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
