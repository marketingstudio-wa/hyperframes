"""Burned-in word-by-word captions (ASS) plus SRT sidecars for YouTube/Meta uploads."""


def _hex_to_ass(color):
    c = color.lstrip("#")
    return f"&H00{c[4:6]}{c[2:4]}{c[0:2]}".upper()


def _ts(t):
    t = max(0.0, t)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _srt_ts(t):
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def phrases(words, max_words, max_gap=0.45):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["s"] - cur[-1]["e"] > max_gap
                    or cur[-1]["w"].endswith((".", "?", "!"))):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def _clean(text, upper):
    text = text.replace("{", "(").replace("}", ")").replace("\\", "/")
    return text.upper() if upper else text


def write_ass(path, words, W, H, brand, vertical, lower_third=None):
    cap = brand["captions"]
    size = round(H * (cap["size_vertical"] if vertical else cap["size_landscape"]))
    margin_v = round(H * (cap["margin_vertical"] if vertical else cap["margin_landscape"]))
    max_words = cap["words_vertical"] if vertical else cap["words_landscape"]
    white, accent = _hex_to_ass(cap["color"]), _hex_to_ass(cap["active_color"])
    outline = _hex_to_ass(cap["outline_color"])
    bg = _hex_to_ass(brand["colors"]["bg"])
    lt_size = round(H * (0.03 if vertical else 0.04))
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Cap,{cap['font']},{size},{white},{accent},{outline},&H80000000,1,0,0,0,100,100,0,0,1,"
        f"{max(2, size // 14)},0,2,{W // 16},{W // 16},{margin_v},1",
        f"Style: LT,{cap['font']},{lt_size},{white},{accent},{bg},{bg},1,0,0,0,100,100,0,0,3,"
        f"{lt_size // 3},0,1,{W // 20},{W // 20},{round(H * (0.40 if vertical else 0.20))},1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    upper = cap.get("uppercase", False)
    groups = phrases(words, max_words)
    for k, ph in enumerate(groups):
        # a phrase never lingers into the next one, or libass stacks them
        hold = min(ph[-1]["e"] + 0.15, groups[k + 1][0]["s"]) if k + 1 < len(groups) else ph[-1]["e"] + 0.15
        for i, w in enumerate(ph):
            start = ph[0]["s"] if i == 0 else w["s"]
            end = ph[i + 1]["s"] if i + 1 < len(ph) else hold
            text = " ".join(
                (f"{{\\c{accent}}}{_clean(x['w'], upper)}{{\\c{white}}}" if j == i else _clean(x["w"], upper))
                for j, x in enumerate(ph))
            lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,{text}")
    if lower_third and lower_third.get("name"):
        t0 = lower_third.get("start", 0.5)
        t1 = t0 + lower_third.get("duration", 4.0)
        role = lower_third.get("role", "")
        sub = f"\\N{{\\fs{round(lt_size * 0.7)}\\b0\\c{accent}}}{_clean(role, False)}" if role else ""
        lines.append(f"Dialogue: 1,{_ts(t0)},{_ts(t1)},LT,,0,0,0,,{{\\fad(300,300)}}"
                     f"{_clean(lower_third['name'], False)}{sub}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_srt(path, words, offset=0.0, max_words=7):
    out = []
    for i, ph in enumerate(phrases(words, max_words), 1):
        text = " ".join(w["w"] for w in ph)
        out.append(f"{i}\n{_srt_ts(ph[0]['s'] + offset)} --> {_srt_ts(ph[-1]['e'] + offset)}\n{text}\n")
    with open(path, "w") as f:
        f.write("\n".join(out))
