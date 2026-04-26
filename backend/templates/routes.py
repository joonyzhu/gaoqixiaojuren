"""Template management — upload/download .docx templates with placeholders."""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.template import Template
from config import settings

router = APIRouter(tags=["templates"])

ALLOWED_EXTENSIONS = {".docx", ".doc"}


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """List all uploaded templates."""
    result = await db.execute(select(Template).order_by(Template.created_at.desc()))
    templates = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "project_type": t.project_type,
            "original_filename": t.original_filename,
            "is_builtin": t.is_builtin,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat(),
        }
        for t in templates
    ]


@router.post("/templates/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(""),
    project_type: str = Form("both"),
    set_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """Upload a .docx template file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{ext}，请上传 .docx 文件")

    content = await file.read()

    template_dir = os.path.join(settings.data_dir, "templates")
    os.makedirs(template_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(template_dir, f"{file_id}{ext}")

    with open(file_path, "wb") as f:
        f.write(content)

    template = Template(
        id=file_id,
        name=name or os.path.splitext(file.filename)[0],
        project_type=project_type,
        file_path=file_path,
        original_filename=file.filename,
        is_active=False,
    )
    db.add(template)

    if set_active:
        await _set_active(db, template)

    await db.commit()
    return {"id": file_id, "name": template.name, "status": "uploaded"}


@router.put("/templates/{template_id}/activate")
async def activate_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Set a template as active for its project type."""
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await _set_active(db, template)
    await db.commit()
    return {"status": "activated", "id": template_id}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an uploaded template (built-in templates cannot be deleted)."""
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_builtin:
        raise HTTPException(status_code=400, detail="内置模板不可删除")

    if os.path.isfile(template.file_path):
        os.remove(template.file_path)
    await db.delete(template)
    await db.commit()
    return {"status": "deleted"}


@router.get("/templates/{template_id}/download")
async def download_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Download a template file."""
    template = await db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if not os.path.isfile(template.file_path):
        raise HTTPException(status_code=404, detail="Template file not found on disk")
    return FileResponse(
        path=template.file_path,
        filename=template.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/templates/active/{project_type}")
async def get_active_template(project_type: str, db: AsyncSession = Depends(get_db)):
    """Get the active template for a project type."""
    q = select(Template).where(
        (Template.project_type == project_type) | (Template.project_type == "both"),
        Template.is_active == True,
    )
    result = await db.execute(q)
    template = result.scalars().first()
    if not template:
        return {"has_template": False, "template_id": None}
    return {"has_template": True, "template_id": template.id, "name": template.name}


async def _set_active(db: AsyncSession, template: Template):
    """Deactivate other templates of the same project_type, activate this one."""
    affected_types = [template.project_type, "both"] if template.project_type != "both" else ["gaoxin", "xiaojuren", "both"]
    q = select(Template).where(
        Template.project_type.in_(affected_types),
        Template.is_active == True,
    )
    result = await db.execute(q)
    for t in result.scalars().all():
        t.is_active = False
    template.is_active = True


def _validate_template_placeholders(file_bytes: bytes) -> dict:
    """Check that a .docx file contains at least the essential placeholders."""
    import io
    from zipfile import ZipFile

    required = {"company_name", "project_name"}
    found = set()

    try:
        with ZipFile(io.BytesIO(file_bytes)) as zf:
            # Read document.xml and header/footer XMLs
            xml_files = [n for n in zf.namelist() if n.startswith("word/") and n.endswith(".xml")]
            for name in xml_files:
                text = zf.read(name).decode("utf-8", errors="ignore")
                for match in __import__('re').findall(r"\{([a-z_]+)\}", text):
                    found.add(match)
    except Exception:
        return {"valid": True, "missing": []}  # Don't block on parse errors

    missing = required - found
    return {"valid": len(missing) == 0, "missing": list(missing)}
