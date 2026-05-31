"""
Database Migration Script for LexGuard AI — Groq Integration
Creates all tables needed for full AI document analysis pipeline.

Run: python migrate_groq_full.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

def run_migration():
    """Create or update all tables for the Groq integration."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    with engine.connect() as conn:
        # ── 1. documents table ──
        if "documents" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE documents (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    path VARCHAR NOT NULL,
                    type VARCHAR NOT NULL,
                    size_in_mb FLOAT,
                    status VARCHAR DEFAULT 'pending',
                    user_id INTEGER REFERENCES users(id),
                    extracted_text TEXT,
                    document_type VARCHAR,
                    risk_score INTEGER,
                    risk_level VARCHAR,
                    summary TEXT,
                    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
                    analyzed_at TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS ix_documents_id ON documents(id);
                CREATE INDEX IF NOT EXISTS ix_documents_name ON documents(name);
            """))
            print("[OK] Created 'documents' table")
        else:
            # Add missing columns
            existing_cols = {c['name'] for c in inspector.get_columns('documents')}
            if 'document_type' not in existing_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN document_type VARCHAR;"))
                print("[OK] Added 'document_type' column to documents")
            if 'risk_score' not in existing_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN risk_score INTEGER;"))
                print("[OK] Added 'risk_score' column to documents")
            if 'risk_level' not in existing_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN risk_level VARCHAR;"))
                print("[OK] Added 'risk_level' column to documents")
            if 'summary' not in existing_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN summary TEXT;"))
                print("[OK] Added 'summary' column to documents")
            if 'extracted_text' not in existing_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN extracted_text TEXT;"))
                print("[OK] Added 'extracted_text' column to documents")
            if 'analyzed_at' not in existing_cols:
                conn.execute(text("ALTER TABLE documents ADD COLUMN analyzed_at TIMESTAMPTZ;"))
                print("[OK] Added 'analyzed_at' column to documents")
            print("[OK] 'documents' table verified")

        # ── 2. document_chunks table ──
        if "document_chunks" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS ix_document_chunks_doc ON document_chunks(document_id);
            """))
            print("[OK] Created 'document_chunks' table")
        else:
            print("[OK] 'document_chunks' table exists")

        # ── 3. analysis table ──
        if "analysis" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE analysis (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
                    risk_level VARCHAR,
                    risk_score INTEGER,
                    summary TEXT,
                    ai_confidence FLOAT,
                    parties JSON,
                    important_dates JSON,
                    recommendations JSON,
                    raw_analysis_data JSON,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            print("[OK] Created 'analysis' table")
        else:
            existing_cols = {c['name'] for c in inspector.get_columns('analysis')}
            if 'raw_analysis_data' not in existing_cols:
                conn.execute(text("ALTER TABLE analysis ADD COLUMN raw_analysis_data JSON;"))
                print("[OK] Added 'raw_analysis_data' column to analysis")
            if 'parties' not in existing_cols:
                conn.execute(text("ALTER TABLE analysis ADD COLUMN parties JSON;"))
                print("[OK] Added 'parties' column to analysis")
            if 'important_dates' not in existing_cols:
                conn.execute(text("ALTER TABLE analysis ADD COLUMN important_dates JSON;"))
                print("[OK] Added 'important_dates' column to analysis")
            if 'recommendations' not in existing_cols:
                conn.execute(text("ALTER TABLE analysis ADD COLUMN recommendations JSON;"))
                print("[OK] Added 'recommendations' column to analysis")
            print("[OK] 'analysis' table verified")

        # ── 4. clauses table ──
        if "clauses" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE clauses (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    risk_level VARCHAR,
                    mitigation_advice TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            print("[OK] Created 'clauses' table")
        else:
            existing_cols = {c['name'] for c in inspector.get_columns('clauses')}
            if 'mitigation_advice' not in existing_cols:
                conn.execute(text("ALTER TABLE clauses ADD COLUMN mitigation_advice TEXT;"))
                print("[OK] Added 'mitigation_advice' column to clauses")
            print("[OK] 'clauses' table verified")

        # ── 5. chat_history table ──
        if "chat_history" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE chat_history (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            print("[OK] Created 'chat_history' table")
        else:
            print("[OK] 'chat_history' table exists")

        conn.commit()
        print("\n✅ All database tables are ready for LexGuard AI!")


if __name__ == "__main__":
    print("=" * 50)
    print("LexGuard AI — Database Migration (Groq Full)")
    print("=" * 50)
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
