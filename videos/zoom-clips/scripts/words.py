"""Word-level transcript of each cut voice track (faster-whisper medium.en) -> out/<clip>/words.json."""
import json, os, sys
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel

OUT = sys.argv[1]
m = WhisperModel("medium.en", device="cpu", compute_type="int8", cpu_threads=4)
for name in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, name, "voice.wav")
    if not os.path.exists(p):
        continue
    a, sr = sf.read(p, dtype="float32")
    import scipy.signal as ss
    a16 = ss.resample_poly(a, 1, 3)  # 48k -> 16k
    segs, _ = m.transcribe(a16, word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    words = [{"w": w.word.strip(), "t": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
    json.dump(words, open(os.path.join(OUT, name, "words.json"), "w"), indent=0)
    print(name, " ".join(x["w"] for x in words))
