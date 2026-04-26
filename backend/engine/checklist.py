"""
Material checklist definitions for each project type.
Derived from the official application requirements in the templates.
"""

GAOXIN_CHECKLIST = [
    # 企业资质
    {"id": "biz_license", "category": "企业资质", "item": "企业营业执照副本", "required": False,
     "description": "最新年检的企业法人营业执照"},
    {"id": "tax_cert", "category": "企业资质", "item": "税务登记证", "required": False,
     "description": "国税、地税税务登记证"},
    {"id": "org_code", "category": "企业资质", "item": "组织机构代码证", "required": False,
     "description": "三证合一后可用营业执照代替"},
    {"id": "legal_id", "category": "企业资质", "item": "法定代表人身份证", "required": False,
     "description": "法人代表身份证明文件"},

    # 知识产权
    {"id": "patent_certs", "category": "知识产权", "item": "专利证书", "required": False,
     "description": "发明专利、实用新型专利、外观设计专利证书"},
    {"id": "sw_copyright", "category": "知识产权", "item": "软件著作权登记证书", "required": False,
     "description": "如企业有软件相关知识产权"},
    {"id": "tm_cert", "category": "知识产权", "item": "商标注册证", "required": False,
     "description": "企业拥有的注册商标"},
    {"id": "ip_ledger", "category": "知识产权", "item": "知识产权清单汇总表", "required": False,
     "description": "所有知识产权的汇总清单"},

    # 财务审计
    {"id": "audit_3year", "category": "财务审计", "item": "近三年年度审计报告", "required": False,
     "description": "近三个会计年度的财务审计报告"},
    {"id": "rd_special_audit", "category": "财务审计", "item": "研发费用专项审计报告", "required": False,
     "description": "近三年研发费用专项审计报告"},
    {"id": "product_rev_audit", "category": "财务审计", "item": "高新技术产品收入专项审计报告", "required": False,
     "description": "近一年高新技术产品（服务）收入专项审计报告"},
    {"id": "tax_report", "category": "财务审计", "item": "近三年企业所得税纳税申报表", "required": False,
     "description": "近三年企业所得税年度纳税申报表"},

    # 人员证明
    {"id": "staff_roster", "category": "人员证明", "item": "科技人员花名册", "required": False,
     "description": "科技人员名单及岗位说明"},
    {"id": "staff_degree", "category": "人员证明", "item": "科技人员学历证书", "required": False,
     "description": "大专以上科技人员学历/学位证书"},
    {"id": "social_ins", "category": "人员证明", "item": "社保缴纳证明", "required": False,
     "description": "近一个月社会保险参保证明"},

    # 研发证明材料
    {"id": "rd_proposals", "category": "研发证明", "item": "研发项目立项报告", "required": False,
     "description": "近三年研发项目的立项决议、可行性报告"},
    {"id": "rd_acceptance", "category": "研发证明", "item": "研发项目验收报告", "required": False,
     "description": "研发项目的中期检查报告、验收结题报告"},
    {"id": "industry_contract", "category": "研发证明", "item": "产学研合作协议", "required": False,
     "description": "与高校、科研院所签订的产学研合作协议"},

    # 其他荣誉
    {"id": "iso_cert", "category": "其他荣誉", "item": "质量管理体系认证证书", "required": False,
     "description": "ISO 9001 等质量管理体系认证"},
    {"id": "honor_certs", "category": "其他荣誉", "item": "企业荣誉证书", "required": False,
     "description": "高新技术产品证书、科技进步奖、行业荣誉等"},
    {"id": "sample_app", "category": "其他荣誉", "item": "样本申报书（参考范文）", "required": False,
     "description": "如有过往申报成功的样本材料可供参考"},
]

XIAOJUREN_CHECKLIST = [
    # 企业资质
    {"id": "biz_license", "category": "企业资质", "item": "企业营业执照副本", "required": False,
     "description": "最新年检的企业法人营业执照"},
    {"id": "tax_cert", "category": "企业资质", "item": "税务登记证", "required": False,
     "description": "国税、地税税务登记证"},
    {"id": "legal_id", "category": "企业资质", "item": "法定代表人身份证", "required": False,
     "description": "法人代表身份证明文件"},

    # 知识产权
    {"id": "patent_certs", "category": "知识产权", "item": "专利证书", "required": False,
     "description": "发明专利、实用新型专利等"},
    {"id": "trademark_certs", "category": "知识产权", "item": "商标注册证", "required": False,
     "description": "企业自主品牌商标"},
    {"id": "ip_summary", "category": "知识产权", "item": "知识产权汇总表", "required": False,
     "description": "全部知识产权清单及法律状态"},

    # 财务审计
    {"id": "audit_reports", "category": "财务审计", "item": "近两年年度审计报告", "required": False,
     "description": "近两个会计年度的财务审计报告"},
    {"id": "revenue_detail", "category": "财务审计", "item": "主营业务收入明细表", "required": False,
     "description": "近两年主营业务收入构成及占比"},
    {"id": "rd_investment", "category": "财务审计", "item": "研发投入证明", "required": False,
     "description": "近两年研发费用投入明细及证明"},
    {"id": "tax_payment", "category": "财务审计", "item": "完税证明", "required": False,
     "description": "近两年纳税证明"},

    # 市场与行业
    {"id": "market_report", "category": "市场行业", "item": "市场占有率证明", "required": False,
     "description": "第三方市场调研报告或行业排名证明"},
    {"id": "industry_position", "category": "市场行业", "item": "行业地位证明", "required": False,
     "description": "行业协会证明、龙头企业认定等"},
    {"id": "export_cert", "category": "市场行业", "item": "出口相关证明", "required": False,
     "description": "如产品有出口，提供出口报关单等"},

    # 资质认证
    {"id": "mgmt_system", "category": "资质认证", "item": "管理体系认证证书", "required": False,
     "description": "ISO 9001、ISO 14001、ISO 45001 等管理体系认证"},
    {"id": "product_cert", "category": "资质认证", "item": "产品认证证书", "required": False,
     "description": "3C认证、CE认证、UL认证等产品认证"},
    {"id": "digital_cert", "category": "资质认证", "item": "数字化/信息化相关证明", "required": False,
     "description": "两化融合认证、智能制造示范等"},

    # 研发创新
    {"id": "rd_institution", "category": "研发创新", "item": "研发机构认定文件", "required": False,
     "description": "企业技术中心、工程研究中心、重点实验室等研发机构认定"},
    {"id": "industry_contract", "category": "研发创新", "item": "产学研合作协议", "required": False,
     "description": "与高校、科研院所的合作协议及成果证明"},
    {"id": "innovation_awards", "category": "研发创新", "item": "创新奖项证书", "required": False,
     "description": "技术创新、产品创新相关获奖证书"},
    {"id": "sample_app", "category": "研发创新", "item": "样本申报书（参考范文）", "required": False,
     "description": "如有过往申报成功的样本材料可供参考"},

    # 企业治理
    {"id": "corp_governance", "category": "企业治理", "item": "公司治理制度文件", "required": False,
     "description": "公司章程、三会制度、内控制度等"},
    {"id": "talent_plan", "category": "企业治理", "item": "人才队伍建设材料", "required": False,
     "description": "研发团队介绍、人才引进培养计划、核心技术人员简历"},
]


def get_checklist(project_type: str) -> list[dict]:
    """Return the material checklist for a given project type."""
    items = []
    if project_type == "gaoxin":
        items = [dict(item) for item in GAOXIN_CHECKLIST]
    elif project_type == "xiaojuren":
        items = [dict(item) for item in XIAOJUREN_CHECKLIST]
    for item in items:
        item.setdefault("uploaded", False)
        item.setdefault("doc_ids", [])
    return items


def get_checklist_stats(checklist: list[dict]) -> dict:
    """Return completion statistics for a checklist."""
    required = sum(1 for i in checklist if i.get("required"))
    required_done = sum(1 for i in checklist if i.get("required") and i.get("uploaded"))
    total_done = sum(1 for i in checklist if i.get("uploaded"))
    return {
        "total_items": len(checklist),
        "required_items": required,
        "completed_items": total_done,
        "required_completed": required_done,
        "completion_pct": round(total_done / len(checklist) * 100, 1) if checklist else 0,
        "all_required_done": required_done >= required,
    }
