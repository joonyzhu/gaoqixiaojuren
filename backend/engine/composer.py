"""AI-powered section-by-section document composer with RAG + web search support."""

import json
import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from engine.prompts.gaoxin import GAOXIN_SECTIONS
from engine.prompts.xiaojuren import XIAOJUREN_SECTIONS
from documents.vector_store import vector_store
from llm.registry import registry, init_registry

# Lazily initialized web search service
_web_search_svc = None


def _get_web_search():
    global _web_search_svc
    if _web_search_svc is None:
        from services.web_search import WebSearchService
        _web_search_svc = WebSearchService()
    return _web_search_svc


@dataclass
class SectionResult:
    section_id: str
    title: str
    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)


@dataclass
class ComposeProgress:
    section_id: str
    title: str
    status: str  # "started" | "generating" | "done" | "error"
    content: str = ""
    error: str = ""


def _render_prompt(template: str, context: dict) -> str:
    """Simple template renderer that replaces {variables}."""
    result = template
    for key, value in context.items():
        result = result.replace("{" + key + "}", str(value) if value else "")
    return result


def _get_sections(project_type: str) -> list[dict]:
    if project_type == "gaoxin":
        return GAOXIN_SECTIONS
    elif project_type == "xiaojuren":
        return XIAOJUREN_SECTIONS
    else:
        return []


async def compose_section(
    section: dict,
    project_context: dict,
    model_id: str,
    project_id: str = "",
    web_search_key: str = "",
    feedback: str = "",
) -> SectionResult:
    """Generate a single section with RAG context injection + web search."""
    init_registry()
    adapter = registry.get_adapter_for_model(model_id)
    if not adapter:
        return SectionResult(
            section_id=section["id"],
            title=section["title"],
            content=f"[错误] 未找到模型 {model_id}",
        )

    # Retrieve relevant context from uploaded documents (RAG)
    rag_context = ""
    if project_id:
        query = f"{section['title']} 企业信息"
        rag_context = vector_store.search_relevant(project_id, query, n_results=3)
        if rag_context:
            rag_context = f"\n\n【参考材料 — 从上传文档中检索的相关内容】\n{rag_context}"

    # Retrieve relevant context from web search
    web_context = ""
    if web_search_key and project_context.get("company_name"):
        try:
            ws = _get_web_search()
            search_query = f"{project_context['company_name']} {section['title']} 申报要点 政策要求"
            web_text = await ws.search_relevant(search_query, api_key=web_search_key, n_results=3)
            if web_text:
                web_context = f"\n\n【联网搜索 — 最新政策与公开信息】\n{web_text}"
        except Exception:
            pass  # Web search is best-effort

    # Combine contexts
    combined_context = f"{rag_context}{web_context}"
    context = {**project_context, "rag_context": combined_context}

    # Render prompts
    system_prompt = section["system_prompt"]
    user_prompt = _render_prompt(section["prompt_template"], context)

    # Append feedback if provided
    if feedback:
        user_prompt += f"\n\n【用户修改意见】\n{feedback}\n请根据以上意见重新撰写本章节。"

    try:
        result = await adapter.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model_id,
        )
        return SectionResult(
            section_id=section["id"],
            title=section["title"],
            content=result.text,
            model=model_id,
            usage=result.usage,
        )
    except Exception as e:
        return SectionResult(
            section_id=section["id"],
            title=section["title"],
            content=f"[生成失败] {e}",
        )


async def compose_section_stream(
    section: dict,
    project_context: dict,
    model_id: str,
    project_id: str = "",
    web_search_key: str = "",
    feedback: str = "",
) -> AsyncIterator[ComposeProgress]:
    """Stream-generate a single section, yielding progress updates."""
    init_registry()
    adapter = registry.get_adapter_for_model(model_id)
    if not adapter:
        yield ComposeProgress(
            section_id=section["id"],
            title=section["title"],
            status="error",
            error=f"未找到模型 {model_id}",
        )
        return

    yield ComposeProgress(
        section_id=section["id"],
        title=section["title"],
        status="started",
    )

    # RAG context
    rag_context = ""
    if project_id:
        query = f"{section['title']} 企业信息"
        rag_context = vector_store.search_relevant(project_id, query, n_results=3)
        if rag_context:
            rag_context = f"\n\n【参考材料 — 从上传文档中检索的相关内容】\n{rag_context}"

    # Web search context
    web_context = ""
    if web_search_key and project_context.get("company_name"):
        try:
            ws = _get_web_search()
            search_query = f"{project_context['company_name']} {section['title']} 申报要点 政策要求"
            web_text = await ws.search_relevant(search_query, api_key=web_search_key, n_results=3)
            if web_text:
                web_context = f"\n\n【联网搜索 — 最新政策与公开信息】\n{web_text}"
        except Exception:
            pass

    # Combine contexts
    combined_context = f"{rag_context}{web_context}"
    context = {**project_context, "rag_context": combined_context}
    system_prompt = section["system_prompt"]
    user_prompt = _render_prompt(section["prompt_template"], context)

    # Append feedback if provided
    if feedback:
        user_prompt += f"\n\n【用户修改意见】\n{feedback}\n请根据以上意见重新撰写本章节。"

    try:
        full_text = ""
        async for chunk in adapter.stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model_id,
        ):
            full_text += chunk
            yield ComposeProgress(
                section_id=section["id"],
                title=section["title"],
                status="generating",
                content=chunk,
            )

        yield ComposeProgress(
            section_id=section["id"],
            title=section["title"],
            status="done",
            content=full_text,
        )
    except Exception as e:
        yield ComposeProgress(
            section_id=section["id"],
            title=section["title"],
            status="error",
            error=str(e),
        )


async def compose_all(
    project_type: str,
    project_context: dict,
    model_id: str,
    project_id: str = "",
    section_ids: list[str] | None = None,
    web_search_key: str = "",
    feedback: str = "",
) -> list[SectionResult]:
    """Generate all sections (or specified ones) for a project."""
    sections = _get_sections(project_type)
    if section_ids:
        sections = [s for s in sections if s["id"] in section_ids]

    results = []
    for section in sorted(sections, key=lambda s: s["order"]):
        result = await compose_section(section, project_context, model_id, project_id,
                                       web_search_key=web_search_key, feedback=feedback)
        results.append(result)
        # Small delay between sections to avoid rate limits
        await asyncio.sleep(0.5)

    return results
