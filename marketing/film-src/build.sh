#!/usr/bin/env bash
# Builds the Agent Marketplace film end to end:
#   voice-over (Azure Sonia if AZURE_SPEECH_KEY/AZURE_SPEECH_REGION are set) -> score -> frames -> MP4.
# Requires: python3 with numpy scipy faster-whisper (and piper-tts for the fallback voice),
#           node + playwright with Chromium, ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
WORKERS=${WORKERS:-4}; FPS=60; FRAMES=$((120*FPS))
python3 build_vo.py
python3 music.py
mkdir -p build/seg; rm -f build/seg/*.mp4
per=$(( (FRAMES + WORKERS - 1) / WORKERS ))
for i in $(seq 0 $((WORKERS-1))); do
  a=$((i*per)); b=$(( (i+1)*per < FRAMES ? (i+1)*per : FRAMES ))
  node render.js $a $b build/seg/p$i.mp4 > build/seg/log$i.txt 2>&1 &
done
wait
for i in $(seq 0 $((WORKERS-1))); do echo "file 'seg/p$i.mp4'"; done > build/list.txt
# 60 fps render blended to 30 fps = natural motion blur; audio normalised to -16 LUFS
ffmpeg -v error -y -f concat -safe 0 -i build/list.txt -i build/mix.wav \
  -filter_complex "[0:v]tmix=frames=2:weights='1 1',fps=30,format=yuv420p[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 17 -profile:v high -movflags +faststart \
  -c:a aac -b:a 256k -ar 48000 -t 120 build/agent-marketplace-film.mp4
# shareable copy under 30 MB
ffmpeg -v error -y -i build/agent-marketplace-film.mp4 -c:v libx264 -preset slow -crf 23 -movflags +faststart \
  -c:a aac -b:a 192k build/agent-marketplace-film-web.mp4
ls -la build/*.mp4
