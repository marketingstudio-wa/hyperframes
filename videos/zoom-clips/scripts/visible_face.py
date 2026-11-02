"""Who is on camera in the face card of base.mp4, sampled at 5 fps.
Architect: greenish blurred background (mean G - (R+B)/2 > 3); presenter: grey office.
Writes out/<clip>/faces.json: runs [{who, t, e}] (runs shorter than 0.6 s are merged)."""
import json, subprocess, sys
import numpy as np

for d in sys.argv[1:]:
    land = "16x9" in d
    segs = json.load(open(f"{d}/segs.json"))["segs"]
    regions = {("split", False): "crop=1000:540:40:260", ("face", False): "crop=1000:380:40:260",
               ("split", True): "crop=740:400:70:180", ("face", True): "crop=1280:280:320:150"}
    g, ts = [], []
    for s in segs:
        a, b = s["out"]
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", f"{d}/base.mp4",
                              "-vf", "fps=5," + regions[(s["mode"], land)] + ",scale=20:10", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        px = np.frombuffer(raw, np.uint8).reshape(-1, 10, 20, 3).astype(float).mean((1, 2))
        n = min(len(px), int(round((b - a) * 5)))
        g += list(px[:n, 1] - (px[:n, 0] + px[:n, 2]) / 2)
        ts += [a + i / 5 for i in range(n)]
    g = np.array(g)
    lab = ["A" if x > 3 else "P" for x in g]
    runs = []
    for i, l in enumerate(lab):
        if runs and runs[-1]["who"] == l:
            runs[-1]["e"] = ts[i] + 0.2
        else:
            runs.append({"who": l, "t": ts[i], "e": ts[i] + 0.2})
    changed = True
    while changed and len(runs) > 1:
        changed = False
        for i, ru in enumerate(runs):
            if ru["e"] - ru["t"] < 0.6:
                j = i - 1 if i > 0 else i + 1
                runs[j]["t"], runs[j]["e"] = min(runs[j]["t"], ru["t"]), max(runs[j]["e"], ru["e"])
                runs.pop(i); changed = True
                break
        merged = []
        for ru in runs:
            if merged and merged[-1]["who"] == ru["who"]:
                merged[-1]["e"] = ru["e"]
            else:
                merged.append(ru)
        runs = merged
    json.dump(runs, open(f"{d}/faces.json", "w"))
    print(d.split("/")[-1], [(r["who"], round(r["t"], 1), round(r["e"], 1)) for r in runs], "g range", g.min().round(1), g.max().round(1))
