import math
import av
import numpy as np


def _decode_mono(path, target_rate=16000):
    container = av.open(path)
    samples = []
    sample_rate = None
    try:
        for frame in container.decode(audio=0):
            sample_rate = frame.sample_rate or sample_rate
            arr = frame.to_ndarray()
            if arr.ndim == 2:
                arr = arr.mean(axis=0)
            samples.append(arr.astype(np.float32))
    finally:
        container.close()

    if not samples or not sample_rate:
        return np.array([], dtype=np.float32), target_rate

    audio = np.concatenate(samples)
    max_abs = np.max(np.abs(audio)) if audio.size else 0
    if max_abs > 1.5:
        audio = audio / 32768.0

    if sample_rate != target_rate and audio.size:
        duration = len(audio) / sample_rate
        new_len = max(1, int(duration * target_rate))
        old_x = np.linspace(0, duration, len(audio), endpoint=False)
        new_x = np.linspace(0, duration, new_len, endpoint=False)
        audio = np.interp(new_x, old_x, audio).astype(np.float32)
        sample_rate = target_rate
    return audio, sample_rate


def analyze_audio(path, word_items, duration_seconds):
    """Estimate 0-100 volume and pausing performance from the audio.

    These are intentionally simple prototype metrics: volume rewards a stable,
    audible RMS level; pausing rewards useful silence between timestamped words.
    """
    audio, sr = _decode_mono(path)
    duration = float(duration_seconds or 0)

    if audio.size == 0 or sr <= 0:
        return {"volume_score": 75.0, "pausing_score": 75.0, "pause_intervals": []}

    rms = float(np.sqrt(np.mean(np.square(audio))) + 1e-9)
    dbfs = 20 * math.log10(min(1.0, rms))
    volume_score = max(0.0, min(100.0, 100.0 - abs(dbfs + 18.0) * 4.0))

    words = sorted(word_items, key=lambda x: x.get("start", 0))
    gaps = []
    for a, b in zip(words, words[1:]):
        gap = float(b.get("start", 0)) - float(a.get("end", 0))
        if gap >= 0.35:
            gaps.append({"start": float(a.get("end", 0)), "end": float(b.get("start", 0)), "duration": round(gap, 2)})

    speaking_time = sum(max(0, float(w.get("end", 0)) - float(w.get("start", 0))) for w in words)
    silence = max(0.0, duration - speaking_time)
    silence_ratio = silence / duration if duration else 0

    # A presentation-friendly pause share is treated as roughly 8-22%.
    if 0.08 <= silence_ratio <= 0.22:
        pausing_score = 100.0
    elif silence_ratio < 0.08:
        pausing_score = max(0.0, 100.0 - (0.08 - silence_ratio) * 600)
    else:
        pausing_score = max(0.0, 100.0 - (silence_ratio - 0.22) * 400)

    return {
        "volume_score": round(volume_score, 1),
        "pausing_score": round(pausing_score, 1),
        "pause_intervals": gaps,
    }
