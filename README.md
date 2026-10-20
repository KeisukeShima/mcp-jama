# mcp-jama

[![PyPI](https://img.shields.io/pypi/v/mcp-jama)](https://pypi.org/project/mcp-jama/)

JAMA Cloud（Jama Connect）を Claude Code / Codex から操作するための MCP サーバー。
両クライアントで同じ stdio サーバーと JAMA 接続設定を利用できます。

## セットアップ

Python 3.10 以上と `uv` が必要です。`uv` のインストールは [公式ガイド](https://docs.astral.sh/uv/getting-started/installation/) を参照してください。
以下のコマンド例は Bash / Zsh 向けです。

### 1. 設定ファイルを作成する

```bash
mkdir -p ~/.config/mcp-jama
curl -sL https://raw.githubusercontent.com/KeisukeShima/mcp-jama/main/config.json.example \
  > ~/.config/mcp-jama/config.json
```

`~/.config/mcp-jama/config.json` を編集して JAMA Cloud の接続情報を入力する。

### 2. 利用するクライアントに登録する

両方を使う場合は、それぞれの登録コマンドを実行します。

#### Claude Code

```bash
claude mcp add jama --scope user --transport stdio \
  --env "JAMA_CONFIG=$HOME/.config/mcp-jama/config.json" -- uvx mcp-jama
```

登録後、Claude Code のセッションを再起動します。

#### Codex（CLI / IDE 拡張）

```bash
codex mcp add jama \
  --env "JAMA_CONFIG=$HOME/.config/mcp-jama/config.json" -- uvx mcp-jama
```

Codex CLI と IDE 拡張は MCP 設定を共有します。登録後、CLI のセッションまたは IDE 拡張を再起動します。

手動で登録する場合は、`~/.codex/config.toml` に以下を追記します。`JAMA_CONFIG` は自分の設定ファイルの絶対パスに置き換えてください。
プロジェクト単位で利用する場合は、信頼済みプロジェクトの `.codex/config.toml` にも同じ設定を書けます。

```toml
[mcp_servers.jama]
command = "uvx"
args = ["mcp-jama"]

[mcp_servers.jama.env]
JAMA_CONFIG = "/absolute/path/to/.config/mcp-jama/config.json"
```

TOML 内の `$HOME` はシェルのようには展開されません。上記の登録コマンドではシェルが `$HOME` を展開し、絶対パスを保存します。

### 3. 接続を確認する

```bash
# Claude Code
claude mcp get jama

# Codex
codex mcp get jama
```

各クライアントのセッションで `/mcp` を開いて `jama` の状態を確認し、「JAMA のプロジェクト一覧を取得して」と依頼してください。
ツール一覧の取得には JAMA の認証は不要ですが、`get_projects` などの実行には有効な接続設定が必要です。

登録方法の詳細は [Claude Code の公式ドキュメント](https://code.claude.com/docs/en/mcp) と [OpenAI Docs の Codex MCP ガイド](https://developers.openai.com/codex/mcp/) を参照してください。

### 設定ファイルのパス

`JAMA_CONFIG` 環境変数で設定ファイルを指定します。未指定の場合は、サーバー起動時の作業ディレクトリの `./config.json` を読み込みます。
`~/...` の指定にも対応します。どのプロジェクトからでも使えるように、クライアントへの登録では絶対パスを指定してください。

### 開発者向け: ローカル実行

```bash
pip install -r requirements.txt
cp config.json.example config.json
# config.json を編集して接続情報を入力
python server.py
```

ローカルの変更をクライアントから検証する場合は、公開済みパッケージを使う `uvx mcp-jama` の代わりに、依存パッケージをインストールした Python と `server.py` の絶対パスを登録します。

```bash
# /absolute/path/to/python は使用する Python の絶対パスに置き換える
# python -c 'import sys; print(sys.executable)' で確認できる
claude mcp add jama-local --scope user --transport stdio \
  --env "JAMA_CONFIG=$PWD/config.json" -- \
  /absolute/path/to/python "$PWD/server.py"

codex mcp add jama-local --env "JAMA_CONFIG=$PWD/config.json" -- \
  /absolute/path/to/python "$PWD/server.py"
```

上記のコマンドはリポジトリ直下で実行してください。登録後はクライアントを再起動し、`jama-local` のツールで動作を確認します。

### PyPI への公開

```bash
# 1. pyproject.toml のバージョンを上げる
# 2. 再ビルド
rm -rf dist/
hatch build
# 3. アップロード（twine は uvx 経由で実行する）
uvx twine upload dist/*
# 4. コミット・プッシュ
git add pyproject.toml
git commit -m "bump: version x.y.z"
git push
```

> **Note:** `twine upload` を直接実行すると `requests_toolbelt` の依存関係エラーが出るため、`uvx twine upload` を使う。

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

**必要なライセンス:** JAMA API を使用するには **Named Creator ライセンス** が必要です。Viewer ライセンスでは API アクセス時に `401 A named Creator license is required for access.` エラーが返されます。
