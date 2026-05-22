import json
import re
from pathlib import Path
import ollama
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("financial-mcp-poc")

MODEL_NAME = "qwen2.5:1.5b"
PROMPT_PATH = Path("prompts/business_evaluation_prompt.txt")


def load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_prompt(
        company_overview: str,
        financial_summary: str,
        business_plan: str,
) -> str:
    template = load_prompt_template()
    return template.format(
        company_overview = company_overview,
        financial_summary = financial_summary,
        business_plan = business_plan,
    )


def extract_json(content: str) -> dict:
    content = content.strip()

    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", content, 0)

    json_text = content[start:end + 1]
    return json.loads(json_text)


def fallback_response(reason: str) -> dict:
    return {
        "risks": [],
        "missing_information": [reason],
        "hearing_questions": [],
        "confidence": 0.0,
        "needs_review": True,
    }


@mcp.tool()
def hello_company(company_name: str) -> dict:
    """return a simple confirmation messege for a target company."""
    return {
	"message": f"{company_name} を分析対象として登録しました。"
    }


@mcp.tool()
def generate_hearing_questions(
    company_overview: str,
    financial_summary: str,
    business_plan: str,
) -> dict:
    """Generate hearing questions for business evaluation support."""

    if not company_overview.strip() or not financial_summary.strip():
        return fallback_response("企業概要または財務サマリが不足しています。")

    prompt = build_prompt(
        company_overview = company_overview,
        financial_summary = financial_summary,
        business_plan = business_plan,
        )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        content = response["message"]["content"].strip()
        return json.loads(content)

    except Exception as e:
        return fallback_response(f"LLM応答の処理に失敗しました: {type(e).__name__}")



if __name__ == "__main__":
    mcp.run()