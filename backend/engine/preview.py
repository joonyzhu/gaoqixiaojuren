"""
Assemble all generated sections into an HTML preview document.
Mimics Chinese government document formatting (宋体 body, 黑体 headings, 楷体 subtitle).
"""

from engine.composer import _get_sections


def assemble_preview_html(
    project_name: str,
    company_name: str,
    project_type: str,
    sections: list[dict],  # [{title, content}, ...]
) -> str:
    """Build a complete HTML document from ordered sections."""

    title_text = (
        "国家高新技术企业认定申请书"
        if project_type == "gaoxin"
        else '国家级专精特新"小巨人"企业申请书'
    )

    def paragraphs(text: str) -> str:
        """Split text into indented paragraphs."""
        lines = text.strip().split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Headings within content
            if stripped.startswith("#") or stripped.startswith("**") or len(stripped) < 30:
                result.append(f'<p style="text-indent:0;font-weight:bold;">{stripped.lstrip("#").strip()}</p>')
            else:
                result.append(f"<p>{stripped}</p>")
        return "\n".join(result)

    section_html = ""
    for sec in sections:
        section_html += f"""
        <h3>{sec.get('title', '')}</h3>
        {paragraphs(sec.get('content', ''))}
        """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  body {{ margin: 0; padding: 24px; background: #e8e8e8; font-size: 14px; }}
  .page {{
    max-width: 800px;
    margin: 0 auto;
    background: #fff;
    padding: 72px 80px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    font-family: "SimSun", "PingFang SC", "Microsoft YaHei", serif;
    line-height: 2;
    color: #333;
  }}
  h1 {{ font-size: 22pt; font-family: "SimHei", "PingFang SC", sans-serif; text-align: center; margin-bottom: 4px; }}
  h2 {{ font-size: 14pt; font-family: "KaiTi", "PingFang SC", serif; text-align: center; font-weight: normal; margin-bottom: 32px; color: #555; }}
  h3 {{ font-size: 14pt; font-family: "SimHei", "PingFang SC", sans-serif; margin-top: 28px; margin-bottom: 12px; }}
  p {{
    text-indent: 2em;
    margin: 4px 0;
    font-family: "SimSun", "PingFang SC", "Microsoft YaHei", serif;
    font-size: 12pt;
  }}
  .footer {{
    margin-top: 40px;
    padding-top: 12px;
    border-top: 1px solid #ddd;
    text-align: right;
    font-size: 12px;
    color: #999;
  }}
</style>
</head>
<body>
<div class="page">
<h1>{title_text}</h1>
<h2>申报企业：{company_name or '（未填写）'}<br>项目名称：{project_name}</h2>
{section_html}
<div class="footer">{company_name or ''}</div>
</div>
</body>
</html>"""
    return html
