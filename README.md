# financial-mcp-poc
 
地域金融機関向け事業性評価支援を題材とした **MCP Workflow PoC（概念実証）** です。
 
単一のtool呼び出しではなく、複数のMCP toolをworkflowとして連結し、
**tool chaining / structured output / fallback handling / needs_review routing** を検証します。
 
LLMは Ollama（ローカル `qwen2.5:1.5b`）、MCPサーバは FastMCP で実装しています。
 
---
 
## 検証スコープ
 
- MCP Server 実装（FastMCP）
- 複数MCP toolによる workflow orchestration
- tool chaining（前段toolの出力を後段が利用）
- structured JSON output
- grounded evidence 生成（根拠付き出力）
- missing information 検出
- needs_review routing（human-in-the-loop への振り分け）
- JSON parser recovery / failure fallback response
- Ollama ローカルLLM連携
---
 
## アーキテクチャ
 
```text
MCP Inspector / MCP Client
            ↓
     MCP Server (FastMCP)
            ↓
  run_business_evaluation_workflow()
            ↓
        Ollama (qwen2.5:1.5b)
```
 
MCPサーバが workflow orchestrator として動作し、内部で複数toolを順次呼び出します。
LLM推論はローカルのOllamaに集約されます。
 
---
 
## 業務フロー
 
`run_business_evaluation_workflow()` は、以下のMCP toolを chaining して最終レポートを生成します。
 
```text
Input (company_overview / financial_summary / business_plan)
        ↓
1. summarize_company_profile          … 企業概要の要約
2. detect_missing_information         … 不足情報の検出
3. extract_business_risks             … リスク抽出（evidence付き）
4. generate_hearing_questions         … 追加ヒアリング項目生成
5. prioritize_hearing_questions       … 優先度付け（high / medium / low）
6. generate_business_evaluation_report … 統合レポート生成
        ↓
Final Report (structured JSON + needs_review flag)
```
 
各段階で structured JSON を返し、後段toolが前段の出力を入力として受け取ります。
 
---
 
## Tool 一覧
 
| Tool | 役割 | 主な出力 |
|---|---|---|
| `hello_company` | 接続確認用 | `message` |
| `summarize_company_profile` | 企業概要の要約 | `summary` |
| `detect_missing_information` | 不足情報の検出 | `missing_information[]` |
| `extract_business_risks` | リスク抽出 | `risks[] { risk, evidence }` |
| `generate_hearing_questions` | 追加ヒアリング項目生成 | `hearing_questions[]` |
| `prioritize_hearing_questions` | 優先度付け | `hearing_questions[] { priority, reason }` |
| `generate_business_evaluation_report` | 統合レポート生成 | `risks / missing_information / hearing_questions / confidence / needs_review` |
| `run_business_evaluation_workflow` | 上記をchainingするorchestrator | Final Report |
 
---
 
## ディレクトリ構成
 
```text
financial-mcp-poc/
├── prompts/
│   ├── company_profile_summary_prompt.txt
│   ├── missing_information_prompt.txt
│   ├── business_risk_extraction_prompt.txt
│   ├── hearing_questions_prompt.txt
│   ├── hearing_question_priority_prompt.txt
│   └── business_evaluation_report_prompt.txt
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
 
---
 
## セットアップ
 
```bash
# 仮想環境
python -m venv .venv
.venv\Scripts\Activate.ps1          # PowerShell
 
# 依存ライブラリ
pip install -r requirements.txt
 
# Ollama (ローカルLLM)
ollama pull qwen2.5:1.5b
 
# MCP Server 起動
python server.py
 
# MCP Inspector から接続
npx @modelcontextprotocol/inspector python server.py
```
 
Inspector上で各toolおよび `run_business_evaluation_workflow` を実行できます。
 
---
 
## 入出力例
 
### 入力
 
```json
{
  "company_overview": "...",
  "financial_summary": "...",
  "business_plan": "..."
}
```
 
### 出力（Final Report）
 
```json
{
  "risks": [
    { "risk": "借入金増加リスク", "evidence": "借入金が増加し、設備更新の資金需要がある" }
  ],
  "missing_information": ["返済計画"],
  "hearing_questions": [
    {
      "question": "借入金の返済計画はどの期間ですか？",
      "priority": "high",
      "reason": "資金繰り確認のため"
    }
  ],
  "confidence": 0.6,
  "needs_review": true
}
```
 
`needs_review = true` の場合は human-in-the-loop によるレビューに振り分ける想定です。
 
---
 
## Sample Cases
 
- **sample_01** — 製造業 / 設備投資リスクケース（売上微減・借入金増加・新規設備投資・顧客集中）
- **sample_02** — 入力不足時の fallback ケース（企業概要・財務情報の欠落）
---
 
## Evaluation Metrics
 
評価観点は以下のとおり。詳細は [`metrics.md`](./metrics.md) を参照。
 
| 指標 | 内容 |
|---|---|
| `schema_validity` | 出力JSONがスキーマに準拠しているか |
| `grounded_evidence` | リスク・質問にevidenceが付与されているか |
| `missing_information_detection` | 不足情報を正しく検出できるか |
| `escalation_validity` | `needs_review` の振り分けが妥当か |
| `json_recovery_success` | JSON崩れからのrecoveryが成立するか |
 
---
 
## 安全設計
 
- hallucination 抑制（grounded evidence 必須）
- missing information の明示
- `needs_review` フラグによるレビュー振り分け
- strict JSON output / JSON parser recovery
- failure fallback response
---
 
## 制限事項
 
- 軽量ローカルLLM（`qwen2.5:1.5b`）を使用、出力品質はモデル性能に依存
- RAG 未実装、財務分析ロジックは簡略化
- 本PoCは技術検証目的
---
 
## 今後の拡張候補
 
- RAG integration（財務資料検索）
- JSON schema validation 強化
- evaluation automation
- MCP client integration
- Docker Compose 対応
- provider abstraction（OpenAI / Claude 対応）
---
 
## ライセンス
 
PoC / Study Purpose