# 拡張ガイド

tts-adapterに新しいProvider、Voice、Modelを追加する手順。

## 目次

1. [Providerの追加](#providerの追加)
2. [Voiceの追加](#voiceの追加)
3. [Modelの追加](#modelの追加)
4. [拡張チェックリスト](#拡張チェックリスト)

---

## Providerの追加

新しいTTSエンジンをProviderとして追加する。

### Step 1: Providerクラスを実装

`app/infrastructure/providers/<provider_name>/provider.py` を作成:

```python
from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult


class QwenTTSProvider:
    provider_name: str = "qwen_tts"

    async def synthesize(
        self, request: ProviderSynthesisRequest
    ) -> SynthesisResult:
        # request.provider_config にProvider固有の設定が入っている
        # request.text に読み上げテキストが入っている
        # 実装...
        return SynthesisResult(audio_bytes=wav_bytes)
```

満たすべき制約:
- `provider_name` 属性を持つ
- `async def synthesize(self, request: ProviderSynthesisRequest) -> SynthesisResult` を実装する
- `SynthesisResult` は `audio_bytes: bytes`, `media_type: "audio/wav"`, `format: "wav"` で返す
- tmpファイルを使う場合は、bytes読み込み後に必ず削除する
- 同時実行数に制限を設ける場合は `asyncio.Semaphore` を使う

### Step 2: main.pyに登録

`app/main.py` の `_provider_registry` に追加:

```python
from app.infrastructure.providers.qwen_tts.provider import QwenTTSProvider

# 既存の登録箇所に追加
_provider_registry.register(QwenTTSProvider())
```

### Step 3: Model Profileを追加

`assets/models/models.yaml` に新しいmodelを追加:

```yaml
models:
  # 既存のmodel...
  - id: qwen-default
    object: model
    display_name: Qwen TTS Default
    provider: qwen_tts        # provider_nameと一致させる
    engine: base
    defaults:
      response_format: wav
      speed: 1.0
      timeout_sec: 120
    provider_config:
      # QwenTTSProviderが必要とする設定
      model_name: Qwen/Qwen2.5-TTS
      device: cuda
```

### Step 4: Voice Profileにbindingを追加

各voiceの `profile.yaml` の `bindings` に新しいmodel用のエントリを追加:

```yaml
bindings:
  # 既存のbinding...
  qwen-default:
    provider_config:
      # QwenTTSProviderが必要とするvoice固有設定
      speaker: "female_01"
      seed: 42
```

### Step 5: テストを追加

1. `tests/infrastructure/qwen_tts/test_provider.py` — Provider単体テスト
2. 既存の統合テストで `qwen-default` + voiceの組み合わせを追加

---

## Voiceの追加

新しい声・人格を追加する。

### Step 1: ディレクトリを作成

```bash
mkdir -p assets/voices/orphe
```

### Step 2: profile.yamlを作成

テンプレートからコピー:

```bash
cp assets/voices/egopulse/profile.example.yaml assets/voices/orphe/profile.yaml
```

内容を編集:

```yaml
voice_id: orphe
display_name: Orphe
description: 落ち着いた男性声

defaults:
  preferred_model: tts-default
  response_format: wav
  speed: 1.0

bindings:
  tts-default:
    provider_config: {}

  irodori-base:
    provider_config:
      ref_latent_path: assets/voices/orphe/ref_latent.pt
      seed: 42
      num_steps: 28
      speaker_kv_scale: 1.0
```

### Step 3: 参照音声を配置

Irodoriを使用する場合、`ref_latent.pt` をディレクトリに配置:

```bash
cp /path/to/orphe_ref_latent.pt assets/voices/orphe/ref_latent.pt
```

### Step 4: 動作確認

```bash
curl -X POST http://127.0.0.1:8012/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-default","voice":"orphe","input":"テスト"}' \
  --output orphe_test.wav
```

---

## Modelの追加

新しいmodelルートを追加する。同じProviderでもパラメータを変えて別ルートとして提供したい場合に使う。

### Step 1: models.yamlにエントリを追加

```yaml
models:
  # 既存...
  - id: irodori-high-quality
    object: model
    display_name: Irodori High Quality
    provider: irodori
    engine: base
    defaults:
      response_format: wav
      speed: 1.0
      timeout_sec: 300    # 高品質なのでタイムアウトを長めに
    provider_config:
      checkpoint: Aratako/Irodori-TTS-500M-v2
      model_device: cuda
      codec_device: cuda
      model_precision: bf16
      codec_precision: bf16
```

### Step 2: 各voiceにbindingを追加

新しいmodel_idに対応するbindingを各voiceの `profile.yaml` に追加する。

### Step 3: 動作確認

```bash
curl http://127.0.0.1:8012/v1/models | jq '.data[] | select(.id=="irodori-high-quality")'
```

---

## 拡張チェックリスト

新規追加時の確認項目。

### Provider追加

- [ ] `TTSProvider` Protocolを満たすクラスを実装した
- [ ] `provider_name` 属性を設定した
- [ ] `synthesize` が `SynthesisResult` を返す
- [ ] tmpファイルを使う場合、bytes読み込み後に削除する
- [ ] `main.py` で `_provider_registry.register()` した
- [ ] 単体テストを書いた
- [ ] 既存テストが全て通る

### Voice追加

- [ ] `assets/voices/<voice_id>/` ディレクトリを作成した
- [ ] `profile.yaml` の `voice_id` がディレクトリ名と一致する
- [ ] 利用する全modelのbindingを定義した
- [ ] 参照音声ファイル（.pt等）を配置した
- [ ] `GET /v1/voices` に表示される
- [ ] `POST /v1/audio/speech` で音声生成できる

### Model追加

- [ ] `models.yaml` にエントリを追加した
- [ ] `provider` が登録済みの `provider_name` と一致する
- [ ] 全voiceにbindingを追加した（またはbindingなしで409を許容する）
- [ ] `GET /v1/models` に表示される
