"""OCR every clip segment of the Zoom source at 4 fps and record on-screen hits of the
presenter's real name (Hasnain / Nasar / Hassan). Output: work/name_hits.json (source time, box, text)."""
import json, re, subprocess, sys
import numpy as np
from rapidocr_onnxruntime import RapidOCR

EDL = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
SRC = EDL["source"]
RX = re.compile(r"has\s*n|hasna|nasar|hassan|asnain", re.I)
eng = RapidOCR()
hits = []
for name, clip in EDL["clips"].items():
    for s in clip["segs"]:
        a, b = s[0], s[1]
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{a:.3f}", "-i", SRC, "-t", f"{b - a:.3f}",
                              "-vf", "fps=4,scale=2560:1440", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        frames = np.frombuffer(raw, np.uint8).reshape(-1, 1440, 2560, 3)
        for i, f in enumerate(frames):
            t = a + i / 4
            res, _ = eng(f)
            for box, txt, conf in (res or []):
                if RX.search(txt):
                    bx = np.array(box) / 2  # back to 1280x720 source pixels
                    hits.append({"clip": name, "t": round(t, 2), "txt": txt,
                                 "box": [float(bx[:, 0].min()), float(bx[:, 1].min()), float(bx[:, 0].max()), float(bx[:, 1].max())]})
        print(name, a, b, "hits so far", len(hits), flush=True)
json.dump(hits, open(OUT, "w"), indent=1)
