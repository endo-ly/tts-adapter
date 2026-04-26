# 開発ガイド

tts-adapterの開発環境構築、テスト、プロジェクト構成を説明する。

## 目次

1. [開発環境構築](#開発環境構築)
2. [プロジェクト構成](#プロジェクト構成)
3. [テスト](#テスト)
4. [TDD運用](#tdd運用)
5. [コーディング規約](#コーディング規約)

---

## 開発環境構築

```bash
# リポジトリをクローン
git clone <repo-url> && cd tts-adapter

# 依存インストール（uv が .venv を自動管理）
uv sync --group dev

# 設定ファイルをテンプレートからコピー
cp assets/models/models.example.yaml assets/models/models.yaml
cp assets/voices/your-voice-name/profile.example.yaml assets/voices/your-voice-name/profile.yaml

# テスト実行で確認
uv run pytest tests/ -v
```

### 必要ツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Python | 3.12+ | 実行環境 |
| uv | 0.9+ | パッケージ管理・仮想環境管理 |
| pytest | 9+ | テストランナー |
| pytest-asyncio | 1.3+ | 非同期テスト |
| httpx | 0.28+ | AsyncClient（APIテスト） |

---

## プロジェクト構成

```
tts-adapter/
  app/
    api/                     # API層: HTTP入出力
      routes/                #   エンドポイント
        health.py            #     GET /health
        models.py            #     GET /v1/models
        voices.py            #     GET /v1/voices
        openai_speech.py     #     POST /v1/audio/speech
        native_speech.py     #     POST /v1/speech
      schemas/               #   リクエスト/レスポンス定義
        openai_speech.py     #     OpenAISpeechRequest
        native_speech.py     #     NativeSpeechRequest
        error.py             #     ErrorResponse

    application/             # Application層: ユースケース・サービス
      use_cases/
        synthesize_speech.py #     音声合成ユースケース
        list_models.py       #     model一覧取得
        list_voices.py       #     voice一覧取得
      services/
        profile_resolver.py  #     model + voice 解決
        provider_registry.py #     Provider lookup
        option_merger.py     #     5層設定マージ
        error_mapper.py      #     domain error → HTTP

    domain/                  # Domain層: 中核概念（依存なし）
      entities/
        model_profile.py     #     ModelProfile Pydantic model
        voice_profile.py     #     VoiceProfile Pydantic model
      value_objects/
        synthesis_request.py #     ProviderSynthesisRequest
        synthesis_result.py  #     SynthesisResult
      interfaces/
        tts_provider.py      #     TTSProvider Protocol
        *_repository.py      #     Repository Protocol
      errors.py              #     domain error群

    infrastructure/          # Infrastructure層: 実装
      config/
        settings.py          #     pydantic-settings
      repositories/
        yaml_model_*.py      #     YAML読み込み（ModelProfile）
        yaml_voice_*.py      #     YAML読み込み（VoiceProfile）
      providers/
        fake/provider.py     #     テスト用ダミーProvider
        irodori/             #     Irodori CLI subprocess
          provider.py        #       Provider本体（Semaphore付き）
          cli_builder.py     #       CLI引数組み立て
          subprocess_runner.py #     asyncio.create_subprocess_exec
      tempfiles/
        manager.py           #     UUID付きtmpファイル管理
      logging/
        logger.py            #     logging設定

    main.py                  # FastAPI app組み立て・DI

  assets/                    # 設定ファイル（.gitignoreで管理）
    models/
      models.example.yaml    #   テンプレート
      models.yaml            #   実際の設定（gitignore）
    voices/
      your-voice-name/
        profile.example.yaml
        profile.yaml
        ref.wav               #   参照音声（gitignore）
        ref_latent.pt         #   バイナリ（gitignore）

  tests/                     # テストコード
    conftest.py              #   セッションスコープ: .example.yaml → .yaml コピー
    domain/                  #   Domain層テスト（70本）
    infrastructure/          #   Infrastructure層テスト（47本）
    application/             #   Application層テスト（30本）
    api/                     #   API層テスト（25本）
    integration/             #   統合テスト（17本）

  docs/                      # ドキュメント
  tmp/                       # 一時ファイル出力先
  plan.md                    # 設計書
  pyproject.toml             # プロジェクト設定
  .env.example               # 環境変数テンプレート
```

---

## テスト

### 実行コマンド

```bash
# 全テスト
uv run pytest tests/ -v

# 層ごと
uv run pytest tests/domain/ -v
uv run pytest tests/infrastructure/ -v
uv run pytest tests/application/ -v
uv run pytest tests/api/ -v
uv run pytest tests/integration/ -v

# ファイル指定
uv run pytest tests/domain/test_errors.py -v

# 詳細表示
uv run pytest tests/ -v --tb=long
```

### テスト構成

| 層 | テスト数 | 内容 |
|----|---------|------|
| Domain | 70 | Pydantic validation、Protocol適合性、errorのフィールド |
| Infrastructure | 47 | YAML読み込み、FakeProvider、Irodori CLI組み立て、subprocess実行、tmp管理 |
| Application | 30 | 設定マージ、Provider lookup、profile解決、errorマッピング、ユースケース |
| API | 25 | schema validation、エンドポイントのstatus code・content-type |
| Integration | 17 | 受け入れ条件（plan.md §7.3）のEnd-to-End検証 |
| **Total** | **189** | |

### conftest.py

`tests/conftest.py` はセッションスコープのfixtureで、テスト実行前に `.example.yaml` から実際のYAMLファイルを自動生成する。テスト終了後に削除する。

---

## TDD運用

このプロジェクトは **ボトムアップTDD** で開発している。

### サイクル

```
1. テストを書く（Red）
2. 最小実装を書く（Green）
3. リファクタする（Refactor）
```

### 実装順序

```
Domain（依存なし）→ Infrastructure → Application → API → Integration
```

内側の層から先にテスト・実装を固めることで、外側の層のテストは内側のモック・スタブを使わずに書ける。

### 新機能追加時の例

QwenTTSProviderを追加する場合:

1. `tests/infrastructure/qwen_tts/test_provider.py` を書く
2. `app/infrastructure/providers/qwen_tts/provider.py` を実装する
3. テストが通ることを確認する
4. `assets/models/models.yaml` にmodelを追加する
5. 各voiceにbindingを追加する
6. 統合テストで確認する

---

## 管理CLI

WAV→PT変換など、音声合成以外の管理操作はCLIで行う。

```bash
# ref.wav から ref_latent.pt を生成
uv run python -m app.cli voices build-ref-latent \
  --voice-id your-voice-name \
  --model-id irodori-base

# 生成ついでに profile.yaml に ref_latent_path を書き込む
uv run python -m app.cli voices build-ref-latent \
  --voice-id your-voice-name \
  --model-id irodori-base \
  --write-profile

# 一括移行: 全voiceのref.wavをref_latent.ptに変換
uv run python -m app.cli voices materialize-ref-latents \
  --all \
  --model-id irodori-base \
  --write-profile

# 特定voiceだけ一括移行
uv run python -m app.cli voices materialize-ref-latents \
  --voice-id your-voice-name \
  --model-id irodori-base \
  --write-profile
```

## コーディング規約

- **型アノテーション**: 全関数・メソッドに型を付ける。`as any`、`@ts-ignore` 等の型抑制は禁止
- **エラー処理**: `TTSAdapterError` のサブクラスを使う。`except Exception` は避ける
- **YAML**: `safe_load` を使う。読み込み後はPydanticでvalidationする
- **subprocess**: `shell=True` 禁止。`list[str]` で引数を組み立てる
- **非同期**: `async def` を使う。`asyncio.Semaphore` で同時実行数を制限する
- **tmpファイル**: UUID付きで作成し、bytes読み込み後に削除する
- **コメント**: コードが自明であれば書かない。必要な場合のみ（複雑なアルゴリズム、セキュリティ、正規表現等）
