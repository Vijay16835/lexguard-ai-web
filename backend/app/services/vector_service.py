"""
Vector Service for LexGuard AI
Handles document chunking, embedding generation, and semantic search.
Uses sentence-transformers and FAISS for efficient retrieval.
Lazy-loads the model to avoid crashing the backend if deps are missing.
"""
import os
import traceback
from typing import List

# Configuration
VECTOR_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "vector_db"
)
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast and efficient for legal text


class VectorService:
    def __init__(self):
        self._model = None
        self._available = None  # None = not checked yet
        self.index_dir = VECTOR_DB_PATH
        os.makedirs(self.index_dir, exist_ok=True)

    def _check_available(self) -> bool:
        """Check if sentence-transformers and faiss are installed."""
        if self._available is not None:
            return self._available
        try:
            import sentence_transformers  # noqa: F401
            import faiss  # noqa: F401
            import numpy  # noqa: F401
            self._available = True
        except ImportError as e:
            print(f"[VectorService] Dependencies not available: {e}")
            print("[VectorService] Install: pip install sentence-transformers faiss-cpu numpy")
            self._available = False
        return self._available

    def _get_model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def _get_index_path(self, document_id: str) -> str:
        return os.path.join(self.index_dir, f"{document_id}.index")

    def _get_metadata_path(self, document_id: str) -> str:
        return os.path.join(self.index_dir, f"{document_id}.meta")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping word-based chunks."""
        chunks = []
        if not text:
            return chunks

        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        step = chunk_size - overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks

    async def create_vector_index(self, document_id: str, text: str):
        """Create and save a FAISS index for a specific document."""
        if not self._check_available():
            print(f"[VectorService] Skipping index creation for {document_id} — deps missing")
            return

        import numpy as np
        import faiss
        import pickle

        try:
            chunks = self.chunk_text(text)
            if not chunks:
                return

            model = self._get_model()
            embeddings = model.encode(chunks)
            embeddings = np.array(embeddings).astype('float32')

            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)

            faiss.write_index(index, self._get_index_path(document_id))
            with open(self._get_metadata_path(document_id), 'wb') as f:
                pickle.dump(chunks, f)

            print(f"[VectorService] Indexed {len(chunks)} chunks for document {document_id}")
        except Exception as e:
            print(f"[VectorService] Index creation failed: {e}")
            traceback.print_exc()

    async def search_similar_chunks(self, document_id: str, query: str, top_k: int = 4) -> List[str]:
        """Search for relevant chunks using semantic similarity."""
        if not self._check_available():
            return []

        import numpy as np
        import faiss
        import pickle

        index_path = self._get_index_path(document_id)
        meta_path = self._get_metadata_path(document_id)

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            return []

        try:
            index = faiss.read_index(index_path)
            with open(meta_path, 'rb') as f:
                chunks = pickle.load(f)

            model = self._get_model()
            query_embedding = model.encode([query])
            query_embedding = np.array(query_embedding).astype('float32')

            distances, indices = index.search(query_embedding, min(top_k, len(chunks)))

            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(chunks):
                    results.append(chunks[idx])

            return results
        except Exception as e:
            print(f"[VectorService] Search failed: {e}")
            traceback.print_exc()
            return []

    def delete_index(self, document_id: str):
        """Remove vector index files for a document."""
        for path in [self._get_index_path(document_id), self._get_metadata_path(document_id)]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass


vector_service = VectorService()
