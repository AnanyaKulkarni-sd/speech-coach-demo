import json
import string
import speech_recognition as sr
from faster_whisper import WhisperModel

_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def record_audio(filename="recording.wav", device_index=None, max_seconds=60):
    """Record from the mic and save as a WAV file."""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.0  # don't cut off at natural pauses

    with sr.Microphone(device_index=device_index) as source:
        print("Adjusting for background noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Recording... speak now! (stops after a long pause)")
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=max_seconds)

    with open(filename, "wb") as f:
        f.write(audio.get_wav_data())
    print(f"Saved recording to {filename}")
    return filename


def transcribe_audio(path):
    """Transcribe any audio file. Returns text, duration and word timestamps."""
    segments, info = get_model().transcribe(
        path,
        word_timestamps=True,
        # Whisper tends to delete "um/uh", so this nudges it to keep them
        initial_prompt="Um, uh, so, like, you know, I mean, basically, actually.",
    )

    words, parts = [], []
    for seg in segments:
        parts.append(seg.text.strip())
        for w in seg.words:
            words.append({
                "word": w.word.strip(),
                "clean": w.word.strip().strip(string.punctuation).lower(),
                "start": round(float(w.start), 2),
                "end": round(float(w.end), 2),
            })

    return {
        "text": " ".join(parts),
        "duration": round(float(info.duration), 2),
        "language": info.language,
        "words": words,
    }


if __name__ == "__main__":
    choice = input("1 = upload audio file, 2 = record from mic: ").strip()

    if choice == "1":
        path = input("Path to audio file: ").strip().strip('"')
    else:
        path = record_audio()

    print("Transcribing...")
    result = transcribe_audio(path)

    print("\nText:", result["text"])
    print("Duration:", result["duration"], "seconds")
    print("First words:", result["words"][:5])

    with open("transcript.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("Saved to transcript.json")