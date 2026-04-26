import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from models.database import get_db
from models.project import Project, ProjectType, ProjectStatus
from services.company_info import search_company, company_info_to_json, merge_company_info
from engine.checklist import get_checklist, get_checklist_stats

router = APIRouter(tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    project_type: str
    company_name: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = None
    company_name: str | None = None
    company_info: str | None = None
    financial_data: str | None = None
    ip_data: str | None = None
    rd_data: str | None = None
    content: str | None = None
    status: str | None = None
    phase: str | None = None
    material_checklist: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    project_type: str
    status: str
    phase: str = "materials"
    company_name: str
    company_info: dict = {}
    financial_data: dict = {}
    ip_data: dict = {}
    rd_data: dict = {}
    content: dict = {}
    material_checklist: list = []
    review_score: int = 0
    review_summary: str = ""
    created_at: str
    updated_at: str


def _project_to_response(p: Project) -> ProjectResponse:
    def safe_json(v):
        if not v:
            return {}
        try:
            return json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return {}

    def safe_list(v):
        if not v:
            return []
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    return ProjectResponse(
        id=p.id,
        name=p.name,
        project_type=p.project_type.value,
        status=p.status.value,
        phase=p.phase,
        company_name=p.company_name,
        company_info=safe_json(p.company_info),
        financial_data=safe_json(p.financial_data),
        ip_data=safe_json(p.ip_data),
        rd_data=safe_json(p.rd_data),
        content=safe_json(p.content),
        material_checklist=safe_list(p.material_checklist),
        review_score=p.review_score,
        review_summary=p.review_summary,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.get("/projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.updated_at.desc()))
    projects = result.scalars().all()
    return [_project_to_response(p) for p in projects]


@router.post("/projects", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        name=data.name,
        project_type=ProjectType(data.project_type),
        status=ProjectStatus.DRAFT,
        company_name=data.company_name,
    )

    # Init material checklist
    checklist = get_checklist(data.project_type)
    project.material_checklist = json.dumps(checklist, ensure_ascii=False)

    if data.company_name:
        try:
            info = await search_company(data.company_name)
            if info:
                project.company_info = json.dumps(company_info_to_json(info), ensure_ascii=False)
        except Exception:
            pass  # Enrichment is best-effort

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return _project_to_response(project)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status" and value:
            setattr(project, key, ProjectStatus(value))
        elif hasattr(project, key):
            setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return _project_to_response(project)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"status": "deleted"}


class EnrichRequest(BaseModel):
    company_name: str


@router.post("/projects/enrich-company")
async def enrich_company_by_name(data: EnrichRequest):
    info = await search_company(data.company_name)
    if info:
        return company_info_to_json(info)
    return {"found": False, "message": "未能从公开渠道获取企业信息，请手动填写"}


@router.post("/projects/{project_id}/enrich-company")
async def enrich_company_info(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.company_name:
        raise HTTPException(status_code=400, detail="No company name set")

    info = await search_company(project.company_name)
    if info:
        project.company_info = merge_company_info(project.company_info, info)
        await db.commit()
        return company_info_to_json(info)
    return {"found": False, "message": "未能从公开渠道获取企业信息，请手动填写"}


# ── Checklist endpoints ────────────────────────────────────────────

class ChecklistInitRequest(BaseModel):
    project_type: str


class ChecklistUpdateRequest(BaseModel):
    item_id: str
    uploaded: bool = False
    doc_ids: list[str] = []


@router.get("/projects/{project_id}/checklist")
async def get_project_checklist(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    checklist = json.loads(project.material_checklist) if project.material_checklist else []
    stats = get_checklist_stats(checklist)
    return {"checklist": checklist, "stats": stats}


@router.post("/projects/{project_id}/checklist/init")
async def init_project_checklist(project_id: str, data: ChecklistInitRequest, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    checklist = get_checklist(data.project_type)
    project.material_checklist = json.dumps(checklist, ensure_ascii=False)
    await db.commit()
    stats = get_checklist_stats(checklist)
    return {"checklist": checklist, "stats": stats}


@router.patch("/projects/{project_id}/checklist")
async def update_checklist_item(project_id: str, data: ChecklistUpdateRequest, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    checklist = json.loads(project.material_checklist) if project.material_checklist else []
    for item in checklist:
        if item["id"] == data.item_id:
            item["uploaded"] = data.uploaded
            if data.uploaded:
                item.setdefault("doc_ids", [])
                for doc_id in data.doc_ids:
                    if doc_id not in item["doc_ids"]:
                        item["doc_ids"].append(doc_id)
            else:
                item["doc_ids"] = [d for d in item.get("doc_ids", []) if d not in data.doc_ids]
                # If no more docs linked, mark as not uploaded
                if not item.get("doc_ids"):
                    item["uploaded"] = False
            break

    project.material_checklist = json.dumps(checklist, ensure_ascii=False)
    await db.commit()
    stats = get_checklist_stats(checklist)
    return {"checklist": checklist, "stats": stats}
