import os
import json
import re
from datetime import datetime
from typing import List, Optional

from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from markdown2 import markdown
from weasyprint import HTML

# loading gemini api key from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# defining the structured data model
class AnnualReport(BaseModel):
    company_name: str = Field(..., description="Name of the company as reported in the 10-K")
    cik: str = Field(..., description="Central Index Key (CIK) of the company, an identifier assigned by SEC")
    fiscal_year_end: datetime = Field(..., description="Fiscal year end date")
    filling_date: datetime = Field(..., description="Date when the 10-K was filed with the SEC")
    total_revenue: Optional[float] = Field(None, description="Total revenue for the fiscal year in USD")
    net_income: Optional[float] = Field(None, description="Profit for the fiscal year in USD")
    total_assets: Optional[float] = Field(None, description="Total assets at fiscal year end in USD")
    total_liabilities: Optional[float] = Field(None, description="Total liabilities at fiscal year end in USD")
    operating_cash_flow: Optional[float] = Field(None, description="Net cash provided by operating activities in USD")
    cash_and_equivalents: Optional[float] = Field(None, description="Cash and cash equivalents at fiscal year end in USD")
    num_employees: Optional[int] = Field(None, description="Number of employees reported")
    auditor: Optional[str] = Field(None, description="Name of the external auditor")
    business_description: Optional[str] = Field(None, description="Company's business overview (Item 1)")
    risk_factors: Optional[str] = Field(None, description="Key risk factors (Item 1A)")
    management_discussion: Optional[str] = Field(None, description="Management's Discussion & Analysis (Item 7)")

# main summary function
def summarize_10k(text: str) -> dict:
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    schema = json.dumps(AnnualReport.model_json_schema(), indent=2, ensure_ascii=False)

    prompt = f"Analyze the following annual report (10-K) and fill the data model based on it:\n\n{text}\n\n"
    prompt += f"The output needs to be in the following format:\n\n{schema}\n\n No extra fields allowed at all!"

    response = model.generate_content(prompt)

    try:
        report = AnnualReport.model_validate_json(response.text)
    except Exception as e:
        raise ValueError(f"Failed to parse Gemini response: {e}\n\nRaw response: {response.text}")
    
    return {
        "report": report,
        "markdown": render_markdown(report),
        "pdf_path":save_pdf(report)
    }

# converts the report to markdown
def render_markdown(ar: AnnualReport) -> str:
    md = [
        f"# {ar.company_name} Annual Report {ar.fiscal_year_end.year}",
        f"**CIK:** {ar.cik}",
        f"**Fiscal Year End:** {ar.fiscal_year_end.strftime('%Y-%m-%d')}",
        f"**Filing Date:** {ar.filling_date.strftime('%Y-%m-%d')}",
        "## Financials"
    ]

    if ar.total_revenue: md.append(f"- **Total Revenue:** ${ar.total_revenue:, .2f}")
    if ar.net_income: md.append(f"- **Net Income:** ${ar.net_income:,.2f}")
    if ar.total_assets: md.append(f"- **Total Assets:** ${ar.total_assets:,.2f}")
    if ar.total_liabilities: md.append(f"- **Total Liabilities:** ${ar.total_liabilities:,.2f}")
    if ar.operating_cash_flow: md.append(f"- **Operating Cash Flow:** ${ar.operating_cash_flow:,.2f}")
    if ar.cash_and_equivalents: md.append(f"- **Cash & Equivalents:** ${ar.cash_and_equivalents:,.2f}")
    if ar.num_employees: md.append(f"- **Number of Employees:** ${ar.num_employees:,.2f}")
    if ar.auditor: md.append(f"- **Auditor:** ${ar.auditor:,.2f}")

    if ar.business_description:
        md += ["\n## Business Description", ar.business_description]
    if ar.risk_factors:
        md += ["\n## Risk Factors"] + [f"- {rf}" for rf in ar.risk_factors]
    if ar.management_discussion:
        md += ["\n## Management Discussion & Analysis", ar.management_discussion]
    

    return "\n\n".join(md)


# converts markdown -> HTML -> PDF
def save_pdf(ar: AnnualReport) -> str:
    md = render_markdown(ar)
    html = markdown(md)
    company = re.sub(r"[^\w\-]", "_", ar.company_name)
    filename = f"FinancialSummary_{company}_{ar.fiscal_year_end.year}.pdf"
    HTML(string=HTML).write_pdf(filename)
    return filename


