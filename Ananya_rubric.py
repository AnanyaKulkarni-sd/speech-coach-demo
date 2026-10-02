"""
ANANYA'S MODULE
Speech Coach — Rubric + Scoring + Improvement Graph + Feedback

This file contains ONLY Ananya's assigned work.

Responsibilities:
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
11. Improvement Tracker bar chart
12. Feedback

This module does NOT:
- record audio
- convert audio to text
- detect filler words from raw audio
- build the complete website

The other team members can pass their outputs into calculate_rubric().

Example input:
    transcript = "Um today I am going to explain AI. Basically AI is useful."
    filler_words = ["Um", "Basically"]
    duration_seconds = 12.5
    volume_score = 78
    pausing_score = 82

The code can initially be tested with dummy data.
Later, replace the dummy values with the outputs from Sinchana and Prakruthi.
"""

import re
from collections import Counter

import streamlit as st


# ============================================================
# 1. COLOURS — inspired by the reference SCORE image
# ============================================================

COLORS = {
    "words": "#E5A900",       # yellow/gold
    "fillers": "#2A9D8F",     # green
    "filler_pct": "#D83A2E",  # red
    "duration": "#2E5D8E",    # dark blue
    "repeated": "#55A9BF",    # light blue
    "pace": "#E5A900",
    "volume": "#2A9D8F",
    "pausing": "#D83A2E",
    "overall": "#2E5D8E",
}


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def tokenize_words(text):
    """Return words from a transcript."""
    return re.findall(r"\b[\w']+\b", text.lower())


def count_words(text):
    """Total number of words in the transcript."""
    return len(tokenize_words(text))


def count_repeated_words(text):
    """
    Count immediate repeated words.

    Example:
        'I I think this is is useful'
    gives:
        I, is
        => 2 repetitions
    """
    words = tokenize_words(text)

    repetitions = []

    for i in range(1, len(words)):
        if words[i] == words[i - 1] and len(words[i]) > 1:
            repetitions.append(words[i])

    return repetitions


def calculate_pace(total_words, duration_seconds):
    """
    Calculate speaking pace in words per minute.

    Returns None when duration is unavailable.
    """
    if duration_seconds is None or duration_seconds <= 0:
        return None

    return total_words / (duration_seconds / 60)


def calculate_pace_score(wpm):
    """
    Prototype pace score.

    Around 145 WPM is used as the centre of the scoring range.
    This is a project heuristic, NOT a medically/academically validated score.
    """
    if wpm is None:
        return None

    difference = abs(wpm - 145)

    if difference <= 20:
        return 100

    score = 100 - ((difference - 20) * 1.2)

    return round(max(0, min(100, score)))


def calculate_filler_score(filler_percentage):
    """Convert filler percentage into a 0–100 quality score."""
    score = 100 - (filler_percentage * 8)
    return round(max(0, min(100, score)))


def calculate_repetition_score(repetition_count, total_words):
    """Convert repeated-word frequency into a 0–100 quality score."""
    if total_words <= 0:
        return None

    repetition_rate = repetition_count / total_words * 100
    score = 100 - (repetition_rate * 7)

    return round(max(0, min(100, score)))


def format_duration(seconds):
    """Format seconds as MM:SS."""
    if seconds is None:
        return "Not available"

    seconds = int(round(seconds))
    minutes, seconds = divmod(seconds, 60)

    return f"{minutes:02d}:{seconds:02d}"


# ============================================================
# 3. MAIN RUBRIC CALCULATION
# ============================================================

def calculate_rubric(
    transcript,
    filler_words=None,
    duration_seconds=None,
    volume_score=None,
    pausing_score=None,
):
    """
    Calculate Ananya's complete speech rubric.

    Parameters
    ----------
    transcript : str
        Transcript produced by Sinchana's speech-to-text module.

    filler_words : list
        Filler words identified by Prakruthi's module.
        Example: ["um", "basically", "you know"]

    duration_seconds : float
        Speech duration supplied by the audio/transcription module.

    volume_score : float
        0–100 volume score supplied by the audio analysis module.
        Ananya does NOT calculate raw audio volume.

    pausing_score : float
        0–100 pausing score supplied by the audio analysis module.
        Ananya does NOT calculate raw audio pauses.

    Returns
    -------
    dict
        All nine requested rubric factors plus scores and feedback.
    """

    if not isinstance(transcript, str):
        raise TypeError("transcript must be a string.")

    filler_words = filler_words or []

    # --------------------------------------------------------
    # Total words
    # --------------------------------------------------------
    total_words = count_words(transcript)

    # --------------------------------------------------------
    # Filler words
    # --------------------------------------------------------
    filler_count = len(filler_words)

    filler_percentage = (
        (filler_count / total_words) * 100
        if total_words > 0
        else 0
    )

    filler_score = calculate_filler_score(filler_percentage)

    # --------------------------------------------------------
    # Repeated words
    # --------------------------------------------------------
    repeated_words = count_repeated_words(transcript)
    repeated_count = len(repeated_words)

    repetition_score = calculate_repetition_score(
        repeated_count,
        total_words,
    )

    # --------------------------------------------------------
    # Speaking pace
    # --------------------------------------------------------
    pace_wpm = calculate_pace(
        total_words,
        duration_seconds,
    )

    pace_score = calculate_pace_score(pace_wpm)

    # --------------------------------------------------------
    # Volume / pausing
    # These values come from audio analysis done elsewhere.
    # --------------------------------------------------------
    if volume_score is not None:
        volume_score = round(max(0, min(100, volume_score)))

    if pausing_score is not None:
        pausing_score = round(max(0, min(100, pausing_score)))

    # --------------------------------------------------------
    # Overall
    # Only quality-oriented scores are averaged.
    # Raw word count and duration are measurements, not quality
    # scores, so they are NOT included in the overall calculation.
    # --------------------------------------------------------
    quality_scores = [
        filler_score,
        repetition_score,
        pace_score,
        volume_score,
        pausing_score,
    ]

    quality_scores = [
        score for score in quality_scores
        if score is not None
    ]

    overall = (
        round(sum(quality_scores) / len(quality_scores))
        if quality_scores
        else None
    )

    return {
        # Requested measurements
        "total_words": total_words,
        "filler_count": filler_count,
        "filler_percentage": round(filler_percentage, 2),
        "duration_seconds": duration_seconds,
        "repeated_count": repeated_count,
        "repeated_words": repeated_words,
        "pace_wpm": round(pace_wpm, 1) if pace_wpm is not None else None,
        "volume_score": volume_score,
        "pausing_score": pausing_score,
        "overall": overall,

        # Internal quality scores used for the graph
        "filler_score": filler_score,
        "repetition_score": repetition_score,
        "pace_score": pace_score,
    }


# ============================================================
# 4. FEEDBACK
# ============================================================

def generate_feedback(result):
    """Generate readable feedback from the rubric."""

    feedback = []

    # Filler feedback
    if result["filler_count"] == 0:
        feedback.append(
            (
                "Filler words",
                "No filler words were detected. Keep maintaining this level of clarity."
            )
        )
    elif result["filler_percentage"] <= 5:
        feedback.append(
            (
                "Filler words",
                f"You used {result['filler_count']} filler word(s), "
                f"which is {result['filler_percentage']:.1f}% of your words. "
                "This is a relatively small proportion; continue replacing fillers "
                "with short pauses where possible."
            )
        )
    else:
        feedback.append(
            (
                "Filler words",
                f"You used {result['filler_count']} filler word(s), "
                f"which is {result['filler_percentage']:.1f}% of your words. "
                "Try pausing briefly instead of using repeated hesitation words."
            )
        )

    # Repetition feedback
    if result["repeated_count"] == 0:
        feedback.append(
            (
                "Repeated words",
                "No immediate repeated words were detected."
            )
        )
    else:
        words = ", ".join(result["repeated_words"])
        feedback.append(
            (
                "Repeated words",
                f"{result['repeated_count']} immediate repetition(s) were detected"
                f" ({words}). Try pausing briefly before restarting a sentence."
            )
        )

    # Pace feedback
    pace = result["pace_wpm"]

    if pace is None:
        feedback.append(
            (
                "Pace",
                "Speaking pace could not be calculated because duration was not provided."
            )
        )
    elif pace < 110:
        feedback.append(
            (
                "Pace",
                f"Your pace is approximately {pace:.0f} WPM. "
                "You may be speaking slowly; consider slightly increasing your pace "
                "while keeping your words clear."
            )
        )
    elif pace > 180:
        feedback.append(
            (
                "Pace",
                f"Your pace is approximately {pace:.0f} WPM. "
                "Consider slowing down and adding intentional pauses between ideas."
            )
        )
    else:
        feedback.append(
            (
                "Pace",
                f"Your pace is approximately {pace:.0f} WPM. "
                "Use natural pauses to maintain clarity and listener comfort."
            )
        )

    # Volume feedback
    if result["volume_score"] is None:
        feedback.append(
            (
                "Volume",
                "Volume data is not available yet. It will be supplied by the audio-analysis module."
            )
        )
    elif result["volume_score"] >= 80:
        feedback.append(
            (
                "Volume",
                "Your volume score is strong. Keep your microphone distance consistent."
            )
        )
    elif result["volume_score"] >= 60:
        feedback.append(
            (
                "Volume",
                "Your volume is usable, but try to keep your loudness more consistent."
            )
        )
    else:
        feedback.append(
            (
                "Volume",
                "Your volume score suggests that delivery volume may need improvement. "
                "Speak clearly and keep a consistent distance from the microphone."
            )
        )

    # Pausing feedback
    if result["pausing_score"] is None:
        feedback.append(
            (
                "Pausing",
                "Pausing data is not available yet. It will be supplied by the audio-analysis module."
            )
        )
    elif result["pausing_score"] >= 80:
        feedback.append(
            (
                "Pausing",
                "Your pausing score is strong. Continue using pauses to separate ideas."
            )
        )
    elif result["pausing_score"] >= 60:
        feedback.append(
            (
                "Pausing",
                "Your pauses are usable. Try making pauses more intentional at major transitions."
            )
        )
    else:
        feedback.append(
            (
                "Pausing",
                "Work on using intentional pauses between ideas instead of rushing through sentences."
            )
        )

    return feedback


# ============================================================
# 5. SCORE-STYLE CSS
# ============================================================

def load_score_styles():
    """Load the visual style inspired by the supplied SCORE image."""

    st.markdown(
        """
        <style>

        .score-container {
            background: #ffffff;
            border: 1px solid #e3e4e6;
            border-radius: 18px;
            padding: 18px 28px 22px 28px;
            margin-top: 10px;
        }

        .score-title {
            text-align: center;
            font-size: 28px;
            font-weight: 800;
            color: #333333;
            margin-bottom: 4px;
        }

        .score-subtitle {
            text-align: center;
            color: #777777;
            font-size: 13px;
            margin: 0 auto 12px auto;
            max-width: 720px;
        }

        .score-spectrum {
            width: 290px;
            height: 4px;
            margin: 10px auto 20px auto;
            background: linear-gradient(
                to right,
                #E5A900 0%,
                #E5A900 20%,
                #2A9D8F 20%,
                #2A9D8F 40%,
                #D83A2E 40%,
                #D83A2E 60%,
                #2E5D8E 60%,
                #2E5D8E 80%,
                #55A9BF 80%,
                #55A9BF 100%
            );
        }

        .score-row {
            display: grid;
            grid-template-columns: 62px 115px 1fr 90px;
            align-items: center;
            column-gap: 14px;
            min-height: 72px;
            padding: 6px 0;
        }

        .score-circle {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 17px;
            font-weight: 800;
            border: 2px solid white;
            box-shadow: 0 0 0 2px var(--circle-color);
        }

        .score-name {
            font-size: 13px;
            font-weight: 800;
        }

        .score-description {
            color: #8a8a8a;
            font-size: 10px;
            line-height: 1.25;
            margin-bottom: 7px;
        }

        .score-track {
            height: 7px;
            background: #d7d7d7;
            border-radius: 10px;
            overflow: hidden;
        }

        .score-fill {
            height: 100%;
            border-radius: 10px;
        }

        .score-number {
            text-align: right;
            font-size: 12px;
            font-weight: 800;
            color: #444444;
        }

        .feedback-box {
            background: #ffffff;
            border: 1px solid #e3e4e6;
            border-radius: 13px;
            padding: 15px 18px;
            margin: 7px 0;
        }

        .feedback-title {
            font-weight: 800;
            color: #333333;
            margin-bottom: 4px;
        }

        .feedback-text {
            color: #666666;
            line-height: 1.45;
        }

        @media (max-width: 750px) {
            .score-container {
                padding: 12px;
            }

            .score-row {
                grid-template-columns: 48px 95px 1fr 65px;
                column-gap: 8px;
            }

            .score-description {
                font-size: 9px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 6. SCORE-STYLE RUBRIC DISPLAY
# ============================================================

def render_score_rubric(result):
    """
    Display the nine requested rubric factors in the style
    of the supplied SCORE Framework reference image.
    """

    load_score_styles()

    def add_row(letter, name, description, score, color, display_value):
        if score is None:
            width = 0
        else:
            width = max(0, min(100, float(score)))

        st.markdown(
            f"""
            <div class="score-row">

                <div>
                    <div class="score-circle"
                         style="background:{color}; --circle-color:{color};">
                        {letter}
                    </div>
                </div>

                <div>
                    <div class="score-name" style="color:{color};">
                        {name}
                    </div>
                </div>

                <div>
                    <div class="score-description">
                        {description}
                    </div>

                    <div class="score-track">
                        <div class="score-fill"
                             style="width:{width}%; background:{color};">
                        </div>
                    </div>
                </div>

                <div class="score-number">
                    {display_value}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="score-container">

            <div class="score-title">
                The Speech SCORE Framework
            </div>

            <div class="score-subtitle">
                Speech performance rubric based on the nine project requirements.
            </div>

            <div class="score-spectrum"></div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Total words
    # Word count is a measurement, so the bar is normalized to 100
    # for display purposes only.
    word_display_score = min(
        100,
        (result["total_words"] / 200) * 100
    )

    add_row(
        "W",
        "Total words",
        "Total number of words detected in the transcript.",
        word_display_score,
        COLORS["words"],
        str(result["total_words"]),
    )

    # 2. Filler count
    add_row(
        "F",
        "Filler words",
        "Number of filler words identified by the filler-analysis module.",
        result["filler_score"],
        COLORS["fillers"],
        str(result["filler_count"]),
    )

    # 3. Filler percentage
    filler_quality = max(
        0,
        min(
            100,
            100 - (result["filler_percentage"] * 5)
        )
    )

    add_row(
        "%",
        "Filler %",
        "Percentage of total words classified as filler words.",
        filler_quality,
        COLORS["filler_pct"],
        f'{result["filler_percentage"]:.1f}%',
    )

    # 4. Duration
    duration_score = 100 if result["duration_seconds"] is not None else None

    add_row(
        "D",
        "Duration",
        "Total speaking duration supplied by the audio/transcription module.",
        duration_score,
        COLORS["duration"],
        format_duration(result["duration_seconds"]),
    )

    # 5. Repeated words
    add_row(
        "R",
        "Repeated words",
        "Immediate repeated words found in the transcript.",
        result["repetition_score"],
        COLORS["repeated"],
        str(result["repeated_count"]),
    )

    # 6. Pace
    add_row(
        "P",
        "Pace",
        "Speaking speed calculated as words per minute.",
        result["pace_score"],
        COLORS["pace"],
        (
            f'{result["pace_wpm"]:.0f} WPM'
            if result["pace_wpm"] is not None
            else "—"
        ),
    )

    # 7. Volume
    add_row(
        "V",
        "Volume",
        "Volume score supplied by the audio-analysis module.",
        result["volume_score"],
        COLORS["volume"],
        (
            f'{result["volume_score"]}/100'
            if result["volume_score"] is not None
            else "—"
        ),
    )

    # 8. Pausing
    add_row(
        "Pa",
        "Pausing",
        "Pausing score supplied by the audio-analysis module.",
        result["pausing_score"],
        COLORS["pausing"],
        (
            f'{result["pausing_score"]}/100'
            if result["pausing_score"] is not None
            else "—"
        ),
    )

    # 9. Overall
    add_row(
        "O",
        "Overall",
        "Average of the available quality-oriented speech scores.",
        result["overall"],
        COLORS["overall"],
        (
            f'{result["overall"]}/100'
            if result["overall"] is not None
            else "—"
        ),
    )

    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 7. IMPROVEMENT TRACKER — BAR CHART
# ============================================================

def get_improvement_tracker_data(result):
    """
    Return the quality-oriented scores used by the improvement
    tracker bar chart.
    """

    return {
        "Filler control": result["filler_score"],
        "Repetition control": result["repetition_score"] or 0,
        "Pace": result["pace_score"] or 0,
        "Volume": result["volume_score"] or 0,
        "Pausing": result["pausing_score"] or 0,
        "Overall": result["overall"] or 0,
    }


def render_improvement_tracker(result):
    """Display the requested Improvement Tracker bar chart."""

    st.subheader("📊 Improvement Tracker")

    chart_data = get_improvement_tracker_data(result)

    st.bar_chart(
        chart_data,
        height=380,
        y_label="Score / 100",
    )

    st.caption(
        "Higher bars represent stronger scores for the corresponding "
        "quality-oriented speech factor."
    )


# ============================================================
# 8. FEEDBACK DISPLAY
# ============================================================

def render_feedback(result):
    """Display feedback generated from the rubric."""

    st.subheader("💬 Feedback")

    feedback = generate_feedback(result)

    for title, message in feedback:
        st.markdown(
            f"""
            <div class="feedback-box">
                <div class="feedback-title">{title}</div>
                <div class="feedback-text">{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 9. COMPLETE ANANYA COMPONENT
# ============================================================

def render_ananya_module(result):
    """
    Render everything belonging to Ananya:

    - Rubric
    - Improvement Tracker
    - Feedback
    """

    render_score_rubric(result)

    st.divider()

    render_improvement_tracker(result)

    st.divider()

    render_feedback(result)


# ============================================================
# 10. DUMMY DATA FOR HACKATHON DEVELOPMENT
# ============================================================

DUMMY_DATA = {
    "transcript": (
        "Um today I am going to explain artificial intelligence. "
        "Basically artificial intelligence is changing the way we work. "
        "I I think this technology is very useful."
    ),

    # This list will eventually come from Prakruthi's filler detector.
    "filler_words": [
        "Um",
        "Basically",
    ],

    # This will eventually come from Sinchana/audio analysis.
    "duration_seconds": 18.5,

    # These are dummy values for now.
    # Later they will come from the audio-analysis pipeline.
    "volume_score": 78,
    "pausing_score": 82,
}


# ============================================================
# 11. STANDALONE TEST MODE
# ============================================================

if __name__ == "__main__":

    result = calculate_rubric(
        transcript=DUMMY_DATA["transcript"],
        filler_words=DUMMY_DATA["filler_words"],
        duration_seconds=DUMMY_DATA["duration_seconds"],
        volume_score=DUMMY_DATA["volume_score"],
        pausing_score=DUMMY_DATA["pausing_score"],
    )

    st.set_page_config(
        page_title="Ananya - Speech Rubric",
        page_icon="📊",
        layout="wide",
    )

    st.title("Ananya's Speech Rubric — Dummy Data")

    st.write(
        "This is a standalone test of the rubric, scoring, "
        "improvement graph and feedback module."
    )

    render_ananya_module(result)

    st.divider()

    st.subheader("🔧 Debug / Data passed to the module")
    st.json(result)
