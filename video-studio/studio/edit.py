"""Decide what to keep: drop fillers and stutters, tighten long silences, apply manual cuts."""
import re

FILLERS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "ah", "hmm", "mm", "mhm"}


def norm(word):
    return re.sub(r"[^a-z']", "", word.lower())


def mark_drops(words, fillers=True, stutters=True, extra=()):
    extra = {norm(x) for x in extra}
    for i, w in enumerate(words):
        n = norm(w["w"])
        w["drop"] = bool(
            (fillers and (n in FILLERS or n in extra))
            or (stutters and i + 1 < len(words) and n and n == norm(words[i + 1]["w"])
                and words[i + 1]["s"] - w["e"] < 0.4))
    return words


def plan_segments(words, duration, silence_max=0.7, gap=0.5, remove=(), mode="speech"):
    """Return [(start, end)] source-time spans to keep, in order.

    A span ends when the silence between two kept words exceeds `silence_max`, or when a
    dropped word sits between them. Each span is padded so a tightened pause lasts ~`gap`.
    """
    if mode == "none" or not words:
        segs = [(0.0, duration)]
    else:
        pre, post = gap * 0.4, gap * 0.6
        segs, cur, prev, drop_end = [], None, None, None
        for w in words:
            if w["drop"]:
                if cur is not None:
                    cur[1] = min(cur[1], w["s"] - 0.02)
                drop_end = w["e"]
                continue
            start = max(0.0, w["s"] - pre)
            if drop_end is not None:
                start = max(start, drop_end + 0.02)
            if cur is None:
                cur = [start, w["e"] + post]
            elif drop_end is not None or w["s"] - prev["e"] > silence_max:
                segs.append(tuple(cur))
                cur = [max(start, cur[1]), w["e"] + post]
            else:
                cur[1] = w["e"] + post
            prev, drop_end = w, None
        if cur is not None:
            segs.append(tuple(cur))
        segs = [(s, min(e, duration)) for s, e in segs if min(e, duration) - s > 0.15]
    for rs, re_ in remove:
        out = []
        for s, e in segs:
            if re_ <= s or rs >= e:
                out.append((s, e))
                continue
            if rs > s:
                out.append((s, rs))
            if re_ < e:
                out.append((re_, e))
        segs = out
    return [(round(s, 3), round(e, 3)) for s, e in segs if e - s > 0.1]


def remap(words, segs):
    """Map kept words from source time onto the edited timeline. Returns (words, duration)."""
    bounds, t0 = [], 0.0
    for s, e in segs:
        bounds.append((s, e, t0))
        t0 += e - s
    out = []
    for w in words:
        if w["drop"]:
            continue
        mid = (w["s"] + w["e"]) / 2
        for s, e, o in bounds:
            if s <= mid < e:
                out.append({"w": w["w"], "s": round(o + max(w["s"], s) - s, 3),
                            "e": round(o + min(w["e"], e) - s, 3)})
                break
    return out, t0
