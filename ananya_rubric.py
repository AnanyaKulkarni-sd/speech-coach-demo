import re


def tokenize_words(text):
    if not text:
        return []
    return re.findall(r"\b[\w']+\b", text.lower())


def count_repeated_words(text):
    words = tokenize_words(text)
    repeated = []
    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            repeated.append(words[i])
    return len(repeated), repeated


def calculate_pace(total_words, duration_seconds):
    if not duration_seconds or duration_seconds <= 0:
        return 0.0
    return round(total_words / (duration_seconds / 60), 1)


def calculate_pace_score(pace_wpm):
    if pace_wpm <= 0:
        return 0.0
    if 130 <= pace_wpm <= 160:
        return 100.0
    if pace_wpm < 130:
        score = 100 - (130 - pace_wpm)
    else:
        score = 100 - (pace_wpm - 160)
    return round(max(0, min(100, score)), 1)


def calculate_filler_score(filler_percentage):
    return round(max(0, min(100, 100 - (filler_percentage * 5))), 1)


def calculate_repetition_score(repeated_count, total_words):
    if total_words <= 0:
        return 100.0
    repetition_percentage = (repeated_count / total_words) * 100
    return round(max(0, min(100, 100 - (repetition_percentage * 5))), 1)


def calculate_rubric(transcript, filler_words=None, duration_seconds=None, volume_score=None, pausing_score=None):
    total_words = len(tokenize_words(transcript))
    filler_words = filler_words or []
    filler_count = len(filler_words)
    filler_percentage = round((filler_count / total_words) * 100, 1) if total_words else 0.0

    repeated_count, repeated_words = count_repeated_words(transcript)
    pace_wpm = calculate_pace(total_words, duration_seconds or 0)
    filler_score = calculate_filler_score(filler_percentage)
    repetition_score = calculate_repetition_score(repeated_count, total_words)
    pace_score = calculate_pace_score(pace_wpm)
    volume_score = round(max(0, min(100, float(volume_score if volume_score is not None else 75))), 1)
    pausing_score = round(max(0, min(100, float(pausing_score if pausing_score is not None else 75))), 1)

    overall = round((filler_score + repetition_score + pace_score + volume_score + pausing_score) / 5, 1)

    return {
        "total_words": total_words,
        "filler_count": filler_count,
        "filler_percentage": filler_percentage,
        "duration_seconds": round(float(duration_seconds or 0), 2),
        "repeated_count": repeated_count,
        "repeated_words": repeated_words,
        "pace_wpm": pace_wpm,
        "volume_score": volume_score,
        "pausing_score": pausing_score,
        "filler_score": filler_score,
        "repetition_score": repetition_score,
        "pace_score": pace_score,
        "overall": overall,
    }


def generate_feedback(result):
    feedback = []
    fp = result["filler_percentage"]
    if fp <= 3:
        feedback.append(f"Filler words are well controlled: {result['filler_count']} ({fp}%).")
    elif fp <= 7:
        feedback.append(f"You used {result['filler_count']} filler word(s), {fp}% of your words. Try replacing hesitation words with short pauses.")
    else:
        feedback.append(f"You used {result['filler_count']} filler word(s), {fp}% of your words. Focus on pausing briefly instead of using filler words.")

    if result["repeated_count"] == 0:
        feedback.append("No immediate repeated words were detected.")
    else:
        repeated = ", ".join(result["repeated_words"][:6])
        feedback.append(f"{result['repeated_count']} immediate repetition(s) detected ({repeated}). Try to slow down slightly between ideas.")

    pace = result["pace_wpm"]
    if pace == 0:
        feedback.append("Speaking pace could not be calculated yet.")
    elif pace < 110:
        feedback.append(f"Your pace is approximately {pace} WPM. Consider increasing your pace slightly while keeping your words clear.")
    elif pace > 180:
        feedback.append(f"Your pace is approximately {pace} WPM. Try slowing down slightly so important ideas are easier to follow.")
    else:
        feedback.append(f"Your pace is approximately {pace} WPM, which is within a practical presentation range.")

    volume = result["volume_score"]
    if volume >= 80:
        feedback.append("Your volume score is strong and should be easy to hear.")
    elif volume >= 60:
        feedback.append("Your volume is usable, but try to keep your loudness more consistent.")
    else:
        feedback.append("Your volume score is low. Try speaking more clearly and consistently.")

    pausing = result["pausing_score"]
    if pausing >= 80:
        feedback.append("Your pausing score is strong. Continue using pauses to separate ideas.")
    elif pausing >= 60:
        feedback.append("Your pausing is reasonable. Add short pauses between important ideas.")
    else:
        feedback.append("Try using more intentional pauses instead of speaking continuously.")

    overall = result["overall"]
    if overall >= 80:
        feedback.append(f"Overall score: {overall}/100. Your speech shows strong overall control.")
    elif overall >= 60:
        feedback.append(f"Overall score: {overall}/100. You have a solid base; focus on the lower-scoring areas.")
    else:
        feedback.append(f"Overall score: {overall}/100. Focus on one or two speech factors at a time and improve gradually.")
    return feedback
