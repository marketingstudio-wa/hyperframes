"""Fast audio offset check (FFT cross-correlation over the whole track) between a render and its mix."""
import subprocess, sys
import numpy as np
def pcm(p):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float)
for render, mix in zip(sys.argv[1::2], sys.argv[2::2]):
    a, b = pcm(render), pcm(mix); n = min(len(a), len(b)); a, b = a[:n], b[:n]
    c = np.fft.irfft(np.fft.rfft(a, 2 * n) * np.conj(np.fft.rfft(b, 2 * n)))
    lag = int(np.argmax(np.concatenate([c[-400:], c[:401]]))) - 400
    print(render.split("/")[-1], f"lag {lag / 8:.2f} ms")
