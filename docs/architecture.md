# アーキテクチャ

tts-adapterの内部構造を説明する。

## 設計原則

1. **voiceはProviderに固定しない** — `voice_id` は論理的な声のIDであり、特定のTTSエンジンに紐付かない
2. **Provider / engineはModelProfileが正** — VoiceProfile側にProvider情報を重複して持たせない
3. **層をまたぐ依存は下向きのみ** — API→Application→Domain←Infrastructure。逆方向の依存はない

## レイヤー構成

```
┌─────────────────────────────────┐
│  API層 (app/api/)               │  HTTP入出力、status code
│  routes / schemas               │
├─────────────────────────────────┤
│  Application層 (app/application/)│  ユースケース、プロファイル解決、設定マージ
│  use_cases / services           │
├─────────────────────────────────┤
│  Domain層 (app/domain/)         │  中核概念、interface、domain error
│  entities / value_objects /     │
│  interfaces / errors            │
├─────────────────────────────────┤
│  Infrastructure層               │  YAML読み込み、Provider実装、subprocess
│  (app/infrastructure/)          │
│  config / repositories /        │
│  providers / tempfiles          │
└─────────────────────────────────┘
```

各層の責務:

| 層 | 責務 | 依存方向 |
|---|------|---------|
| API | HTTPリクエスト/レスポンス、schema validation、status code決定 | → Application |
| Application | model/voice解決、Provider選択、設定マージ、ユースケース実行 | → Domain |
| Domain | 中核概念（ModelProfile, VoiceProfile, SynthesisRequest等）、Protocol定義、domain error | 依存なし |
| Infrastructure | YAML読み込み、Provider実装、subprocess実行、tmp管理 | → Domain（interfaceを実装） |

API層にProvider選択ロジックを書かない。Infrastructure層にHTTPリクエストの都合を書かない。

## データフロー

```
client
  │ model=tts-default, voice=your-voice-name
  ▼
API層 (routes/openai_speech.py)
  │ requestをschemaでvalidation
  ▼
Application層 (use_cases/synthesize_speech.py)
  │
  ├─ ProfileResolver.resolve(model_id, voice_id)
  │   ├─ ModelProfileRepository.get_by_id() → ModelProfile
  │   ├─ VoiceProfileRepository.get_by_id() → VoiceProfile
  │   ├─ VoiceBinding の存在確認
  │   └─ OptionMerger.merge(5層の設定) → merged config
  │
  ├─ ProviderRegistry.get(provider_name) → TTSProvider
  │
  └─ provider.synthesize(ProviderSynthesisRequest) → SynthesisResult
      │
      ▼
Infrastructure層 (IrodoriProvider 等)
  │ CLI command組み立て → subprocess実行 → tmp wav読み込み → bytes返却
  ▼
API層
  │ Response(content=audio_bytes, media_type=audio/wav)
  ▼
client
```

## 主要クラス

### Domain

| クラス | 役割 |
|--------|------|
| `ModelProfile` | model定義（id, provider, engine, defaults, provider_config） |
| `VoiceProfile` | voice定義（voice_id, display_name, bindings） |
| `VoiceBinding` | model_idごとのprovider_config |
| `ProviderSynthesisRequest` | Providerへの入力（text, config, format等） |
| `SynthesisResult` | Providerからの出力（audio_bytes, media_type） |
| `TTSAdapterError` | 全domain errorの基底クラス |

### Application

| クラス | 役割 |
|--------|------|
| `ProfileResolver` | model + voiceの解決、binding存在確認、設定マージ |
| `OptionMerger` | 5層の設定を優先度順にマージ |
| `ProviderRegistry` | provider_name → TTSProviderのlookup |
| `ErrorMapper` | domain error → HTTP status + OpenAI互換error body |
| `SynthesizeSpeech` | 音声合成ユースケース（validation → resolve → dispatch） |

### Infrastructure

| クラス | 役割 |
|--------|------|
| `YamlModelProfileRepository` | models.yamlの読み込み（safe_load + Pydantic validation、キャッシュ付き） |
| `YamlVoiceProfileRepository` | voices/*/profile.yamlの読み込み |
| `IrodoriProvider` | Irodori CLI subprocess実行（Semaphore=1、tmp管理） |
| `IrodoriCliBuilder` | engine種別に応じたCLI引数のlist[str]組み立て |
| `SubprocessRunner` | asyncio.create_subprocess_execのラッパー（timeout、exit code、stderr捕捉） |
| `TempFileManager` | uuid付きtmp wavパスの発行と削除 |
| `FakeProvider` | テスト・開発用のダミーProvider（最小有効WAVを返す） |

## エラー設計

domain errorは `TTSAdapterError` を継承し、Application層の `ErrorMapper` がHTTPステータスに変換する。

```
TTSAdapterError
├── ModelNotFoundError          → 404
├── VoiceNotFoundError          → 404
├── VoiceBindingNotFoundError   → 409
├── UnsupportedResponseFormatError → 400
├── UnsupportedSpeedError       → 400
├── ProviderNotFoundError       → 500
├── ProviderExecutionError      → 500
├── ProviderTimeoutError        → 504
└── InvalidProfileError         → 500
```

エラー形式はOpenAI互換:

```json
{
  "error": {
    "message": "Voice 'your-voice-name' does not support model 'qwen-tts'",
    "type": "invalid_request_error",
    "param": "voice",
    "code": "voice_binding_not_found"
  }
}
```
