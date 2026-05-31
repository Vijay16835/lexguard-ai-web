# LexGuard AI - Backend Architecture

This is the production-ready backend for the LexGuard AI application, built with FastAPI, PostgreSQL, and LangChain.

## Tech Stack
- **FastAPI**: Modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.
- **PostgreSQL**: Robust relational database for user and document metadata.
- **SQLAlchemy**: SQL Toolkit and Object Relational Mapper for database interactions.
- **LangChain**: Framework for developing applications powered by large language models (LLMs).
- **JWT**: Secure authentication system.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   - Copy `.env.example` to `.env`.
   - Update `DATABASE_URL`, `OPENAI_API_KEY`, and other credentials.

3. **Database Initialization**:
   - Ensure PostgreSQL is running and the database is created.
   - Run migrations (or use `SQLAlchemy` auto-creation for dev).

4. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Directory Structure
- `app/api/`: API endpoints organized by feature (Auth, Documents, AI, etc.).
- `app/core/`: Global configurations, security settings, and environment variables.
- `app/db/`: Database session management and base model.
- `app/models/`: SQLAlchemy ORM models.
- `app/schemas/`: Pydantic schemas for request/response validation.
- `app/services/`: Business logic and external service integrations (AI, Files).

## Features
- **RAG Chat**: Context-aware document chat using LangChain and vector embeddings.
- **AI Analysis**: Automated risk detection and document summarization.
- **Secure Auth**: JWT-based user authentication.
- **File Management**: Secure upload, history tracking, and deletion.
