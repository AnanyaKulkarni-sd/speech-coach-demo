from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Temporary demo data.
# Later, Sinchana/Prakruthi/Ananya's real outputs will replace this.
DEMO_RESULT = {
    "transcript": [
        {"word": "Good", "start": 0.20, "end": 0.50, "filler": False},
        {"word": "morning", "start": 0.51, "end": 0.90, "filler": False},
        {"word": "um", "start": 1.00, "end": 1.30, "filler": True},
        {"word": "today", "start": 1.40, "end": 1.80, "filler": False},
        {"word": "we", "start": 1.81, "end": 2.00, "filler": False},
        {"word": "are", "start": 2.01, "end": 2.20, "filler": False},
        {"word": "going", "start": 2.21, "end": 2.55, "filler": False},
        {"word": "to", "start": 2.56, "end": 2.70, "filler": False},
        {"word": "uh", "start": 3.10, "end": 3.35, "filler": True},
        {"word": "present", "start": 3.40, "end": 3.85, "filler": False},
        {"word": "our", "start": 3.86, "end": 4.05, "filler": False},
        {"word": "project", "start": 4.06, "end": 4.50, "filler": False}
    ],
    "metrics": {
        "total_words": 125,
        "filler_count": 8,
        "filler_percentage": 6.4,
        "duration": 92.5,
        "repeated_words": 4,
        "pace": 81,
        "volume": 72,
        "pausing": 8,
        "overall": 78,
        "filler_score": 68,
        "repetition_score": 84
    },
    "feedback": [
        "Try reducing filler words such as 'um' and 'uh'.",
        "Your speaking pace is fairly steady.",
        "Practice smoother transitions between ideas."
    ]
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    audio = request.files.get("audio")

    if audio and audio.filename:
        filename = secure_filename(audio.filename)
        saved_name = f"{uuid.uuid4().hex}_{filename}"
        audio.save(UPLOAD_FOLDER / saved_name)

    # For now this returns demonstration results.
    # Later this is where the real analysis pipeline will be connected.
    return jsonify(DEMO_RESULT)

if __name__ == "__main__":
    app.run(debug=True)
