import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://postgres:2004@localhost/lexguard_db"

def run_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Checking for missing columns in users table...")
        
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='otp_code') THEN
                    ALTER TABLE users ADD COLUMN otp_code VARCHAR(255);
                END IF;
            END $$;
        """)
        
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='users' AND column_name='otp_expiry') THEN
                    ALTER TABLE users ADD COLUMN otp_expiry TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("Migration completed successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
