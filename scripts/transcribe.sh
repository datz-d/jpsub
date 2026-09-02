#!/bin/bash
# Usage: transcribe.sh <video> <out_dir> [model]
# Runs openai-whisper on the video's audio. Outputs .srt/.json/.txt into out_dir.
set -euo pipefail
VIDEO="$1"
OUT="$2"
MODEL="${3:-turbo}"
mkdir -p "$OUT"
/opt/homebrew/bin/whisper "$VIDEO" --model "$MODEL" \
  --output_format all --output_dir "$OUT" --verbose False --word_timestamps True
echo "done: $(ls "$OUT" | tr '\n' ' ')"
