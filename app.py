import streamlit as st
import re
import io
from collections import Counter

# Optional audio transcription dependencies:
# pip install faster-whisper
# ffmpeg may be required for some audio formats.
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False

st.set_page_config(page_title="Speech Coach", page_icon="🎤", layout="wide")

st.markdown("""
<style>
.stApp {background: #f7f8fc;}
.hero {padding: 1.4rem 1.6rem; border-radius: 20px; background: linear-gradient(120deg,#14213d,#315c91); color:white;}
.hero h1 {color:white; margin-bottom:.25rem;}
.muted {color:#687386;}
.metric-card {background:white; padding:1rem; border-radius:15px; border:1px solid #e5e9f2;}
.word-bad {background:#ffe1e1; color:#9c2020; padding:2px 5px; border-radius:5px; font-weight:700;}
.word-good {background:#dff7e8; color:#146c43; padding:2px 5px; border-radius:5px; font-weight:700;}
</style>
""", unsafe_allow_html=True)

FILLERS = {"um", "uh", "erm", "ah", "basically", "actually", "literally"}
PHRASE_FILLERS = ["you know", "i mean", "kind of", "sort of"]

def tokenize(text):
    return re.findall(r"\b[\w']+\b|[.,!?;:]", text)

def analyze_text(text, duration_seconds=None):
    """Transparent baseline analysis from a transcript. Timestamps are estimated unless word times are available."""
    words = re.findall(r"\b[\w']+\b", text.lower())
    if not words:
        return None
    filler_hits = []
    for m in re.finditer(r"\b(?:um|uh|erm|ah|basically|actually|literally)\b", text, re.I):
        filler_hits.append({"word": m.group(0), "char_start": m.start(), "char_end": m.end(),
                            "reason": "Filler or hesitation word", "suggestion": "Remove it or replace it with a brief pause."})
    for phrase in PHRASE_FILLERS:
        for m in re.finditer(r"\b" + re.escape(phrase) + r"\b", text, re.I):
            filler_hits.append({"word": m.group(0), "char_start": m.start(), "char_end": m.end(),
                                "reason": "Potentially unnecessary phrase", "suggestion": "Keep it only if it adds meaning."})
    # Estimate word timestamps evenly across supplied duration; clearly labelled as estimates.
    if duration_seconds and duration_seconds > 0:
        total = len(words)
        for hit in filler_hits:
            word_index = len(re.findall(r"\b[\w']+\b", text[:hit["char_start"]]))
            hit["start"] = duration_seconds * word_index / total
            hit["end"] = duration_seconds * min(word_index + 1, total) / total
            hit["timestamp_note"] = "Estimated from transcript position; not an audio-aligned timestamp."
    else:
        for hit in filler_hits:
            hit["start"] = None
            hit["end"] = None
            hit["timestamp_note"] = "Upload audio duration to estimate a timestamp, or use real word-level alignment."
    filler_rate = len(filler_hits) / len(words) * 100
    wpm = (len(words) / (duration_seconds / 60)) if duration_seconds and duration_seconds > 0 else None
    # Simple deterministic rubric; this is a demo heuristic, not a validated speech assessment.
    filler_score = max(0, min(100, round(100 - filler_rate * 8)))
    pacing_score = (max(0, min(100, round(100 - max(0, abs(wpm - 145) - 20) * 1.2))) if wpm is not None else None)
    clarity_score = max(0, min(100, round(100 - (len(re.findall(r"[.!?]", text)) == 0) * 10 - min(len(filler_hits)*3, 30))))
    return {"words": words, "word_count": len(words), "filler_hits": sorted(filler_hits, key=lambda x:x["char_start"]),
            "filler_rate": filler_rate, "wpm": wpm, "filler_score": filler_score,
            "pacing_score": pacing_score, "clarity_score": clarity_score}

def highlight_text(text, hits):
    # Render escaped transcript safely, wrapping detected terms.
    from html import escape
    ranges = sorted([(h["char_start"], h["char_end"], h["word"]) for h in hits], key=lambda x:x[0])
    out, pos = [], 0
    for start, end, word in ranges:
        if start < pos: 
            continue
        out.append(escape(text[pos:start]))
        out.append(f'<span class="word-bad">{escape(text[start:end])}</span>')
        pos = end
    out.append(escape(text[pos:]))
    return "".join(out)

def simple_improve(text, hits):
    """Rule-based demonstration: remove common fillers and suggest plain-language swaps."""
    improved = text
    replacements = [
        (r"\b(um+|uh+|erm+|ah+)\b", ""),
        (r"\bbasically\b", ""),
        (r"\bactually\b", ""),
        (r"\bliterally\b", ""),
        (r"\byou know\b", ""),
        (r"\bi mean\b", ""),
        (r"\bkind of\b", "somewhat"),
        (r"\bsort of\b", "somewhat"),
        (r"\butilize\b", "use"),
        (r"\bdemonstrate\b", "show"),
        (r"\bcommence\b", "begin"),
        (r"\bapproximately\b", "about"),
        (r"\bobtain\b", "get"),
        (r"\bassist\b", "help"),
        (r"\bterminate\b", "end"),
    ]
    for pattern, replacement in replacements:
        improved = re.sub(pattern, replacement, improved, flags=re.I)
    improved = re.sub(r"\s+([,.!?;:])", r"\1", improved)
    improved = re.sub(r"([,.!?;:])(?=\S)", r"\1 ", improved)
    improved = re.sub(r"\s{2,}", " ", improved).strip()
    improved = re.sub(r"^[,;:\s]+", "", improved)
    return improved or text

def seconds_label(value):
    if value is None: return "Timestamp unavailable"
    mins, secs = divmod(max(0, int(value)), 60)
    return f"{mins:02d}:{secs:02d}"

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "transcript" not in st.session_state:
    st.session_state.transcript = ""

# HOME
st.markdown("""
<div class="hero">
  <h1>🎤 Speech Coach</h1>
  <p>Speak clearly. Find the moment. Improve one sentence at a time.</p>
</div>
""", unsafe_allow_html=True)
st.write("")
home, analyze_tab, about_tab = st.tabs(["🏠 Home", "🔎 Analyze speech", "ℹ️ How it works"])

with home:
    st.subheader("Your personal speech improvement space")
    st.write("Upload a recording and review simple, actionable suggestions. You can also paste a transcript to try the demo without setting up speech recognition.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="metric-card"><h3>🔍 Understand</h3><p>See highlighted words, why they may distract listeners, and where to focus.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card"><h3>✨ Improvise</h3><p>Get a simpler rewritten version with filler words removed and clearer word choices.</p></div>', unsafe_allow_html=True)
    st.info("Demo note: this first version flags common fillers and a few wordy phrases. It does not yet judge every grammar, pronunciation, or delivery mistake.")

with analyze_tab:
    st.subheader("Analyze your speech")
    audio_file = st.file_uploader("Upload audio (WAV, MP3, M4A)", type=["wav", "mp3", "m4a", "mpeg", "mp4"])
    duration = st.number_input("Audio duration in seconds (optional; helps estimate timestamps)", min_value=0.0, value=0.0, step=1.0)
    transcript_input = st.text_area("Or paste a transcript here to try the demo", height=150,
                                    placeholder="Example: Um, basically, today I want to demonstrate how this app can assist you.")
    run_button = st.button("Analyze speech", type="primary", use_container_width=True)

    if run_button:
        transcript = transcript_input.strip()
        audio_duration = duration if duration > 0 else None
        if audio_file is not None and WHISPER_AVAILABLE:
            try:
                with st.spinner("Transcribing audio with Whisper..."):
                    model = WhisperModel("tiny", device="cpu", compute_type="int8")
                    segments, info = model.transcribe(io.BytesIO(audio_file.getvalue()), word_timestamps=True, vad_filter=True)
                    segments = list(segments)
                    transcript = " ".join(seg.text.strip() for seg in segments).strip()
                    if info.duration:
                        audio_duration = float(info.duration)
                st.success("Audio transcription complete.")
            except Exception as e:
                st.error("Could not transcribe this audio. You can paste a transcript below, or check the optional setup instructions.")
                st.caption(f"Technical detail: {e}")
        elif audio_file is not None and not WHISPER_AVAILABLE and not transcript:
            st.warning("Audio was uploaded, but speech-to-text is not installed in this environment. Paste a transcript for the demo, or install faster-whisper as described in the README.")
        if not transcript:
            st.warning("Upload audio with speech recognition enabled, or paste a transcript first.")
        else:
            st.session_state.transcript = transcript
            st.session_state.analysis = analyze_text(transcript, audio_duration)
            st.session_state.audio_duration = audio_duration

    if st.session_state.analysis:
        result = st.session_state.analysis
        transcript = st.session_state.transcript
        st.divider()
        st.subheader("📊 Delivery snapshot")
        m1, m2, m3 = st.columns(3)
        m1.metric("Words", result["word_count"])
        m2.metric("Filler words / phrases", len(result["filler_hits"]))
        m3.metric("Speaking rate", f'{result["wpm"]:.0f} WPM' if result["wpm"] is not None else "Add duration")
        score_cols = st.columns(3)
        score_cols[0].metric("Clarity demo score", f'{result["clarity_score"]}/100')
        score_cols[1].metric("Filler-word score", f'{result["filler_score"]}/100')
        score_cols[2].metric("Pacing demo score", f'{result["pacing_score"]}/100' if result["pacing_score"] is not None else "Insufficient data")
        st.caption("Scores are transparent prototype heuristics, not validated measures of speaking ability. Vocal variation and pause scoring are not implemented in this demo.")
        st.subheader("📝 Transcript — detected phrases highlighted")
        st.markdown(highlight_text(transcript, result["filler_hits"]), unsafe_allow_html=True)
        st.subheader("📍 Detected issues")
        if result["filler_hits"]:
            for hit in result["filler_hits"]:
                timestamp = seconds_label(hit["start"])
                with st.expander(f'{timestamp} · “{hit["word"]}” · {hit["reason"]}'):
                    st.write(hit["suggestion"])
                    st.caption(hit["timestamp_note"])
        else:
            st.success("No phrases from the current demo detection list were found.")
        st.subheader("What would you like to do next?")
        choice = st.radio("Choose one", ["Understand", "Improvise"], horizontal=True, label_visibility="collapsed")
        if choice == "Understand":
            st.markdown("### Understand the feedback")
            st.write("Highlighted phrases are common fillers or phrases that can sometimes be removed. They are not always mistakes: words such as “like” or “actually” may be correct in context. Review each one before changing your speech.")
            if result["filler_hits"]:
                st.write("**Your focus points:**")
                for hit in result["filler_hits"]:
                    st.write(f"- **{hit['word']}** — {hit['reason']}. {hit['suggestion']}")
        else:
            st.markdown("### ✨ An improvised version")
            st.write("This rule-based rewrite removes common fillers and swaps a few formal words for simpler synonyms. Please review it to ensure the meaning stays the same.")
            st.markdown(f"> {simple_improve(transcript, result['filler_hits'])}")
            st.caption("This demo does not yet use a generative AI model to rewrite full sentences contextually.")
        if st.button("Clear analysis"):
            st.session_state.analysis = None
            st.session_state.transcript = ""
            st.rerun()

with about_tab:
    st.subheader("What this prototype does")
    st.markdown("""
- Highlights common filler words and selected wordy phrases.
- Gives simple explanations and a basic rewrite option.
- Calculates word count and, when duration is known, estimated words per minute.
- Shows estimated timestamps only when audio duration is supplied; true timestamps require word-level audio alignment.
- Keeps unsupported metrics clearly labelled rather than inventing results.
""")
    st.subheader("Next features for the hackathon")
    st.markdown("""
1. Use real word-level timestamps from Whisper for precise highlighting.
2. Add pause detection and pitch/energy analysis from the audio.
3. Build a labelled **ideal vs flawed** contrastive dataset and a repeatable rubric.
4. Add an optional LLM for contextual grammar and synonym suggestions.
""")
