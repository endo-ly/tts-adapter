# tts-adapter 設計書 v5

## 1. 目的とスコープ

`tts-adapter` は、常駐するTTS APIサーバーである。

外部からはOpenAI互換のTTS APIとして利用でき、内部では複数のTTSエンジンをProviderとして切り替えられる構造にする。

本プロジェクトの目的は次の3つである。

| 目的           | 内容                                      |
| ------------ | --------------------------------------- |
| 固定声の管理       | `voice_id` によって人格声・固定声を管理する             |
| 利用元の統一       | OpenClaw、自作エージェント、その他クライアントが同じAPIで利用できる |
| TTSエンジンの差し替え | Irodoriに固定せず、将来Qwen-TTSなどを追加できる         |

v0では、最初の実Providerとして `IrodoriProvider` を実装する。
ただし、プロジェクト全体はIrodori専用にしない。

### v0でやること

```text
- FastAPIで常駐APIサーバーを作る
- デフォルト待受は 127.0.0.1:8012 とする
- POST /v1/audio/speech を実装する
- POST /v1/speech を実装する
- GET /health を実装する
- GET /v1/models を実装する
- GET /v1/voices を実装する
- model profile をYAMLで管理する
- voice profile をYAMLで管理する
- Provider抽象を作る
- FakeProviderを作る
- IrodoriProviderをCLI subprocess方式で作る
- OpenClawから baseUrl 差し替えで利用できるようにする
```

### v0でやらないこと

```text
- DB導入
- 管理UI
- 音声ストリーミング
- 複雑なジョブキュー
- fine-tune / 学習機能
- 双方向Talk Mode
- 本格的な認証認可
- providerごとの高度な感情制御
```

---

## 2. 基本概念

`tts-adapter` では、次の3つを分離する。

| 概念         | 意味                  | 例                             |
| ---------- | ------------------- | ----------------------------- |
| `voice`    | 論理的な声・人格ID          | `egopulse`, `lira`, `orphe`   |
| `model`    | クライアントが指定するTTSルートID | `tts-default`, `irodori-base` |
| `provider` | 実際に音声生成を行う実装        | `irodori`, `fake`, `qwen_tts` |

重要なのは、**voiceはproviderに固定しない**こと。

たとえば `voice_id = egopulse` は、Irodoriの `ref_latent.pt` そのものではない。
それは「EgoPulseという声」を表す論理IDであり、現在はIrodoriで実現していても、将来別のTTSエンジンで実現してよい。

また、クライアントにはなるべく物理的なTTS実装名を見せない。
そのため、OpenClawや自作エージェントからは原則として `model = tts-default` を使う。

```text
client
  model = tts-default
  voice = egopulse
        ↓
tts-adapter
        ↓
ModelProfile で provider を決定
        ↓
VoiceProfile で voice 固有設定を決定
        ↓
IrodoriProvider などで音声生成
```

---

## 3. API設計

APIの入出力はJSONとする。
設定ファイルはYAMLで管理するが、HTTP APIのrequest / response形式はJSONのままにする。

v0では、APIを次の4種類に分ける。

| 種別       | endpoint                           | 役割                |
| -------- | ---------------------------------- | ----------------- |
| OpenAI互換 | `POST /v1/audio/speech`            | OpenAI互換クライアント向け  |
| Native   | `POST /v1/speech`                  | 自作エージェントなど向け      |
| 一覧       | `GET /v1/models`, `GET /v1/voices` | model / voice の確認 |
| 死活監視     | `GET /health`                      | サーバー起動確認          |

---

### 3.1 OpenAI互換TTS API

#### `POST /v1/audio/speech`

OpenAI互換クライアントから呼ぶためのAPI。
ただし、完全互換ではなく、v0では必要最小限のsubsetとして実装する。

#### request

```json
{
  "model": "tts-default",
  "voice": "egopulse",
  "input": "こんにちは。今日は静かに話します。",
  "response_format": "wav",
  "speed": 1.0
}
```

#### 対応パラメータ

| field             | v0対応 | 備考               |
| ----------------- | ---: | ---------------- |
| `model`           |   対応 | `tts-default` 推奨 |
| `voice`           |   対応 | `voice_id` として解釈 |
| `input`           |   対応 | 読み上げ本文           |
| `response_format` | 一部対応 | v0では `wav` のみ    |
| `speed`           | 一部対応 | v0では `1.0` のみ    |
| `instructions`    |  非対応 | v0では受け付けない       |

#### response

```text
Content-Type: audio/wav
Body: wav binary
```

---

### 3.2 Native Speech API

#### `POST /v1/speech`

自作エージェントなど、OpenAI互換に縛られない利用元向けのAPI。

#### request

```json
{
  "model": "tts-default",
  "voice_id": "egopulse",
  "speech_text": "了解しました。今から調べます。",
  "display_text": "了解しました。今から調べます。",
  "style_hints": {
    "emotion": "gentle",
    "energy": 0.3
  },
  "response_format": "wav"
}
```

#### 意味

| field             | 意味                    |
| ----------------- | --------------------- |
| `model`           | 使用するTTSルートID          |
| `voice_id`        | 論理的な声ID               |
| `speech_text`     | 実際に読み上げるテキスト          |
| `display_text`    | UIやログで使う表示用テキスト       |
| `style_hints`     | Providerが可能なら解釈する補助情報 |
| `response_format` | v0では `wav` のみ         |

`display_text` はTTS生成には使わない。
TTS生成の正入力は `speech_text` である。

`style_hints` は命令ではなくヒントである。
v0では受け取るだけでよい。Providerが未対応なら無視してよい。

---

### 3.3 一覧API

#### `GET /v1/models`

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

#### `GET /v1/voices`

```json
{
  "object": "list",
  "data": [
    {
      "id": "egopulse",
      "object": "voice",
      "display_name": "EgoPulse",
      "preferred_model": "tts-default"
    }
  ]
}
```

`/v1/voices` はOpenAI標準ではなく、`tts-adapter` の運用補助APIである。

---

### 3.4 Health API

#### `GET /health`

```json
{
  "status": "ok"
}
```

v0では軽量な死活監視のみとする。
profileやProvider設定の詳細検査は、必要になった段階で `/health/deep` などを追加する。

---

## 4. Profile設計

Profileは `assets/` 配下でYAML管理する。

```text
assets/
  models/
    models.yaml
  voices/
    egopulse/
      profile.yaml
      ref_latent.pt
    lira/
      profile.yaml
      ref_latent.pt
```

Profile設計の責務は次のように分ける。

| Profile      | 責務                          |
| ------------ | --------------------------- |
| ModelProfile | どのProvider / engineを使うかを決める |
| VoiceProfile | そのmodelでvoiceをどう実現するかを決める   |

Providerやengineの正本は **ModelProfile** とする。
VoiceProfile側にはProviderやengineを重複して持たせない。

---

### 4.1 YAML採用方針

設定ファイルはYAMLで管理する。
理由は、人間が編集しやすく、コメントを書けるためである。

ただし、YAMLの自由度をそのまま許すと事故りやすいため、次の制約を置く。

```text
- 拡張子は .yaml に統一する
- 読み込みは safe_load を使う
- 読み込み後は Pydantic 等で必ずschema validationする
- YAML anchors / aliases などの高度な記法には依存しない
- secrets はYAMLに書かない
- API request / response はJSONのままにする
```

---

### 4.2 ModelProfile

#### `assets/models/models.yaml`

```yaml
models:
  - id: tts-default
    object: model
    display_name: Default TTS
    provider: irodori
    engine: base
    actual_model: irodori-base
    defaults:
      response_format: wav
      speed: 1.0
      timeout_sec: 120
    provider_config:
      checkpoint: Aratako/Irodori-TTS-500M-v2
      model_device: cuda
      codec_device: cuda
      model_precision: bf16
      codec_precision: bf16

  - id: irodori-base
    object: model
    display_name: Irodori Base
    provider: irodori
    engine: base
    defaults:
      response_format: wav
      speed: 1.0
      timeout_sec: 120
    provider_config:
      checkpoint: Aratako/Irodori-TTS-500M-v2
      model_device: cuda
      codec_device: cuda
      model_precision: bf16
      codec_precision: bf16

  - id: irodori-voicedesign
    object: model
    display_name: Irodori VoiceDesign
    provider: irodori
    engine: voicedesign
    defaults:
      response_format: wav
      speed: 1.0
      timeout_sec: 120
    provider_config:
      checkpoint: Aratako/Irodori-TTS-500M-v2-VoiceDesign
      model_device: cuda
      codec_device: cuda
      model_precision: bf16
      codec_precision: bf16
```

`model` は、クライアントから指定されるTTSルートIDである。
`provider` と `engine` はこのModelProfile側を正とする。

---

### 4.3 VoiceProfile

#### `assets/voices/egopulse/profile.yaml`

```yaml
voice_id: egopulse
display_name: EgoPulse
description: 静かで知的、近い距離感の男性声

defaults:
  preferred_model: tts-default
  response_format: wav
  speed: 1.0

bindings:
  tts-default:
    provider_config:
      ref_latent_path: assets/voices/egopulse/ref_latent.pt
      seed: 42
      num_steps: 28
      speaker_kv_scale: 1.1

  irodori-base:
    provider_config:
      ref_latent_path: assets/voices/egopulse/ref_latent.pt
      seed: 42
      num_steps: 28
      speaker_kv_scale: 1.1

  irodori-voicedesign:
    provider_config:
      caption: 20代前半の男性。落ち着いていて知的だがやわらかい。距離感は近め。
      seed: 42
      num_steps: 28
```

`bindings` のkeyは `model_id` である。

```yaml
bindings:
  tts-default:
    provider_config: {}
```

`provider_config` の中身はProvider固有である。
Application層は中身を基本的に解釈しない。
解釈するのはProviderである。

---

### 4.4 設定マージ規則

音声生成時の設定は、次の順で組み立てる。

```text
1. ModelProfile.defaults
2. VoiceProfile.defaults
3. ModelProfile.provider_config
4. VoiceProfile.bindings[model].provider_config
5. request options
```

IrodoriProviderに渡る最終設定例。

```yaml
checkpoint: Aratako/Irodori-TTS-500M-v2
model_device: cuda
codec_device: cuda
model_precision: bf16
codec_precision: bf16
ref_latent_path: assets/voices/egopulse/ref_latent.pt
seed: 42
num_steps: 28
speaker_kv_scale: 1.1
```

---

## 5. Provider設計

Providerは、実際のTTSエンジンを呼び出す実装単位である。

v0では次の2つを用意する。

| Provider          | 役割                                   |
| ----------------- | ------------------------------------ |
| `FakeProvider`    | API・profile解決・エラー処理を先に固めるためのダミー      |
| `IrodoriProvider` | 実際にIrodori CLIを呼び出してwavを生成するProvider |

---

### 5.1 Provider interface

```python
from typing import Protocol

class TTSProvider(Protocol):
    provider_name: str

    async def synthesize(
        self,
        request: "ProviderSynthesisRequest"
    ) -> "SynthesisResult":
        ...
```

---

### 5.2 ProviderSynthesisRequest

```python
from pydantic import BaseModel, Field
from typing import Any, Literal

class ProviderSynthesisRequest(BaseModel):
    model_id: str
    voice_id: str
    text: str = Field(min_length=1)
    response_format: Literal["wav"] = "wav"
    speed: float = 1.0
    provider: str
    engine: str
    provider_config: dict[str, Any]
```

---

### 5.3 SynthesisResult

v0では、Providerは音声データをbytesで返す。

```python
from pydantic import BaseModel
from typing import Literal

class SynthesisResult(BaseModel):
    audio_bytes: bytes
    media_type: Literal["audio/wav"] = "audio/wav"
    format: Literal["wav"] = "wav"
```

`FileResponse` ではなくbytes返却を基本にする。
理由は、tmp wavを安全に削除しやすいからである。

---

### 5.4 IrodoriProvider

IrodoriProviderはCLI subprocess方式で実装する。

最低限、次を守る。

```text
- shell=True を使わない
- command は list[str] で組み立てる
- timeout を設定する
- stdout / stderr を捕捉する
- exit code を確認する
- output wav の存在を確認する
- output wav のサイズが0でないことを確認する
- 同時生成数は1に制限する
- tmp wav はuuid付きで作成する
- wavをbytesで読んだ後にtmp wavを削除する
```

#### base engine 実行イメージ

```bash
uv run python infer.py \
  --hf-checkpoint Aratako/Irodori-TTS-500M-v2 \
  --text "こんにちは" \
  --ref-latent assets/voices/egopulse/ref_latent.pt \
  --output-wav tmp/out-uuid.wav \
  --num-steps 28 \
  --seed 42 \
  --speaker-kv-scale 1.1 \
  --model-device cuda \
  --codec-device cuda \
  --model-precision bf16 \
  --codec-precision bf16
```

#### voicedesign engine 実行イメージ

```bash
uv run python infer.py \
  --hf-checkpoint Aratako/Irodori-TTS-500M-v2-VoiceDesign \
  --text "こんにちは" \
  --caption "20代前半の男性。落ち着いていて知的だがやわらかい。" \
  --no-ref \
  --output-wav tmp/out-uuid.wav \
  --num-steps 28 \
  --seed 42 \
  --model-device cuda \
  --codec-device cuda \
  --model-precision bf16 \
  --codec-precision bf16
```

---

## 6. 実装構成

ディレクトリ構成は `app/` ベースにする。

```text
tts-adapter/
  app/
    api/
      routes/
        health.py
        models.py
        voices.py
        openai_speech.py
        native_speech.py
      schemas/
        openai_speech.py
        native_speech.py
        error.py

    application/
      use_cases/
        synthesize_speech.py
        list_models.py
        list_voices.py
      services/
        profile_resolver.py
        provider_registry.py
        option_merger.py
        error_mapper.py

    domain/
      entities/
        model_profile.py
        voice_profile.py
      value_objects/
        synthesis_request.py
        synthesis_result.py
      interfaces/
        tts_provider.py
        model_profile_repository.py
        voice_profile_repository.py
      errors.py

    infrastructure/
      config/
        settings.py
      repositories/
        yaml_model_profile_repository.py
        yaml_voice_profile_repository.py
      providers/
        fake/
          provider.py
        irodori/
          provider.py
          cli_builder.py
          subprocess_runner.py
      tempfiles/
        manager.py
      logging/
        logger.py

    main.py

  assets/
    models/
      models.yaml
    voices/
      egopulse/
        profile.yaml
        ref_latent.pt

  tests/
    api/
    application/
    domain/
    infrastructure/

  tmp/
  README.md
  pyproject.toml
  .env.example
```

---

### 6.1 責務分離

| 層                | 責務                                   |
| ---------------- | ------------------------------------ |
| `api`            | HTTP入出力、schema、status code           |
| `application`    | model/voice解決、Provider選択、設定マージ       |
| `domain`         | 中核概念、interface、domain error          |
| `infrastructure` | YAML読み込み、Provider実装、subprocess、tmp管理 |

API層にProvider選択ロジックを書かない。
Infrastructure層にHTTP requestの都合を書かない。

---

### 6.2 最小環境変数

環境変数は必要最低限にする。

```env
IRODORI_REPO_DIR=/path/to/irodori
```

それ以外はv0ではデフォルト固定でよい。

```text
host = 127.0.0.1
port = 8012
assets_dir = ./assets
tmp_dir = ./tmp
timeout_sec = 120
max_concurrency = 1
```

将来必要になった場合だけ、環境変数として外に出す。

---

### 6.3 起動イメージ

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8012
```

OpenClaw側の接続例。

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

---

## 7. エラー設計と受け入れ条件

### 7.1 エラー設計

| status | 条件                             |
| -----: | ------------------------------ |
|    400 | request値が仕様違反                  |
|    404 | model または voice が存在しない         |
|    409 | voiceは存在するが、指定modelのbindingがない |
|    500 | Provider実行失敗                   |
|    504 | Provider timeout               |

エラー形式はOpenAI互換クライアントを意識して、以下に寄せる。

```json
{
  "error": {
    "message": "Voice 'egopulse' does not support model 'qwen-tts-default'",
    "type": "invalid_request_error",
    "param": "voice",
    "code": "voice_binding_not_found"
  }
}
```

---

### 7.2 主なdomain error

```text
ModelNotFoundError
VoiceNotFoundError
VoiceBindingNotFoundError
UnsupportedResponseFormatError
UnsupportedSpeedError
ProviderNotFoundError
ProviderExecutionError
ProviderTimeoutError
InvalidProfileError
```

---

### 7.3 v0受け入れ条件

```text
1. uvicorn app.main:app --host 127.0.0.1 --port 8012 で起動できる
2. GET /health が 200 を返す
3. GET /v1/models が model 一覧を返す
4. GET /v1/voices が voice 一覧を返す
5. POST /v1/audio/speech が audio/wav を返す
6. POST /v1/speech が audio/wav を返す
7. model=tts-default が使える
8. voice=egopulse が使える
9. 存在しないmodelは404になる
10. 存在しないvoiceは404になる
11. voiceはあるがmodel bindingがない場合は409になる
12. response_format=wav のみ許可される
13. speed=1.0 のみ許可される
14. IrodoriProviderがsubprocessで実行される
15. shell=True を使っていない
16. subprocess timeout が機能する
17. 同時生成数が1に制限される
18. tmp wav が生成後に削除される
19. YAML profile は safe_load + schema validation される
20. OpenClawから baseUrl 差し替えで呼べる
21. 将来QwenTTSProviderを追加できる構造になっている
```

---

# Appendix: 実装指示文

```text
tts-adapter v5を実装する。

目的:
- tts-adapterは常駐TTS APIサーバーである
- Irodori専用ではなく、複数TTS Providerを扱うアダプタ層として作る
- v0では最初の実ProviderとしてIrodoriProviderを実装する
- OpenAI互換APIは完全互換ではなく、必要最小限のsubsetとする

構成:
- Python + FastAPI
- app/ ベースのディレクトリ構成
- assets/models/models.yaml でmodel profileを管理する
- assets/voices/<voice_id>/profile.yaml でvoice profileを管理する
- 設定ファイルはYAML、API入出力はJSONとする
- デフォルト待受は 127.0.0.1:8012 とする

必須API:
- GET /health
- GET /v1/models
- GET /v1/voices
- POST /v1/audio/speech
- POST /v1/speech

重要な概念:
- voice は logical voice_id
- model はクライアント向けTTSルートID
- provider は実際のTTS実装
- provider / engine は ModelProfile 側を正とする
- VoiceProfile の bindings は model_id ごとの provider_config のみ持つ
- Irodori固有項目は provider_config に閉じ込める
- model は tts-default を用意する
- OpenClawには model=tts-default を渡す

YAML:
- 拡張子は .yaml に統一する
- safe_load を使う
- 読み込み後は Pydantic 等でschema validationする
- YAML anchors / aliases などの高度な記法には依存しない
- secrets はYAMLに書かない

OpenAI互換API:
- POST /v1/audio/speech
- model, voice, input, response_format, speed のみ対応
- response_format は wav のみ
- speed は 1.0 のみ
- instructions は v0では受け付けない
- response は audio/wav

Native API:
- POST /v1/speech
- speech_text をTTS生成の正入力とする
- display_text はUI/trace用の補助情報
- style_hints はProviderが可能な範囲で解釈するヒント
- v0ではstyle_hintsは受け取るだけでよい

Provider:
- TTSProvider interfaceを作る
- FakeProviderを先に実装する
- IrodoriProviderはCLI subprocess方式
- shell=Trueは禁止
- commandはlist[str]で組み立てる
- timeoutを設定する
- stdout/stderrを捕捉する
- exit codeを検査する
- output wavの存在とサイズを検査する
- 同時生成数は1に制限する

tmp file:
- uuid付きtmp wav pathを発行する
- subprocess完了後にwavをbytesで読む
- bytes化後にtmp wavを削除する
- v0ではFileResponseではなくbytes返却を基本とする

環境変数:
- IRODORI_REPO_DIR のみ必須
- host, port, assets_dir, tmp_dir, timeout_sec, max_concurrency はv0ではデフォルト固定でよい

完了条件:
- uvicorn app.main:app --host 127.0.0.1 --port 8012 で起動できる
- /health が返る
- /v1/models と /v1/voices が返る
- /v1/audio/speech が wav を返る
- /v1/speech が wav を返る
- model=tts-default, voice=egopulse で生成できる
- YAML profile が safe_load + schema validation される
- OpenClawのbaseUrl差し替えで利用できる
- 将来QwenTTSProviderを追加できる構造になっている
```
