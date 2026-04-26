# APIリファレンス

tts-adapterが提供する全エンドポイントの仕様。

## エンドポイント一覧

| メソッド | パス | 用途 |
|---------|------|------|
| `GET` | `/health` | 死活監視 |
| `GET` | `/v1/models` | model一覧取得 |
| `GET` | `/v1/voices` | voice一覧取得 |
| `POST` | `/v1/audio/speech` | OpenAI互換TTS |
| `POST` | `/v1/speech` | Native TTS |

---

## GET /health

サーバーの死活確認。

### Response

```json
{ "status": "ok" }
```

| フィールド | 型 | 常に |
|-----------|-----|------|
| `status` | string | `"ok"` |

---

## GET /v1/models

利用可能なmodel一覧を返す。

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "tts-default",
      "object": "model",
      "display_name": "Default TTS"
    },
    {
      "id": "irodori-base",
      "object": "model",
      "display_name": "Irodori Base"
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `object` | string | 常に `"list"` |
| `data[].id` | string | model識別子 |
| `data[].object` | string | 常に `"model"` |
| `data[].display_name` | string | 表示名 |

---

## GET /v1/voices

利用可能なvoice一覧を返す。OpenAI標準ではなく、tts-adapter独自の運用補助API。

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "your-voice-name",
      "object": "voice",
      "display_name": "your-voice-name",
      "preferred_model": "tts-default"
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `data[].id` | string | voice識別子 |
| `data[].object` | string | 常に `"voice"` |
| `data[].display_name` | string | 表示名 |
| `data[].preferred_model` | string | 推奨model ID |

---

## POST /v1/audio/speech

OpenAI互換クライアント向けのTTS API。完全互換ではなく、必要最小限のsubset。

### Request

```json
{
  "model": "tts-default",
  "voice": "your-voice-name",
  "input": "こんにちは。今日は静かに話します。",
  "response_format": "wav",
  "speed": 1.0
}
```

| フィールド | 型 | 必須 | v0対応 | 説明 |
|-----------|-----|------|--------|------|
| `model` | string | **Yes** | 対応 | model ID。`tts-default` 推奨 |
| `voice` | string | **Yes** | 対応 | voice ID。`voice_id` として解釈 |
| `input` | string | **Yes** | 対応 | 読み上げテキスト。空文字不可 |
| `response_format` | string | No | `wav`のみ | 省略時 `"wav"` |
| `speed` | float | No | `1.0`のみ | 省略時 `1.0` |
| `instructions` | string | No | 非対応 | v0では受け付けない |

### Response (成功)

```
Status: 200
Content-Type: audio/wav
Body: WAVバイナリ
```

### Response (エラー)

| ステータス | code | 発生条件 |
|-----------|------|---------|
| 400 | `unsupported_response_format` | `response_format` が `wav` 以外 |
| 400 | `unsupported_speed` | `speed` が `1.0` 以外 |
| 404 | `model_not_found` | 存在しない `model` |
| 404 | `voice_not_found` | 存在しない `voice` |
| 409 | `voice_binding_not_found` | voiceは存在するが、指定modelのbindingがない |
| 500 | `provider_execution_error` | Provider実行失敗 |
| 504 | `provider_timeout` | Provider timeout |

エラー形式:

```json
{
  "error": {
    "message": "Model not found: unknown",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found"
  }
}
```

---

## POST /v1/speech

自作エージェント向けのNative TTS API。OpenAI互換に縛られない拡張パラメータを利用できる。

### Request

```json
{
  "model": "tts-default",
  "voice_id": "your-voice-name",
  "speech_text": "了解しました。今から調べます。",
  "display_text": "了解しました。今から調べます。",
  "style_hints": {
    "emotion": "gentle",
    "energy": 0.3
  },
  "response_format": "wav"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `model` | string | **Yes** | model ID |
| `voice_id` | string | **Yes** | voice ID |
| `speech_text` | string | **Yes** | TTS生成の正入力。空文字不可 |
| `display_text` | string | No | UI/ログ用の表示テキスト。TTS生成には使わない。省略時 `""` |
| `style_hints` | object | No | Providerが解釈可能な補助情報。未対応なら無視される。省略時 `null` |
| `response_format` | string | No | v0では `wav` のみ。省略時 `"wav"` |

### Response

`POST /v1/audio/speech` と同じ。
