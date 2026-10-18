"""Branded intro / outro cards rendered as stills (Pillow), animated later with ffmpeg fades."""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont


def font_file(family, weight):
    return subprocess.run(["fc-match", "-f", "%{file}", f"{family}:{weight}"],
                          capture_output=True, text=True).stdout.strip()


def _wrap(draw, text, font, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=font) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def _logo(brand, base_dir, max_w, max_h):
    path = brand.get("logo")
    if not path:
        return None
    path = os.path.join(base_dir, path)
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    scale = min(max_w / img.width, max_h / img.height)
    return img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)


def wordmark(brand, W, H, out_path):
    """Logo as a transparent PNG, or the brand name as a text wordmark when no logo file exists."""
    base = brand["_dir"]
    logo = _logo(brand, base, W, H)
    if logo is None:
        font = ImageFont.truetype(font_file(brand["font"], "black"), int(H * 0.7))
        tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        tw = int(tmp.textlength(brand["name"], font=font)) + 4
        logo = Image.new("RGBA", (tw, H), (0, 0, 0, 0))
        ImageDraw.Draw(logo).text((0, H // 2), brand["name"], font=font,
                                  fill=brand["colors"]["text"], anchor="lm")
        if tw > W:
            logo = logo.resize((W, int(H * W / tw)), Image.LANCZOS)
    logo.save(out_path)
    return out_path


def render_card(brand, W, H, out_path, headline, sub=None, small=None):
    c = brand["colors"]
    img = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(img)
    vertical = H > W
    margin = int(W * 0.1)
    unit = H if not vertical else W * 1.1

    logo = _logo(brand, brand["_dir"], int(W * (0.55 if vertical else 0.32)), int(H * 0.16))
    head_font = ImageFont.truetype(font_file(brand["font"], "black"), int(unit * 0.075))
    sub_font = ImageFont.truetype(font_file(brand["font"], "semibold"), int(unit * 0.038))
    small_font = ImageFont.truetype(font_file(brand["font"], "medium"), int(unit * 0.026))
    head_lines = _wrap(d, headline, head_font, W - 2 * margin)
    sub_lines = _wrap(d, sub, sub_font, W - 2 * margin) if sub else []

    head_h = int(head_font.size * 1.15) * len(head_lines)
    sub_h = int(sub_font.size * 1.35) * len(sub_lines)
    logo_h = (logo.height + int(unit * 0.06)) if logo else 0
    rule_h = int(unit * 0.05)
    y = (H - (logo_h + head_h + rule_h + sub_h)) // 2

    if logo:
        img.paste(logo, ((W - logo.width) // 2, y), logo)
        y += logo_h
    elif brand.get("name"):
        name_font = ImageFont.truetype(font_file(brand["font"], "black"), int(unit * 0.045))
        d.text((W // 2, y), brand["name"].upper(), font=name_font, fill=c["accent"], anchor="mt")
        y += int(unit * 0.1)
    for line in head_lines:
        d.text((W // 2, y), line, font=head_font, fill=c["text"], anchor="mt")
        y += int(head_font.size * 1.15)
    rule_w = int(W * 0.12)
    d.rectangle([(W - rule_w) // 2, y + rule_h // 3, (W + rule_w) // 2, y + rule_h // 3 + max(4, H // 220)],
                fill=c["accent"])
    y += rule_h
    for line in sub_lines:
        d.text((W // 2, y), line, font=sub_font, fill=c["secondary"], anchor="mt")
        y += int(sub_font.size * 1.35)
    if small:
        d.text((W // 2, H - int(H * 0.06)), small, font=small_font, fill=c["secondary"], anchor="mb")
    img.save(out_path)
    return out_path
