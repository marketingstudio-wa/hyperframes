"""Generate the Reel #2 "Option A vs Option B" composition (index.html) and timing.json for mix.py.

v4: a story told to the viewer. Desmond's hook, then one middle line that walks Option B (base scope)
and Option A (the client's upgrades), then the outro over the side-by-side, then the end card.
Every screen is labeled OPTION B or OPTION A; what changes in Option A gets a gold "+" tag.
Recreated UI only (no app footage). On-screen cues follow the VO word starts (word start - 0.08 s).
Usage: python3 gen.py <dir with hook_tw.json, mid_tw.json, outro_tw.json>
"""
import html, json, re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "../../../reel2/in4"
HOOK = json.load(open(f"{SRC}/hook_tw.json"))
MID = json.load(open(f"{SRC}/mid_tw.json"))
OUTRO = json.load(open(f"{SRC}/outro_tw.json"))
MID_LEN = MID[-1]["e"] + 0.2
OUTRO_LEN = 3.52
# the 40 s cap: the outro line only fits when the middle line is short enough
USE_OUTRO = 7.70 + MID_LEN + 0.2 + OUTRO_LEN + 0.1 + 0.6 + 3.6 <= 40.0

LEAD = 0.08
r = lambda x: f"{x:.2f}"
norm = lambda w: re.sub(r"[^a-z0-9-]", "", w.lower()).replace("hardy", "hardie")


def find(word, nth=1, after=0):
    """index of the nth MID word matching `word` at or after index `after`"""
    k = 0
    for i in range(after, len(MID)):
        if norm(MID[i]["w"]) == word:
            k += 1
            if k == nth:
                return i
    raise SystemExit(f"cue word not found: {word} #{nth}")


H0, M0 = 0.10, 7.70
MID_END = M0 + MID_LEN
# the end card must land on a music beat that leads into the 122.95 end hit (beats every 0.6 s from 7.70)
END0 = 7.70 + 0.6 * -(-(MID_END + (0.2 + OUTRO_LEN + 0.1 if USE_OUTRO else 0.3) - 7.70) // 0.6)
O0 = END0 - OUTRO_LEN - 0.1
T = round(END0 + 3.6, 2)
SPLICE = END0 - 2.4  # beat-aligned jump to the track's last phrase
hw = lambda i: H0 + HOOK[i]["s"] - LEAD
mw = lambda i: M0 + MID[i]["s"] - LEAD
ow = lambda i: O0 + OUTRO[i]["s"] - LEAD

B_TOTAL, A_TOTAL, DIFF = "$590,279", "$606,982", "+$16,703"
FINE = "Example project &mdash; every project&rsquo;s estimate differs."

# cue words in the middle line
iSAME = 0
iOB = find("option", 1)
iVINYL = find("vinyl")
is_money = lambda i, pre: MID[i]["w"].startswith(pre)  # ASR may already write a figure as "$590,279."
iFIVE = next(i for i, w in enumerate(MID) if is_money(i, "$590") or norm(w["w"]) == "five")
iOA = find("option", 2)
iSINK = find("sink")
iUNDER = next(i for i in range(iSINK, len(MID)) if norm(MID[i]["w"]).startswith("under"))
iPOT = find("pot")
iHARDIE = find("hardie")
iSTONE = find("stone")
iSIX = find("six", 1, iSTONE)
iSIXTEEN = next(i for i, w in enumerate(MID) if is_money(i, "$16") or norm(w["w"]) == "sixteen")
iNOW = find("now", 1, iSIXTEEN)
CMP = mw(iSIXTEEN) - 0.25  # side-by-side comes in as the difference is spoken


def money_end(i):
    j = i
    if MID[i]["w"].startswith("$"):
        return i
    while not norm(MID[j]["w"]).startswith("dollar"):
        j += 1
    return j


# captions: phrase chunks (<= 5 words), money read-outs merged into one token, active word gold
def mid_chunks():
    out, cur = [], []
    i = 0
    while i < len(MID):
        if i in (iFIVE, iSIX, iSIXTEEN):
            if cur:
                out.append(cur); cur = []
            j = money_end(i)
            text = {iFIVE: B_TOTAL + ".", iSIX: A_TOTAL + ".", iSIXTEEN: "$16,703"}[i]
            if i == iSIXTEEN and j + 1 < len(MID) and norm(MID[j + 1]["w"]) == "more":
                text, j = "$16,703 more.", j + 1
            out.append([(text, i, j)])
            i = j + 1
            continue
        w = MID[i]["w"]
        disp = {"hardy": "Hardie"}.get(w.lower().strip(".,"), w)
        if disp != w and w[-1] in ".,":
            disp += w[-1]
        if i == iSINK - 1 and disp == "a":
            disp = "A"
        j = i
        if norm(w) == "under" and i + 1 < len(MID) and norm(MID[i + 1]["w"]) == "cabinet":
            disp, j = "under-" + MID[i + 1]["w"], i + 1
        cur.append((disp, i, j))
        if MID[j]["w"][-1] in ".,?" or norm(MID[j]["w"]) == "front":  # the take has no comma after "front"
            n = -(-len(cur) // 5)  # balance long phrases into <= 5-word lines
            k = -(-len(cur) // n)
            out += [cur[x:x + k] for x in range(0, len(cur), k)]
            cur = []
        i = j + 1
    if cur:
        out.append(cur)
    return [{"words": [d for d, _, _ in c], "starts": [mw(a) for _, a, _ in c], "end": M0 + MID[c[-1][2]]["e"]} for c in out]


CAPS = mid_chunks() + ([] if not USE_OUTRO else [
    {"words": ["Change", "the", "scope", "out", "loud."], "starts": [ow(k) for k in range(5)], "end": O0 + OUTRO[4]["e"]},
    {"words": ["Watch", "the", "total", "move."], "starts": [ow(k) for k in range(5, 9)], "end": O0 + OUTRO[8]["e"]},
])
cap_html, cap_js = [], []
for c, ch in enumerate(CAPS):
    a = ch["starts"][0]
    nxt = CAPS[c + 1]["starts"][0] if c + 1 < len(CAPS) else T
    b = min(nxt, ch["end"] + 0.6)
    spans = " ".join(f'<span id="w{c}_{k}">{html.escape(w)}</span>' for k, w in enumerate(ch["words"]))
    cap_html.append(f'        <div class="cap" id="c{c}">{spans}</div>')
    cap_js.append(f'      tl.fromTo("#c{c}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: IN }}, {r(a)});')
    cap_js.append(f'      tl.set("#c{c}", {{ opacity: 0 }}, {r(b)});')
    for k, t in enumerate(ch["starts"]):
        cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#d4af37" }}, {r(t)});')
        if k + 1 < len(ch["starts"]):
            cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#ffffff" }}, {r(ch["starts"][k + 1])});')

# ---------- card geometry (card coords 960 x 1040, shown at 0.9) ----------
RX, RW = 36, 888
TOT_TOP, TOT_H = 780, 160
B_ROWS = [("Second-story addition", "3 bed &middot; primary bath &middot; full bath &middot; laundry"),
          ("First floor + basement", "Gut remodel"),
          ("Kitchen", "Mid-sized &middot; 200 sq ft"),
          ("Siding", "Vinyl &middot; whole house")]
b_rows = "\n".join(
    f'              <div class="ent row" id="b_r{i}" style="top:{186 + i * 146}px"><div class="rt">{t}</div><div class="rd">{d}</div></div>'
    for i, (t, d) in enumerate(B_ROWS))
A_SAME = (186, 96)
A_KIT = (298, 252)
A_SID = (566, 196)
KIT_TAGS = [("Sink disposal", iSINK), ("Under-cabinet lights", iUNDER), ("Pot filler", iPOT)]
SID_TAGS = [("Hardie plank front", iHARDIE), ("3 ft stone base back", iSTONE)]
tag = lambda tid, t: f'<span class="tag" id="{tid}">+ {t}</span>'
a_rows = f"""              <div class="ent row same" style="top:{A_SAME[0]}px;height:{A_SAME[1]}px"><div class="rt">Addition + gut remodels</div><div class="rs">Same as Option B</div></div>
              <div class="ent row" id="a_kit" style="top:{A_KIT[0]}px;height:{A_KIT[1]}px"><div class="rt">Kitchen <span class="rd2">&middot; mid-sized &middot; 200 sq ft</span></div>
                <div class="tags">{"".join(tag(f"kt{i}", t) for i, (t, _) in enumerate(KIT_TAGS))}</div></div>
              <div class="ent row" id="a_sid" style="top:{A_SID[0]}px;height:{A_SID[1]}px"><div class="rt">Siding <span class="rd2">&middot; vinyl on 3 sides</span></div>
                <div class="tags">{"".join(tag(f"st{i}", t) for i, (t, _) in enumerate(SID_TAGS))}</div></div>"""

box = lambda top, h: (RX - 10, top - 10, RW + 20, h + 20)
FOCUS = {
    "b": [(mw(iVINYL), box(186 + 3 * 146, 130), ["b_r3"]), (mw(iFIVE), box(TOT_TOP, TOT_H), ["b_tot"])],
    "a": [(mw(iSINK), box(*A_KIT), ["a_kit"]), (mw(iHARDIE), box(*A_SID), ["a_sid"]), (mw(iSIX), box(TOT_TOP, TOT_H), ["a_tot"])],
}
SCR = {"b": (mw(iSAME), mw(iOA)), "a": (mw(iOA), CMP)}
focus_js, focus_html = [], {}
for s, path in FOCUS.items():
    focus_html[s] = "\n".join(
        f'              <div class="fb" id="fb_{s}{k}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'
        for k, (_, (x, y, w, h), _) in enumerate(path))
    for k, (t, (x, y, w, h), rows) in enumerate(path):
        fb = f"#fb_{s}{k}"
        if k == 0:
            focus_js.append(f'      tl.fromTo("{fb}", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: IN }}, {r(t)});')
        else:
            dy = y - path[k - 1][1][1]
            focus_js.append(f'      tl.to("#fb_{s}{k - 1}", {{ y: {dy}, opacity: 0, duration: 0.45, ease: "power3.inOut" }}, {r(t - 0.1)});')
            focus_js.append(f'      tl.fromTo("{fb}", {{ y: {-dy}, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power3.inOut" }}, {r(t - 0.1)});')
        nxt = path[k + 1][0] if k + 1 < len(path) else SCR[s][1] - 0.1
        sel = "[" + ", ".join(f'"#{q}"' for q in rows) + "]"
        focus_js.append(f'      tl.to({sel}, {{ scale: 1.03, duration: 0.35, ease: IN }}, {r(t)});')
        focus_js.append(f'      tl.to({sel}, {{ scale: 1, duration: 0.3, ease: "power2.inOut" }}, {r(nxt - 0.1)});')
tags_js = [f'      tl.fromTo("#kt{i}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {r(mw(w))});'
           for i, (_, w) in enumerate(KIT_TAGS)]
tags_js += [f'      tl.fromTo("#st{i}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {r(mw(w))});'
            for i, (_, w) in enumerate(SID_TAGS)]


def logo(cls, width):
    s = width / 1182
    return (f'<div class="{cls}" data-layout-allow-overflow style="width:{width}px;height:{828 * s:.1f}px">'
            f'<img src="assets/logo.png" alt="Home Estimator" style="width:{1920 * s:.1f}px;height:{1920 * s:.1f}px;'
            f'left:{-374 * s:.1f}px;top:{-476 * s:.1f}px" /></div>')


def bar(title, tag_text):
    return (f'<div class="bar"><span class="dots"><i></i><i></i><i></i></span>{logo("lg", 40)}'
            f'<div class="ti">{title}</div><div class="btag">{tag_text}</div></div>')


json.dump({"T": T, "vo": [["hook_t.wav", H0], ["mid_t.wav", M0]] + ([["outro_t.wav", O0]] if USE_OUTRO else []),
           "music": [[0.0, round(SPLICE, 2), 2.45], [round(SPLICE, 2), T, round(122.95 - END0, 2)]]},
          open("timing.json", "w"))

doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Option A vs Option B Reel</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      :root {{
        --navy: #171a2e;
        --card: #2d2d44;
        --line: #3a3a55;
        --sand: #c9a96e;
        --gold: #d4af37;
        --gray: #a0aab2;
        --white: #ffffff;
        --ink: #171a2e;
        --muted: #586074;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: var(--navy); }}
      body {{ font-family: "Inter", sans-serif; color: var(--white); }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--navy); }}
      #bg {{ position: absolute; inset: 0; background: var(--navy); }}
      .lg {{ position: relative; overflow: hidden; }}
      .lg img {{ position: absolute; max-width: none; }}
      #top {{ position: absolute; left: 494px; top: 226px; opacity: 0; }}
      #labels {{ position: absolute; left: 0; top: 300px; width: 1080px; height: 240px; perspective: 900px; }}
      .lab {{ position: absolute; left: 0; top: 0; width: 1080px; text-align: center; opacity: 0; }}
      .lab .big {{ display: block; font-size: 128px; font-weight: 900; letter-spacing: -4px; line-height: 1.02; }}
      .lab .sub {{ display: block; margin-top: 6px; font-size: 46px; font-weight: 700; color: var(--white); }}
      #labB .big {{ color: var(--sand); }}
      #labA .big {{ color: var(--gold); }}
      #lab0 {{ top: 40px; }}
      #lab0 .big {{ font-size: 84px; letter-spacing: -2px; color: var(--white); }}
      #stage {{ position: absolute; left: 0; top: 548px; width: 1080px; height: 920px; perspective: 2200px; }}
      #float {{ position: absolute; left: 60px; top: 0; width: 960px; height: 1040px; transform-style: preserve-3d; transform-origin: 50% 0; }}
      .scr {{ position: absolute; inset: 0; border-radius: 34px; overflow: hidden; background: #f3f4f9; opacity: 0;
        box-shadow: 0 50px 90px rgba(5, 6, 14, 0.55), 0 12px 24px rgba(5, 6, 14, 0.35); }}
      .bar {{ position: absolute; left: 0; top: 0; width: 960px; height: 104px; background: #ffffff; border-bottom: 2px solid #e1e4ec;
        display: flex; align-items: center; gap: 18px; padding: 0 36px; }}
      .dots {{ display: flex; gap: 10px; }}
      .dots i {{ display: block; width: 16px; height: 16px; border-radius: 8px; background: #d5d9e3; }}
      .bar .ti {{ font-size: 38px; font-weight: 800; color: var(--ink); letter-spacing: -0.5px; }}
      .bar .btag {{ margin-left: auto; height: 52px; padding: 0 22px; border-radius: 26px; font-size: 32px; font-weight: 900;
        letter-spacing: 2px; display: flex; align-items: center; }}
      #b .btag {{ border: 3px solid var(--sand); color: #8a6a2e; }}
      #a .btag {{ background: var(--gold); color: var(--navy); }}
      .kick {{ position: absolute; left: 36px; top: 132px; font-size: 32px; font-weight: 800; letter-spacing: 3px; color: var(--muted); }}
      .row {{ position: absolute; left: {RX}px; width: {RW}px; height: 130px; background: #ffffff; border-radius: 20px;
        border: 2px solid #e4e7ef; padding: 22px 32px; box-shadow: 0 8px 18px rgba(23, 26, 46, 0.07); }}
      .rt {{ font-size: 40px; font-weight: 800; color: var(--ink); letter-spacing: -0.5px; white-space: nowrap; }}
      .rd {{ margin-top: 8px; font-size: 32px; font-weight: 500; color: var(--muted); white-space: nowrap; }}
      .rd2 {{ font-size: 32px; font-weight: 600; color: var(--muted); letter-spacing: 0; }}
      .same {{ display: flex; align-items: center; justify-content: space-between; padding: 0 32px; background: #eceef4; box-shadow: none; }}
      .same .rt {{ font-size: 34px; color: var(--muted); }}
      .rs {{ font-size: 32px; font-weight: 700; color: var(--muted); }}
      .tags {{ display: flex; flex-wrap: wrap; gap: 14px; margin-top: 18px; }}
      .tag {{ display: inline-flex; align-items: center; height: 60px; padding: 0 22px; border-radius: 30px; background: #fbf1d2;
        border: 2px solid var(--gold); font-size: 32px; font-weight: 800; color: #6b4f0a; opacity: 0; }}
      .tot {{ position: absolute; left: {RX}px; top: {TOT_TOP}px; width: {RW}px; height: {TOT_H}px; background: var(--navy);
        border-radius: 22px; padding: 26px 32px; box-shadow: 0 16px 30px rgba(23, 26, 46, 0.35); }}
      .tot .tl {{ font-size: 32px; font-weight: 800; letter-spacing: 4px; color: var(--gray); }}
      .tot .tv {{ position: absolute; right: 32px; top: 34px; font-size: 88px; font-weight: 900; letter-spacing: -2px; line-height: 1;
        font-variant-numeric: tabular-nums; }}
      .tot .tn {{ position: absolute; left: 32px; top: 90px; font-size: 32px; font-weight: 700; }}
      #b .tn {{ color: var(--sand); }}
      #a .tn {{ color: var(--gold); }}
      .fine {{ position: absolute; left: 0; top: 968px; width: 960px; text-align: center; font-size: 32px; font-weight: 500; color: var(--muted); }}
      .fb {{ position: absolute; border: 5px solid var(--gold); border-radius: 26px; opacity: 0; }}
      #hook {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center; perspective: 1200px; }}
      .hs {{ font-size: 64px; font-weight: 800; letter-spacing: -1px; }}
      .hb {{ font-size: 140px; font-weight: 900; letter-spacing: -4px; line-height: 1.02; margin-bottom: 40px; }}
      #h2, #hb2, #h3, #h4 {{ opacity: 0; }}
      #hb1 {{ color: var(--gold); }}
      #hb2 {{ color: var(--sand); }}
      #h3 {{ font-size: 72px; font-weight: 900; margin-top: 6px; }}
      #h4 {{ margin-top: 16px; font-size: 46px; font-weight: 600; color: var(--gray); }}
      .cap {{ position: absolute; left: 40px; top: 1520px; width: 1000px; text-align: center; font-size: 56px; font-weight: 900;
        letter-spacing: -1px; line-height: 1.1; white-space: nowrap; opacity: 0; }}
      #cmp {{ position: absolute; inset: 0; perspective: 2000px; }}
      .pnl {{ position: absolute; left: 80px; width: 920px; height: 236px; background: var(--card); border: 2px solid var(--line);
        border-radius: 28px; padding: 34px 44px; opacity: 0; box-shadow: 0 40px 70px rgba(5, 6, 14, 0.5); }}
      .pnl .pk {{ font-size: 36px; font-weight: 800; letter-spacing: 1px; }}
      .pnl .pv {{ margin-top: 12px; font-size: 104px; font-weight: 900; letter-spacing: -3px; line-height: 1; }}
      #pB {{ top: 430px; }}
      #pB .pk, #pB .pv {{ color: var(--sand); }}
      #pA {{ top: 700px; }}
      #pA .pk {{ color: var(--gold); }}
      #pA .pv {{ color: var(--white); }}
      #dif {{ position: absolute; left: 0; top: 990px; width: 1080px; text-align: center; opacity: 0; }}
      #dif .dk {{ font-size: 36px; font-weight: 800; letter-spacing: 5px; color: var(--gray); }}
      #dif .dv {{ margin-top: 6px; font-size: 140px; font-weight: 900; letter-spacing: -4px; color: var(--gold); line-height: 1.05; }}
      #cfine {{ position: absolute; left: 0; top: 1250px; width: 1080px; text-align: center; font-size: 32px; font-weight: 500;
        color: var(--gray); opacity: 0; }}
      #outro {{ position: absolute; inset: 0; background: var(--navy); }}
      #outro-in {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
      #outro-rule {{ width: 300px; height: 4px; background: var(--gold); margin: 70px 0 56px; }}
      #outro-line {{ font-size: 54px; font-weight: 500; }}
      #outro-cta {{ margin-top: 30px; font-size: 72px; font-weight: 900; color: var(--gold); letter-spacing: 1px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{r(T)}" data-width="1080" data-height="1920">
      <div id="bg" class="clip" data-start="0" data-duration="{r(T)}" data-track-index="0"></div>
      <audio id="mix" src="assets/reel_mix.m4a" data-start="0" data-duration="{r(T)}" data-track-index="10" data-volume="1"></audio>

      <section id="main-sec" class="clip" data-start="0" data-duration="{r(END0)}" data-track-index="1">
        <div id="top">{logo("lg", 91)}</div>
        <div id="labels">
          <div class="lab" id="lab0"><span class="big">Same house. Two prices.</span></div>
          <div class="lab" id="labB"><span class="big">OPTION B</span><span class="sub">The base scope</span></div>
          <div class="lab" id="labA"><span class="big">OPTION A</span><span class="sub">What the client wants</span></div>
        </div>
        <div id="stage" data-layout-allow-occlusion data-layout-allow-overlap data-layout-allow-overflow>
          <div id="float">
            <div class="scr" id="b">
              {bar("Project estimate", "OPTION B")}
              <div class="ent kick">SCOPE &middot; RANCH HOUSE</div>
{b_rows}
              <div class="ent tot" id="b_tot"><div class="tl">TOTAL</div><div class="tn">Base scope</div><div class="tv">{B_TOTAL}</div></div>
              <div class="ent fine">{FINE}</div>
{focus_html["b"]}
            </div>
            <div class="scr" id="a">
              {bar("Project estimate", "OPTION A")}
              <div class="ent kick">SCOPE &middot; RANCH HOUSE</div>
{a_rows}
              <div class="ent tot" id="a_tot"><div class="tl">TOTAL</div><div class="tn">With upgrades</div><div class="tv" id="tvA">{B_TOTAL}</div></div>
              <div class="ent fine">{FINE}</div>
{focus_html["a"]}
            </div>
          </div>
        </div>
        <div id="hook">
          <div class="hs" id="h1">Your client loves</div>
          <div class="hb" id="hb1">OPTION A.</div>
          <div class="hs" id="h2">Their budget loves</div>
          <div class="hb" id="hb2">OPTION B.</div>
          <div id="h3">Show them both.</div>
          <div class="hs" id="h4">before they fall for the plan.</div>
        </div>
        <div id="cmp" data-layout-allow-overflow>
          <div class="pnl" id="pB"><div class="pk">OPTION B &middot; Base scope</div><div class="pv">{B_TOTAL}</div></div>
          <div class="pnl" id="pA"><div class="pk">OPTION A &middot; Upgraded kitchen + siding</div><div class="pv">{A_TOTAL}</div></div>
          <div id="dif"><div class="dk">DIFFERENCE</div><div class="dv">{DIFF}</div></div>
          <div id="cfine">{FINE}</div>
        </div>
{chr(10).join(cap_html)}
      </section>

      <section id="outro" class="clip" data-start="{r(END0)}" data-duration="{r(T - END0)}" data-track-index="2">
        <div id="outro-in">
          <div id="outro-logo">{logo("lg", 560)}</div>
          <div id="outro-rule"></div>
          <div id="outro-line">Visit HomeEstimator.ai to learn more</div>
          <div id="outro-cta">BOOK A DEMO</div>
        </div>
      </section>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const IN = "power3.out";
      const OUT = "power2.in";
      const fmt = (v) => "$" + Math.round(v).toLocaleString("en-US");

      // hook: type only on flat navy; the first frame already reads "Your client loves OPTION A."
      tl.fromTo("#h2", {{ opacity: 0, rotationX: -80, y: 30 }}, {{ opacity: 1, rotationX: 0, y: 0, duration: 0.5, ease: IN }}, {r(hw(5))});
      tl.fromTo("#hb2", {{ opacity: 0, rotationX: -80, y: 40 }}, {{ opacity: 1, rotationX: 0, y: 0, duration: 0.55, ease: IN }}, {r(hw(8))});
      tl.fromTo("#h3", {{ opacity: 0, rotationX: -80, y: 30 }}, {{ opacity: 1, rotationX: 0, y: 0, duration: 0.5, ease: IN }}, {r(hw(10))});
      tl.fromTo("#h4", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(hw(13))});
      tl.to("#hook", {{ opacity: 0, y: -40, duration: 0.35, ease: OUT }}, {r(M0 - 0.45)});
      tl.set("#hook", {{ visibility: "hidden" }}, {r(M0)});
      tl.fromTo("#top", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(M0)});

      // labels: "Same house. Two prices." -> OPTION B -> OPTION A
      tl.fromTo("#lab0", {{ opacity: 0, rotationX: -70, y: 20 }}, {{ opacity: 1, rotationX: 0, y: 0, duration: 0.55, ease: IN }}, {r(mw(iSAME))});
      tl.to("#lab0", {{ opacity: 0, rotationX: 60, duration: 0.3, ease: OUT }}, {r(mw(iOB) - 0.3)});
      tl.fromTo("#labB", {{ opacity: 0, rotationX: -70, y: 20 }}, {{ opacity: 1, rotationX: 0, y: 0, duration: 0.55, ease: IN }}, {r(mw(iOB))});
      tl.to("#labB", {{ opacity: 0, rotationX: 60, duration: 0.3, ease: OUT }}, {r(mw(iOA) - 0.3)});
      tl.fromTo("#labA", {{ opacity: 0, rotationX: -70, y: 20 }}, {{ opacity: 1, rotationX: 0, y: 0, duration: 0.55, ease: IN }}, {r(mw(iOA))});
      tl.to("#labA", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(CMP - 0.3)});

      // the app window floats gently while the options play
      tl.fromTo("#float", {{ scale: 0.86, rotationX: 7, rotationY: -8, y: 6 }}, {{ scale: 0.86, rotationX: 3, rotationY: -3, y: -8, duration: {r(CMP - M0 - 0.1)}, ease: "sine.inOut" }}, {r(M0 - 0.1)});

      // Option B card turns in; Option A card turns in on "Option A"
      tl.fromTo("#b", {{ rotationY: 32, x: 260, z: -220 }}, {{ rotationY: 0, x: 0, z: 0, duration: 0.7, ease: IN }}, {r(M0 - 0.1)});
      tl.fromTo("#b", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.14, ease: "none" }}, {r(M0 - 0.1)});
      tl.fromTo("#b .ent", {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: IN, stagger: 0.06 }}, {r(M0 - 0.05)});
      tl.to("#b", {{ rotationY: -32, x: -260, z: -220, duration: 0.32, ease: OUT }}, {r(mw(iOA) - 0.3)});
      tl.to("#b", {{ opacity: 0, duration: 0.14, ease: "none" }}, {r(mw(iOA) - 0.12)});
      tl.fromTo("#a", {{ rotationY: 32, x: 260, z: -220 }}, {{ rotationY: 0, x: 0, z: 0, duration: 0.7, ease: IN }}, {r(mw(iOA) + 0.02)});
      tl.fromTo("#a", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.14, ease: "none" }}, {r(mw(iOA) + 0.02)});
      tl.fromTo("#a .ent", {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: IN, stagger: 0.06 }}, {r(mw(iOA) + 0.06)});

      // gold focus box glides to each spoken item; the item lifts
{chr(10).join(focus_js)}

      // what Option A adds: gold "+" tags pop in as they're named
{chr(10).join(tags_js)}

      // Option A total moves from the base price to the new one
      const cnt = {{ v: 590279 }};
      tl.to(cnt, {{ v: 606982, duration: 1.0, ease: "power2.out", onUpdate: () => {{
        document.getElementById("tvA").textContent = fmt(cnt.v);
      }} }}, {r(mw(iSIX))});
      tl.set("#tvA", {{ textContent: "{A_TOTAL}" }}, {r(mw(iSIX) + 1.0)});

      // captions
{chr(10).join(cap_js)}

      // side-by-side: the card turns away, both options turn in, the difference pops
      tl.to("#a", {{ rotationY: -32, x: -260, z: -220, duration: 0.32, ease: OUT }}, {r(CMP - 0.3)});
      tl.to("#a", {{ opacity: 0, duration: 0.14, ease: "none" }}, {r(CMP - 0.12)});
      tl.to("#top", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(CMP - 0.1)});
      tl.fromTo("#pB", {{ opacity: 0, rotationY: 35, x: 160 }}, {{ opacity: 1, rotationY: 0, x: 0, duration: 0.6, ease: IN }}, {r(CMP + 0.05)});
      tl.fromTo("#pA", {{ opacity: 0, rotationY: 35, x: 160 }}, {{ opacity: 1, rotationY: 0, x: 0, duration: 0.6, ease: IN }}, {r(CMP + 0.2)});
      tl.fromTo("#dif", {{ opacity: 0, scale: 0.85, y: 20 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "back.out(1.6)" }}, {r(mw(iSIXTEEN))});
      tl.fromTo("#cfine", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(mw(iSIXTEEN) + 0.3)});

      // end card
      tl.fromTo("#outro-logo", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: IN }}, {r(END0 + 0.05)});
      tl.fromTo("#outro-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: IN }}, {r(END0 + 0.4)});
      tl.fromTo("#outro-line", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(END0 + 0.65)});
      tl.fromTo("#outro-cta", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(END0 + 0.9)});

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open("index.html", "w").write(doc)
print("outro", USE_OUTRO, "T", T, "mid end", r(MID_END), "outro", r(O0), "end card", r(END0), "captions", len(CAPS))
