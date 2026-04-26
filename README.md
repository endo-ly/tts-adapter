# tts-adapter

常駐TTS APIサーバー。OpenAI互換のTTS APIとして外部から利用でき、内部では複数のTTSエンジンをProviderとして切り替えられる。

## 特徴

- **OpenAI互換API** — `POST /v1/audio/speech` でOpenClaw等から `baseUrl` 差し替えで利用可能
- **Native API** — `POST /v1/speech` で自作エージェント向けの拡張パラメータを利用可能
- **マルチProvider** — Irodori、Fake（テスト用）を搭載。将来のProvider追加に対応
- **YAMLプロファイル** — model / voice の設定をYAMLで管理。再起動せずに設定変更可能（v0ではキャッシュあり）

## クイックスタート

### 1. セットアップ

```bash
uv sync --group dev
```

### 2. 設定ファイルの配置

```bash
cp assets/models/models.example.yaml assets/models/models.yaml
cp assets/voices/egopulse/profile.example.yaml assets/voices/egopulse/profile.yaml
```

Irodoriを使う場合は環境変数を設定:

```bash
export IRODORI_REPO_DIR=/path/to/irodori
```

### 3. 起動

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8012
```

### 4. 動作確認

```bash
curl http://127.0.0.1:8012/health
# → {"status":"ok"}

curl http://127.0.0.1:8012/v1/models | jq .
curl http://127.0.0.1:8012/v1/voices | jq .

curl -X POST http://127.0.0.1:8012/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-default","voice":"egopulse","input":"こんにちは"}' \
  --output test.wav
```

## OpenClawからの利用

```json
{
  "messages": {
    "tts": {
      "auto": "tagged",
      "provider": "openai",
      "providers": {
        "openai": {
          "apiKey": "local",
          "baseUrl": "http://127.0.0.1:8012/v1",
          "model": "tts-default",
          "voice": "egopulse"
        }
      }
    }
  }
}
```

## ドキュメント

| 対象 | ドキュメント | 内容 |
|------|------------|------|
| 利用者 | [APIリファレンス](docs/api-reference.md) | 全エンドポイントの入出力仕様 |
| 運用者 | [設定ガイド](docs/configuration.md) | 環境変数、プロファイル、マージ規則 |
| 開発者 | [アーキテクチャ](docs/architecture.md) | レイヤー分離、データフロー、主要クラス |
| 開発者 | [拡張ガイド](docs/extension-guide.md) | Provider・Voice・Modelの追加手順 |
| 関発者 | [開発ガイド](docs/development.md) | 環境構築、テスト、プロジェクト構成 |

## ライセンス

Private
