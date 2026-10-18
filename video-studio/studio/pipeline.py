"""Job runner: raw footage -> trimmed, captioned, branded 16:9 / 9:16 / 1:1 deliverables."""
import json
import os
import shutil
import subprocess

import yaml

from . import captions, cards, edit, transcribe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
FORMATS = {"landscape": (1920, 1080), "vertical": (1080, 1920), "square": (1080, 1080)}
SHARE_LIMIT_MB = 29
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def sh(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:200])
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    w, h = (int(v["width"]), int(v["height"])) if v else (0, 0)
    rot = int((v or {}).get("tags", {}).get("rotate", 0) or 0)
    for sd in (v or {}).get("side_data_list", []):
        rot = int(sd.get("rotation", rot) or rot)
    if abs(rot) in (90, 270):
        w, h = h, w
    return {"duration": float(info["format"]["duration"]), "w": w, "h": h, "audio": has_audio}


def deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_brand(name):
    path = os.path.join(ROOT, "brands", f"{name}.yaml")
    with open(path) as f:
        brand = yaml.safe_load(f)
    brand["_dir"] = os.path.dirname(path)
    return brand


# ---------------------------------------------------------------- steps

def normalize(src, dst, info):
    """Constant 30 fps, 48 kHz stereo, silent track if the clip has none."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src]
    if not info["audio"]:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest", "-map", "0:v:0", "-map", "1:a"]
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a:0"]
    sh(cmd + ["-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
              "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", dst])


def cut(src, segs, dst, work):
    """Concatenate kept spans with 10 ms audio fades so joins never click."""
    parts = []
    for i, (s, e) in enumerate(segs):
        d = e - s
        parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.01,afade=t=out:st={max(0, d - 0.01):.3f}:d=0.01[a{i}];")
    graph = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(len(segs))) + \
        f"concat=n={len(segs)}:v=1:a=1[v][a]"
    script = os.path.join(work, "cut.filter")
    with open(script, "w") as f:
        f.write(graph)
    sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex_script", script, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", FPS,
        "-c:a", "pcm_s16le", dst])


def frame_main(src, info, fmt, brand, job, ass, logo_png, dst):
    """Fit the edited footage into the target frame, add logo + captions."""
    W, H = FORMATS[fmt]
    fill = job.get("fill", {}).get(fmt) or brand["fill"].get(fmt, "blur")
    bg = brand["colors"]["bg"]
    same_shape = abs(info["w"] / max(1, info["h"]) - W / H) < 0.02
    if same_shape or fill == "crop":
        x_off = job.get("crop_x", 0.5)
        v = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H}:(iw-{W})*{x_off}:(ih-{H})/2,setsar=1[base]")
    elif fill == "blur":
        v = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
             f"boxblur=40:2,eq=brightness=-0.12[bgv];[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
             f"[bgv][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base]")
    else:  # "brand": solid brand colour, footage centred slightly high (HEAI reel layout)
        v = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
             f"color=c={bg.replace('#', '0x')}:s={W}x{H}:r={FPS}[bgv];"
             f"[bgv][fg]overlay=(W-w)/2:(H-h)/2-H*0.04:shortest=1,setsar=1[base]")
    chain, last = [v], "base"
    inputs = ["-i", src]
    wm = brand.get("watermark", {})
    if logo_png and (wm.get(fmt) or wm.get("all")):
        inputs += ["-i", logo_png]
        pos = wm.get("position", "top-right")
        m = int(min(W, H) * 0.04)
        xy = {"top-right": f"W-w-{m}:{m}", "top-left": f"{m}:{m}", "top": f"(W-w)/2:{int(H * 0.06)}",
              "bottom-right": f"W-w-{m}:H-h-{m}"}[pos]
        chain.append(f"[1:v]format=rgba,colorchannelmixer=aa={wm.get('opacity', 0.9)}[lg];[{last}][lg]overlay={xy}[wm]")
        last = "wm"
    if ass:
        esc = ass.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        chain.append(f"[{last}]ass='{esc}'[out]")
        last = "out"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain),
        "-map", f"[{last}]", "-map", "0:a", *ENC, dst])


def card_clip(png, seconds, dst):
    sh(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", seconds, "-i", png,
        "-f", "lavfi", "-t", seconds, "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", f"fade=t=in:d=0.35,fade=t=out:st={seconds - 0.35}:d=0.35,fps={FPS},format=yuv420p",
        "-shortest", *ENC, dst])


def concat(parts, dst, work):
    lst = os.path.join(work, os.path.basename(dst) + ".txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    sh(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", dst])


def loudness(path, extra_filters=""):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af",
                        f"{extra_filters}loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    return json.loads(txt[txt.rindex("{"):txt.rindex("}") + 1])


def finish_audio(src, dst, music, intro_d, outro_start, total, mode, bed_db, lufs):
    """Optional music bed, then two-pass loudnorm to the brand target (default -14 LUFS)."""
    inputs, pre = ["-i", src], "[0:a]"
    if music:
        bed = 10 ** (bed_db / 20)
        on_cards = (f"if(lt(t,{intro_d}),1,if(lt(t,{intro_d + 0.6}),1-(t-{intro_d})/0.6*(1-{bed}),"
                    f"if(lt(t,{outro_start - 0.6}),{bed},if(lt(t,{outro_start}),{bed}+(t-{outro_start - 0.6})/0.6*(1-{bed}),1))))")
        vol = on_cards if mode == "cards" else str(bed)
        inputs += ["-stream_loop", "-1", "-i", music]
        pre_graph = (f"[1:a]aresample=48000,volume=0.5,volume='{vol}':eval=frame,"
                     f"afade=t=out:st={max(0, total - 1.5)}:d=1.5,atrim=0:{total}[m];"
                     f"[0:a][m]amix=inputs=2:duration=first:normalize=0[mx];[mx]")
    else:
        pre_graph = pre
    # tame speech dynamics and peaks first, so linear loudnorm has headroom to reach the target
    pre_graph += "acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2,alimiter=limit=0.5:level=false,"
    measure_graph = (pre_graph + "loudnorm=I=%s:TP=-1.5:LRA=11:print_format=json" % lufs)
    r = subprocess.run(["ffmpeg", "-hide_banner", *inputs, "-filter_complex", measure_graph, "-f", "null", "-"],
                       capture_output=True, text=True)
    t = r.stderr
    m = json.loads(t[t.rindex("{"):t.rindex("}") + 1])
    ln = (f"loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true,aresample=48000[aout]")
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", pre_graph + ln,
        "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst])


def share_copy(src, dst, duration):
    size_mb = os.path.getsize(src) / 1e6
    if size_mb <= SHARE_LIMIT_MB:
        shutil.copy(src, dst)
        return
    kbps = int(SHARE_LIMIT_MB * 8000 * 0.93 / duration) - 128
    sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k",
        "-maxrate", f"{int(kbps * 1.3)}k", "-bufsize", f"{kbps * 2}k", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", dst])


def qa(path, dst_png):
    d = probe(path)["duration"]
    n = 12
    sh(["ffmpeg", "-y", "-v", "error", "-i", path, "-vf",
        f"fps={n / d},scale=320:-2,tile=4x3:padding=6:color=white", "-frames:v", "1", dst_png])
    m = loudness(path)
    bd = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "blackdetect=d=0.5:pix_th=0.05",
                         "-an", "-f", "null", "-"], capture_output=True, text=True).stderr.count("black_start")
    return {"duration": round(d, 2), "lufs": float(m["input_i"]), "true_peak": float(m["input_tp"]),
            "black_gaps": bd, "size_mb": round(os.path.getsize(path) / 1e6, 1)}


# ---------------------------------------------------------------- main

def run(job_path, only=None):
    with open(job_path) as f:
        job = yaml.safe_load(f)
    job_dir = os.path.dirname(os.path.abspath(job_path))
    brand = load_brand(job["brand"])
    brand = deep_merge(brand, job.get("brand_overrides"))
    name = job.get("name") or os.path.splitext(os.path.basename(job_path))[0]
    out_dir = os.path.join(job_dir, job.get("out_dir", f"out/{name}"))
    work = os.path.join(out_dir, "work")
    os.makedirs(work, exist_ok=True)
    src = os.path.join(job_dir, job["source"])
    music = job.get("music", brand.get("music", {}).get("file"))
    music = os.path.join(job_dir, music) if music else None

    print(f"[1/6] probe + normalize  {src}")
    info = probe(src)
    norm = os.path.join(work, "norm.mov")
    if not os.path.exists(norm):
        normalize(src, norm, info)

    trim = deep_merge(brand.get("trim", {}), job.get("trim"))
    print("[2/6] transcribe (local Parakeet)")
    model = os.environ.get("PARAKEET_DIR", os.path.join(ROOT, "models", "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"))
    need_words = trim.get("mode", "speech") != "none" or job.get("captions", True)
    words = transcribe.transcribe(norm, model, os.path.join(work, "words.json")) if need_words else []

    print("[3/6] plan cuts")
    edit.mark_drops(words, trim.get("fillers", True), trim.get("stutters", True), trim.get("drop_words", []))
    segs = edit.plan_segments(words, info["duration"], trim.get("silence_max", 0.7), trim.get("gap", 0.5),
                              [tuple(r) for r in trim.get("remove", [])], trim.get("mode", "speech"))
    new_words, main_d = edit.remap(words, segs)
    with open(os.path.join(out_dir, "edit_plan.json"), "w") as f:
        json.dump({"source_duration": info["duration"], "edited_duration": round(main_d, 2),
                   "kept_segments": segs,
                   "dropped_words": [w for w in words if w["drop"]]}, f, indent=1)
    with open(os.path.join(out_dir, "transcript.txt"), "w") as f:
        f.write(" ".join(w["w"] for w in new_words) + "\n")
    print(f"      {info['duration']:.1f}s -> {main_d:.1f}s in {len(segs)} spans, "
          f"{sum(w['drop'] for w in words)} words dropped")
    cut_path = os.path.join(work, "cut.mov")
    cut(norm, segs, cut_path, work)

    print("[4/6] cards")
    intro_cfg = deep_merge(brand.get("intro", {}), job.get("intro"))
    outro_cfg = deep_merge(brand.get("outro", {}), job.get("outro"))
    intro_d = float(intro_cfg.get("seconds", 0)) if intro_cfg.get("enabled", True) else 0
    outro_d = float(outro_cfg.get("seconds", 0)) if outro_cfg.get("enabled", True) else 0

    results = {}
    fmts = only or job.get("formats", ["landscape", "vertical"])
    for fmt in fmts:
        W, H = FORMATS[fmt]
        vertical = H > W
        print(f"[5/6] {fmt} {W}x{H}")
        wm = brand.get("watermark", {})
        logo_png = cards.wordmark(brand, int(W * wm.get("width_vertical" if vertical else "width_landscape",
                                                        0.3 if vertical else 0.14)),
                                  int(H * wm.get("max_height", 0.06)), os.path.join(work, f"logo_{fmt}.png"))
        ass = None
        if job.get("captions", True) and new_words:
            ass = os.path.join(work, f"captions_{fmt}.ass")
            captions.write_ass(ass, new_words, W, H, brand, vertical, job.get("lower_third"))
        main = os.path.join(work, f"main_{fmt}.mp4")
        frame_main(cut_path, info, fmt, brand, job, ass, logo_png, main)
        parts = []
        if intro_d:
            png = cards.render_card(brand, W, H, os.path.join(work, f"intro_{fmt}.png"),
                                    job.get("hook") or job.get("title", brand["name"]),
                                    job.get("subtitle") or intro_cfg.get("sub"))
            card_clip(png, intro_d, os.path.join(work, f"intro_{fmt}.mp4"))
            parts.append(os.path.join(work, f"intro_{fmt}.mp4"))
        parts.append(main)
        if outro_d:
            png = cards.render_card(brand, W, H, os.path.join(work, f"outro_{fmt}.png"),
                                    job.get("cta") or outro_cfg["cta"], outro_cfg.get("sub"),
                                    outro_cfg.get("small"))
            card_clip(png, outro_d, os.path.join(work, f"outro_{fmt}.mp4"))
            parts.append(os.path.join(work, f"outro_{fmt}.mp4"))
        joined = os.path.join(work, f"joined_{fmt}.mp4")
        concat(parts, joined, work)
        total = probe(joined)["duration"]
        master = os.path.join(out_dir, f"{name}_{fmt}.mp4")
        mcfg = brand.get("music", {})
        finish_audio(joined, master, music, intro_d, intro_d + main_d, total,
                     mcfg.get("under", "cards"), mcfg.get("bed_db", -60), brand.get("lufs", -14))
        share = os.path.join(out_dir, f"{name}_{fmt}_share.mp4")
        share_copy(master, share, total)
        captions.write_srt(os.path.join(out_dir, f"{name}_{fmt}.srt"), new_words, offset=intro_d)
        print("[6/6] QA")
        results[fmt] = r = qa(master, os.path.join(out_dir, f"{name}_{fmt}_contact.png"))
        r["warnings"] = [w for w in (
            abs(r["lufs"] - brand.get("lufs", -14)) > 1 and f"loudness {r['lufs']} LUFS is off target",
            r["true_peak"] > -1 and f"true peak {r['true_peak']} dBTP is hot",
            r["black_gaps"] and f"{r['black_gaps']} black gap(s) over 0.5 s",
            not new_words and job.get("captions", True) and "no speech found, so no captions") if w]
        results[fmt]["master"] = master
        results[fmt]["share"] = share
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(results, f, indent=1)
    if not job.get("keep_work"):
        for f_ in os.listdir(work):
            if f_.endswith((".mp4",)) and not f_.startswith("main_"):
                os.remove(os.path.join(work, f_))
    return results
