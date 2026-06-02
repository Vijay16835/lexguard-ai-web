-- ============================================================
-- LexGuard AI — Production Performance Indexes
-- Run once in: Supabase Dashboard → SQL Editor
-- All statements are idempotent (IF NOT EXISTS).
-- ============================================================

-- 1. Documents filtered/sorted by user  (GET /documents/history)
--    Without this, every history fetch is a full-table scan.
CREATE INDEX IF NOT EXISTS idx_documents_user_id
    ON documents (user_id);

-- 2. Documents ordered by upload date per user  (history list sort)
CREATE INDEX IF NOT EXISTS idx_documents_user_uploaded
    ON documents (user_id, uploaded_at DESC);

-- 3. Documents filtered by processing status  (status polling)
CREATE INDEX IF NOT EXISTS idx_documents_status
    ON documents (status)
    WHERE status IN ('pending', 'extracting', 'analyzing');

-- 4. Analysis record by document  (GET /documents/{id})
--    1-to-1 relationship but queried by FK — needs an index.
CREATE INDEX IF NOT EXISTS idx_analysis_document_id
    ON analysis (document_id);

-- 5. Clauses by document  (1-to-N, fetched on every document detail)
CREATE INDEX IF NOT EXISTS idx_clauses_document_id
    ON clauses (document_id);

-- 6. Chat history by document + user  (loaded on every chat message)
CREATE INDEX IF NOT EXISTS idx_chat_history_doc_user
    ON chat_history (document_id, user_id);

-- 7. Chat history ordered chronologically  (history scroll)
CREATE INDEX IF NOT EXISTS idx_chat_history_created
    ON chat_history (document_id, user_id, created_at ASC);

-- 8. OTP lookup by email  (signup, login, password reset)
--    If otp_verifications table exists in PostgreSQL (currently Firestore):
CREATE INDEX IF NOT EXISTS idx_otp_email
    ON otp_verifications (email)
    WHERE EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'otp_verifications'
    );

-- Verify indexes were created:
SELECT indexname, tablename, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
