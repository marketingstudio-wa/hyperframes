#!/bin/bash
# Master every raw render: -14 LUFS (two-pass loudnorm) + limiter (true peak <= -1.5), video copied.
# Also writes a cover JPG (frame at 1.0 s: face + hook) for each video.
R=/home/user/media/zoom-demo/renders; F=$R/final; mkdir -p $F/covers
declare -A N=([c1-sell-this]=HEAI-Real-Call-01-Sell-This [c2-just-talk]=HEAI-Real-Call-02-Just-Talk [c3-you-built-this]=HEAI-Real-Call-03-You-Built-This
  [c4-20-hours]=HEAI-Real-Call-04-20-Hours [c5-verdict]=HEAI-Real-Call-05-Verdict [explainer]=HEAI-Real-Call-Explainer-9x16
  [explainer-16x9]=HEAI-Real-Call-Explainer-16x9 [hands-free]=HEAI-Hands-Free-Alex-9x16 [hands-free-16x9]=HEAI-Hands-Free-Alex-16x9)
for c in "$@"; do
  IN=$R/$c-raw.mp4; OUT=$F/${N[$c]}
  J=$(ffmpeg -nostdin -i "$IN" -af loudnorm=I=-14:TP=-2:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
  g() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
  ffmpeg -nostdin -v error -y -i "$IN" -c:v copy -af "loudnorm=I=-14:TP=-2:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,alimiter=limit=0.84:level=false,aresample=48000" \
    -c:a aac -b:a 256k -movflags +faststart "$OUT.mp4"
  ffmpeg -nostdin -v error -y -ss 1.0 -i "$OUT.mp4" -frames:v 1 -q:v 3 "$F/covers/${N[$c]}-cover.jpg"
  L=$(ffmpeg -nostdin -i "$OUT.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2 | tr -s ' ' | tr '\n' ' ')
  echo "${N[$c]} $L $(du -h "$OUT.mp4" | cut -f1)"
done
