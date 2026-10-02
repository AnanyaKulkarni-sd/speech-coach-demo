"""
ANANYA'S MODULE
Speech Coach - Rubric + Scoring + Improvement Tracker + Feedback

This module contains only Ananya's assigned work:
1. Total words count
2. Filler words count
3. Filler %
4. Speaking duration
5. Repeated words
6. Pace
7. Volume
8. Pausing
9. Overall score
10. SCORE-style rubric display
11. Improvement Tracker chart
12. Feedback

It does NOT record audio, transcribe audio, or detect filler words from raw audio.
Those values are expected from the other team modules.
"""
import textwrap
import re
from collections import Counter

import streamlit as st

try:
    import altair as alt
except ImportError:
    alt = None


# ---------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------

def tokenize_words(text):
    """Return simple word tokens from a transcript."""
    if not text:
        return []
    return re.findall(r"\b[\w']+\b", text.lower())


def count_words(text):
    return len(tokenize_words(text))


def count_repeated_words(text):
    """
    Count immediate repeated words such as:
    'I I think' -> 1
    'the the presentation' -> 1
    """
    words = tokenize_words(text)
    repeated = []

    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            repeated.append(words[i])

    return len(repeated), repeated


def calculate_pace(total_words, duration_seconds):
    """Words per minute."""
    if not duration_seconds or duration_seconds <= 0:
        return 0.0

    return round(total_words / (duration_seconds / 60), 1)


def calculate_pace_score(pace_wpm):
    """
    Prototype pace score.
    Around 130-160 WPM is treated as the target range.
    """
    if pace_wpm <= 0:
        return 0.0

    if 130 <= pace_wpm <= 160:
        return 100.0

    if pace_wpm < 130:
        score = 100 - (130 - pace_wpm) * 1.0
    else:
        score = 100 - (pace_wpm - 160) * 1.0

    return round(max(0, min(100, score)), 1)


def calculate_filler_score(filler_percentage):
    """Lower filler percentage gives a higher score."""
    score = 100 - (filler_percentage * 5)
    return round(max(0, min(100, score)), 1)


def calculate_repetition_score(repeated_count, total_words):
    """Lower immediate repetition gives a higher score."""
    if total_words <= 0:
        return 100.0

    repetition_percentage = (repeated_count / total_words) * 100
    score = 100 - (repetition_percentage * 5)

    return round(max(0, min(100, score)), 1)


def format_duration(seconds):
    """Convert seconds into a readable duration."""
    seconds = max(0, int(seconds or 0))
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"


# ---------------------------------------------------------------------
# Main scoring
# ---------------------------------------------------------------------

def calculate_rubric(
    transcript,
    filler_words=None,
    duration_seconds=None,
    volume_score=None,
    pausing_score=None,
):
    """
    Calculate Ananya's rubric.

    filler_words:
        Can be a list such as ["um", "like", "uh"].
        These values come from Prakruthi's filler-word module.

    duration_seconds:
        Comes from the audio/speech analysis module.

    volume_score / pausing_score:
        Scores from 0-100 supplied by the audio analysis module.
    """

    transcript = transcript or ""
    filler_words = filler_words or []

    total_words = count_words(transcript)

    # Count filler words supplied by the filler-word module.
    transcript_words = tokenize_words(transcript)
    normalized_fillers = [str(word).lower().strip() for word in filler_words]

    filler_count = sum(
        1 for word in transcript_words if word in normalized_fillers
    )

    filler_percentage = (
        round((filler_count / total_words) * 100, 1)
        if total_words
        else 0.0
    )

    duration_seconds = float(duration_seconds or 0)

    repeated_count, repeated_words = count_repeated_words(transcript)

    pace_wpm = calculate_pace(total_words, duration_seconds)

    # Values received from other modules.
    volume_score = (
        75.0 if volume_score is None
        else float(max(0, min(100, volume_score)))
    )

    pausing_score = (
        75.0 if pausing_score is None
        else float(max(0, min(100, pausing_score)))
    )

    # Internal quality scores.
    filler_score = calculate_filler_score(filler_percentage)
    repetition_score = calculate_repetition_score(
        repeated_count,
        total_words
    )
    pace_score = calculate_pace_score(pace_wpm)

    # Overall combines the quality-oriented factors.
    overall = round(
        (
            filler_score
            + repetition_score
            + pace_score
            + volume_score
            + pausing_score
        ) / 5,
        1,
    )

    return {
        "total_words": total_words,
        "filler_count": filler_count,
        "filler_percentage": filler_percentage,
        "duration_seconds": duration_seconds,
        "repeated_count": repeated_count,
        "repeated_words": repeated_words,
        "pace_wpm": pace_wpm,
        "volume_score": round(volume_score, 1),
        "pausing_score": round(pausing_score, 1),
        "filler_score": filler_score,
        "repetition_score": repetition_score,
        "pace_score": pace_score,
        "overall": overall,
    }


# ---------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------

def generate_feedback(result):
    """Generate simple, readable feedback from the rubric."""

    feedback = []

    filler_count = result["filler_count"]
    filler_percentage = result["filler_percentage"]

    if filler_percentage <= 3:
        filler_text = (
            f"Filler words are well controlled: {filler_count} "
            f"({filler_percentage}%)."
        )
    elif filler_percentage <= 7:
        filler_text = (
            f"You used {filler_count} filler word(s), "
            f"which is {filler_percentage}% of your words. "
            "Try replacing hesitation words with short pauses."
        )
    else:
        filler_text = (
            f"You used {filler_count} filler word(s), "
            f"which is {filler_percentage}% of your words. "
            "Focus on pausing briefly instead of using filler words."
        )

    feedback.append(("Filler words", filler_text))

    if result["repeated_count"] == 0:
        repetition_text = "No immediate repeated words were detected."
    else:
        repeated = ", ".join(result["repeated_words"][:6])
        repetition_text = (
            f"{result['repeated_count']} immediate repetition(s) detected"
            f" ({repeated}). Try to slow down slightly between ideas."
        )

    feedback.append(("Repeated words", repetition_text))

    pace = result["pace_wpm"]

    if pace == 0:
        pace_text = "Speaking pace could not be calculated yet."
    elif pace < 110:
        pace_text = (
            f"Your pace is approximately {pace} WPM. "
            "Consider increasing your pace slightly while keeping your words clear."
        )
    elif pace > 180:
        pace_text = (
            f"Your pace is approximately {pace} WPM. "
            "Try slowing down slightly so important ideas are easier to follow."
        )
    else:
        pace_text = (
            f"Your pace is approximately {pace} WPM, "
            "which is within a practical presentation range."
        )

    feedback.append(("Pace", pace_text))

    volume = result["volume_score"]

    if volume >= 80:
        volume_text = "Your volume score is strong and should be easy to hear."
    elif volume >= 60:
        volume_text = (
            "Your volume is usable, but try to keep your loudness more consistent."
        )
    else:
        volume_text = (
            "Your volume score is low. Try speaking more clearly and consistently."
        )

    feedback.append(("Volume", volume_text))

    pausing = result["pausing_score"]

    if pausing >= 80:
        pausing_text = (
            "Your pausing score is strong. Continue using pauses to separate ideas."
        )
    elif pausing >= 60:
        pausing_text = (
            "Your pausing is reasonable. Add short pauses between important ideas."
        )
    else:
        pausing_text = (
            "Try using more intentional pauses instead of speaking continuously."
        )

    feedback.append(("Pausing", pausing_text))

    overall = result["overall"]

    if overall >= 80:
        overall_text = (
            f"Overall score: {overall}/100. Your speech shows strong overall control."
        )
    elif overall >= 60:
        overall_text = (
            f"Overall score: {overall}/100. "
            "You have a solid base; focus on the lower-scoring areas."
        )
    else:
        overall_text = (
            f"Overall score: {overall}/100. "
            "Focus on one or two speech factors at a time and improve gradually."
        )

    feedback.append(("Overall", overall_text))

    return feedback


# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------

def load_score_styles():
    """Load the visual styling for Ananya's section."""

    st.markdown(
        """
        <style>
        .ananya-wrapper {
            font-family: "Inter", "Segoe UI", Arial, sans-serif;
        }

        .score-header {
            margin-top: 8px;
            margin-bottom: 26px;
        }

        .score-title {
            font-family: "Georgia", "Times New Roman", serif;
            font-size: 36px;
            font-weight: 700;
            letter-spacing: -0.5px;
            color: #202124;
            margin-bottom: 6px;
        }

        .score-subtitle {
            font-family: "Inter", "Segoe UI", Arial, sans-serif;
            font-size: 16px;
            color: #6b7280;
            margin-bottom: 18px;
        }

        .score-card {
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 20px 22px;
            margin-bottom: 24px;
            background: #ffffff;
            box-shadow: 0 3px 14px rgba(15, 23, 42, 0.05);
        }

        .score-row {
            display: grid;
            grid-template-columns: 48px 180px 1fr 72px;
            gap: 16px;
            align-items: center;
            margin: 16px 0;
        }

        .score-badge {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 14px;
            color: #ffffff;
        }

        .score-label {
            font-size: 15px;
            font-weight: 650;
            color: #252a34;
        }

        .score-value {
            text-align: right;
            font-size: 15px;
            font-weight: 750;
            color: #252a34;
        }

        .score-progress {
            height: 9px;
            width: 100%;
            background: #eef1f5;
            border-radius: 999px;
            overflow: hidden;
        }

        .score-progress-fill {
            height: 100%;
            border-radius: 999px;
        }

        .section-title {
            font-family: "Georgia", "Times New Roman", serif;
            font-size: 30px;
            font-weight: 700;
            color: #202124;
            margin-top: 12px;
            margin-bottom: 6px;
        }

        .section-subtitle {
            font-size: 15px;
            color: #6b7280;
            margin-bottom: 16px;
        }

        .feedback-card {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 18px 20px;
            margin: 12px 0;
            background: #ffffff;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        }

        .feedback-title {
            font-size: 16px;
            font-weight: 750;
            color: #202124;
            margin-bottom: 7px;
        }

        .feedback-text {
            font-size: 15px;
            line-height: 1.55;
            color: #60656f;
        }

        @media (max-width: 750px) {
            .score-row {
                grid-template-columns: 42px 1fr 65px;
            }

            .score-row .progress-column {
                grid-column: 2 / 4;
            }

            .score-title {
                font-size: 30px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# SCORE rubric display
# ---------------------------------------------------------------------

def _score_row(letter, label, value_text, score, color):
    """Render one SCORE-style rubric row."""

    score = max(0, min(100, float(score)))

    st.markdown(f"""<div class="score-row">
    <div class="score-badge" style="background:{color};">
        {letter}
    </div>
    <div class="score-label">
        {label}
    </div>
    <div class="progress-container">
        <div class="progress-bar">
            <div class="progress-fill" style="width:{score}%; background:{color};"></div>
        </div>
    </div>
    <div class="score-value">
        {value_text}
    </div>
</div>""", unsafe_allow_html=True)

def render_score_rubric(result):
    """Render the complete nine-factor rubric."""

    st.markdown(
       textwrap.dedent ("""
        <div class="score-header">
            <div class="score-title">The Speech SCORE Framework</div>
            <div class="score-subtitle">
                Speech performance rubric based on the nine project requirements.
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="score-card">', unsafe_allow_html=True)

    _score_row(
        "W",
        "Total words",
        str(result["total_words"]),
        min(result["total_words"], 100),
        "#4F46E5",
    )

    _score_row(
        "F",
        "Filler words",
        str(result["filler_count"]),
        result["filler_score"],
        "#E11D48",
    )

    _score_row(
        "%",
        "Filler %",
        f'{result["filler_percentage"]}%',
        result["filler_score"],
        "#DB2777",
    )

    duration_score = min(100, result["duration_seconds"] / 3)

    _score_row(
        "D",
        "Duration",
        format_duration(result["duration_seconds"]),
        duration_score,
        "#7C3AED",
    )

    _score_row(
        "R",
        "Repeated words",
        str(result["repeated_count"]),
        result["repetition_score"],
        "#0891B2",
    )

    _score_row(
        "P",
        "Pace",
        f'{result["pace_wpm"]} WPM',
        result["pace_score"],
        "#0284C7",
    )

    _score_row(
        "V",
        "Volume",
        f'{result["volume_score"]}/100',
        result["volume_score"],
        "#16A34A",
    )

    _score_row(
        "Pa",
        "Pausing",
        f'{result["pausing_score"]}/100',
        result["pausing_score"],
        "#CA8A04",
    )

    _score_row(
        "O",
        "Overall",
        f'{result["overall"]}/100',
        result["overall"],
        "#EA580C",
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Improvement Tracker
# ---------------------------------------------------------------------

def get_improvement_tracker_data(result):
    """
    Return the quality-oriented factors used in the Improvement Tracker.

    All values are normalized to 0-100 so the chart has one sensible scale.
    """

    return {
        "Filler Control": result["filler_score"],
        "Repetition Control": result["repetition_score"],
        "Pace": result["pace_score"],
        "Volume": result["volume_score"],
        "Pausing": result["pausing_score"],
        "Overall": result["overall"],
    }


def render_improvement_tracker(result):
    """Render a clean, multi-colour 0-100 improvement chart."""

    data = get_improvement_tracker_data(result)

    st.markdown(
        """
        <div class="section-title">Improvement Tracker</div>
        <div class="section-subtitle">
            Quality scores across the main speech-performance factors.
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_data = [
        {"Factor": factor, "Score": float(score)}
        for factor, score in data.items()
    ]

    if alt is not None:
        chart = (
            alt.Chart(alt.Data(values=chart_data))
            .mark_bar(
                cornerRadiusTopLeft=7,
                cornerRadiusTopRight=7,
                size=45,
            )
            .encode(
                x=alt.X(
                    "Factor:N",
                    sort=list(data.keys()),
                    axis=alt.Axis(
                        title=None,
                        labelAngle=-25,
                        labelFont="Arial",
                        labelFontSize=13,
                        labelColor="#4B5563",
                    ),
                ),
                y=alt.Y(
                    "Score:Q",
                    scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(
                        title="Score",
                        titleFont="Arial",
                        titleFontSize=13,
                        labelFont="Arial",
                        labelFontSize=12,
                        labelColor="#6B7280",
                        gridColor="#E5E7EB",
                    ),
                ),
                color=alt.Color(
                    "Factor:N",
                    scale=alt.Scale(
                        domain=list(data.keys()),
                        range=[
                            "#4F46E5",
                            "#E11D48",
                            "#0284C7",
                            "#16A34A",
                            "#CA8A04",
                            "#EA580C",
                        ],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Factor:N", title="Factor"),
                    alt.Tooltip("Score:Q", title="Score", format=".1f"),
                ],
            )
            .properties(height=390)
            .configure_view(strokeOpacity=0)
            .configure_axis(
                titleFont="Arial",
                labelFont="Arial",
            )
        )

        st.altair_chart(chart, use_container_width=True)

    else:
        # Fallback if Altair is unavailable.
        st.bar_chart(
            chart_data,
            x="Factor",
            y="Score",
            height=390,
        )

    st.caption(
        "Higher scores represent stronger performance for the corresponding speech factor."
    )


# ---------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------

def render_feedback(result):
    """Render clean feedback cards."""

    st.markdown(
        """
        <div class="section-title">Feedback</div>
        <div class="section-subtitle">
            Practical suggestions based on your speech-performance scores.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for title, message in generate_feedback(result):
        st.markdown(
            f"""
            <div class="feedback-card">
                <div class="feedback-title">{title}</div>
                <div class="feedback-text">{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------
# Main module renderer
# ---------------------------------------------------------------------

def render_ananya_module(result):
    """Render Ananya's complete section."""

    load_score_styles()

    st.markdown('<div class="ananya-wrapper">', unsafe_allow_html=True)

    render_score_rubric(result)

    st.markdown("<br>", unsafe_allow_html=True)

    render_improvement_tracker(result)

    st.markdown("<br>", unsafe_allow_html=True)

    render_feedback(result)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Dummy data for testing
# ---------------------------------------------------------------------

DUMMY_DATA = {
    "transcript": (
        "Today I want to explain our speech coach project. "
        "It helps speakers improve clarity confidence and delivery. "
        "Um, the system analyzes speech and gives useful feedback."
    ),
    "filler_words": ["um", "uh", "like", "you know"],
    "duration_seconds": 42,
    "volume_score": 78,
    "pausing_score": 86,
}


# ---------------------------------------------------------------------
# Standalone testing
# ---------------------------------------------------------------------

if __name__ == "__main__":
    result = calculate_rubric(
        transcript=DUMMY_DATA["transcript"],
        filler_words=DUMMY_DATA["filler_words"],
        duration_seconds=DUMMY_DATA["duration_seconds"],
        volume_score=DUMMY_DATA["volume_score"],
        pausing_score=DUMMY_DATA["pausing_score"],
    )

    render_ananya_module(result)
