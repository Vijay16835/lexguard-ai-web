import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://postgres:2004@localhost/lexguard_db"

def run_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Checking for missing columns in otp_verifications...")
        
        # Add 'purpose' column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='otp_verifications' AND column_name='purpose') THEN
                    ALTER TABLE otp_verifications ADD COLUMN purpose VARCHAR(50) DEFAULT 'registration';
                END IF;
            END $$;
        """)
        
        # Add 'registration_data' column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='otp_verifications' AND column_name='registration_data') THEN
                    ALTER TABLE otp_verifications ADD COLUMN registration_data JSONB;
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
