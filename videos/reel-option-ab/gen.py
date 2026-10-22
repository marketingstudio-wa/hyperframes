"""Generate the Reel #2 "Option A vs Option B" composition (index.html).

Recreated estimate UI (no app footage), Desmond VO only. On-screen cues follow the
VO word starts (word start - 0.08 s). Word timings come from asr.py on the tightened VO.
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

# beat boundaries
S1, S2, S3, S4, CMP = mw(0), mw(12), mw(25), mw(45), 32.20
STEPS = [("st1", "STEP 1", "Start with the base scope", S1, S2),
         ("st2", "STEP 2", "Add it by voice", S2, S3),
         ("st3", "STEP 3", "Change the siding", S3, S4),
         ("st4", "RESULT", "Updated price", S4, CMP)]

# captions: (display words, first word index per display word), <= 5 words, from MID / OUTRO
def chunk(words, src, base, idx, end_idx):
    return {"words": words, "starts": [base + src[i]["s"] - LEAD for i in idx],
            "end": base + src[end_idx]["e"]}

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
    b = min(nxt, ch["end"] + 0.6)
    if c == 14:
        b = CMP  # hold the updated total caption to the comparison cut
    spans = " ".join(f'<span id="w{c}_{k}">{html.escape(w)}</span>' for k, w in enumerate(ch["words"]))
    cap_html.append(f'        <div class="cap" id="c{c}">{spans}</div>')
    cap_js.append(f'      tl.set("#c{c}", {{ opacity: 1 }}, {r(a)});')
    cap_js.append(f'      tl.set("#c{c}", {{ opacity: 0 }}, {r(b)});')
    for k, t in enumerate(ch["starts"]):
        cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#d4af37" }}, {r(t)});')
        if k + 1 < len(ch["starts"]):
            cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#ffffff" }}, {r(ch["starts"][k + 1])});')

steps_html = "\n".join(
    f'        <div class="step" id="{sid}"><span class="k">{k}</span><span class="t">{html.escape(t)}</span></div>'
    for sid, k, t, _, _ in STEPS)
steps_js = []
for sid, _, _, a, b in STEPS:
    steps_js.append(f'      tl.fromTo("#{sid}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(a)});')
    steps_js.append(f'      tl.to("#{sid}", {{ opacity: 0, duration: 0.2, ease: OUT }}, {r(b - 0.2)});')


def est_rows(kitchen, siding):
    rows = [("Second-story addition", "3 bed &middot; primary bath &middot; full bath &middot; laundry"),
            ("First floor + basement", "Gut remodel"),
            ("Kitchen", kitchen),
            ("Siding", siding)]
    return "\n".join(
        f'              <div class="row" style="top:{196 + i * 148}px"><div class="rt">{t}</div><div class="rd">{d}</div></div>'
        for i, (t, d) in enumerate(rows))


ADDONS = ["Sink disposal", "Under-cabinet lights", "Pot filler", "Second sink", "Sound solution", "Reverse osmosis filter"]
addon_rows = "\n".join(
    f'              <div class="row opt" style="top:{196 + i * 126}px"><div class="cb" id="cb{i}"><span id="ck{i}">&#10003;</span></div>'
    f'<div class="ot">{t}</div></div>' for i, t in enumerate(ADDONS))

SIDES = [("Front", "sv0"), ("Left side", "sv1"), ("Right side", "sv2"), ("Back", "sv3")]
side_rows = "\n".join(
    f'              <div class="row side" style="top:{196 + i * 166}px"><div class="rt">{t}</div>'
    f'<div class="sv" id="{sid}">Vinyl</div></div>' for i, (t, sid) in enumerate(SIDES))


def box(bid, x, y, w, h):
    return f'            <div class="gbox" id="{bid}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'


BOXES = [
    # screen 1: siding row, total
    ("bx_sid", 36, 632, 1008, 148, mw(5), mw(11)),
    ("bx_tb", 36, 788, 1008, 184, mw(11), S2),
    # screen 2: one box per add-on, each moves on with the next item
    ("bx_k0", 36, 188, 1008, 126, mw(17), mw(19)),
    ("bx_k1", 36, 314, 1008, 126, mw(19), mw(22)),
    ("bx_k2", 36, 440, 1008, 126, mw(22), S3),
    # screen 3: three vinyl sides, Hardie front, stone base at the back
    ("bx_s3", 36, 354, 1008, 498, mw(28), mw(32)),
    ("bx_sf", 36, 188, 1008, 166, mw(32), mw(37)),
    ("bx_sb", 36, 686, 1008, 166, mw(37), S4),
    # screen 4: updated total
    ("bx_ta", 36, 788, 1008, 184, mw(50), CMP),
]
boxes_html = "\n".join(box(b[0], *b[1:5]) for b in BOXES)
boxes_js = []
for bid, *_, a, b in BOXES:
    boxes_js.append(f'      tl.fromTo("#{bid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: IN }}, {r(a)});')
    boxes_js.append(f'      tl.to("#{bid}", {{ opacity: 0, duration: 0.2, ease: OUT }}, {r(b - 0.2)});')

LOGO_TOP = (91, 1182, 828)  # display width, visible bbox w/h in Original-Logo.png


def logo(cls, width):
    s = width / 1182
    return (f'<div class="{cls}" data-layout-allow-overflow style="width:{width}px;height:{828 * s:.1f}px">'
            f'<img src="assets/logo.png" alt="Home Estimator" style="width:{1920 * s:.1f}px;height:{1920 * s:.1f}px;'
            f'left:{-374 * s:.1f}px;top:{-476 * s:.1f}px" /></div>')


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
      .step {{ position: absolute; left: 0; top: 300px; width: 1080px; text-align: center; opacity: 0; }}
      .step .k {{ display: block; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: var(--gold); }}
      .step .t {{ display: block; margin-top: 4px; font-size: 52px; font-weight: 900; letter-spacing: -1px; }}
      #win {{ position: absolute; left: 0; top: 412px; width: 1080px; height: 1080px; overflow: hidden; background: #eef0f6; }}
      .scr {{ position: absolute; inset: 0; opacity: 0; }}
      .bar {{ position: absolute; left: 0; top: 0; width: 1080px; height: 110px; background: #ffffff;
        border-bottom: 2px solid #dfe2ea; display: flex; align-items: center; justify-content: space-between; padding: 0 48px; }}
      .bar .ti {{ font-size: 40px; font-weight: 800; color: var(--ink); letter-spacing: -0.5px; }}
      .bar .tag {{ font-size: 32px; font-weight: 600; color: var(--muted); }}
      .kick {{ position: absolute; left: 48px; top: 138px; font-size: 32px; font-weight: 800; letter-spacing: 3px; color: var(--muted); }}
      .row {{ position: absolute; left: 48px; width: 984px; height: 132px; background: #ffffff; border-radius: 20px;
        border: 2px solid #e1e4ec; padding: 22px 34px; }}
      .rt {{ font-size: 40px; font-weight: 800; color: var(--ink); letter-spacing: -0.5px; }}
      .rd {{ margin-top: 8px; font-size: 32px; font-weight: 500; color: var(--muted); white-space: nowrap; }}
      .tot {{ position: absolute; left: 48px; top: 800px; width: 984px; height: 160px; background: var(--navy); border-radius: 20px;
        padding: 26px 34px; }}
      .tot .tl {{ font-size: 32px; font-weight: 800; letter-spacing: 4px; color: var(--gray); }}
      .chip {{ position: absolute; left: 34px; top: 82px; height: 52px; padding: 0 22px; border-radius: 26px; font-size: 32px;
        font-weight: 900; letter-spacing: 2px; display: flex; align-items: center; opacity: 0; }}
      .chip.b {{ border: 3px solid var(--sand); color: var(--sand); }}
      .chip.a {{ background: var(--gold); color: var(--navy); }}
      .tot .tv {{ position: absolute; right: 34px; top: 34px; font-size: 88px; font-weight: 900; letter-spacing: -2px; line-height: 1; }}
      .tot .upd {{ position: absolute; right: 34px; top: 52px; font-size: 48px; font-weight: 700; color: var(--gray); }}
      .fine {{ position: absolute; left: 0; top: 994px; width: 1080px; text-align: center; font-size: 32px; font-weight: 500; color: var(--muted); }}
      .opt {{ height: 112px; display: flex; align-items: center; gap: 30px; padding: 0 34px; }}
      .cb {{ width: 56px; height: 56px; border-radius: 12px; border: 3px solid #c3c8d6; display: flex; align-items: center;
        justify-content: center; font-size: 38px; font-weight: 900; color: #ffffff; }}
      .cb span {{ opacity: 0; }}
      .ot {{ font-size: 40px; font-weight: 700; color: var(--ink); }}
      .side {{ height: 150px; display: flex; align-items: center; justify-content: space-between; }}
      .sv {{ text-align: right; font-size: 40px; font-weight: 800; color: var(--ink); line-height: 1.15; }}
      .sv small {{ display: block; font-size: 32px; font-weight: 700; color: #8a6a14; }}
      .gbox {{ position: absolute; border: 5px solid var(--gold); border-radius: 12px; opacity: 0; }}
      #hook {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center; }}
      .hs {{ font-size: 64px; font-weight: 800; letter-spacing: -1px; }}
      .hb {{ font-size: 132px; font-weight: 900; letter-spacing: -3px; line-height: 1.02; margin-bottom: 36px; }}
      #h2, #hb2, #h3, #h4 {{ opacity: 0; }}
      #hb1 {{ color: var(--gold); }}
      #hb2 {{ color: var(--sand); }}
      #h3 {{ font-size: 64px; font-weight: 900; margin-top: 10px; }}
      #h4 {{ margin-top: 14px; font-size: 44px; font-weight: 600; color: var(--gray); }}
      .cap {{ position: absolute; left: 40px; top: 1502px; width: 1000px; text-align: center; font-size: 56px; font-weight: 900;
        letter-spacing: -1px; line-height: 1.1; white-space: nowrap; opacity: 0; }}
      #cmp {{ position: absolute; inset: 0; background: var(--navy); opacity: 0; }}
      .pnl {{ position: absolute; left: 80px; width: 920px; height: 236px; background: var(--card); border: 2px solid var(--line);
        border-radius: 24px; padding: 34px 44px; opacity: 0; }}
      .pnl .pk {{ font-size: 36px; font-weight: 800; letter-spacing: 1px; }}
      .pnl .pv {{ margin-top: 12px; font-size: 104px; font-weight: 900; letter-spacing: -3px; line-height: 1; }}
      #pB {{ top: 420px; }}
      #pB .pk, #pB .pv {{ color: var(--sand); }}
      #pA {{ top: 690px; }}
      #pA .pk {{ color: var(--white); }}
      #pA .pv {{ color: var(--white); }}
      #dif {{ position: absolute; left: 0; top: 980px; width: 1080px; text-align: center; opacity: 0; }}
      #dif .dk {{ font-size: 36px; font-weight: 800; letter-spacing: 5px; color: var(--gray); }}
      #dif .dv {{ margin-top: 6px; font-size: 132px; font-weight: 900; letter-spacing: -3px; color: var(--gold); line-height: 1.05; }}
      #cfine {{ position: absolute; left: 0; top: 1220px; width: 1080px; text-align: center; font-size: 32px; font-weight: 500;
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
{steps_html}
        <div id="win" data-layout-allow-occlusion data-layout-allow-overlap>
          <div class="scr" id="scr1">
            <div class="bar"><div class="ti">Project estimate</div><div class="tag">Option B</div></div>
            <div class="kick">SCOPE &middot; RANCH HOUSE</div>
{est_rows("Mid-sized &middot; 200 sq ft", "Vinyl &middot; whole house")}
            <div class="tot"><div class="tl">TOTAL</div><div class="chip b" id="chipB">OPTION B</div><div class="tv">{B_TOTAL}</div></div>
            <div class="fine">{FINE}</div>
          </div>
          <div class="scr" id="scr2">
            <div class="bar"><div class="ti">Kitchen</div><div class="tag">Mid-sized &middot; 200 sq ft</div></div>
            <div class="kick">ADD-ONS</div>
{addon_rows}
          </div>
          <div class="scr" id="scr3">
            <div class="bar"><div class="ti">Siding</div><div class="tag">By elevation</div></div>
            <div class="kick">MATERIAL PER SIDE</div>
{side_rows}
          </div>
          <div class="scr" id="scr4">
            <div class="bar"><div class="ti">Project estimate</div><div class="tag">Option A</div></div>
            <div class="kick">SCOPE &middot; RANCH HOUSE</div>
{est_rows("Mid-sized &middot; 200 sq ft &middot; 3 add-ons", "Vinyl 3 sides &middot; Hardie front &middot; stone base")}
            <div class="tot"><div class="tl">TOTAL</div><div class="chip a" id="chipA">OPTION A</div>
              <div class="upd" id="upd">Updating&hellip;</div><div class="tv" id="tvA" style="opacity:0">{A_TOTAL}</div></div>
            <div class="fine">{FINE}</div>
          </div>
{boxes_html}
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
        <div id="cmp">
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

      // hook over the dimmed estimate; first frame already reads "Your client loves OPTION A."
      tl.set("#scr1", {{ opacity: 0.06 }}, 0);
      tl.set("#win", {{ backgroundColor: "#171a2e" }}, 0);
      tl.fromTo("#h2", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(hw(5))});
      tl.fromTo("#hb2", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(hw(8))});
      tl.fromTo("#h3", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(hw(10))});
      tl.fromTo("#h4", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(hw(13))});
      tl.to("#hook", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(S1 - 0.45)});
      tl.to("#win", {{ backgroundColor: "#eef0f6", duration: 0.35, ease: IN }}, {r(S1 - 0.15)});
      tl.to("#scr1", {{ opacity: 1, duration: 0.35, ease: IN }}, {r(S1 - 0.15)});
      tl.set("#hook", {{ visibility: "hidden" }}, {r(S1 + 0.1)});
      tl.fromTo("#top", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(S1)});

      // screens: static per beat, swapped on the cue word
      tl.to("#scr1", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(S2 - 0.15)});
      tl.fromTo("#scr2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: IN }}, {r(S2)});
      tl.to("#scr2", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(S3 - 0.15)});
      tl.fromTo("#scr3", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: IN }}, {r(S3)});
      tl.to("#scr3", {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(S4 - 0.15)});
      tl.fromTo("#scr4", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: IN }}, {r(S4)});

      // step 1: base total, OPTION B chip
      tl.fromTo("#chipB", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.45, ease: IN }}, {r(mw(11))});

      // step 2: tick the add-ons
      tl.set("#cb0", {{ backgroundColor: "#171a2e", borderColor: "#171a2e" }}, {r(mw(17))});
      tl.fromTo("#ck0", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: IN }}, {r(mw(17))});
      tl.set("#cb1", {{ backgroundColor: "#171a2e", borderColor: "#171a2e" }}, {r(mw(19))});
      tl.fromTo("#ck1", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: IN }}, {r(mw(19))});
      tl.set("#cb2", {{ backgroundColor: "#171a2e", borderColor: "#171a2e" }}, {r(mw(22))});
      tl.fromTo("#ck2", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: IN }}, {r(mw(22))});

      // step 3: Hardie front, stone base at the back
      tl.set("#sv0", {{ textContent: "Hardie plank" }}, {r(mw(32))});
      tl.set("#sv3", {{ innerHTML: "Vinyl<small>+ 3 ft stone base</small>" }}, {r(mw(39))});

      // result: updated total, OPTION A chip
      tl.set("#upd", {{ opacity: 0 }}, {r(mw(50))});
      tl.fromTo("#tvA", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(mw(50))});
      tl.fromTo("#chipA", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.45, ease: IN }}, {r(mw(50))});

      // highlight boxes
{chr(10).join(boxes_js)}

      // step labels
{chr(10).join(steps_js)}

      // captions
{chr(10).join(cap_js)}

      // comparison card
      tl.fromTo("#cmp", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: IN }}, {r(CMP)});
      tl.fromTo("#pB", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(CMP + 0.05)});
      tl.fromTo("#pA", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(ow(2))});
      tl.fromTo("#dif", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(ow(5))});
      tl.fromTo("#cfine", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(CMP + 0.3)});
      tl.set("#win", {{ visibility: "hidden" }}, {r(CMP + 0.35)});

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
print("T", T, "captions", len(CAPS), "S1-4", [r(x) for x in (S1, S2, S3, S4)], "boxes", len(BOXES))
