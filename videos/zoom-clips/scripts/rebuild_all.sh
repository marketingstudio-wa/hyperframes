#!/bin/bash
# Full rebuild: bases (with name patches) -> explainer words -> captions -> visible faces -> mixes -> compositions -> check.
set -e
cd "$(dirname "$0")/.."
OUT=/home/user/media/zoom-demo/out
FULL=/tmp/claude-0/-home-user/24c4d295-4351-5708-b965-354b17000acf/scratchpad/work/transcript.json
python3 -I scripts/build_base.py edl.json $OUT patches.json
[ -f $OUT/explainer/words.json ] && [ -f $OUT/explainer-16x9/words.json ] || python3 -I scripts/words.py $OUT > /dev/null 2>&1
python3 -I scripts/align_captions.py $OUT captions.json $FULL
python3 -I scripts/visible_face.py $OUT/*
for d in $OUT/*/; do scripts/mix.sh ${d%/} /home/user/media/music/bed.mp3 3.6; done
for c in c1-sell-this c2-just-talk c3-you-built-this c4-20-hours c5-verdict explainer explainer-16x9; do
  mkdir -p $c/assets; cp -n c1-sell-this/assets/{gsap.min.js,logo-rail.png,logo-end.png} $c/assets/ 2>/dev/null || true
  python3 -I scripts/gen_clip.py $c $OUT $c
  (cd $c && printf "$c: " && node /home/user/hyperframes/packages/cli/dist/cli.js check 2>&1 | grep -E "✗|Check (passed|failed)" | tr '\n' ' '; echo)
done
