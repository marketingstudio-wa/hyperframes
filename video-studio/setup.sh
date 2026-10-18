#!/usr/bin/env bash
# One-time setup per cloud session (~1 min + 600 MB model download).
set -euo pipefail
cd "$(dirname "$0")"
pip install -q sherpa-onnx numpy soundfile pillow pyyaml
if [ ! -d models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8 ]; then
  mkdir -p models
  curl -sSL https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 \
    | tar xj -C models
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg missing: apt-get install -y ffmpeg"; exit 1; }
fc-list | grep -qi "Inter" || echo "warning: Inter font not installed (apt-get install -y fonts-inter)"
echo "video studio ready"
