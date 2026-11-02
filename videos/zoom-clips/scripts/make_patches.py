"""Turn OCR name hits into timed name-neutral patches (presenter shown by title only) (source pixels/seconds) with sampled colours.
Groups hits by clip + position, covers [first-0.3, last+0.3] inside the segment, samples background
(median border) and text colour (pixels farthest from the background) from a mid-group frame."""
import collections, json, re, subprocess, sys
import numpy as np

EDL = json.load(open(sys.argv[1])); OUTP = sys.argv[-1]
HITS = [h for f in sys.argv[2:-1] for h in json.load(open(f))]
SRC = EDL["source"]


def seg_of(clip, t):
    for s in EDL["clips"][clip]["segs"]:
        if s[0] - 0.01 <= t <= s[1] + 0.01:
            return s[0], s[1]
    return t - 0.3, t + 0.3


def new_text(txts):
    j = " ".join(txts)
    if re.search(r"contact", j, re.I):
        return "Contact: CEO & Founder"
    if re.search(r"ema", j, re.I):
        return ""  # blank the email line
    if re.search(r"welcome", j, re.I):
        return "Welcome back"
    digits = collections.Counter(m for t in txts for m in re.findall(r"(?:has\w*?)([0-9oc?D]{2,3})", t, re.I)).most_common(1)
    num = digits[0][0].translate(str.maketrans("ocD?", "0007")) if digits else ""
    num = re.sub(r"^7", "07", num) if len(num) == 2 else num
    if re.search(r"resume", j, re.I):
        return f"Resume: Project{num}"
    return f"Project{num}"


def frame(t):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(720, 1280, 3).astype(int)


groups = []
for h in sorted(HITS, key=lambda h: (h["clip"], h["t"])):
    b = h["box"]
    for g in groups:
        gb = g["box"]
        if g["clip"] == h["clip"] and abs(gb[0] - b[0]) < 8 and abs(gb[1] - b[1]) < 5:
            g["times"].append(h["t"]); g["txts"].append(h["txt"])
            g["box"] = [min(gb[0], b[0]), min(gb[1], b[1]), max(gb[2], b[2]), max(gb[3], b[3])]
            break
    else:
        groups.append({"clip": h["clip"], "box": list(b), "times": [h["t"]], "txts": [h["txt"]]})

patches = []
for g in groups:
    # split into runs per segment
    by_seg = collections.defaultdict(list)
    for t in g["times"]:
        by_seg[seg_of(g["clip"], t)].append(t)
    x0, y0, x1, y1 = g["box"]; x0 -= 2; y0 -= 2; x1 += 3; y1 += 2
    for (a, b), ts in by_seg.items():
        t0, t1 = a, b  # cover the whole segment: a missed OCR frame must never let the name through
        img = frame((min(ts) + max(ts)) / 2)
        xi0, yi0, xi1, yi1 = int(x0), int(max(y0, 0)), int(x1), int(y1)
        border = np.concatenate([img[max(yi0 - 1, 0), xi0:xi1], img[min(yi1 + 1, 719), xi0:xi1]])
        bg = np.median(border, 0)
        reg = img[yi0:yi1, xi0:xi1].reshape(-1, 3)
        dist = np.abs(reg - bg).sum(1)
        fg = np.median(reg[dist >= np.percentile(dist, 95)], 0)
        hexc = lambda c: "0x%02x%02x%02x" % tuple(int(v) for v in c)
        patches.append({"clip": g["clip"], "t0": round(t0, 2), "t1": round(t1, 2), "box": [x0, y0, x1, y1],
                        "bg": hexc(bg), "fg": hexc(fg), "new": new_text(g["txts"]), "n": len(ts)})
json.dump(patches, open(OUTP, "w"), indent=1)
for p in patches:
    print(p["clip"], p["t0"], p["t1"], [round(v) for v in p["box"]], p["bg"], p["fg"], p["new"], p["n"])
