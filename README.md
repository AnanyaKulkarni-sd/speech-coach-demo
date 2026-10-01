# Speech Coach demo

## Easiest route: run in a terminal
1. Install Python 3.10 or newer.
2. In this folder, run:
   `python -m pip install -r requirements.txt`
3. Run:
   `python -m streamlit run app.py`
4. Open the local URL Streamlit prints (usually http://localhost:8501).

## Try it without installing speech recognition
Paste a transcript into the text box, optionally enter the audio duration, and click Analyze speech.

## Optional audio transcription
`faster-whisper` is included in requirements. Its first run downloads the small Whisper model and may take a while. On some systems, audio decoding may require FFmpeg. If the model install is too heavy, use pasted transcript mode for the demo.

## Important limitations
- The current timestamp mapping is an estimate based on transcript position and total duration, not precise word alignment.
- Only common filler words and a small list of phrases are detected.
- Scores are transparent demo heuristics, not scientifically validated speaking scores.
- Pause detection, vocal variation scoring, robust grammar correction, and true contrastive dataset evaluation are not yet implemented.
