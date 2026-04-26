import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database import Base
import enum


class ProjectType(str, enum.Enum):
    GAOXIN = "gaoxin"        # 国家高新技术企业
    XIAOJUREN = "xiaojuren"  # 专精特新小巨人


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"               # 材料收集中
    GENERATING = "generating"     # AI 撰写中
    REVIEW = "review"            # 人工审核中
    DONE = "done"                # 已定稿


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    project_type: Mapped[ProjectType] = mapped_column(SAEnum(ProjectType))
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    company_name: Mapped[str] = mapped_column(String(200), default="")
    company_info: Mapped[str] = mapped_column(Text, default="")       # JSON: 企业基本信息
    financial_data: Mapped[str] = mapped_column(Text, default="")     # JSON: 财务数据
    ip_data: Mapped[str] = mapped_column(Text, default="")            # JSON: 知识产权
    rd_data: Mapped[str] = mapped_column(Text, default="")            # JSON: 产学研数据
    content: Mapped[str] = mapped_column(Text, default="")            # JSON: AI 生成的内容
    phase: Mapped[str] = mapped_column(String(20), default="materials")  # materials / writing / review / done
    material_checklist: Mapped[str] = mapped_column(Text, default="[]")  # JSON: 材料清单
    review_score: Mapped[int] = mapped_column(default=0)
    review_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan")


class SectionComment(Base):
    __tablename__ = "section_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(50), default="user")
    resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SectionRevision(Base):
    __tablename__ = "section_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(default=1)
    content: Mapped[str] = mapped_column(Text, default="")
    model_used: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
