"""Vector store for RAG: stores document chunks in ChromaDB for semantic retrieval."""

import os
import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings


class VectorStore:
    """Wrapper around ChromaDB for document chunk storage and retrieval."""

    def __init__(self):
        os.makedirs(settings.chroma_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, project_id: str):
        """Get or create a ChromaDB collection for a project."""
        collection_name = f"project_{project_id}"
        try:
            return self._client.get_collection(collection_name)
        except Exception:
            return self._client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def delete_collection(self, project_id: str):
        try:
            self._client.delete_collection(f"project_{project_id}")
        except Exception:
            pass

    def add_document(
        self,
        project_id: str,
        document_id: str,
        text: str,
        metadata: dict | None = None,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ) -> int:
        """Chunk a document and add to the vector store. Returns number of chunks added."""
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        if not chunks:
            return 0

        collection = self.get_or_create_collection(project_id)
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": document_id, "chunk_index": i, "source": (metadata or {}).get("file_name", ""),
             **(metadata or {})}
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def remove_document(self, project_id: str, document_id: str):
        """Remove all chunks of a document from the vector store."""
        try:
            collection = self._client.get_collection(f"project_{project_id}")
            # Query for chunks belonging to this document
            results = collection.get(
                where={"document_id": document_id},
            )
            if results["ids"]:
                collection.delete(ids=results["ids"])
        except Exception:
            pass

    def search(
        self,
        project_id: str,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """Semantic search for relevant document chunks."""
        try:
            collection = self._client.get_collection(f"project_{project_id}")
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            chunks = []
            if results["ids"] and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    chunks.append({
                        "id": chunk_id,
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    })
            return chunks
        except Exception:
            return []

    def search_relevant(
        self,
        project_id: str,
        query: str,
        n_results: int = 5,
    ) -> str:
        """Search and return concatenated relevant text for LLM context injection."""
        chunks = self.search(project_id, query, n_results)
        if not chunks:
            return ""
        return "\n\n---\n\n".join(
            f"[参考材料 {i+1}]\n{c['text']}"
            for i, c in enumerate(chunks)
        )

    def _chunk_text(self, text: str, chunk_size: int = 1500, chunk_overlap: int = 200) -> list[str]:
        """Split text into overlapping chunks, trying to break at natural boundaries."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at a sentence boundary (。！？\n)
            if end < len(text):
                for sep in ["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";"]:
                    last_sep = chunk.rfind(sep)
                    if last_sep > chunk_size // 2:
                        end = start + last_sep + 1
                        chunk = text[start:end]
                        break

            chunks.append(chunk.strip())
            start = end - chunk_overlap

        return chunks


# Singleton
vector_store = VectorStore()
