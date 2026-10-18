"""Local word-level transcription with Parakeet TDT (sherpa-onnx). No API cost."""
import json
import os
import subprocess

import numpy as np

SR = 16000
CHUNK_S = 24.0  # Parakeet is happiest on < 30 s windows


def _load_audio(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def _chunks(samples):
    """Split into <= CHUNK_S windows, cutting at the quietest 20 ms frame of each window's last 4 s."""
    n, step, frame = len(samples), int(CHUNK_S * SR), int(0.02 * SR)
    start = 0
    while start < n:
        end = min(n, start + step)
        if end < n:
            lo = end - 4 * SR
            seg = samples[lo:end]
            frames = seg[: len(seg) // frame * frame].reshape(-1, frame)
            end = lo + int(np.argmin((frames ** 2).mean(axis=1))) * frame + frame // 2
        yield start, samples[start:end]
        start = end


def _recognizer(model_dir):
    import sherpa_onnx
    p = lambda f: os.path.join(model_dir, f)
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=p("encoder.int8.onnx"), decoder=p("decoder.int8.onnx"), joiner=p("joiner.int8.onnx"),
        tokens=p("tokens.txt"), num_threads=os.cpu_count() or 4,
        model_type="nemo_transducer", decoding_method="greedy_search")


def transcribe(media_path, model_dir, cache_path=None):
    """Return [{"w": word, "s": start, "e": end}] in seconds on the media's timeline."""
    if cache_path and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    samples = _load_audio(media_path)
    rec = _recognizer(model_dir)
    words = []
    for offset, chunk in _chunks(samples):
        if len(chunk) < SR // 4:
            continue
        stream = rec.create_stream()
        stream.accept_waveform(SR, chunk)
        rec.decode_stream(stream)
        r = stream.result
        base = offset / SR
        durs = list(getattr(r, "durations", []) or [])
        chunk_words = []
        for i, (tok, ts) in enumerate(zip(r.tokens, r.timestamps)):
            t = base + ts
            tok_end = t + (durs[i] if i < len(durs) and durs[i] > 0 else 0.08)
            if tok.startswith(("▁", " ")) or not chunk_words:
                chunk_words.append({"w": tok.lstrip("▁ "), "s": t, "e": tok_end})
            else:
                chunk_words[-1]["w"] += tok
                chunk_words[-1]["e"] = tok_end
        chunk_end = base + len(chunk) / SR
        for i, w in enumerate(chunk_words):
            nxt = chunk_words[i + 1]["s"] if i + 1 < len(chunk_words) else chunk_end
            # token timestamps mark starts; keep word ends sane and non-overlapping
            w["e"] = round(min(max(w["e"], w["s"] + 0.12), nxt, w["s"] + 1.5), 3)
            w["s"] = round(w["s"], 3)
        words += [w for w in chunk_words if w["w"]]
    if cache_path:
        with open(cache_path, "w") as f:
            json.dump(words, f)
    return words
