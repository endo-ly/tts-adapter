# tts-adapter 実装計画書

## 目的

**WAV 参照で即運用できるようにしつつ、最終的には PT（ref_latent）運用へ自然に移行する**ことです。
つまり、

1. **WAV でも voice を定義できる**
2. **WAV → PT 変換を adapter 側で実行できる**
3. **本番は PT 優先で運用できる**

の3段階です。現行 repo の profile / provider / use case 構造を活かし、公開 API はできるだけ増やさず、管理操作は adapter 側の管理コマンドに寄せます。これは、現在の公開 API が synth 系に絞られていることと整合します。 ([GitHub][2])

---

## 全体方針

外部クライアントから見える契約は、なるべく変えません。
つまり **`POST /v1/audio/speech` と `POST /v1/speech` はそのまま**にし、**voice の内部実装だけを拡張**します。公開 API を増やさずに済むので、OpenClaw や自作エージェントとの接続層も壊れません。 ([GitHub][2])

内部では、Base binding に **`ref_wav_path`** を追加し、**`ref_latent_path` があればそれを優先、なければ `ref_wav_path` を使う**、という解決順にします。これで、**WAV で onboarding → PT に昇格 → PT 優先本番運用**が一本の道になります。現行 docs では Base binding は `ref_latent_path` 前提なので、ここを後方互換を壊さず広げるのがポイントです。 ([GitHub][3])

---

# Phase 1: WAV 対応

## 目的

**Base voice を `ref_wav_path` でも定義できるようにする**ことです。
これで、今もう安定している `lira_ref_01.wav` をそのまま本番候補として使えます。現行 docs では Base binding は `ref_latent_path` 前提ですが、repo の設計原則上、VoiceProfile は provider を持たず **model ごとの provider_config を持つだけ**なので、ここに `ref_wav_path` を追加する拡張は自然です。 ([GitHub][3])

## やること

### 1. Voice binding スキーマ拡張

Base 用 `provider_config` に次を追加します。

```yaml
ref_wav_path: string   # 追加
ref_latent_path: string  # 既存
seed: int
num_steps: int
speaker_kv_scale: float
```

ルールはこうします。

* `ref_latent_path` があれば **最優先**
* `ref_latent_path` がなく `ref_wav_path` があれば **WAV 参照運用**
* どちらもなければ **設定エラー**

この順にすると、**後方互換を壊さず**、しかも将来の PT 移行も滑らかです。現行 config docs では `provider_config` は Provider 側にそのまま渡す前提なので、Application 層の責務も崩れません。 ([GitHub][3])

### 2. Irodori CLI builder 拡張

`IrodoriCliBuilder` で Base engine の引数組み立てを拡張します。

* `ref_latent_path` がある → `--ref-latent ...`
* ないが `ref_wav_path` がある → `--ref-wav ...`

Irodori 側は `--ref-wav` と `--ref-latent` の両方を想定しているため、adapter はその切り替えを吸収するだけでよいです。現在の repo でも IrodoriProvider は CLI command を組み立てて subprocess 実行する責務なので、この変更は Infrastructure 層に綺麗に収まります。 ([GitHub][4])

### 3. ドキュメント更新

更新対象は最低でも次です。

* `README.md`
* `docs/configuration.md`
* `assets/voices/*/profile.example.yaml`

ここで **「Base binding は `ref_latent_path` 推奨だが、v1 では `ref_wav_path` にも対応する」** と明記します。現状の設定ガイドと README は onboarding の入口になっているので、ここを先に変える価値が高いです。 ([GitHub][1])

### 4. テスト追加

最低限、次のテストを入れます。

* `ref_latent_path` のみ → 成功
* `ref_wav_path` のみ → 成功
* 両方あり → `ref_latent_path` 優先
* どちらもなし → validation error / config error

repo の extension guide でも、Provider 追加や Voice 追加時には **単体テスト** が前提になっているので、この方針に沿います。 ([GitHub][5])

## 変更対象ファイルの目安

* `app/domain/...` の provider config schema / entity validation
* `app/infrastructure/providers/irodori/...` の CLI builder
* `docs/configuration.md`
* `assets/voices/.../profile.example.yaml`
* `tests/...`

## Done の基準

* `voice profile` に `ref_wav_path` を書いた Base voice で `POST /v1/audio/speech` が成功する
* `GET /v1/voices` / `GET /v1/models` / API 契約に変更がない
* 既存の `ref_latent_path` voice が壊れない ([GitHub][2])

---

# Phase 2: WAV → PT 変換対応

## 目的

**adapter 側が voice onboarding の一工程として `ref.wav` から `ref_latent.pt` を作れるようにする**ことです。
ここが、repo を「単なる synth server」から「固定 voice 運用サーバ」へ押し上げるコアです。現行 repo は Irodori 実行先として `IRODORI_REPO_DIR` を持ち、IrodoriProvider はそのリポジトリを cwd にして `uv run python infer.py` を叩く設計なので、この依存関係を再利用するのが自然です。 ([GitHub][3])

## なぜ HTTP ではなく管理コマンドか

これは **公開 API にしない方がよい**です。
理由は、変換はユーザーの通常推論リクエストではなく、**voice 登録時の管理操作**だからです。現在の公開 API も synth 系に絞られているので、ここへ `/admin/...` を足すより、まずは管理 CLI として切るほうが repo の温度感に合います。 ([GitHub][2])

## やること

### 1. 管理コマンド追加

たとえばこういうコマンドにします。

```bash
uv run python -m app.cli voices build-ref-latent \
  --voice-id lira \
  --model-id tts-default
```

または、もう少し露骨に

```bash
uv run python -m app.cli irodori build-ref-latent \
  --input-wav assets/voices/lira/ref.wav \
  --output-pt assets/voices/lira/ref_latent.pt \
  --checkpoint Aratako/Irodori-TTS-500M-v2
```

でも構いません。
ただ、repo の思想に合わせるなら **voice_id / model_id を渡して profile 解決させる**方がきれいです。repo では model/voice 解決と 5 層マージが Application 層の責務なので、それを使い回した方が一貫します。 ([GitHub][4])

### 2. 変換用 bridge 実装

実装イメージはこうです。

* adapter 側が `voice_id` と `model_id` を解決
* `checkpoint` と `ref_wav_path` を取得
* `IRODORI_REPO_DIR` を使って、**Irodori 環境で動く bridge script** を呼ぶ
* bridge script が wav を読み、latent tensor を `.pt` として保存

ここで大事なのは、**adapter 側が Irodori の依存を二重に持たない**ことです。
すでに repo は Irodori を subprocess で使う設計なので、変換も同じ方針に寄せた方が依存管理が単純です。現在の IrodoriProvider も subprocess 実行が中心です。 ([GitHub][4])

### 3. profile 更新の扱い

このコマンドは、まず **非破壊** がよいです。

つまり第一段階では

* `ref_latent.pt` を生成するだけ
* profile は自動で書き換えない

にします。

そのうえでオプションで

```bash
--write-profile
```

を付けた時だけ、`profile.yaml` に `ref_latent_path` を追加する。
この方が安全です。voice 周りは壊すと面倒なので、初期段階では「生成」と「採用」を分けるのがよいです。

### 4. profile 例

Phase 2 完了後の voice profile はこうなります。

```yaml
voice_id: lira
display_name: Lira
description: クーデレ感を残した、やや低めで静かな女性声

defaults:
  preferred_model: tts-default
  response_format: wav
  speed: 1.0

bindings:
  tts-default:
    provider_config:
      ref_wav_path: assets/voices/lira/ref.wav
      ref_latent_path: assets/voices/lira/ref_latent.pt
      seed: 42
      num_steps: 32
      speaker_kv_scale: 1.1
```

この形にしておけば、**PT があれば PT、なければ WAV** という運用ができます。
つまり、ここで初めて **移行可能な voice profile** になります。現行 docs では binding は model_id ごとの provider_config を持つ形なので、この拡張はその枠内です。 ([GitHub][3])

## 変更対象ファイルの目安

* `app/application/...` の管理ユースケース
* `app/infrastructure/providers/irodori/...` に bridge 呼び出し
* `app/cli/...` の新設
* `docs/development.md` または `docs/configuration.md` に運用手順
* `tests/...`

## Done の基準

* `ref_wav_path` を持つ voice から `.pt` が生成できる
* 生成された `.pt` を profile に設定すると、以後の synth が PT 経由で成功する
* `--write-profile` なしでは profile を壊さない

---

# Phase 3: PT 優先運用への移行

## 目的

**本番運用では PT を優先し、WAV は onboarding / fallback にする**ことです。
ここまで来ると、repo の current design とかなり綺麗に一致します。現行 docs でも Base binding の中核は `ref_latent_path` ですし、voice 追加チェックリストでも **参照音声ファイル（.pt 等）を配置する**前提になっています。 ([GitHub][3])

## やること

### 1. 優先順位を明文化

runtime の実装と docs の両方で、次を明文化します。

* `ref_latent_path` が存在し読める → **本番はこちら**
* ない場合のみ `ref_wav_path` へフォールバック
* 両方なければエラー

これで **運用ポリシー** がぶれません。

### 2. 一括移行コマンド

後で voice が増えた時のために、まとめて latent 化できる管理コマンドを用意しておくと便利です。

```bash
uv run python -m app.cli voices materialize-ref-latents --all
```

または

```bash
uv run python -m app.cli voices materialize-ref-latents --voice-id lira --voice-id orphe
```

のような形です。
repo には `assets/voices/<voice_id>/profile.yaml` という voice ディレクトリ構造があるので、バッチ処理とも相性がよいです。 ([GitHub][3])

### 3. OpenClaw / 自作エージェント側は変更なし

ここは計画上かなり良い点です。
公開 API は `POST /v1/audio/speech` / `POST /v1/speech` のままなので、**接続先は変わらず、voice の内部実装だけが WAV から PT 優先に変わる**だけです。OpenClaw も README の通り `baseUrl` 差し替えで使う構成なので、クライアント側の変更は不要です。 ([GitHub][1])

## Done の基準

* PT がある voice は常に PT 優先で動く
* WAV onboarding voice も引き続き動く
* OpenClaw / 自作エージェントのリクエスト形式に変更がない
* docs に「onboarding は WAV、production は PT」が明記される

---

# 実装順序のおすすめ

ここはこの順で進めるのが最短です。

## Step 1

**Phase 1 を先に入れる**
理由は、今もう持っている `lira_ref_01.wav` で本番に近い運用がすぐできるからです。
ここが通ると、repo 全体の骨格がほぼ確定します。

## Step 2

**Phase 2 の CLI を作る**
まず `voice_id` 1件だけを latent 化できれば十分です。
一括移行は後回しでよいです。

## Step 3

**Phase 3 の優先順位固定と docs 仕上げ**
最後に運用ポリシーを docs とコードで揃えます。

---

# リスクと対策

一番大きいリスクは、**Irodori の内部 latent 生成処理をどの粒度で呼ぶか**です。
今の repo は synth を CLI subprocess に寄せていますが、latent 生成も同じ方針に揃えた方が依存管理は綺麗です。Irodori の実行先は `IRODORI_REPO_DIR` で外出しされているので、その repo 環境で bridge script を動かす形が一番安全です。 ([GitHub][3])

次のリスクは、**profile を自動書き換えして事故ること**です。
これは、最初は `--write-profile` を明示 opt-in にすればかなり防げます。

---

# この計画で最初に着手する具体作業

最初の1本目はこれで十分です。

1. `docs/configuration.md` の Base binding に `ref_wav_path` を追加
2. Voice schema / validation に `ref_wav_path` を追加
3. `IrodoriCliBuilder` に `--ref-wav` 分岐を追加
4. `assets/voices/lira/profile.yaml` を WAV 版で通す
5. `POST /v1/audio/speech` で Lira が喋るところまで確認
6. そのあと `build-ref-latent` CLI を追加する

---

# ひとことでまとめると

この repo では、

**Phase 1: WAV で今すぐ使えるようにする**
**Phase 2: adapter 側に WAV→PT の管理コマンドを追加する**
**Phase 3: 本番は PT 優先、WAV は onboarding / fallback にする**

この3段階がいちばん綺麗で、repo の設計思想とも衝突しません。
特に今の `tts-adapter` は **profile 解決・5層マージ・provider subprocess** という骨格がすでに整っているので、やるべきことは「作り直し」ではなく **voice 運用の導線を継ぎ足すこと**です。 ([GitHub][4])

