import json
import os
import re
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from models.database import get_db
from models.project import Project, SectionComment, SectionRevision
from models.template import Template
from engine.composer import compose_section, compose_section_stream, compose_all, _get_sections
from engine.reviewer import review_content
from engine.exporter import export_to_word
from engine.preview import assemble_preview_html
from config import settings

router = APIRouter(tags=["engine"])


class ComposeRequest(BaseModel):
    project_id: str
    model_id: str
    section_ids: list[str] | None = None  # None = all sections
    web_search_key: str = ""
    feedback: str = ""


class ComposeSectionRequest(BaseModel):
    project_id: str
    section_id: str
    model_id: str
    web_search_key: str = ""
    feedback: str = ""


class ReviewRequest(BaseModel):
    project_id: str
    model_id: str
    web_search_key: str = ""


class ExportRequest(BaseModel):
    project_id: str
    template_id: str | None = None  # If not provided, uses the active template for this project type


@router.get("/engine/sections/{project_type}")
async def get_sections(project_type: str):
    """Get the section structure for a project type."""
    sections = _get_sections(project_type)
    return [
        {"id": s["id"], "title": s["title"], "order": s["order"]}
        for s in sections
    ]


@router.post("/engine/compose-section")
async def compose_section_api(data: ComposeSectionRequest, db: AsyncSession = Depends(get_db)):
    """Generate a single section (non-streaming)."""
    project = await db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sections = _get_sections(project.project_type.value)
    section = next((s for s in sections if s["id"] == data.section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {data.section_id} not found")

    context = _build_project_context(project)

    result = await compose_section(
        section=section,
        project_context=context,
        model_id=data.model_id,
        project_id=data.project_id,
        web_search_key=data.web_search_key,
        feedback=data.feedback,
    )

    return {
        "section_id": result.section_id,
        "title": result.title,
        "content": result.content,
        "model": result.model,
        "usage": result.usage,
    }


@router.post("/engine/compose-section-stream")
async def compose_section_stream_api(data: ComposeSectionRequest, db: AsyncSession = Depends(get_db)):
    """Generate a single section with SSE streaming."""
    project = await db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sections = _get_sections(project.project_type.value)
    section = next((s for s in sections if s["id"] == data.section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {data.section_id} not found")

    context = _build_project_context(project)

    async def event_stream():
        async for progress in compose_section_stream(
            section=section,
            project_context=context,
            model_id=data.model_id,
            project_id=data.project_id,
            web_search_key=data.web_search_key,
            feedback=data.feedback,
        ):
            data_json = json.dumps({
                "section_id": progress.section_id,
                "title": progress.title,
                "status": progress.status,
                "content": progress.content,
                "error": progress.error,
            }, ensure_ascii=False)
            yield f"data: {data_json}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/engine/compose-all")
async def compose_all_api(data: ComposeRequest, db: AsyncSession = Depends(get_db)):
    """Generate all sections for a project."""
    project = await db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    context = _build_project_context(project)

    # Update phase to writing
    if project.phase == "materials":
        project.phase = "writing"

    results = await compose_all(
        project_type=project.project_type.value,
        project_context=context,
        model_id=data.model_id,
        project_id=data.project_id,
        section_ids=data.section_ids,
        web_search_key=data.web_search_key,
        feedback=data.feedback,
    )

    # Save results to project content, preserving old content as revisions
    content_dict = {}
    if project.content:
        try:
            content_dict = json.loads(project.content)
        except json.JSONDecodeError:
            pass

    for r in results:
        # Save previous version as revision
        if r.section_id in content_dict:
            old = content_dict[r.section_id]
            await _save_revision(
                project_id=data.project_id,
                section_id=r.section_id,
                old_content=old.get("content", ""),
                section_title=old.get("title", ""),
                db=db,
            )
        content_dict[r.section_id] = {
            "title": r.title,
            "content": r.content,
            "model": r.model,
        }

    project.content = json.dumps(content_dict, ensure_ascii=False, indent=2)
    await db.commit()

    return {
        "sections": [
            {"section_id": r.section_id, "title": r.title, "content": r.content}
            for r in results
        ]
    }


@router.post("/engine/review")
async def review_api(data: ReviewRequest, db: AsyncSession = Depends(get_db)):
    """Review generated content against scoring criteria."""
    project = await db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gather all generated content
    content_dict = {}
    if project.content:
        try:
            content_dict = json.loads(project.content)
        except json.JSONDecodeError:
            pass

    if not content_dict:
        raise HTTPException(status_code=400, detail="No generated content to review")

    full_text = "\n\n".join([
        f"## {v.get('title', '')}\n{v.get('content', '')}"
        for v in content_dict.values()
    ])

    result = await review_content(
        content=full_text,
        project_type=project.project_type.value,
        model_id=data.model_id,
    )

    # Parse score from review summary
    score = 0
    score_match = re.search(r'(\d+)\s*分', result.summary)
    if not score_match:
        score_match = re.search(r'(\d+)\s*/\s*100', result.summary)
    if score_match:
        score = int(score_match.group(1))

    # Update project with review results — auto-advance to done phase
    project.review_score = score
    project.review_summary = result.summary
    project.phase = "done"
    await db.commit()

    return {"summary": result.summary, "max_score": result.max_score, "score": score}


@router.post("/engine/export")
async def export_api(data: ExportRequest, db: AsyncSession = Depends(get_db)):
    """Export project content as a Word document (requires review first)."""
    project = await db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Quality gate: must have completed review
    if project.phase not in ("review", "done"):
        raise HTTPException(status_code=400,
                            detail=f"请先完成质量审查再导出。当前阶段：{project.phase}")

    content_dict = {}
    if project.content:
        try:
            content_dict = json.loads(project.content)
        except json.JSONDecodeError:
            pass

    if not content_dict:
        raise HTTPException(status_code=400, detail="No generated content to export")

    # Build section list in order
    sections = _get_sections(project.project_type.value)
    ordered = []
    for sec in sorted(sections, key=lambda s: s["order"]):
        if sec["id"] in content_dict:
            ordered.append({
                "id": sec["id"],
                "title": content_dict[sec["id"]].get("title", sec["title"]),
                "content": content_dict[sec["id"]].get("content", ""),
            })

    # Resolve template path
    template_path = ""
    if data.template_id:
        tpl = await db.get(Template, data.template_id)
        if tpl and os.path.isfile(tpl.file_path):
            template_path = tpl.file_path
        else:
            raise HTTPException(status_code=404, detail=f"Template {data.template_id} not found")
    else:
        # Auto-select active template for this project type
        q = select(Template).where(
            (Template.project_type == project.project_type.value) | (Template.project_type == "both"),
            Template.is_active == True,
        )
        result = await db.execute(q)
        active_tpl = result.scalars().first()
        if active_tpl and os.path.isfile(active_tpl.file_path):
            template_path = active_tpl.file_path

    output_dir = os.path.join(settings.data_dir, "exports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{project.id}.docx")

    export_to_word(
        project_name=project.name,
        company_name=project.company_name,
        project_type=project.project_type.value,
        sections=ordered,
        output_path=output_path,
        template_path=template_path,
    )

    return FileResponse(
        path=output_path,
        filename=f"{project.company_name or '申报书'}_{project.project_type.value}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ── Preview endpoint ──────────────────────────────────────────────

@router.get("/engine/preview/{project_id}")
async def preview_api(project_id: str, db: AsyncSession = Depends(get_db)):
    """Assemble all sections into an HTML preview of the full document."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content_dict = {}
    if project.content:
        try:
            content_dict = json.loads(project.content)
        except json.JSONDecodeError:
            pass

    if not content_dict:
        raise HTTPException(status_code=400, detail="No generated content to preview")

    sections = _get_sections(project.project_type.value)
    ordered = []
    for sec in sorted(sections, key=lambda s: s["order"]):
        if sec["id"] in content_dict:
            ordered.append({
                "id": sec["id"],
                "title": content_dict[sec["id"]].get("title", sec["title"]),
                "content": content_dict[sec["id"]].get("content", ""),
            })

    html = assemble_preview_html(
        project_name=project.name,
        company_name=project.company_name,
        project_type=project.project_type.value,
        sections=ordered,
    )
    return {"html": html}


# ── Comments endpoints ────────────────────────────────────────────

class CommentCreate(BaseModel):
    section_id: str
    content: str
    author: str = "user"


class CommentUpdate(BaseModel):
    content: str | None = None
    resolved: bool | None = None


@router.get("/projects/{project_id}/comments")
async def list_comments(project_id: str, section_id: str | None = None, db: AsyncSession = Depends(get_db)):
    """List comments for a project, optionally filtered by section."""
    q = select(SectionComment).where(SectionComment.project_id == project_id)
    if section_id:
        q = q.where(SectionComment.section_id == section_id)
    q = q.order_by(SectionComment.created_at.asc())
    result = await db.execute(q)
    comments = result.scalars().all()
    return [
        {
            "id": c.id,
            "section_id": c.section_id,
            "content": c.content,
            "author": c.author,
            "resolved": c.resolved,
            "created_at": c.created_at.isoformat(),
        }
        for c in comments
    ]


@router.post("/projects/{project_id}/comments")
async def create_comment(project_id: str, data: CommentCreate, db: AsyncSession = Depends(get_db)):
    """Add a comment on a section."""
    comment = SectionComment(
        id=str(uuid.uuid4()),
        project_id=project_id,
        section_id=data.section_id,
        content=data.content,
        author=data.author,
    )
    db.add(comment)
    await db.commit()
    return {"id": comment.id, "status": "created"}


@router.patch("/projects/{project_id}/comments/{comment_id}")
async def update_comment(project_id: str, comment_id: str, data: CommentUpdate, db: AsyncSession = Depends(get_db)):
    """Resolve or edit a comment."""
    comment = await db.get(SectionComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if data.resolved is not None:
        comment.resolved = data.resolved
    if data.content is not None:
        comment.content = data.content
    await db.commit()
    return {"status": "updated"}


@router.delete("/projects/{project_id}/comments/{comment_id}")
async def delete_comment(project_id: str, comment_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a comment."""
    comment = await db.get(SectionComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.delete(comment)
    await db.commit()
    return {"status": "deleted"}


# ── Revisions endpoints ───────────────────────────────────────────

@router.get("/projects/{project_id}/revisions/{section_id}")
async def list_revisions(project_id: str, section_id: str, db: AsyncSession = Depends(get_db)):
    """List revision history for a section."""
    q = (
        select(SectionRevision)
        .where(SectionRevision.project_id == project_id)
        .where(SectionRevision.section_id == section_id)
        .order_by(SectionRevision.version.desc())
    )
    result = await db.execute(q)
    revs = result.scalars().all()
    return [
        {
            "id": r.id,
            "section_id": r.section_id,
            "version": r.version,
            "content": r.content,
            "model_used": r.model_used,
            "created_at": r.created_at.isoformat(),
        }
        for r in revs
    ]


async def _save_revision(project_id: str, section_id: str, old_content: str, section_title: str, db: AsyncSession):
    """Save previous section content as a revision before overwriting."""
    # Get max version number for this section
    q = (
        select(func.max(SectionRevision.version))
        .where(SectionRevision.project_id == project_id)
        .where(SectionRevision.section_id == section_id)
    )
    result = await db.execute(q)
    max_ver = result.scalar() or 0

    rev = SectionRevision(
        id=str(uuid.uuid4()),
        project_id=project_id,
        section_id=section_id,
        version=max_ver + 1,
        content=old_content,
        model_used="",
    )
    db.add(rev)


def _build_project_context(project: Project) -> dict:
    return {
        "project_name": project.name,
        "company_name": project.company_name,
        "company_info": project.company_info or "",
        "financial_data": project.financial_data or "",
        "ip_data": project.ip_data or "",
        "rd_data": project.rd_data or "",
        "uploaded_docs": "暂无",
    }
