"""Generate the Reel #2 "Option A vs Option B" composition (index.html), v2 with a 3D app window.

Recreated estimate UI (no app footage), Desmond VO only. On-screen cues follow the
VO word starts (word start - 0.08 s). Word timings come from asr.py on the tightened VO.
v2: clean type-only hook on flat navy, a floating tilted app window whose screens turn and
slide into each other, one gold focus box per screen that glides to each spoken item,
row pops, and the total counting from Option B to Option A on "updated price".
Usage: python3 gen.py <dir with hook_tw.json, mid_tw.json, outro_tw.json>
"""
import html, json, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "../../../reel2/in"
HOOK = json.load(open(f"{SRC}/hook_tw.json"))
MID = json.load(open(f"{SRC}/mid_tw.json"))
OUTRO = json.load(open(f"{SRC}/outro_tw.json"))

H0, M0, O0 = 0.10, 7.70, 32.35  # VO placement (s)
END0, T = 35.90, 39.50  # end card start, total length
LEAD = 0.08
r = lambda x: f"{x:.2f}"
hw = lambda i: H0 + HOOK[i]["s"] - LEAD
mw = lambda i: M0 + MID[i]["s"] - LEAD
ow = lambda i: O0 + OUTRO[i]["s"] - LEAD

B_TOTAL, A_TOTAL, DIFF = "$590,279", "$606,982", "+$16,703"
FINE = "Example project &mdash; every project&rsquo;s estimate differs."

S1, S2, S3, S4, CMP = mw(0), mw(12), mw(25), mw(45), 32.20
STEPS = [("st1", "STEP 1", "Start with the base scope", S1, S2),
         ("st2", "STEP 2", "Add it by voice", S2, S3),
         ("st3", "STEP 3", "Change the siding", S3, S4),
         ("st4", "RESULT", "Updated price", S4, CMP)]


def chunk(words, src, base, idx, end_idx):
    return {"words": words, "starts": [base + src[i]["s"] - LEAD for i in idx], "end": base + src[end_idx]["e"]}


# captions: <= 5 words, active word gold
CAPS = [
    chunk(["Start", "with", "the", "base", "scope,"], MID, M0, [0, 1, 2, 3, 4], 4),
    chunk(["vinyl", "siding", "on"], MID, M0, [5, 6, 7], 7),
    chunk(["the", "whole", "house."], MID, M0, [8, 9, 10], 10),
    chunk([B_TOTAL + "."], MID, M0, [11], 11),
    chunk(["Now,", "add", "it", "by", "voice."], MID, M0, [12, 13, 14, 15, 16], 16),
    chunk(["Sink", "disposal."], MID, M0, [17, 18], 18),
    chunk(["Under-cabinet", "lights."], MID, M0, [19, 21], 21),
    chunk(["A", "pot", "filler."], MID, M0, [22, 23, 24], 24),
    chunk(["Change", "the", "siding."], MID, M0, [25, 26, 27], 27),
    chunk(["Vinyl", "on", "three", "sides,"], MID, M0, [28, 29, 30, 31], 31),
    chunk(["Hardie", "plank", "on", "the", "front,"], MID, M0, [32, 33, 34, 35, 36], 36),
    chunk(["and", "a", "three-foot", "stone"], MID, M0, [37, 38, 39, 40], 40),
    chunk(["base", "at", "the", "back."], MID, M0, [41, 42, 43, 44], 44),
    chunk(["Ask", "for", "the", "updated", "price."], MID, M0, [45, 46, 47, 48, 49], 49),
    chunk([A_TOTAL + "."], MID, M0, [50], 59),
    chunk(["Change", "the", "scope", "out", "loud."], OUTRO, O0, [0, 1, 2, 3, 4], 4),
    chunk(["Watch", "the", "total", "move."], OUTRO, O0, [5, 6, 7, 8], 8),
]
cap_html, cap_js = [], []
for c, ch in enumerate(CAPS):
    a = ch["starts"][0]
    nxt = CAPS[c + 1]["starts"][0] if c + 1 < len(CAPS) else T
    b = CMP if c == 14 else min(nxt, ch["end"] + 0.6)
    spans = " ".join(f'<span id="w{c}_{k}">{html.escape(w)}</span>' for k, w in enumerate(ch["words"]))
    cap_html.append(f'        <div class="cap" id="c{c}">{spans}</div>')
    cap_js.append(f'      tl.fromTo("#c{c}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: IN }}, {r(a)});')
    cap_js.append(f'      tl.set("#c{c}", {{ opacity: 0 }}, {r(b)});')
    for k, t in enumerate(ch["starts"]):
        cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#d4af37" }}, {r(t)});')
        if k + 1 < len(ch["starts"]):
            cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#ffffff" }}, {r(ch["starts"][k + 1])});')

steps_html = "\n".join(
    f'          <div class="step" id="{sid}"><span class="k">{k}</span><span class="t">{html.escape(t)}</span></div>'
    for sid, k, t, _, _ in STEPS)
steps_js = []
for sid, _, _, a, b in STEPS:
    steps_js.append(f'      tl.fromTo("#{sid}", {{ opacity: 0, rotationX: -70, y: 20 }}, '
                    f'{{ opacity: 1, rotationX: 0, y: 0, duration: 0.55, ease: IN }}, {r(a)});')
    steps_js.append(f'      tl.to("#{sid}", {{ opacity: 0, rotationX: 60, duration: 0.3, ease: OUT }}, {r(b - 0.3)});')

# ---------- app window screens (card coords: 960 x 1040) ----------
RX, RW = 36, 888  # row x / width inside the card


def row_box(top, h):
    return (RX - 10, top - 10, RW + 20, h + 20)


EST_TOP, EST_H, EST_GAP = 186, 130, 146
TOT_TOP, TOT_H = 780, 160


def est_rows(sid, kitchen, siding):
    rows = [("Second-story addition", "3 bed &middot; primary bath &middot; full bath &middot; laundry"),
            ("First floor + basement", "Gut remodel"), ("Kitchen", kitchen), ("Siding", siding)]
    return "\n".join(
        f'              <div class="ent row" id="{sid}r{i}" style="top:{EST_TOP + i * EST_GAP}px"><div class="rt">{t}</div>'
        f'<div class="rd">{d}</div></div>' for i, (t, d) in enumerate(rows))


ADDONS = ["Sink disposal", "Under-cabinet lights", "Pot filler", "Second sink", "Sound solution", "Reverse osmosis filter"]
OPT_TOP, OPT_H, OPT_GAP = 186, 110, 124
addon_rows = "\n".join(
    f'              <div class="ent row opt" id="s2r{i}" style="top:{OPT_TOP + i * OPT_GAP}px"><div class="cb" id="cb{i}">'
    f'<span id="ck{i}">&#10003;</span></div><div class="ot">{t}</div></div>' for i, t in enumerate(ADDONS))

SID_TOP, SID_H, SID_GAP = 186, 148, 164
SIDES = ["Front", "Left side", "Right side", "Back"]
side_rows = "\n".join(
    f'              <div class="ent row side" id="s3r{i}" style="top:{SID_TOP + i * SID_GAP}px"><div class="rt">{t}</div>'
    f'<div class="sv" id="sv{i}">Vinyl</div></div>' for i, t in enumerate(SIDES))

# focus path per screen: (time, box, rows that lift)
FOCUS = {
    "s1": [(mw(5), row_box(EST_TOP + 3 * EST_GAP, EST_H), ["s1r3"]),
           (mw(11), row_box(TOT_TOP, TOT_H), ["s1tot"])],
    "s2": [(mw(17), row_box(OPT_TOP, OPT_H), ["s2r0"]),
           (mw(19), row_box(OPT_TOP + OPT_GAP, OPT_H), ["s2r1"]),
           (mw(22), row_box(OPT_TOP + 2 * OPT_GAP, OPT_H), ["s2r2"])],
    "s3": [(mw(28), (RX - 10, SID_TOP + SID_GAP - 10, RW + 20, 2 * SID_GAP + SID_H + 20), ["s3r1", "s3r2", "s3r3"]),
           (mw(32), row_box(SID_TOP, SID_H), ["s3r0"]),
           (mw(37), row_box(SID_TOP + 3 * SID_GAP, SID_H), ["s3r3"])],
    "s4": [(mw(50), row_box(TOT_TOP, TOT_H), ["s4tot"])],
}
SCR_END = {"s1": S2, "s2": S3, "s3": S4, "s4": CMP}
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
            py = path[k - 1][1][1]
            dy = y - py
            focus_js.append(f'      tl.to("#fb_{s}{k - 1}", {{ y: {dy}, opacity: 0, duration: 0.45, ease: "power3.inOut" }}, {r(t - 0.1)});')
            focus_js.append(f'      tl.fromTo("{fb}", {{ y: {-dy}, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power3.inOut" }}, {r(t - 0.1)});')
        nxt = path[k + 1][0] if k + 1 < len(path) else SCR_END[s] - 0.1
        sel = "[" + ", ".join(f'"#{q}"' for q in rows) + "]"
        focus_js.append(f'      tl.to({sel}, {{ scale: 1.03, duration: 0.35, ease: IN }}, {r(t)});')
        focus_js.append(f'      tl.to({sel}, {{ scale: 1, duration: 0.3, ease: "power2.inOut" }}, {r(nxt - 0.1)});')

# screen transitions: turn + slide (out to the left, in from the right)
SCREENS = [("s1", S1), ("s2", S2), ("s3", S3), ("s4", S4)]
screen_js = []
for i, (s, t) in enumerate(SCREENS):
    t_in = t - 0.1 if i == 0 else t + 0.02
    if i:
        prev = SCREENS[i - 1][0]
        screen_js.append(f'      tl.to("#{prev}", {{ rotationY: -32, x: -260, z: -220, duration: 0.32, ease: OUT }}, {r(t - 0.3)});')
        screen_js.append(f'      tl.to("#{prev}", {{ opacity: 0, duration: 0.14, ease: "none" }}, {r(t - 0.12)});')
    screen_js.append(f'      tl.fromTo("#{s}", {{ rotationY: 32, x: 260, z: -220 }}, {{ rotationY: 0, x: 0, z: 0, duration: 0.7, ease: IN }}, {r(t_in)});')
    screen_js.append(f'      tl.fromTo("#{s}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.14, ease: "none" }}, {r(t_in)});')
    screen_js.append(f'      tl.fromTo("#{s} .ent", {{ opacity: 0, y: 26 }}, '
                     f'{{ opacity: 1, y: 0, duration: 0.4, ease: IN, stagger: 0.06 }}, {r(t_in + 0.04)});')


def logo(cls, width):
    s = width / 1182
    return (f'<div class="{cls}" data-layout-allow-overflow style="width:{width}px;height:{828 * s:.1f}px">'
            f'<img src="assets/logo.png" alt="Home Estimator" style="width:{1920 * s:.1f}px;height:{1920 * s:.1f}px;'
            f'left:{-374 * s:.1f}px;top:{-476 * s:.1f}px" /></div>')


def bar(title, tag):
    return (f'<div class="bar"><span class="dots"><i></i><i></i><i></i></span>{logo("lg", 40)}'
            f'<div class="ti">{title}</div><div class="tag">{tag}</div></div>')


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
      #steps {{ position: absolute; left: 0; top: 296px; width: 1080px; height: 120px; perspective: 900px; }}
      .step {{ position: absolute; left: 0; top: 0; width: 1080px; text-align: center; opacity: 0; }}
      .step .k {{ display: block; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: var(--gold); }}
      .step .t {{ display: block; margin-top: 4px; font-size: 52px; font-weight: 900; letter-spacing: -1px; }}
      #stage {{ position: absolute; left: 0; top: 430px; width: 1080px; height: 1060px; perspective: 2200px; }}
      #float {{ position: absolute; left: 60px; top: 0; width: 960px; height: 1040px; transform-style: preserve-3d; }}
      .scr {{ position: absolute; inset: 0; border-radius: 34px; overflow: hidden; background: #f3f4f9; opacity: 0;
        box-shadow: 0 50px 90px rgba(5, 6, 14, 0.55), 0 12px 24px rgba(5, 6, 14, 0.35); }}
      .bar {{ position: absolute; left: 0; top: 0; width: 960px; height: 104px; background: #ffffff; border-bottom: 2px solid #e1e4ec;
        display: flex; align-items: center; gap: 18px; padding: 0 36px; }}
      .dots {{ display: flex; gap: 10px; }}
      .dots i {{ display: block; width: 16px; height: 16px; border-radius: 8px; background: #d5d9e3; }}
      .bar .ti {{ font-size: 38px; font-weight: 800; color: var(--ink); letter-spacing: -0.5px; }}
      .bar .tag {{ margin-left: auto; font-size: 32px; font-weight: 600; color: var(--muted); }}
      .kick {{ position: absolute; left: 36px; top: 132px; font-size: 32px; font-weight: 800; letter-spacing: 3px; color: var(--muted); }}
      .row {{ position: absolute; left: {RX}px; width: {RW}px; height: {EST_H}px; background: #ffffff; border-radius: 20px;
        border: 2px solid #e4e7ef; padding: 22px 32px; box-shadow: 0 8px 18px rgba(23, 26, 46, 0.07); }}
      .rt {{ font-size: 40px; font-weight: 800; color: var(--ink); letter-spacing: -0.5px; }}
      .rd {{ margin-top: 8px; font-size: 32px; font-weight: 500; color: var(--muted); white-space: nowrap; }}
      .tot {{ position: absolute; left: {RX}px; top: {TOT_TOP}px; width: {RW}px; height: {TOT_H}px; background: var(--navy);
        border-radius: 22px; padding: 26px 32px; box-shadow: 0 16px 30px rgba(23, 26, 46, 0.35); }}
      .tot .tl {{ font-size: 32px; font-weight: 800; letter-spacing: 4px; color: var(--gray); }}
      .chip {{ position: absolute; left: 32px; top: 82px; height: 52px; padding: 0 22px; border-radius: 26px; font-size: 32px;
        font-weight: 900; letter-spacing: 2px; display: flex; align-items: center; opacity: 0; }}
      .chip.b {{ border: 3px solid var(--sand); color: var(--sand); }}
      .chip.a {{ background: var(--gold); color: var(--navy); }}
      .tot .tv {{ position: absolute; right: 32px; top: 34px; font-size: 88px; font-weight: 900; letter-spacing: -2px; line-height: 1;
        font-variant-numeric: tabular-nums; }}
      .fine {{ position: absolute; left: 0; top: 968px; width: 960px; text-align: center; font-size: 32px; font-weight: 500; color: var(--muted); }}
      .opt {{ height: {OPT_H}px; display: flex; align-items: center; gap: 28px; padding: 0 32px; }}
      .cb {{ width: 56px; height: 56px; border-radius: 12px; border: 3px solid #c3c8d6; display: flex; align-items: center;
        justify-content: center; font-size: 38px; font-weight: 900; color: #ffffff; }}
      .cb span {{ opacity: 0; }}
      .ot {{ font-size: 40px; font-weight: 700; color: var(--ink); }}
      .side {{ height: {SID_H}px; display: flex; align-items: center; justify-content: space-between; }}
      .sv {{ text-align: right; font-size: 40px; font-weight: 800; color: var(--ink); line-height: 1.15; }}
      .sv small {{ display: block; font-size: 32px; font-weight: 700; color: #8a6a14; }}
      .note {{ position: absolute; left: 0; top: 880px; width: 960px; text-align: center; font-size: 32px; font-weight: 500; color: var(--muted); }}
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
      .cap {{ position: absolute; left: 40px; top: 1508px; width: 1000px; text-align: center; font-size: 56px; font-weight: 900;
        letter-spacing: -1px; line-height: 1.1; white-space: nowrap; opacity: 0; }}
      #cmp {{ position: absolute; inset: 0; perspective: 2000px; }}
      .pnl {{ position: absolute; left: 80px; width: 920px; height: 236px; background: var(--card); border: 2px solid var(--line);
        border-radius: 28px; padding: 34px 44px; opacity: 0; box-shadow: 0 40px 70px rgba(5, 6, 14, 0.5); }}
      .pnl .pk {{ font-size: 36px; font-weight: 800; letter-spacing: 1px; }}
      .pnl .pv {{ margin-top: 12px; font-size: 104px; font-weight: 900; letter-spacing: -3px; line-height: 1; }}
      #pB {{ top: 470px; }}
      #pB .pk, #pB .pv {{ color: var(--sand); }}
      #pA {{ top: 740px; }}
      #pA .pk, #pA .pv {{ color: var(--white); }}
      #dif {{ position: absolute; left: 0; top: 1030px; width: 1080px; text-align: center; opacity: 0; }}
      #dif .dk {{ font-size: 36px; font-weight: 800; letter-spacing: 5px; color: var(--gray); }}
      #dif .dv {{ margin-top: 6px; font-size: 140px; font-weight: 900; letter-spacing: -4px; color: var(--gold); line-height: 1.05; }}
      #cfine {{ position: absolute; left: 0; top: 1290px; width: 1080px; text-align: center; font-size: 32px; font-weight: 500;
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
        <div id="steps">
{steps_html}
        </div>
        <div id="stage" data-layout-allow-occlusion data-layout-allow-overlap data-layout-allow-overflow>
          <div id="float">
            <div class="scr" id="s1">
              {bar("Project estimate", "Option B")}
              <div class="ent kick">SCOPE &middot; RANCH HOUSE</div>
{est_rows("s1", "Mid-sized &middot; 200 sq ft", "Vinyl &middot; whole house")}
              <div class="ent tot" id="s1tot"><div class="tl">TOTAL</div><div class="chip b" id="chipB">OPTION B</div><div class="tv">{B_TOTAL}</div></div>
              <div class="ent fine">{FINE}</div>
{focus_html["s1"]}
            </div>
            <div class="scr" id="s2">
              {bar("Kitchen", "Mid-sized &middot; 200 sq ft")}
              <div class="ent kick">ADD-ONS</div>
{addon_rows}
{focus_html["s2"]}
            </div>
            <div class="scr" id="s3">
              {bar("Siding", "By elevation")}
              <div class="ent kick">MATERIAL PER SIDE</div>
{side_rows}
              <div class="ent note">Base scope: vinyl on the whole house</div>
{focus_html["s3"]}
            </div>
            <div class="scr" id="s4">
              {bar("Project estimate", "Option A")}
              <div class="ent kick">SCOPE &middot; RANCH HOUSE</div>
{est_rows("s4", "Mid-sized &middot; 200 sq ft &middot; 3 add-ons", "Vinyl 3 sides &middot; Hardie front &middot; stone base")}
              <div class="ent tot" id="s4tot"><div class="tl">TOTAL</div><div class="chip b" id="chipB2" style="opacity:1">OPTION B</div>
                <div class="chip a" id="chipA">OPTION A</div><div class="tv" id="tvA">{B_TOTAL}</div></div>
              <div class="ent fine">{FINE}</div>
{focus_html["s4"]}
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
{chr(10).join(cap_html[:15])}
        <div id="cmp" data-layout-allow-overflow>
          <div class="pnl" id="pB"><div class="pk">OPTION B &middot; Base scope</div><div class="pv">{B_TOTAL}</div></div>
          <div class="pnl" id="pA"><div class="pk">OPTION A &middot; Upgraded kitchen + siding</div><div class="pv">{A_TOTAL}</div></div>
          <div id="dif"><div class="dk">DIFFERENCE</div><div class="dv">{DIFF}</div></div>
          <div id="cfine">{FINE}</div>
        </div>
{chr(10).join(cap_html[15:])}
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
      tl.to("#hook", {{ opacity: 0, y: -40, duration: 0.35, ease: OUT }}, {r(S1 - 0.45)});
      tl.set("#hook", {{ visibility: "hidden" }}, {r(S1)});
      tl.fromTo("#top", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(S1)});

      // the app window floats gently while the steps play
      tl.fromTo("#float", {{ rotationX: 7, rotationY: -8, y: 6 }}, {{ rotationX: 3, rotationY: -3, y: -8, duration: {r(CMP - S1 - 0.05)}, ease: "sine.inOut" }}, {r(S1 - 0.1)});

      // screens turn and slide into each other
{chr(10).join(screen_js)}

      // gold focus box glides to each spoken item; the item lifts
{chr(10).join(focus_js)}

      // step 1: OPTION B chip on the base total
      tl.fromTo("#chipB", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.45, ease: IN }}, {r(mw(11))});

      // step 2: tick the add-ons
      tl.set("#cb0", {{ backgroundColor: "#171a2e", borderColor: "#171a2e" }}, {r(mw(17))});
      tl.fromTo("#ck0", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {r(mw(17))});
      tl.set("#cb1", {{ backgroundColor: "#171a2e", borderColor: "#171a2e" }}, {r(mw(19))});
      tl.fromTo("#ck1", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {r(mw(19))});
      tl.set("#cb2", {{ backgroundColor: "#171a2e", borderColor: "#171a2e" }}, {r(mw(22))});
      tl.fromTo("#ck2", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {r(mw(22))});

      // step 3: Hardie front, stone base at the back
      tl.fromTo("#sv0", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.15 }}, {r(mw(32))});
      tl.set("#sv0", {{ textContent: "Hardie plank" }}, {r(mw(32) + 0.15)});
      tl.to("#sv0", {{ opacity: 1, duration: 0.25, ease: IN }}, {r(mw(32) + 0.15)});
      tl.fromTo("#sv3", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.15 }}, {r(mw(39))});
      tl.set("#sv3", {{ innerHTML: "Vinyl<small>+ 3 ft stone base</small>" }}, {r(mw(39) + 0.15)});
      tl.to("#sv3", {{ opacity: 1, duration: 0.25, ease: IN }}, {r(mw(39) + 0.15)});

      // result: the total moves from Option B to Option A
      const cnt = {{ v: 590279 }};
      tl.to(cnt, {{ v: 606982, duration: 1.0, ease: "power2.out", onUpdate: () => {{
        document.getElementById("tvA").textContent = fmt(cnt.v);
      }} }}, {r(mw(50))});
      tl.set("#tvA", {{ textContent: "{A_TOTAL}" }}, {r(mw(50) + 1.0)});
      tl.to("#chipB2", {{ opacity: 0, x: 16, duration: 0.25, ease: OUT }}, {r(mw(50))});
      tl.fromTo("#chipA", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.45, ease: IN }}, {r(mw(50) + 0.2)});

      // step labels
{chr(10).join(steps_js)}

      // captions
{chr(10).join(cap_js)}

      // comparison card: the window turns away, two 3D panels turn in
      tl.to("#s4", {{ rotationY: -32, x: -260, z: -220, duration: 0.32, ease: OUT }}, {r(CMP - 0.3)});
      tl.to("#s4", {{ opacity: 0, duration: 0.14, ease: "none" }}, {r(CMP - 0.12)});
      tl.to("#top", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(CMP - 0.1)});
      tl.fromTo("#pB", {{ opacity: 0, rotationY: 35, x: 160 }}, {{ opacity: 1, rotationY: 0, x: 0, duration: 0.6, ease: IN }}, {r(CMP + 0.05)});
      tl.fromTo("#cfine", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(CMP + 0.3)});
      tl.fromTo("#pA", {{ opacity: 0, rotationY: 35, x: 160 }}, {{ opacity: 1, rotationY: 0, x: 0, duration: 0.6, ease: IN }}, {r(ow(2))});
      tl.fromTo("#dif", {{ opacity: 0, scale: 0.85, y: 20 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "back.out(1.6)" }}, {r(ow(5))});

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
print("T", T, "captions", len(CAPS), "S1-4", [r(x) for x in (S1, S2, S3, S4)])
