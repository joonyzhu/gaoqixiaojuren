"""
Company information enrichment service.
Searches public sources (企查查, 爱企查, 天眼查, 国家企业信用信息公示系统)
to automatically fill in enterprise registration details given a company name.
"""

import json
import re
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, field


@dataclass
class CompanyInfo:
    name: str = ""                      # 企业全称
    legal_representative: str = ""      # 法定代表人
    registered_capital: str = ""        # 注册资本
    paid_in_capital: str = ""           # 实缴资本
    established_date: str = ""          # 成立日期
    business_status: str = ""           # 经营状态 (存续/在业/吊销等)
    unified_code: str = ""              # 统一社会信用代码
    registration_number: str = ""       # 工商注册号
    company_type: str = ""              # 企业类型 (有限责任公司等)
    industry: str = ""                  # 所属行业
    business_scope: str = ""            # 经营范围
    address: str = ""                   # 注册地址
    website: str = ""                   # 官网
    phone: str = ""                     # 联系电话
    email: str = ""                     # 邮箱
    employee_count: str = ""            # 参保人数
    shareholders: str = ""              # 股东信息(简要)
    source: str = ""                    # 信息来源


def _parse_qichacha(html: str) -> CompanyInfo | None:
    """Try to parse company info from 企查查 search results."""
    soup = BeautifulSoup(html, "html.parser")
    info = CompanyInfo()

    # Try to extract info from meta tags and structured data
    text = soup.get_text()

    if not text or len(text) < 50:
        return None

    # Try extracting from common patterns
    patterns = {
        "legal_representative": r"法定代表人[：:]\s*(\S+)",
        "registered_capital": r"注册资本[：:]\s*(\S+)",
        "established_date": r"成立日期[：:]\s*(\S+)",
        "business_status": r"经营状态[：:]\s*([存续在营吊销注销迁出]+)",
        "unified_code": r"统一社会信用代码[：:]\s*(\S+)",
        "company_type": r"企业类型[：:]\s*(\S+)",
        "industry": r"所属行业[：:]\s*(\S+)",
        "business_scope": r"经营范围[：:]\s*(\S+)",
        "address": r"注册地址[：:]\s*(\S+)",
        "phone": r"电话[：:]\s*(\S+)",
        "email": r"邮箱[：:]\s*(\S+)",
    }

    for field_name, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            setattr(info, field_name, match.group(1).strip())

    # Only return if we found at least name and some other info
    if info.legal_representative or info.unified_code:
        info.source = "企查查"
        return info
    return None


def _parse_aiqicha(html: str) -> CompanyInfo | None:
    """Try to parse company info from 爱企查 search results."""
    return _parse_qichacha(html)  # Same patterns, different source


def _parse_tianyancha(html: str) -> CompanyInfo | None:
    """Try to parse company info from 天眼查 search results."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    if not text or len(text) < 50:
        return None

    info = CompanyInfo()
    patterns = {
        "legal_representative": r"法定代表人[：:]\s*(\S+)",
        "registered_capital": r"注册资本[：:]\s*(\S+)",
        "established_date": r"成立日期[：:]\s*(\S+)",
        "business_status": r"经营状态[：:]\s*([存续在营吊销注销迁出]+)",
        "unified_code": r"统一社会信用代码[：:]\s*(\S+)",
        "business_scope": r"经营范围[：:]\s*(\S+)",
        "address": r"注册地址[：:]\s*(\S+)",
        "phone": r"电话[：:]\s*(\S+)",
        "email": r"邮箱[：:]\s*(\S+)",
    }

    for field_name, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            setattr(info, field_name, match.group(1).strip())

    if info.legal_representative or info.unified_code:
        info.source = "天眼查"
        return info
    return None


def _parse_gsxt(html: str) -> CompanyInfo | None:
    """Try to parse company info from 国家企业信用信息公示系统."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    if not text or len(text) < 50:
        return None

    info = CompanyInfo()
    patterns = {
        "name": r"企业名称[：:]\s*(\S+)",
        "legal_representative": r"法定代表人[：:]\s*(\S+)",
        "registered_capital": r"注册资本[：:]\s*(\S+)",
        "established_date": r"成立日期[：:]\s*(\S+)",
        "business_status": r"经营状态[：:]\s*([存续在营吊销注销迁出]+)",
        "unified_code": r"统一社会信用代码[：:]\s*(\S+)",
        "registration_number": r"注册号[：:]\s*(\S+)",
        "company_type": r"类型[：:]\s*(\S+)",
        "business_scope": r"经营范围[：:]\s*(\S+)",
        "address": r"住所[：:]\s*(\S+)",
    }

    for field_name, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            setattr(info, field_name, match.group(1).strip())

    if info.legal_representative or info.unified_code:
        info.source = "国家企业信用信息公示系统"
        return info
    return None


def _search_and_parse(company_name: str, url: str, parser_func) -> CompanyInfo | None:
    """Search for company info at a given URL and parse the response."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            # Try to detect if we got blocked or hit a captcha
            if len(resp.text) < 200 or "验证" in resp.text[:500] or "captcha" in resp.text[:500].lower():
                return None
            return parser_func(resp.text)
    except Exception:
        return None


async def search_company(company_name: str) -> CompanyInfo | None:
    """
    Search for company information from multiple sources.
    Returns a CompanyInfo object with whatever was found.
    """
    query = company_name.strip()
    if not query:
        return None

    # Source URLs (search pages)
    sources = [
        (f"https://www.qcc.com/web/search?key={query}", _parse_qichacha),
        (f"https://aiqicha.baidu.com/s?q={query}", _parse_aiqicha),
        (f"https://www.tianyancha.com/search?key={query}", _parse_tianyancha),
        (f"http://www.gsxt.gov.cn/search?key={query}", _parse_gsxt),
    ]

    # Try each source until we get a result
    for url, parser in sources:
        result = _search_and_parse(query, url, parser)
        if result:
            result.name = query
            return result

    return None


def company_info_to_json(info: CompanyInfo | None) -> dict:
    """Convert CompanyInfo to JSON-serializable dict."""
    if info is None:
        return {"name": "", "found": False, "message": "未找到企业信息"}
    data = asdict(info)
    data["found"] = bool(info.legal_representative or info.unified_code or info.business_scope)
    return data


def merge_company_info(existing_json: str, new_info: CompanyInfo) -> str:
    """Merge newly searched info into existing company_info JSON string."""
    existing = {}
    if existing_json:
        try:
            existing = json.loads(existing_json)
        except json.JSONDecodeError:
            pass

    new_data = asdict(new_info)
    # Don't overwrite manually edited fields with empty search results
    for key, value in new_data.items():
        if value and (key not in existing or not existing[key]):
            existing[key] = value

    return json.dumps(existing, ensure_ascii=False, indent=2)
