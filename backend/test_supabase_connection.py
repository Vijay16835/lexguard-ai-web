import os
import urllib.parse
import psycopg2
from dotenv import load_dotenv

load_dotenv()

raw_url = os.getenv("DATABASE_URL")
if raw_url:
    url = raw_url.replace("Tvijay@1098", "Tvijay%401098")
else:
    url = ""

def verify_connection():
    print("Testing Supabase PostgreSQL Connection...")
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        print("[OK] Database connection successful.")
        
        tables_to_check = ['users', 'documents', 'analysis'] 
        missing_tables = []
        for table in tables_to_check:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"[OK] Table '{table}' verified (Record count: {count}).")
            except Exception as e:
                print(f"[FAIL] Table '{table}' is missing or inaccessible: {e}")
                missing_tables.append(table)
                conn.rollback()

        cur.close()
        conn.close()
        
        if missing_tables:
            print("\nWARNING: Missing tables detected.")
            print(",".join(missing_tables))
        else:
            print("\n[OK] All required tables are present.")
            
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")

if __name__ == "__main__":
    verify_connection()
