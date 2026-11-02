"""OCR every rendered base.mp4 at 3 fps (2x upscale); print any remaining real-name hit."""
import re, subprocess, sys
import numpy as np
from rapidocr_onnxruntime import RapidOCR
eng = RapidOCR(); RX = re.compile(r"has\s*n|hasna|nasar|hassan|asnain|hasn", re.I)
for p in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", p, "-vf", "fps=3,crop=1080:1400:0:200,scale=2160:2800",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 2800, 2160, 3)
    bad = []
    for i, f in enumerate(fr):
        for box, txt, conf in (eng(f)[0] or []):
            if RX.search(txt):
                bad.append((round(i / 3, 2), txt))
    print(p.split("/")[-2], "frames", len(fr), "leaks", bad[:10])
