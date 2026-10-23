"""Mix Reel #2 audio: Desmond VO (-16 LUFS) over the StudioKolomna bed, ducked ~12 dB under the voice,
then master to -14 LUFS / true peak <= -1.5 dBFS.
Usage: python3 mix.py <src dir> <out.m4a>   (reads VO placement and music splice from timing.json)
Music: track offset 2.45 puts the drop (10.15) on the first step (7.70); a beat-aligned splice
jumps ahead so the end hit (122.95) lands on the end card."""
import json, subprocess, sys
import numpy as np, soundfile as sf

SRC, OUT = sys.argv[1], sys.argv[2]
SR = 48000
# timing.json (written by gen.py): {"T", "vo": [[file, offset], ...], "music": [[from, to, offset], ...]}
TM = json.load(open("timing.json"))
T, VO, MUSIC_IN = TM["T"], TM["vo"], TM["music"]  # music: (video from, video to, track = video + offset)
DUCK_DB, BED_DB = -12.0, -17.0


def run(*a):
    return subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *a], check=True)


def lufs(path):
    o = subprocess.run(["ffmpeg", "-nostdin", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = o[o.rindex("Summary:"):]
    I = float(s.split("I:")[1].split("LUFS")[0])
    P = float(s.split("Peak:")[1].split("dBFS")[0])
    return I, P


def load(path):
    run("-i", path, "-ac", "2", "-ar", str(SR), "/tmp/_l.wav")
    y, _ = sf.read("/tmp/_l.wav")
    return y


n = int(T * SR)
vo = np.zeros((n, 2))
for f, off in VO:
    y = load(f"{SRC}/{f}")
    i = int(round(off * SR)); vo[i:i + len(y)] += y[: n - i]
sf.write("/tmp/_vo.wav", vo, SR)
I, _ = lufs("/tmp/_vo.wav")
vo *= 10 ** ((-16 - I) / 20)

track = load(f"{SRC}/music.mp3")
mus = np.zeros((n, 2))
xf = int(0.015 * SR)
for k, (a, b, off) in enumerate(MUSIC_IN):
    i, j = int(round(a * SR)), int(round(b * SR))
    s = int(round((a + off) * SR))
    seg = track[s - (xf if k else 0): s + (j - i) + xf].copy()
    if k:
        seg[:xf] *= np.linspace(0, 1, xf)[:, None]; i -= xf
    if k + 1 < len(MUSIC_IN):
        seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
    seg = seg[: n - i]
    mus[i:i + len(seg)] += seg
fade = int(0.8 * SR)
mus[-fade:] *= np.linspace(1, 0, fade)[:, None]
sf.write("/tmp/_mus.wav", mus, SR)
I, _ = lufs("/tmp/_mus.wav")
mus *= 10 ** ((BED_DB - I) / 20)

# duck envelope from VO activity (20 ms frames), 60 ms attack, 350 ms release
hop = int(0.02 * SR)
rms = np.sqrt(np.mean(vo[: len(vo) // hop * hop, 0].reshape(-1, hop) ** 2, axis=1))
act = (20 * np.log10(rms + 1e-9) > -45).astype(float)
g, cur = np.zeros_like(act), 0.0
for k, v in enumerate(act):
    tc = 0.02 / (0.06 if v > cur else 0.35)
    cur += (v - cur) * min(1.0, tc * 3)
    g[k] = cur
gain = 10 ** (DUCK_DB * g / 20)
gain = np.interp(np.arange(n), np.arange(len(gain)) * hop + hop / 2, gain)
mix = vo + mus * gain[:, None]
sf.write("/tmp/_mix.wav", mix, SR)

o = subprocess.run(["ffmpeg", "-nostdin", "-i", "/tmp/_mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(o[o.rindex("{"):])
run("-i", "/tmp/_mix.wav", "-af",
    f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
    f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true", "-ar", str(SR), "/tmp/_m.wav")
I, P = lufs("/tmp/_m.wav")
trim = -14.0 - I
if abs(trim) > 0.1 and P + trim <= -1.5:
    run("-i", "/tmp/_m.wav", "-af", f"volume={trim:.2f}dB", "/tmp/_m2.wav"); subprocess.run(["mv", "/tmp/_m2.wav", "/tmp/_m.wav"])
run("-i", "/tmp/_m.wav", "-c:a", "aac", "-b:a", "256k", OUT)
print("master", lufs("/tmp/_m.wav"), "->", OUT)
