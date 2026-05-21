# financial-mcp-poc

ビジネス評価支援のためのMCPサーバーPoC（概念実証）

## 1日目の結果
- Python仮想環境を構築
- MCP Python SDKとOllamaクライアントをインストール
- OllamaローカルLLM呼び出しを確認
- FastMCPを使用してMCPサーバーを構築
- 以下のツールを追加：
 * hello\_company
 * generate\_hearing\_questions
- MCP Inspectorでツールの実行を確認
- MCPサーバー
- OllamaローカルLLM
- 構造化JSON出力
- 安全性を重視したプロンプト設計
- レビュールーティング
- JSONリカバリ処理

## 現在の目標
SIGNATE Partnersプロジェクトに申請する前に、ビジネス評価支援のための軽量MCPツール構造を検証する。


## サンプルケース
- sample_01：投資リスクのある製造会社
- sample_02：入力不足時のフォールバックケース


## 今後の改善点
- RAGとの連携
- 財務文書の取得
- MCPクライアントとの連携
- JSON検証機能の強化
- 評価の自動化
- Dockerサポート