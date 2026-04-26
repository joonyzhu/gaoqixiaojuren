from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models.database import init_db
from templates.builtin import init_builtin_templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_builtin_templates()
    yield


app = FastAPI(title="高企小巨人智能申报系统", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Import and register routers
from projects.routes import router as project_router
from documents.routes import router as document_router
from templates.routes import router as template_router
from engine.routes import router as engine_router
from llm.routes import router as llm_router

app.include_router(project_router, prefix="/api")
app.include_router(document_router, prefix="/api")
app.include_router(template_router, prefix="/api")
app.include_router(engine_router, prefix="/api")
app.include_router(llm_router, prefix="/api")
