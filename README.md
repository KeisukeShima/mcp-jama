# mcp-jama

JAMA Cloud（Jama Connect）を Claude Code から操作するための MCP サーバー。

## セットアップ

### 1. 設定ファイルを作成する

```bash
mkdir -p ~/.config/mcp-jama
curl -sL https://raw.githubusercontent.com/KeisukeShima/mcp-jama/main/config.json.example \
  > ~/.config/mcp-jama/config.json
```

`~/.config/mcp-jama/config.json` を編集して JAMA Cloud の接続情報を入力する。

### 2. Claude Code に登録する

```bash
claude mcp add jama -e JAMA_CONFIG=~/.config/mcp-jama/config.json -- uvx mcp-jama
```

以上でセットアップ完了。`uv` がインストールされていない場合は https://docs.astral.sh/uv/getting-started/installation/ を参照。

### 開発者向け: ローカル実行

```bash
pip install -r requirements.txt
cp config.json.example config.json
# config.json を編集して接続情報を入力
python server.py
```

## テスト実行

```bash
pytest tests/
```

## 利用可能なツール

| ツール | 説明 |
|---|---|
| `get_projects` | プロジェクト一覧 |
| `get_items` | アイテム一覧（ページネーション対応） |
| `get_item` | アイテム詳細 |
| `search_items` | キーワード検索 |
| `create_item` | アイテム作成 |
| `update_item` | アイテム更新 |
| `get_relationships` | トレーサビリティリンク一覧 |
| `create_relationship` | リンク作成 |
| `delete_relationship` | リンク削除 |
| `get_test_plans` | テストプラン一覧 |
| `create_test_plan` | テストプラン作成 |
| `get_test_cycles` | テストサイクル一覧 |
| `get_test_runs` | テストラン一覧 |
| `create_test_result` | テスト結果記録 |
| `add_comment` | コメント追加 |

## 認証

Basic 認証のみ対応（v1）。SSO/SAML 環境では OAuth 認証が必要になる場合があります（将来バージョンで対応予定）。
