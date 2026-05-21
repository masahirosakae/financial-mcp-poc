import json
import re
import ollama
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("financial-mcp-poc")

MODEL_NAME = "qwen2.5:1.5b"


def extract_json(content: str) -> dict:
    content = content.strip()

    # ```json ... ``` を除去
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    # 前後に説明文が混ざる場合、最初の { から最後の } までを抽出
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", content, 0)

    json_text = content[start:end + 1]
    return json.loads(json_text)


@mcp.tool()
def hello_company(company_name: str) -> dict:
    """return a simple confirmation messege for a target company."""
    return {
	"message": f"{company_name} を分析対象として登録しました。"
    }


def build_prompt(
        company_overview: str,
        financial_summary: str,
        business_plan: str,
) -> str:
    return f"""
# Role

あなたは地域金融機関の法人営業担当者を支援するAIです。

目的は、
- 事業性評価の論点整理
- リスク抽出
- 追加ヒアリング項目の生成
です。

融資可否を決定してはいけません。

# Policy

- 入力文だけを根拠にしてください
- 推測で断定しないでください
- evidence には入力文の実際の記述を短く引用してください
- evidence が存在しない場合は "insufficient evidence" を設定してください
- missing_information が存在する場合は needs_review を true にしてください
- 重要情報が不足する場合、confidence は 0.7 以下にしてください

# Procedure

以下の順番で考えてください。

1. 不足情報を確認
2. リスクを整理
3. 追加ヒアリング項目を作成
4. confidence を決定
5. needs_review を決定
6. JSONのみ返却

# Input

## 企業概要
{company_overview}

## 財務サマリ
{financial_summary}

## 事業計画
{business_plan}

# Output Format

JSONのみ返してください。

{{
  "risks": [
    {{
      "risk": "設備投資負担増加リスク",
      "evidence": "借入金は増加しており"
    }}
  ],
  "missing_information": [
    "返済計画"
  ],
  "hearing_questions": [
    {{
      "question": "設備投資の回収計画はありますか？",
      "priority": "high",
      "reason": "返済計画確認のため",
      "evidence": "設備更新に伴う資金需要"
    }}
  ],
  "confidence": 0.6,
  "needs_review": true
}}
"""


def fallback_response(reason: str) -> dict:
    return {
        "risks": [],
        "missing_information": [reason],
        "hearing_questions": [],
        "confidence": 0.0,
        "needs_review": True,
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

    prompt = build_prompt(company_overview, financial_summary, business_plan)

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