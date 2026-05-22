# financial-mcp-poc

ビジネス評価支援のためのMCPサーバーPoC（概念実証）

本PoCは、地域金融機関向けの事業性評価支援を想定した、
軽量なMCP（Model Context Protocol）Serverの技術検証です。

MCP Python SDK、FastMCP、Ollamaを用いて、
構造化出力・追加ヒアリング項目生成・review routingを検証しています。

---

# 概要

本PoCでは以下を検証しています。

- MCP Server実装
- FastMCPによるtool登録
- OllamaローカルLLM連携
- structured JSON output
- grounded evidence生成
- missing information検出
- needs_review routing
- JSON recovery handling
- failure fallback response

---

# アーキテクチャ

```text
MCP Inspector
      ↓
MCP Server (FastMCP)
      ↓
generate_hearing_questions()
      ↓
Ollama (qwen2.5:1.5b)
```

ディレクトリ構成

```
financial-mcp-poc/
├── prompts/
│   └── business_evaluation_prompt.txt
├── samples/
│   ├── sample_01_input.json
│   ├── sample_01_output.json
│   ├── sample_02_input.json
│   └── sample_02_output.json
├── server.py
├── metrics.md
├── requirements.txt
├── README.md
├── Dockerfile
├── .dockerignore
└── .gitignore
```

セットアップ
仮想環境作成

```
python -m venv .venv
```

仮想環境有効化（PowerShell）

```
.venv\Scripts\Activate.ps1
```

ライブラリインストール

```
pip install -r requirements.txt
```

Ollama起動
本PoCではローカルLLMとしてOllamaを使用しています。
モデル取得

```
ollama pull qwen2.5:1.5b
```

動作確認

```
ollama run qwen2.5:1.5b
```

MCP Server起動

```
python server.py
```

MCP Inspector起動

```
npx @modelcontextprotocol/inspector python server.py
```

Inspectorから以下のtoolを確認できます。

* hello_company
* generate_hearing_questions

Tool概要
hello_company
簡易的な接続確認用tool。
入力

```
{
  "company_name": "ABC株式会社"
}
```

出力

```
{
  "message": "ABC株式会社 を分析対象として登録しました。"
}
```

generate_hearing_questions
事業性評価支援向けtool。
以下を生成します。

* リスク
* 不足情報
* 追加ヒアリング項目
* confidence
* needs_review

入力

```
{
  "company_overview": "...",
  "financial_summary": "...",
  "business_plan": "..."
}
```

出力例

```
{
  "risks": [
    {
      "risk": "借入金増加リスク",
      "evidence": "借入金は増加しており、設備更新に伴う資金需要がある"
    }
  ],
  "missing_information": [
    "返済計画"
  ],
  "hearing_questions": [
    {
      "question": "借入金の返済計画はどの期間ですか？",
      "priority": "high",
      "reason": "資金繰り確認のため",
      "evidence": "借入金が増加しており、設備更新に伴う資金需要がある"
    }
  ],
  "confidence": 0.6,
  "needs_review": true
}
```

Sample Cases
sample_01
設備投資リスクを持つ製造業ケース。

* 売上微減
* 借入金増加
* 新規設備投資
* 顧客集中

を含む。

sample_02
入力不足時のfailure fallbackケース。

* 企業概要不足
* 財務情報不足

時の挙動を確認。

Evaluation Metrics
本PoCでは以下を評価観点として定義。

* schema_validity
* grounded_evidence
* missing_information_detection
* escalation_validity
* json_recovery_success

詳細は `metrics.md` を参照。

安全設計
本PoCでは以下を重視。

* hallucination抑制
* grounded evidence
* missing information明示
* human review routing
* strict JSON output
* parser recovery
* fallback response

制限事項

* 軽量ローカルLLM（qwen2.5:1.5b）を使用
* 出力品質はモデル性能に依存
* RAG未実装
* 財務分析ロジックは簡略化
* 本PoCは技術検証目的

今後の改善

* RAG integration
* 財務資料検索
* JSON validation強化
* evaluation automation
* MCP client integration
* Docker Compose対応
* provider abstraction
* OpenAI / Claude対応

ライセンス
PoC / Study Purpose