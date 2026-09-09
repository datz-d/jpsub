---
name: jpsub
description: 動画を書き起こして日本語字幕+下部黒グラデを焼き込む。DL済み動画に洋画風JP字幕を付けるとき、DeNAスレ/Velocity等のクリップ制作時に使う
---

# jpsub: 日本語字幕焼き込みパイプライン

DL済み動画 → whisper書き起こし → Claude翻訳(cues.json) → 透過PNG字幕 → 黒グラデと共にffmpeg焼き込み。
スタイルはUlyssesプロジェクト(`~/Downloads/ulysses_a16z/`)で確立した洋画字幕風。

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
- 意訳・平易化OK（縦型/SNS向け。逐語より読み切れることを優先）
- 技術用語は英語のまま+必要なら日本語グロス（カタカナ訳禁止）
- **基本は1行・15文字前後・短いキューでリズムよく**（ユーザー確認済みの好み）。2行は固有名詞が長い等どうしてもの時だけ
- 冒頭がフェードインの動画は黒フレームに字幕を乗せない。輝度をffmpegでサンプルし、明るくなってから最初のキューを開始
- 冒頭に黒フレームが残る場合は `burn.py --trim-start <秒>` で頭を切る（キュー時刻は自動シフト）。1フレーム=約0.042s(23.976fps)
- 文末の「。」は付けない。読点の代わりに半角スペース可（洋画字幕流）
- em dash / en dash 絶対禁止
- 短いsrtセグメントは意味単位でマージ
- **字幕は常に連続表示・空白なし**: 各キューのendは次のキューのstartまで延長、先頭キューは0秒から、最後のキューは動画末尾まで表示
- 無音・BGMだけの区間はキューを置かない

**cues.jsonの訳文一覧をユーザーに提示し、OKをもらってから次へ進む。**

### 4. 黒グラデ生成

```
python3 ~/.claude/skills/jpsub/scripts/make_gradient.py -w W -H H -o <workdir>/gradient.png
```

Ulysses実測プロファイル（高さ2/3から始まり下端でalpha 0.82）。不要と言われた場合のみ省略。

### 5. 字幕PNGレンダリング

```
python3 ~/.claude/skills/jpsub/scripts/render_cues.py <workdir>/cues.json <workdir>/subpng -w W -H H
```

headless Chromeで透過PNG化。フォントはHiragino Sans W6、サイズはmin(W,H)/1080比で自動スケール（1080p基準46px/下端56px）。
特定キューだけ直す時は `--only 3,7`。スタイル自体を変えたい時はキューの `.html` を直接編集してChromeで撮り直してもよい（Ulyssesと同じ運用）。

### 5.5 翻訳クレジット(DeNAスレ等、必要な時)

```
python3 ~/.claude/skills/jpsub/scripts/make_credit.py -w W -H H -o <workdir>/credit.png [--pos tr|tl] [--text "翻訳：事業家のDNA（DeNA公式）"]
```

ロゴ(既定=dena/brand/dna_logo_bubble.png)+一行テキストの透過PNG。右上(tr)既定。burn.pyに `--credit <workdir>/credit.png` を渡すと全尺オーバーレイ。2026-09-08 Giantクリップで導入。

### 6. 焼き込み

```
python3 ~/.claude/skills/jpsub/scripts/burn.py <video> <workdir>/cues.json <workdir>/subpng --gradient <workdir>/gradient.png [--credit <workdir>/credit.png]
```

`<video名>_JPsub.mp4` と `check1-4.jpg`（キュー中間点のフレーム）が出る。crf 18 / 音声copy / faststart。

**黒ファーストフレーム対策(burn.pyに組み込み済み)**: ffmpegで切り出した素材はvideoのstart_timeが約1フレーム(0.033s@30fps)ずれ、audioが0秒のままになることがある。QuickTime/Finderはこの隙間を黒で埋めてポスターにするため「1フレーム目が黒い」ように見える(ffmpegのフレーム抽出では黒フレームが見えないので気づきにくい)。burn.pyは出力時に `setpts=PTS-STARTPTS` で映像PTSを0始まりに正規化してこれを防ぐ(2026-09-02 Statusクリップで発覚)。

### 7. QA（自己判定で完了にしない）

- `check*.jpg` を自分で目視（文字切れ・2行超え・グラデの濃さ）
- `ffprobe -v error -show_entries stream=codec_type,start_time -of compact <出力>` で**videoのstart_time=0を確認**(0.03等ならQuickTimeで頭が黒く見える)。ffmpegのフレーム抽出だけでQA完了にしない
- `open -R <check1.jpg>` でFinder提示し、**ユーザーの目視確認を待つ**
- 修正指示が来たら: cues.json修正 → `--only` で該当PNGだけ再レンダ → burn.py再実行

## 注意

- 元動画は絶対にリネーム/移動しない（NLE参照事故防止）。成果物は必ず別名
- 尺の長い動画はburnが重い。60キュー/9分で数分かかる（Ulysses実績）
- 翻訳の平易化度合いはプロジェクトのSSOT/標準に合わせる（DeNAスレならELI5寄り）
