"""Cut each clip's segments from the Zoom source and lay them out on a 1080x1920 navy canvas.

split layout: Zoom active-speaker thumbnail (256x144 @ 1024,0) enlarged into a 1000x562 face card at
(40,250); the app crop below it at (40,850). face layout: full-frame camera, 1000x1000 card at (40,250).
Name patches (presenter name -> neutral text) from patches.json are applied in source pixels before layout.
Writes out/<clip>/base.mp4 (video only), voice.wav (48 kHz mono, 30 ms joins) and segs.json (out times)."""
import json, os, subprocess, sys

EDL = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
PATCH = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else []
SRC = EDL["source"]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
NAVY = "0x1a1a2e"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])


def patch_filters(a, b):
    """drawbox + drawtext for every name patch that overlaps [a,b] (times relative to segment start)."""
    fs = []
    for p in PATCH:
        if p["t1"] < a or p["t0"] > b:
            continue
        x0, y0, x1, y1 = p["box"]
        en = f"between(t,{max(p['t0'] - a, 0):.3f},{p['t1'] - a:.3f})"
        fs.append(f"drawbox=x={x0:.0f}:y={y0:.0f}:w={x1 - x0:.0f}:h={y1 - y0:.0f}:color={p['bg']}:t=fill:enable='{en}'")
        if not p["new"]:
            continue
        txt = p["new"].replace(":", r"\:").replace(",", r"\,").replace("&", r"\&")
        fs.append(f"drawtext=fontfile={FONT}:text='{txt}':x={x0 + 1:.0f}:y={y0:.0f}+({y1 - y0:.0f}-th)/2:"
                  f"fontsize={max(int((y1 - y0) * 0.8), 6)}:fontcolor={p['fg']}:enable='{en}'")
    return fs


for name, clip in EDL["clips"].items():
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    cx, cy, cw, ch = EDL["crops"][clip.get("crop", "default")]
    app_h = round(1000 * ch / cw / 2) * 2
    mk = EDL.get("masks", {}).get(clip.get("crop", "default"))
    mask = f",drawbox=x={mk[0]}:y={mk[1]}:w={mk[2]}:h={mk[3]}:color=white:t=fill" if mk else ""
    parts, segs, t = [], [], 0.0
    for i, s in enumerate(clip["segs"]):
        a, b = s[0], s[1]
        mode = s[2] if len(s) > 2 else "split"
        fx = s[3] if len(s) > 3 else 280  # face-mode crop x (mediapipe face centre - 360, clamped)
        pf = patch_filters(a, b)
        pre = ",".join(pf) + "," if pf else ""
        if clip.get("orient") == "landscape" and mode == "split":
            app_h = round(1000 * ch / cw / 2) * 2
            fc = (f"[0:v]fps=30,{pre}split=2[s1][s2];"
                  f"[s1]crop=256:144:1024:0,scale=760:428:flags=lanczos,unsharp=5:5:0.8[face];"
                  f"[s2]crop={cw}:{ch}:{cx}:{cy}{mask},scale=1000:{app_h}:flags=lanczos[app];"
                  f"color={NAVY}:s=1920x1080:r=30[bg];[bg][face]overlay=60:170[t1];[t1][app]overlay=860:170:shortest=1[v]")
        elif clip.get("orient") == "landscape":
            fc = (f"[0:v]fps=30,{pre}scale=1280:720:flags=lanczos[face];"
                  f"color={NAVY}:s=1920x1080:r=30[bg];[bg][face]overlay=320:150:shortest=1[v]")
        elif mode == "split":
            fc = (f"[0:v]fps=30,{pre}split=2[s1][s2];"
                  f"[s1]crop=256:144:1024:0,scale=1000:562:flags=lanczos,unsharp=5:5:0.8[face];"
                  f"[s2]crop={cw}:{ch}:{cx}:{cy}{mask},scale=1000:{app_h}:flags=lanczos[app];"
                  f"color={NAVY}:s=1080x1920:r=30[bg];[bg][face]overlay=40:250[t1];[t1][app]overlay=40:850:shortest=1[v]")
        else:
            fc = (f"[0:v]fps=30,{pre}crop=720:720:{fx}:0,scale=1000:1000:flags=lanczos[face];"
                  f"color={NAVY}:s=1080x1920:r=30[bg];[bg][face]overlay=40:250:shortest=1[v]")
        p = os.path.join(d, f"seg{i:02d}.mp4")
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", SRC, "-t", f"{b - a:.3f}",
             "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
             "-pix_fmt", "yuv420p", "-r", "30", p])
        w = os.path.join(d, f"seg{i:02d}.wav")
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", SRC, "-t", f"{b - a:.3f}",
             "-af", "highpass=f=80,afftdn=nf=-30,afade=t=in:d=0.03,areverse,afade=t=in:d=0.03,areverse",
             "-ar", "48000", "-ac", "1", w])
        nfr = round((b - a) * 30)
        segs.append({"src": [a, b], "out": [round(t, 4), round(t + nfr / 30, 4)], "mode": mode})
        t += nfr / 30
        parts.append((p, w))
    with open(os.path.join(d, "list.txt"), "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p, _ in parts)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"),
         "-c", "copy", os.path.join(d, "base.mp4")])
    ins = sum((["-i", w] for _, w in parts), [])
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", *ins, "-filter_complex",
         "".join(f"[{i}:a]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[a]", "-map", "[a]",
         os.path.join(d, "voice.wav")])
    json.dump({"segs": segs, "dur": round(t, 4), "app_h": app_h}, open(os.path.join(d, "segs.json"), "w"), indent=1)
    print(name, f"{t:.2f}s", len(segs), "segs")
