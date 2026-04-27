---
name: tts-api
description: >
  REST API でテキストから音声を生成する。OpenAI 互換 TTS エンドポイント。
  トリガー: 音声生成、TTS、text to speech、読み上げ、声を生成、speech合成。
  Phrases: "generate speech", "text to speech", "TTS", "音声生成", "読み上げ".
---

# tts-adapter API

OpenAI 互換 TTS API。`TTS_URL` にベースURLを設定して使う。

## エンドポイント一覧

| メソッド | パス | 用途 |
|---|---|---|
| GET | `/health` | 死活確認 |
| GET | `/v1/models` | モデル一覧 |
| GET | `/v1/voices` | 音声一覧 |
| POST | `/v1/audio/speech` | 音声合成（OpenAI互換） |
| POST | `/v1/speech` | 音声合成（Native） |

## POST /v1/audio/speech（OpenAI互換）

```bash
curl -X POST "$TTS_URL/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{"model":"irodori-base","voice":"lyre","input":"こんにちは。"}' \
  -o output.wav
```

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `model` | string | **Yes** | `/v1/models` の ID |
| `voice` | string | **Yes** | `/v1/voices` の ID |
| `input` | string | **Yes** | 読み上げテキスト。**制御文字（改行・タブ等）はエスケープ必須** |
| `response_format` | string | No | `"wav"` のみ対応（省略時 `"wav"`） |
| `speed` | float | No | `1.0` のみ対応（省略時 `1.0`） |

成功時: `200` / `Content-Type: audio/wav` / PCM 16bit mono 48kHz

## POST /v1/speech（Native）

```bash
curl -X POST "$TTS_URL/v1/speech" \
  -H "Content-Type: application/json" \
  -d '{"model":"irodori-base","voice_id":"lyre","speech_text":"了解しました。"}' \
  -o output.wav
```

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `model` | string | **Yes** | モデル ID |
| `voice_id` | string | **Yes** | 音声 ID |
| `speech_text` | string | **Yes** | TTS入力テキスト |
| `display_text` | string | No | UI/ログ用（v0では未使用） |
| `style_hints` | object | No | スタイル指定（v0では未使用） |

## エラーレスポンス

```json
{"error":{"message":"...","type":"invalid_request_error","param":null,"code":"model_not_found"}}
```

| status | code | 条件 |
|---|---|---|
| 400 | `json_invalid` | 不正なJSON / 未エスケープの制御文字 |
| 400 | `unsupported_response_format` | `wav` 以外 |
| 404 | `model_not_found` | 不明なモデルID |
| 404 | `voice_not_found` | 不明な音声ID |
| 409 | `voice_binding_not_found` | 音声は存在するがモデルとのバインディングがない |
| 500 | `provider_execution_error` | TTSエンジン実行失敗 |
| 504 | `provider_timeout` | TTSエンジンタイムアウト |

## 注意事項

- `input` / `speech_text` に生の改行やタブを含めると `json_invalid` エラーになる。`\\n` のようにエスケープすること。
- 音声生成にはテキスト長に応じて 10〜30秒程度かかる。クライアント側で適切なタイムアウトを設定すること。
