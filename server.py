import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import ollama
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("financial-mcp-poc")

MODEL_NAME = "qwen2.5:1.5b"
PROMPT_DIR = Path("prompts")
LOG_DIR = Path("logs")


# -----------------------------
# Common utilities
# -----------------------------

def build_prompt_from_file(prompt_file: str, **kwargs: Any) -> str:
    template = (PROMPT_DIR / prompt_file).read_text(encoding="utf-8")
    return template.format(**kwargs)


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

    # Remove trailing commas before } or ]
    json_text = re.sub(r",\s*([}\]])", r"\1", json_text)

    return json.loads(json_text)


def fallback_response(reason: str) -> dict:
    return {
        "risks": [],
        "missing_information": [reason],
        "hearing_questions": [],
        "confidence": 0.0,
        "needs_review": True,
    }


def save_raw_content(label: str, content: str) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", label)

    log_path = LOG_DIR / f"{timestamp}_{safe_name}.txt"
    log_path.write_text(content, encoding="utf-8")


def normalize_japanese_text(value: Any) -> Any:
    if isinstance(value, str):
        return (
            value
            .replace("風險", "リスク")
            .replace("风险", "リスク")
            .replace("資金需要直接関連", "資金需要に直接関連")
            .replace("资金需要直接相关", "資金需要に直接関連")
            .replace("资金", "資金")
            .replace("相关", "関連")
        )

    if isinstance(value, list):
        return [normalize_japanese_text(item) for item in value]

    if isinstance(value, dict):
        return {key: normalize_japanese_text(val) for key, val in value.items()}

    return value


def enforce_review_policy(result: dict) -> dict:
    if not isinstance(result, dict):
        return result

    missing_info = result.get("missing_information")

    if missing_info:
        result["needs_review"] = True
        result["confidence"] = min(float(result.get("confidence", 0.7)), 0.7)

    return result


def run_llm_json(prompt: str, fallback_reason: str) -> dict:
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1},
        )

        content = response["message"]["content"].strip()
        save_raw_content(fallback_reason, content)

        result = extract_json(content)
        result = normalize_japanese_text(result)
        result = enforce_review_policy(result)

        return result

    except Exception as e:
        return fallback_response(f"{fallback_reason}: {type(e).__name__}")


def summarize_workflow_status(steps: list[dict]) -> dict:
    valid_steps = [step for step in steps if isinstance(step, dict)]

    needs_review = any(
        step.get("needs_review", True)
        for step in valid_steps
    )

    confidence_values = [
        float(step.get("confidence", 0.0))
        for step in valid_steps
    ]

    confidence = min(confidence_values) if confidence_values else 0.0

    return {
        "confidence": confidence,
        "needs_review": needs_review,
    }


# -----------------------------
# MCP tools
# -----------------------------

@mcp.tool()
def hello_company(company_name: str) -> dict:
    """Return a simple confirmation message for a target company."""
    return {
        "message": f"{company_name} を分析対象として登録しました。"
    }


@mcp.tool()
def summarize_company_profile(
    company_overview: str,
    financial_summary: str,
    business_plan: str,
) -> dict:
    """Summarize company profile for business evaluation."""

    if not company_overview.strip():
        return fallback_response("企業概要が不足しています。")

    prompt = build_prompt_from_file(
        "company_profile_summary_prompt.txt",
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    return run_llm_json(prompt, "企業概要整理に失敗しました")


@mcp.tool()
def detect_missing_information(
    company_overview: str,
    financial_summary: str,
    business_plan: str,
) -> dict:
    """Detect missing information for business evaluation."""

    prompt = build_prompt_from_file(
        "missing_information_prompt.txt",
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    return run_llm_json(prompt, "不足情報検出に失敗しました")


@mcp.tool()
def extract_business_risks(
    company_overview: str,
    financial_summary: str,
    business_plan: str,
) -> dict:
    """Extract business risks for business evaluation."""

    prompt = build_prompt_from_file(
        "business_risk_extraction_prompt.txt",
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    return run_llm_json(prompt, "事業リスク抽出に失敗しました")


@mcp.tool()
def generate_hearing_questions(
    company_overview: str,
    financial_summary: str,
    business_plan: str,
) -> dict:
    """Generate additional hearing questions for business evaluation."""

    prompt = build_prompt_from_file(
        "hearing_questions_prompt.txt",
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    return run_llm_json(prompt, "追加ヒアリング項目生成に失敗しました")


@mcp.tool()
def prioritize_hearing_questions(
    hearing_questions: dict,
) -> dict:
    """Prioritize hearing questions."""

    prompt = build_prompt_from_file(
        "hearing_question_priority_prompt.txt",
        hearing_questions_json=json.dumps(
            hearing_questions,
            ensure_ascii=False,
            indent=2,
        ),
    )

    return run_llm_json(prompt, "ヒアリング優先順位付けに失敗しました")


@mcp.tool()
def generate_business_evaluation_report(
    company_summary: dict,
    missing_information: dict,
    business_risks: dict,
    prioritized_questions: dict,
) -> dict:
    """Generate a business evaluation support report from tool outputs."""

    prompt = build_prompt_from_file(
        "business_evaluation_report_prompt.txt",
        company_summary_json=json.dumps(
            company_summary,
            ensure_ascii=False,
            indent=2,
        ),
        missing_information_json=json.dumps(
            missing_information,
            ensure_ascii=False,
            indent=2,
        ),
        business_risks_json=json.dumps(
            business_risks,
            ensure_ascii=False,
            indent=2,
        ),
        prioritized_questions_json=json.dumps(
            prioritized_questions,
            ensure_ascii=False,
            indent=2,
        ),
    )

    return run_llm_json(prompt, "事業性評価レポート生成に失敗しました")


@mcp.tool()
def run_business_evaluation_workflow(
    company_overview: str,
    financial_summary: str,
    business_plan: str,
) -> dict:
    """Run the full business evaluation support workflow."""

    summary = summarize_company_profile(
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    missing = detect_missing_information(
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    risks = extract_business_risks(
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    questions = generate_hearing_questions(
        company_overview=company_overview,
        financial_summary=financial_summary,
        business_plan=business_plan,
    )

    prioritized = prioritize_hearing_questions(
        hearing_questions=questions,
    )

    report = generate_business_evaluation_report(
        company_summary=summary,
        missing_information=missing,
        business_risks=risks,
        prioritized_questions=prioritized,
    )

    workflow_steps = [
        summary,
        missing,
        risks,
        questions,
        prioritized,
        report,
    ]

    workflow_status = summarize_workflow_status(workflow_steps)

    return {
        "workflow": {
            "company_summary": summary,
            "missing_information": missing,
            "business_risks": risks,
            "hearing_questions": questions,
            "prioritized_questions": prioritized,
            "final_report": report,
        },
        "confidence": workflow_status["confidence"],
        "needs_review": workflow_status["needs_review"],
    }


if __name__ == "__main__":
    mcp.run()