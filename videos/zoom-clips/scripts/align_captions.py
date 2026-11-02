"""Align the hand-corrected caption text (captions.json) to word timings.

Timing sources, in order: medium.en words of the cut track (out/<clip>/words.json), then the full-call
small.en words mapped through segs.json. Each caption word takes the time of its fuzzy match; unmatched words
are interpolated between neighbours. Output: out/<clip>/caps.json [{w, t, e, spk, line}]."""
import difflib, json, re, sys

OUT, CAPS, FULL = sys.argv[1], json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower().replace("gonna", "going").replace("wanna", "want"))
full_words = [w for s in FULL for w in s["words"]]

for name, lines in CAPS.items():
    if name == "speakers":
        continue
    d = f"{OUT}/{name}"
    segs = json.load(open(f"{d}/segs.json"))["segs"]
    med = json.load(open(f"{d}/words.json"))
    mapped = []
    for s in segs:
        a, b = s["src"]; o = s["out"][0]
        mapped += [{"w": w[2].strip(), "t": w[0] - a + o, "e": w[1] - a + o} for w in full_words if a - 0.05 <= w[0] < b]
    cap = [{"w": w, "spk": spk, "line": i} for i, (spk, text) in enumerate(lines) for w in text.split()]
    ck = [norm(c["w"]) for c in cap]
    for src in (med, mapped):
        sk = [norm(x["w"]) for x in src]
        for blk in difflib.SequenceMatcher(None, ck, sk, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                c = cap[blk.a + k]
                if "t" not in c:
                    c["t"], c["e"] = src[blk.b + k]["t"], src[blk.b + k]["e"]
    # monotonic + interpolate gaps
    known = [i for i, c in enumerate(cap) if "t" in c]
    for i, c in enumerate(cap):
        if "t" in c:
            continue
        p = max([k for k in known if k < i], default=None); n = min([k for k in known if k > i], default=None)
        t0 = cap[p]["e"] if p is not None else 0.0
        t1 = cap[n]["t"] if n is not None else t0 + 0.4
        span = (n if n is not None else i + 1) - (p if p is not None else -1)
        f = (i - (p if p is not None else -1)) / span
        c["t"] = round(t0 + (t1 - t0) * f, 3); c["e"] = round(c["t"] + 0.25, 3); c["interp"] = True
    for i in range(1, len(cap)):
        cap[i]["t"] = max(cap[i]["t"], cap[i - 1]["t"] + 0.04)
    json.dump(cap, open(f"{d}/caps.json", "w"), indent=0)
    miss = [c["w"] for c in cap if c.get("interp")]
    print(name, len(cap), "words; interpolated:", miss)
