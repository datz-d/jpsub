# jpsub

A [Claude Code](https://claude.com/claude-code) skill that burns cinema-style Japanese subtitles into any video.

**video → whisper transcription → Claude translation (with your review) → transparent PNG subtitles → ffmpeg burn-in, with a bottom black gradient for legibility.**

<br>

日本語字幕焼き込みのClaude Codeスキルです。海外のインタビュー・講演・デモ動画に、洋画風の字幕（白文字+多重シャドウ+下部黒グラデ）を一発で焼き込みます。翻訳はClaudeが行い、焼き込み前に必ず訳文レビューを挟みます。

## How it works

1. `ffprobe` probes the video
2. `transcribe.sh` runs openai-whisper (word timestamps included)
3. Claude translates into `cues.json` (`[[start, end, "line"], ...]`) following built-in subtitle style rules (1 line, ~15 chars, rhythm-first), and **asks you to approve the translation**
4. `make_gradient.py` renders a bottom black gradient PNG (measured profile: starts at 2/3 height, alpha 0.82 at the bottom)
5. `render_cues.py` renders each cue to a transparent full-frame PNG via headless Chrome (Hiragino Sans, auto-scaled from a 1080p baseline, works for vertical video too)
6. `burn.py` builds the ffmpeg overlay chain (`enable='between(t,...)'`), burns everything at crf 18 with audio copied, and extracts QA frames

Fix one line? Edit `cues.json`, re-render just that cue with `--only N`, burn again.

## Requirements

- macOS (uses Hiragino Sans and the Google Chrome binary for rendering)
- `ffmpeg`, [`openai-whisper`](https://github.com/openai/whisper), Python 3 + Pillow, Google Chrome

## Install

```sh
git clone https://github.com/datz-d/jpsub ~/.claude/skills/jpsub
```

Then in Claude Code:

```
/jpsub この動画に日本語字幕つけて ~/Downloads/talk.mp4
```

## Notes

- The subtitle look (font weight, shadow stack, margins, gradient curve) lives in `templates/sub.html` and `scripts/make_gradient.py`. Edit those to change the style globally.
- `burn.py --trim-start <sec>` trims black lead-in frames; cue times shift automatically.

## License

MIT
