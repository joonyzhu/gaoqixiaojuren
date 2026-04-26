"""AI quality reviewer — checks generated content against official scoring criteria."""

from dataclasses import dataclass, field
from llm.registry import registry, init_registry


@dataclass
class ReviewResult:
    score: int = 0                     # Overall score estimate
    max_score: int = 100
    dimensions: list[dict] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    summary: str = ""


GAOXIN_CRITERIA = {
    "知识产权": 30,
    "科技成果转化能力": 30,
    "研究开发组织管理水平": 20,
    "企业成长性": 20,
}

XIAOJUREN_CRITERIA = {
    "专业化程度": 20,
    "精细化程度": 20,
    "特色化程度": 15,
    "创新能力": 25,
    "产业链配套能力": 10,
    "经营管理水平": 10,
}


def _get_criteria(project_type: str) -> dict:
    if project_type == "gaoxin":
        return GAOXIN_CRITERIA
    return XIAOJUREN_CRITERIA


async def review_content(
    content: str,
    project_type: str,
    model_id: str,
) -> ReviewResult:
    """Review generated application content against scoring criteria."""
    init_registry()
    adapter = registry.get_adapter_for_model(model_id)
    if not adapter:
        return ReviewResult(summary="[错误] 模型未配置，无法审查")

    criteria = _get_criteria(project_type)
    criteria_text = "\n".join([f"- {k}（{v}分）" for k, v in criteria.items()])

    system_prompt = """你是一位资深的项目申报评审专家，曾多次参与高新技术企业和专精特新小巨人企业认定评审工作。
请严格对照评分标准，审查申报书内容的完整性、准确性和竞争力。给出具体改进建议。"""

    prompt = f"""请审查以下申报书内容，对照评分标准进行逐项评估。

【评分标准】
{criteria_text}

【申报书内容】
{content}

请输出以下格式的审查报告：
1. 逐项评分（每项给出得分/满分，并说明扣分原因或得分依据）
2. 缺失内容（哪些关键要素未覆盖或描述不足）
3. 数据问题（数据是否充分、是否有前后矛盾）
4. 语言质量（表述是否专业、逻辑是否清晰）
5. 改进建议（按优先级列出具体的修改建议）
6. 综合评分预估"""

    try:
        result = await adapter.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_id,
            temperature=0.3,
            max_tokens=2048,
        )
        return ReviewResult(
            summary=result.text,
            max_score=sum(criteria.values()),
        )
    except Exception as e:
        return ReviewResult(summary=f"[审查失败] {e}")
