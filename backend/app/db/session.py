"""
Firebase Session Configuration for LexGuard AI
Replaces SQLAlchemy PostgreSQL session management with Firebase Service.
"""
from app.services.firebase_service import firebase_service

# Mock Base class for SQLAlchemy declarative base compatibility.
# This prevents imports from breaking and makes Base.metadata.create_all a safe no-op.
class MockMetadata:
    def create_all(self, *args, **kwargs):
        pass

class Base:
    metadata = MockMetadata()

# Dependency to get DB session.
# Yields the firebase_service instance, acting as the document client for repositories.
def get_db():
    yield firebase_service
