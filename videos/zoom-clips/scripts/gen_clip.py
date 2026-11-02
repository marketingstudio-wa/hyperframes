"""Generate one 9:16 HyperFrames composition (index.html) for a Zoom-call clip.

Inputs (from out/<clip>/): base.mp4 (laid-out footage), segs.json (layout per output time), caps.json
(word captions with speaker), mix.m4a (voice + ducked music bed). House style: navy / gold / Inter,
captions with the active word in gold, speaker lower-third on the face card, logo only in the
top rail and on the end card, CTA end card.
Usage: gen_clip.py <clip> <out_dir> <project_dir>
"""
import html, json, shutil, sys

NAME, OUT, PROJ = sys.argv[1], sys.argv[2], sys.argv[3]
EDL = json.load(open("edl.json"))["clips"][NAME]
SPK = json.load(open("captions.json"))["speakers"]
SG = json.load(open(f"{OUT}/{NAME}/segs.json"))
CAPS = json.load(open(f"{OUT}/{NAME}/caps.json"))
DEMO = SG["dur"]
END = 3.6
T = round(DEMO + END, 2)
APP_H = SG["app_h"]
r = lambda x: f"{x:.2f}"
LAND = EDL.get("orient") == "landscape"
W, H = (1920, 1080) if LAND else (1080, 1920)
# geometry per orientation: face card (split / face mode), app card, lower-third y per mode, captions, rail
if LAND:
    G = dict(split=(54, 164, 772, 440), face=(314, 144, 1292, 732), app=(856, 166, 1008), lt_split=(80, 520), lt_face=(340, 790),
             cap=(60, 930, 1800, 56), rail=(60, 36, 1800, 100), hook=(60, 20, 1800, 130, 52), chap=(60, 650, 760))
else:
    G = dict(split=(34, 244, 1012, 574), face=(34, 244, 1012, 1012), app=(36, 846, 1008), lt_split=(70, 700), lt_face=(70, 1140),
             cap=(50, 1620, 980, 70), rail=(40, 90, 1000, 120), hook=(40, 52, 1000, 190, 64), chap=(40, 1810, 1000))
CHAPS = EDL.get("chapters", [])

CTA = {
    "c2-just-talk": ("Try our hands-free mode", "GO TO HOMEESTIMATOR.AI"),
}.get(NAME, ("See it on your next project", "BOOK A DEMO AT HOMEESTIMATOR.AI"))

# ---------- layout windows (split vs face) ----------
lay_js = []
for s in SG["segs"]:
    a, b = s["out"]
    fx, fy, fw, fh = G[s["mode"]]
    lx, ly = G["lt_" + s["mode"]]
    lay_js.append(f'      tl.set("#facebox", {{ left: {fx}, top: {fy}, width: {fw}, height: {fh} }}, {r(a)});')
    lay_js.append(f'      tl.set("#appbox", {{ opacity: {1 if s["mode"] == "split" else 0} }}, {r(a)});')
    lay_js.append(f'      tl.set(".lt", {{ left: {lx}, top: {ly} }}, {r(a)});')
    lay_js.append(f'      tl.set("#chap", {{ visibility: "{"visible" if s["mode"] == "split" else "hidden"}" }}, {r(a)});')

# ---------- chapter titles ----------
ch_html, ch_js = [], []
for j, (si, kick, title) in enumerate(CHAPS):
    a = SG["segs"][si]["out"][0]
    e = SG["segs"][CHAPS[j + 1][0]]["out"][0] if j + 1 < len(CHAPS) else DEMO
    ch_html.append(f'          <div class="ch" id="ch{j}"><span class="k">{html.escape(kick)}</span><span class="t">{html.escape(title)}</span></div>')
    ch_js.append(f'      tl.fromTo("#ch{j}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(a + 0.1)});')
    ch_js.append(f'      tl.to("#ch{j}", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(e - 0.35)});')
    ch_js.append(f'      tl.set("#ch{j}", {{ opacity: 0 }}, {r(e - 0.05)});')

# ---------- speaker lower-thirds (one per caption line, merged when speaker repeats) ----------
lines = []
for c in CAPS:
    if not lines or lines[-1]["line"] != c["line"]:
        lines.append({"line": c["line"], "spk": c["spk"], "t": c["t"], "e": c["e"]})
    else:
        lines[-1]["e"] = c["e"]
# The label names whoever is ON CAMERA in the face card (Zoom's thumbnail lags the voice), from faces.json.
runs = [{"spk": f["who"], "t": f["t"], "e": f["e"]} for f in json.load(open(f"{OUT}/{NAME}/faces.json"))]
lt_html, lt_js = [], []
for i, ru in enumerate(runs):
    if ru["e"] - ru["t"] < 1.0:
        continue
    nm, _, role = SPK[ru["spk"]].partition(" · ")
    start = ru["t"] + (0.15 if i else 0.3)
    end = min(ru["e"], DEMO)
    lt_html.append(f'          <div class="lt" id="lt{i}"><span class="n">{html.escape(nm)}</span>'
                   f'<span class="r">{html.escape(role)}</span></div>')
    lt_js.append(f'      tl.fromTo("#lt{i}", {{ opacity: 0, x: -24 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: IN }}, {r(start)});')
    lt_js.append(f'      tl.to("#lt{i}", {{ opacity: 0, duration: 0.2, ease: OUT }}, {r(max(end - 0.2, start + 0.3))});')
    lt_js.append(f'      tl.set("#lt{i}", {{ opacity: 0 }}, {r(max(end, start + 0.5))});')

# ---------- captions: <= 4 words per chunk, break after punctuation or a speaker change ----------
chunks, cur = [], []
for k, c in enumerate(CAPS):
    cur.append(c)
    nxt = CAPS[k + 1] if k + 1 < len(CAPS) else None
    brk = (nxt is None or len(cur) >= 4 or c["w"][-1] in ".?!," or nxt["line"] != c["line"]
           or nxt["t"] - c["e"] > 0.6)
    if brk and not (nxt is not None and len(cur) == 1 and c["w"][-1] not in ".?!" and nxt["line"] == c["line"]):
        chunks.append(cur)
        cur = []
if cur:
    chunks.append(cur)
cap_html, cap_js = [], []
for ci, ch in enumerate(chunks):
    start = ch[0]["t"]
    nxt = chunks[ci + 1][0]["t"] if ci + 1 < len(chunks) else DEMO
    end = min(nxt, ch[-1]["e"] + 0.9, DEMO)
    spans = " ".join(f'<span id="w{ci}_{k}">{html.escape(w["w"])}</span>' for k, w in enumerate(ch))
    cap_html.append(f'        <div class="cap" id="c{ci}">{spans}</div>')
    cap_js.append(f'      tl.set("#c{ci}", {{ opacity: 1 }}, {r(start)});')
    cap_js.append(f'      tl.set("#c{ci}", {{ opacity: 0 }}, {r(end)});')
    for k, w in enumerate(ch):
        cap_js.append(f'      tl.set("#w{ci}_{k}", {{ color: "#d4af37" }}, {r(w["t"])});')
        if k + 1 < len(ch):
            cap_js.append(f'      tl.set("#w{ci}_{k}", {{ color: "#ffffff" }}, {r(ch[k + 1]["t"])});')

hook = html.escape(EDL["hook"])
HOOK_END = 3.2

for f in ("base.mp4", "mix.m4a"):
    shutil.copy(f"{OUT}/{NAME}/{f}", f"{PROJ}/assets/{f}")

doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Real Call Clip</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      :root {{
        --navy: #1a1a2e;
        --card: #2d2d44;
        --line: #3a3a55;
        --sand: #c9a96e;
        --gold: #d4af37;
        --gray: #a0aab2;
        --white: #ffffff;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: var(--navy); }}
      body {{ font-family: "Inter", sans-serif; color: var(--white); }}
      #root {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; background: var(--navy); }}
      #base {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; object-fit: fill; }}
      #rail {{ position: absolute; left: {G["rail"][0]}px; top: {G["rail"][1]}px; width: {G["rail"][2]}px; height: {G["rail"][3]}px; display: flex;
        align-items: center; justify-content: space-between; opacity: 0; }}
      #rail-logo {{ height: {G["rail"][3] - 8}px; width: auto; }}
      #live {{ display: flex; align-items: center; gap: 14px; font-size: 32px; font-weight: 800; letter-spacing: 5px; color: var(--sand); }}
      #live i {{ width: 18px; height: 18px; border-radius: 50%; background: #e5484d; display: block; }}
      #hook {{ position: absolute; left: {G["hook"][0]}px; top: {G["hook"][1]}px; width: {G["hook"][2]}px; height: {G["hook"][3]}px; display: flex; align-items: center;
        font-size: {G["hook"][4]}px; font-weight: 900; letter-spacing: -2px; line-height: 1.04; }}
      #hook span {{ color: var(--gold); }}
      #facebox {{ position: absolute; left: {G["split"][0]}px; top: {G["split"][1]}px; width: {G["split"][2]}px; height: {G["split"][3]}px; border: 6px solid var(--gold); }}
      #appbox {{ position: absolute; left: {G["app"][0]}px; top: {G["app"][1]}px; width: {G["app"][2]}px; height: {APP_H + 8}px; border: 4px solid var(--line); }}
      .lt {{ position: absolute; left: {G["lt_split"][0]}px; top: {G["lt_split"][1]}px; padding: 14px 26px 14px 22px; background: rgba(26, 26, 46, 0.94);
        border-left: 6px solid var(--gold); opacity: 0; }}
      .lt .n {{ display: block; font-size: 36px; font-weight: 800; letter-spacing: -0.5px; }}
      .lt .r {{ display: block; margin-top: 2px; font-size: 26px; font-weight: 700; letter-spacing: 3px; color: var(--sand); text-transform: uppercase; }}
      .cap {{ position: absolute; left: {G["cap"][0]}px; top: {G["cap"][1]}px; width: {G["cap"][2]}px; text-align: center; font-size: {G["cap"][3]}px; font-weight: 900;
        letter-spacing: -1px; line-height: 1.1; opacity: 0; text-shadow: 0 4px 18px rgba(0, 0, 0, 0.55); }}
      #chap {{ position: absolute; left: {G["chap"][0]}px; top: {G["chap"][1]}px; width: {G["chap"][2]}px; }}
      .ch {{ position: absolute; left: 0; top: 0; width: 100%; opacity: 0; {"" if LAND else "text-align: center;"} }}
      .ch .k {{ display: block; font-size: {30 if LAND else 26}px; font-weight: 800; letter-spacing: 5px; color: var(--gold); }}
      .ch .t {{ display: {"block" if LAND else "inline"}; margin-top: 10px; font-size: {60 if LAND else 34}px; font-weight: 900; letter-spacing: -1px; line-height: 1.05; }}
      #outro {{ position: absolute; inset: 0; background: var(--navy); opacity: 0; }}
      #outro-in {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
      #outro-logo {{ width: 560px; height: auto; }}
      #outro-rule {{ width: 390px; height: 4px; background: var(--gold); margin: 70px 0 56px; }}
      #outro-line {{ font-size: 54px; font-weight: 500; }}
      #outro-cta {{ margin-top: 30px; font-size: 56px; font-weight: 900; color: var(--gold); letter-spacing: 0.5px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{r(T)}" data-width="{W}" data-height="{H}">
      <audio id="mix" src="assets/mix.m4a" data-start="0" data-duration="{r(T)}" data-track-index="10" data-volume="1"></audio>
      <video id="base" class="clip" src="assets/base.mp4" data-start="0" data-duration="{r(DEMO)}" data-track-index="1" muted playsinline></video>
      <section id="call">
        <div id="facebox"></div>
        <div id="appbox"></div>
{chr(10).join(lt_html)}
        <div id="rail"><img id="rail-logo" src="assets/logo-rail.png" alt="Home Estimator" /><div id="live"><i></i>REAL DEMO CALL</div></div>
        <div id="hook"><div>{hook}</div></div>
{chr(10).join(cap_html)}
        <div id="chap">
{chr(10).join(ch_html)}
        </div>
      </section>

      <section id="outro">
        <div id="outro-in">
          <img id="outro-logo" src="assets/logo-end.png" alt="Home Estimator" />
          <div id="outro-rule"></div>
          <div id="outro-line">{html.escape(CTA[0])}</div>
          <div id="outro-cta">{html.escape(CTA[1])}</div>
        </div>
      </section>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const IN = "power3.out";
      const OUT = "power2.in";

      // hook: lands on frame 1 over the live call, then hands the top rail to the logo
      tl.fromTo("#hook", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: IN }}, 0.05);
      tl.to("#hook", {{ opacity: 0, y: -20, duration: 0.3, ease: OUT }}, {r(HOOK_END - 0.3)});
      tl.set("#hook", {{ opacity: 0 }}, {r(HOOK_END)});
      tl.fromTo("#rail", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: IN }}, {r(HOOK_END)});

      // layout per segment (split: face + app, face: full camera)
{chr(10).join(lay_js)}

      // speaker lower-thirds
{chr(10).join(lt_js)}

      // chapter titles
{chr(10).join(ch_js)}

      // captions (active word gold)
{chr(10).join(cap_js)}

      // end card
      tl.set("#outro", {{ opacity: 1 }}, {r(DEMO)});
      tl.set("#call", {{ opacity: 0 }}, {r(DEMO)});
      tl.fromTo("#outro-logo", {{ opacity: 0, scale: 0.95 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: IN }}, {r(DEMO + 0.05)});
      tl.fromTo("#outro-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: IN }}, {r(DEMO + 0.4)});
      tl.fromTo("#outro-line", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(DEMO + 0.65)});
      tl.fromTo("#outro-cta", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(DEMO + 0.9)});

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(f"{PROJ}/index.html", "w").write(doc)
print(NAME, "T", T, "captions", len(chunks), "lower-thirds", len(runs))
