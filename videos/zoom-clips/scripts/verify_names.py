"""OCR rendered videos at 2 fps (1.6x upscale); print any remaining real-name (or stale 'Henry') hit."""
import re, subprocess, sys
import numpy as np
from rapidocr_onnxruntime import RapidOCR
eng = RapidOCR(); RX = re.compile(r"has\s*n|hasna|nasar|hassan|asnain|hasn|henry|nasar", re.I)
for p in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", p, "-vf", "fps=1,scale=iw*1.6:ih*1.6",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                    "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip().split(","))
    fr = np.frombuffer(raw, np.uint8).reshape(-1, int(h * 1.6), int(w * 1.6), 3)
    bad = []
    for i, f in enumerate(fr):
        for box, txt, conf in (eng(f)[0] or []):
            if RX.search(txt):
                bad.append((round(i, 2), txt))
    print(p.split("/")[-1], "frames", len(fr), "leaks", bad[:10], flush=True)
