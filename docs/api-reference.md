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
      "id": "tts-fake",
      "object": "model",
      "display_name": "Fake TTS"
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
  "input": "こんにちは。今日は静かに話します。"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `model` | string | **Yes** | model ID |
| `voice` | string | **Yes** | voice ID |
| `input` | string | **Yes** | 読み上げテキスト。空文字不可 |
| `response_format` | string | No | v0では `wav` のみ。省略時 `"wav"` |
| `speed` | float | No | v0では `1.0` のみ。省略時 `1.0` |

> **Note**: OpenAI APIの `instructions` はv0未対応。送信するとバリデーションエラーになる。

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
  "speech_text": "了解しました。今から調べます。"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `model` | string | **Yes** | model ID |
| `voice_id` | string | **Yes** | voice ID |
| `speech_text` | string | **Yes** | 読み上げテキスト。空文字不可。Irodoriでは絵文字によるスタイル制御に対応 |
| `response_format` | string | No | v0では `wav` のみ。省略時 `"wav"` |
| `style_hints` | object | No | **予約**。将来Providerが解釈可能な補助情報。v0では未使用。省略時 `null` |

### Response

`POST /v1/audio/speech` と同じ。

---

## プロバイダー対応状況

各エンドポイントのパラメータが、現在対応しているProviderでどう扱われるか。

### POST /v1/audio/speech

| パラメータ | Irodori (base) | Irodori (voicedesign) |
|-----------|---------------|----------------------|
| `model` | ✅ ModelProfile解決に使用 | ✅ ModelProfile解決に使用 |
| `voice` | ✅ VoiceProfile解決に使用 | ✅ VoiceProfile解決に使用 |
| `input` | ✅ `--text` に渡す | ✅ `--text` に渡す |
| `response_format` | `wav` のみ対応 | `wav` のみ対応 |
| `speed` | `1.0` のみ対応 | `1.0` のみ対応 |

### POST /v1/speech

| パラメータ | Irodori (base) | Irodori (voicedesign) |
|-----------|---------------|----------------------|
| `model` | ✅ ModelProfile解決に使用 | ✅ ModelProfile解決に使用 |
| `voice_id` | ✅ VoiceProfile解決に使用 | ✅ VoiceProfile解決に使用 |
| `speech_text` | ✅ `--text` に渡す | ✅ `--text` に渡す |
| `response_format` | `wav` のみ対応 | `wav` のみ対応 |
| `style_hints` | ⏭ v0では未使用（将来: Providerが解釈） | ⏭ v0では未使用（将来: Providerが解釈） |

### YAML設定経由のIrodori固有パラメータ

APIのリクエストパラメータではなく、YAMLプロファイル（`models.yaml` / `profile.yaml`）の `provider_config` で制御するIrodori固有の設定。

| 設定キー | engine | 出処 | Irodori CLI引数 |
|---------|--------|------|----------------|
| `checkpoint` | base / voicedesign | ModelProfile | `--hf-checkpoint` |
| `model_device` | base / voicedesign | ModelProfile | `--model-device` |
| `codec_device` | base / voicedesign | ModelProfile | `--codec-device` |
| `model_precision` | base / voicedesign | ModelProfile | `--model-precision` |
| `codec_precision` | base / voicedesign | ModelProfile | `--codec-precision` |
| `ref_latent_path` | base | VoiceBinding | `--ref-latent` |
| `ref_wav_path` | base | VoiceBinding | `--ref-wav` |
| `caption` | voicedesign | VoiceBinding | `--caption` |
| `num_steps` | base / voicedesign | VoiceBinding | `--num-steps` |
| `seed` | base / voicedesign | VoiceBinding | `--seed` |
| `max_text_len` | base / voicedesign | ModelProfile / VoiceBinding | `--max-text-len` |
| `max_caption_len` | base / voicedesign | ModelProfile / VoiceBinding | `--max-caption-len` |
| `speaker_kv_scale` | base | VoiceBinding | `--speaker-kv-scale` |

> 詳細は [プロバイダー: Irodori](providers/irodori.md) を参照。
