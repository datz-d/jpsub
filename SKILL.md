---
name: jpsub
description: 動画を書き起こして日本語字幕+下部黒グラデを焼き込む。海外の動画クリップに洋画風のJP字幕を付けたいときに使う
---

# jpsub: 日本語字幕焼き込みパイプライン

動画 → whisper書き起こし → Claude翻訳(cues.json) → 透過PNG字幕 → 黒グラデと共にffmpeg焼き込み。
洋画字幕風のスタイル(白文字+多重黒シャドウ、下端配置)。

## ワークフロー

作業フォルダは `<動画のある場所>/<動画名>_jpsub/` を作り、そこに全成果物を置く。

### 1. プローブ

```
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 <video>
```

W, H, 尺を控える。以後のコマンドは全てこのW/Hを渡す。

### 2. 書き起こし

```
bash ~/.claude/skills/jpsub/scripts/transcribe.sh <video> <workdir> [model]
```

モデルはデフォルト `turbo`。精度が要る長尺は `large-v3`。出力srt/jsonを読む。

### 3. 翻訳 → cues.json（人力レビューポイント）

srtを読み、Claudeが翻訳して `<workdir>/cues.json` を書く。形式:

```json
[[0.4, 5.4, "1行目\n2行目"], [5.4, 13.9, "..."], ...]
```

翻訳ルール:
- 意訳・平易化OK（SNS/縦型向け。逐語より読み切れることを優先）
- 技術用語は無理にカタカナ化しない
- 基本は1行・15文字前後・短いキューでリズムよく。2行は固有名詞が長い等どうしてもの時だけ
- 文末の「。」は付けない。読点の代わりに半角スペース可（洋画字幕流）
- em dash / en dash は使わない
- 短いsrtセグメントは意味単位でマージ。隣接キューは前のendの直後から（0.01s空ける）
- 無音・BGMだけの区間はキューを置かない
- 冒頭がフェードインの動画は黒フレームに字幕を乗せない。輝度をffmpegでサンプルし、明るくなってから最初のキューを開始

**cues.jsonの訳文一覧をユーザーに提示し、OKをもらってから次へ進む。**

### 4. 黒グラデ生成

```
python3 ~/.claude/skills/jpsub/scripts/make_gradient.py -w W -H H -o <workdir>/gradient.png
```

高さ2/3から始まり下端でalpha 0.82の実測プロファイル。不要と言われた場合のみ省略。

### 5. 字幕PNGレンダリング

```
python3 ~/.claude/skills/jpsub/scripts/render_cues.py <workdir>/cues.json <workdir>/subpng -w W -H H
```

headless Chromeで透過PNG化。フォントはHiragino Sans W6、サイズはmin(W,H)/1080比で自動スケール（1080p基準46px/下端56px）。
特定キューだけ直す時は `--only 3,7`。スタイル自体を変えたい時はキューの `.html` を直接編集してChromeで撮り直してもよい。

### 6. 焼き込み

```
python3 ~/.claude/skills/jpsub/scripts/burn.py <video> <workdir>/cues.json <workdir>/subpng --gradient <workdir>/gradient.png
```

`<video名>_JPsub.mp4` と `check1-4.jpg`（キュー中間点のフレーム）が出る。crf 18 / 音声copy / faststart。
元動画の頭に黒フレームが残る場合は `--trim-start <秒>` で頭を切る（キュー時刻は自動シフト。1フレーム=約0.042s @23.976fps）。

### 7. QA（自己判定で完了にしない）

- `check*.jpg` を目視（文字切れ・2行超え・グラデの濃さ）
- ユーザーにcheckフレームを提示して確認を待つ
- 修正指示が来たら: cues.json修正 → `--only` で該当PNGだけ再レンダ → burn.py再実行

## 注意

- 元動画は絶対にリネーム/移動しない。成果物は必ず別名
- 尺の長い動画はburnが重い（60キュー/9分で数分）
