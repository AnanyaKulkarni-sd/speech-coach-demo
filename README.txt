SPEECH COACH - FINAL MERGED FLASK VERSION

Team pipeline
1. Sinchana - Faster-Whisper transcription + word-level timestamps.
2. Prakruthi - filler and hedging detection adapted to timestamped words.
3. Ananya - 0-100 rubric, scoring and feedback.
4. Risha - Flask frontend, upload/record UI, transcript highlighting, rings, theme and visual design.

Run
---
1. Create/activate a Python virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Start:
   python app.py
4. Open the local Flask address shown in the terminal.

Notes
-----
- The browser handles microphone recording. Sinchana's desktop microphone helper is not needed by the web app.
- The first analysis loads the Faster-Whisper base model and can take a little longer.
- The final dashboard uses 0-100 performance scores.
- Ring colors are: below 30 red, 30-80 yellow, above 80 green.
- Volume and pausing are prototype audio-derived metrics; they can be replaced later if the team has a dedicated acoustic-analysis module.
- Do not commit uploaded audio or model/cache folders to GitHub.
