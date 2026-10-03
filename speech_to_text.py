import string
from faster_whisper import WhisperModel

_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_audio(path):
    """Return transcript, duration, language and word-level timestamps."""
    segments, info = get_model().transcribe(
        path,
        word_timestamps=True,
        initial_prompt="Um, uh, so, like, you know, I mean, basically, actually.",
    )

    words = []
    parts = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            parts.append(text)
        if seg.words:
            for w in seg.words:
                raw = (w.word or "").strip()
                if not raw:
                    continue
                words.append(
                    {
                        "word": raw,
                        "clean": raw.strip(string.punctuation).lower(),
                        "start": round(float(w.start), 2),
                        "end": round(float(w.end), 2),
                    }
                )

    return {
        "text": " ".join(parts),
        "duration": round(float(info.duration), 2),
        "language": info.language,
        "words": words,
    }
