from pathlib import Path
import uuid

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from speech_to_text import transcribe_audio
from praku_filler_analysis import analyze_fillers
from ananya_rubric import calculate_rubric, generate_feedback
from audio_features import analyze_audio

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    audio = request.files.get("audio")
    if not audio or not audio.filename:
        return jsonify({"error": "Please upload or record an audio file."}), 400

    filename = secure_filename(audio.filename) or "speech_audio"
    saved_path = UPLOAD_FOLDER / f"{uuid.uuid4().hex}_{filename}"
    audio.save(saved_path)

    try:
        # 1) Sinchana: transcription + word-level temporal grounding.
        transcription = transcribe_audio(str(saved_path))
        words = transcription["words"]

        # 2) Praku: filler + hedging detection on the timestamped transcript.
        filler_result = analyze_fillers(words)
        filler_occurrences = filler_result["fillers"]
        filler_indices = set()
        for occurrence in filler_occurrences:
            filler_indices.update(occurrence.get("indices", [occurrence.get("index")]))

        transcript_words = []
        for i, word in enumerate(words):
            transcript_words.append({
                "word": word["word"],
                "clean": word["clean"],
                "start": word["start"],
                "end": word["end"],
                "filler": i in filler_indices,
            })

        # 3) Audio-level volume and pause features.
        audio_metrics = analyze_audio(saved_path, words, transcription["duration"])

        # 4) Ananya: final 0-100 rubric and feedback.
        rubric = calculate_rubric(
            transcription["text"],
            filler_words=filler_occurrences,
            duration_seconds=transcription["duration"],
            volume_score=audio_metrics["volume_score"],
            pausing_score=audio_metrics["pausing_score"],
        )
        feedback = generate_feedback(rubric)

        return jsonify({
            "transcript": transcript_words,
            "text": transcription["text"],
            "language": transcription["language"],
            "hedging": filler_result["hedging"],
            "fillers": filler_occurrences,
            "pause_intervals": audio_metrics["pause_intervals"],
            "metrics": {
                "total_words": rubric["total_words"],
                "filler_count": rubric["filler_count"],
                "filler_percentage": rubric["filler_percentage"],
                "duration": rubric["duration_seconds"],
                "repeated_words": rubric["repeated_count"],
                "pace": rubric["pace_wpm"],
                "volume": rubric["volume_score"],
                "pausing": rubric["pausing_score"],
                "overall": rubric["overall"],
                "filler_score": rubric["filler_score"],
                "repetition_score": rubric["repetition_score"],
                "pace_score": rubric["pace_score"],
            },
            "feedback": feedback,
        })
    except Exception as exc:
        app.logger.exception("Speech analysis failed")
        return jsonify({
            "error": "The audio could not be analyzed.",
            "details": str(exc),
        }), 500
    finally:
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    app.run(debug=True)
