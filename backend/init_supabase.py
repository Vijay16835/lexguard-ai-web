import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    if "[YOUR-SUPABASE-PASSWORD]" in DATABASE_URL:
        print("ERROR: Please replace [YOUR-SUPABASE-PASSWORD] in the .env file with your actual Supabase password before running this script.")
        return

    print(f"Connecting to Supabase PostgreSQL...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Reading database_schema.sql...")
        with open("database_schema.sql", "r") as f:
            schema_sql = f.read()
            
        print("Executing schema...")
        cur.execute(schema_sql)
        
        conn.commit()
        print("[OK] Supabase database initialized successfully!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[FAIL] Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
