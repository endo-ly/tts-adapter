# tts-adapter

常駐TTS APIサーバー。OpenAI互換のTTS APIとして外部から利用でき、内部では複数のTTSエンジンをProviderとして切り替えられる。

## Why tts-adapter

`tts-adapter` は、TTSエンジンを直接使うためのライブラリではなく、**複数のTTSエンジンをエージェントや外部ツールから同じ形で扱うためのアダプタサーバー**である。

TTSエンジンは、それぞれAPI形式、モデル指定、声の指定方法、実行方法が異なる。`tts-adapter` はその差分を吸収し、クライアント側からは次のように扱えるようにする。

```json
{
  "model": "tts-default",
  "voice": "your-voice-name",
  "input": "こんにちは"
}
```

目的は **「TTSを動かすこと」そのものよりも、「声の出口を安定したAPIとして固定すること」**。詳細は [CONCEPT](docs/CONCEPT.md) を参照。

## 特徴

- **OpenAI互換API** — `POST /v1/audio/speech` でOpenClaw等から `baseUrl` 差し替えで利用可能
- **Native API** — `POST /v1/speech` で自作エージェント向けの拡張パラメータを利用可能
- **YAMLプロファイル** — model / voice の設定をYAMLで管理。v0では起動時に読み込み、将来的に再読み込みに対応予定

現在対応しているTTSエンジン:

| Provider | 説明 |
|----------|------|
| [Irodori-TTS](https://github.com/Aratako/Irodori-TTS) | Flow Matchingベースの日本語TTS。ゼロショット音声クローン（base）とキャプション条件付き音声設計（VoiceDesign）に対応 |

追加のTTSエンジンはProviderとして拡張可能。詳細は [拡張ガイド](docs/extension-guide.md) を参照。

## クイックスタート

### 1. セットアップ

```bash
uv sync --group dev
```

### 2. 設定ファイルの配置

```bash
cp assets/models/models.example.yaml assets/models/models.yaml
cp assets/voices/your-voice-name/profile.example.yaml assets/voices/your-voice-name/profile.yaml
```

環境変数を設定:

```bash
export IRODORI_REPO_DIR=/path/to/Irodori-TTS
```

詳細は [設定ガイド](docs/configuration.md) を参照。

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
  -d '{"model":"tts-default","voice":"your-voice-name","input":"こんにちは"}' \
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
          "voice": "your-voice-name"
        }
      }
    }
  }
}
```

## ドキュメント

| 対象 | ドキュメント | 内容 |
|------|------------|------|
| 全般 | [CONCEPT](docs/CONCEPT.md) | 設計思想、使う理由、使わないケース |
| 利用者 | [APIリファレンス](docs/api-reference.md) | 全エンドポイントの入出力仕様 |
| 運用者 | [設定ガイド](docs/configuration.md) | 環境変数、プロファイル、マージ規則 |
| 開発者 | [アーキテクチャ](docs/architecture.md) | レイヤー分離、データフロー、主要クラス |
| 開発者 | [拡張ガイド](docs/extension-guide.md) | Provider・Voice・Modelの追加手順 |
| 開発者 | [開発ガイド](docs/development.md) | 環境構築、テスト、プロジェクト構成 |

## ライセンス

Private
