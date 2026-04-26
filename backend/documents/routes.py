import json
import os
import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.database import get_db
from models.document import Document
from models.project import Project
from documents.parser import parse_file
from documents.vector_store import vector_store

router = APIRouter(tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md", ".csv", ".html", ".htm"}


@router.get("/documents")
async def list_documents(project_id: str | None = None, db: AsyncSession = Depends(get_db)):
    """List documents, optionally filtered by project."""
    q = select(Document).order_by(Document.created_at.desc())
    if project_id:
        q = q.where(Document.project_id == project_id)
    result = await db.execute(q)
    documents = result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "project_id": d.project_id or "",
            "size": os.path.getsize(d.file_path) if d.file_path and os.path.isfile(d.file_path) else 0,
            "parsed_length": len(d.parsed_text) if d.parsed_text else 0,
            "chunks_indexed": 0,
            "created_at": d.created_at.isoformat(),
        }
        for d in documents
    ]


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(""),
    doc_type: str = Form("other"),  # sample / financial / patent / contract / other
    checklist_item_id: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document, parse it, and index it for RAG."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type: {ext}. Supported: {', '.join(ALLOWED_EXTENSIONS)}")

    # Save file
    os.makedirs(settings.upload_dir, exist_ok=True)
    doc_id = str(uuid.uuid4())
    saved_name = f"{doc_id}{ext}"
    saved_path = os.path.join(settings.upload_dir, saved_name)

    content = await file.read()
    with open(saved_path, "wb") as f:
        f.write(content)

    # Parse document
    parsed = parse_file(saved_path)
    parsed_text = parsed.text[:100000]  # Cap at 100K chars for storage

    # Save to DB
    doc = Document(
        id=doc_id,
        project_id=project_id or None,
        filename=file.filename,
        file_path=saved_path,
        doc_type=doc_type,
        parsed_text=parsed_text,
        content="",
    )
    db.add(doc)
    await db.commit()

    # Index for RAG if project is specified
    chunks_added = 0
    if project_id:
        try:
            chunks_added = vector_store.add_document(
                project_id=project_id,
                document_id=doc_id,
                text=parsed_text,
                metadata={"file_name": file.filename, "doc_type": doc_type},
            )
        except Exception:
            pass  # Vector store might not be available

        # Link to checklist item if specified
        if checklist_item_id and project_id:
            project = await db.get(Project, project_id)
            if project and project.material_checklist:
                try:
                    checklist = json.loads(project.material_checklist)
                    for item in checklist:
                        if item["id"] == checklist_item_id:
                            item["uploaded"] = True
                            item.setdefault("doc_ids", [])
                            if doc_id not in item["doc_ids"]:
                                item["doc_ids"].append(doc_id)
                            break
                    project.material_checklist = json.dumps(checklist, ensure_ascii=False)
                    await db.commit()
                except Exception:
                    pass

    return {
        "id": doc_id,
        "filename": file.filename,
        "size": len(content),
        "doc_type": doc_type,
        "project_id": project_id or "",
        "parsed_length": len(parsed_text),
        "chunks_indexed": chunks_added,
        "metadata": parsed.metadata,
    }


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get document parsed content."""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "parsed_text": doc.parsed_text[:2000],  # Preview only
        "full_length": len(doc.parsed_text),
        "created_at": doc.created_at.isoformat(),
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, project_id: str = "", db: AsyncSession = Depends(get_db)):
    """Delete a document and its vector index."""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pid = project_id or doc.project_id

    # Remove from filesystem
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Remove from vector store
    if pid:
        vector_store.remove_document(pid, doc_id)

        # Unlink from checklist
        project = await db.get(Project, pid)
        if project and project.material_checklist:
            try:
                checklist = json.loads(project.material_checklist)
                for item in checklist:
                    if doc_id in item.get("doc_ids", []):
                        item["doc_ids"].remove(doc_id)
                        if not item["doc_ids"]:
                            item["uploaded"] = False
                project.material_checklist = json.dumps(checklist, ensure_ascii=False)
            except Exception:
                pass

    await db.delete(doc)
    await db.commit()
    return {"status": "deleted"}


@router.post("/documents/search")
async def search_documents(project_id: str, query: str, n_results: int = 5):
    """Semantic search within project documents (RAG)."""
    results = vector_store.search(project_id, query, n_results)
    return {"query": query, "results": results, "count": len(results)}
