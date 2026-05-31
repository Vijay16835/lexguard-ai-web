"""
Database migration script for Groq AI integration.
Adds new columns to the documents table for AI analysis results.
"""
import psycopg2

DATABASE_URL = "postgresql://postgres:2004@localhost/lexguard_db"

def run_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Running Groq AI integration migration...")
        
        # Add new columns to documents table
        columns = [
            ("documents", "extracted_text", "TEXT"),
            ("documents", "document_type", "VARCHAR(100)"),
            ("documents", "risk_score", "INTEGER"),
            ("documents", "risk_level", "VARCHAR(20)"),
            ("documents", "summary", "TEXT"),
            ("documents", "analyzed_at", "TIMESTAMP WITH TIME ZONE"),
        ]
        
        for table, column, col_type in columns:
            cur.execute(f"""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='{table}' AND column_name='{column}') THEN
                        ALTER TABLE {table} ADD COLUMN {column} {col_type};
                    END IF;
                END $$;
            """)
            print(f"  OK {table}.{column}")
        
        conn.commit()
        print("Migration completed successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
