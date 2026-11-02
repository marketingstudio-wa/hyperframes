#!/bin/bash
# Voice (-16 LUFS) + music bed ducked under the voice, lifted on the end card, faded out.
# Usage: mix.sh <clip_out_dir> <music.mp3> <end_card_seconds>
set -e
D=$1; MUSIC=$2; END=$3
DEMO=$(python3 -c "import json;print(json.load(open('$D/segs.json'))['dur'])")
T=$(python3 -c "print(round($DEMO+$END,3))")
ffmpeg -nostdin -v error -y -i "$D/voice.wav" -af "loudnorm=I=-16:TP=-2:LRA=9,apad=whole_dur=$T" -ar 48000 -ac 2 "$D/voice_n.wav"
ffmpeg -nostdin -v error -y -i "$MUSIC" -af "atrim=0:$T,asetpts=PTS-STARTPTS,volume='if(lt(t,$DEMO),0.16,0.36)':eval=frame,afade=t=in:d=0.4,afade=t=out:st=$(python3 -c "print($T-1.2)"):d=1.2" -ar 48000 -ac 2 "$D/bed.wav"
ffmpeg -nostdin -v error -y -i "$D/bed.wav" -i "$D/voice_n.wav" -filter_complex \
  "[1:a]asplit=2[v][sc];[0:a][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];[duck][v]amix=inputs=2:normalize=0:duration=longest,atrim=0:$T[a]" \
  -map "[a]" -c:a aac -b:a 256k "$D/mix.m4a"
ffmpeg -nostdin -v error -y -i "$D/mix.m4a" -ar 48000 "$D/mix.wav"
echo "$(basename $D) mix $T s"
