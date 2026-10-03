import re


def _clean(value):
    return re.sub(r"^[\W_]+|[\W_]+$", "", value.lower())


def analyze_fillers(words):
    """Adapt Prakruthi's filler rules to Sinchana's timestamped word list.

    Returns filler occurrences with their original timestamps and a separate
    hedging list. Matching is performed on the transcript words rather than
    asking the user for text.
    """
    normalized = []
    for item in words:
        raw = item.get("word", "")
        normalized.append(
            {
                **item,
                "clean": _clean(raw),
            }
        )

    fillers = []
    hedging = []
    filler_indices = set()

    def add_filler(i, label=None):
        if i in filler_indices:
            return
        item = normalized[i]
        filler_indices.add(i)
        fillers.append(
            {
                "word": item["word"],
                "label": label or item["clean"],
                "start": item["start"],
                "end": item["end"],
                "index": i,
            }
        )

    # Single-word filler variations from Praku's rules.
    for i, item in enumerate(normalized):
        w = item["clean"]
        raw = item["word"]
        if re.fullmatch(r"u+m+", w) or re.fullmatch(r"u+h+", w) or re.fullmatch(r"e+r+", w) or re.fullmatch(r"e+r+m+", w):
            add_filler(i)
            continue

        # The original module treats "like" contextually.
        if re.fullmatch(r"like+", w):
            prev_w = normalized[i - 1]["clean"] if i > 0 else ""
            next_w = normalized[i + 1]["clean"] if i < len(normalized) - 1 else ""
            if prev_w in {"would", "could", "should", "really", "i", "we", "they", "you"}:
                continue
            if raw.endswith(",") or next_w in {"really", "very", "so", "just", "actually", "literally"} or prev_w in {"without", "with", "and", "so", "but", "then"}:
                add_filler(i, "like")

        # Ambiguous stretched words from the original module.
        if re.fullmatch(r"basicallyy*", w):
            normalized[i]["clean"] = "basically"
        elif re.fullmatch(r"actuallyy*", w):
            normalized[i]["clean"] = "actually"
        elif re.fullmatch(r"literallyy*", w):
            normalized[i]["clean"] = "literally"
        elif re.fullmatch(r"so+", w):
            normalized[i]["clean"] = "so"
        elif re.fullmatch(r"wel+l+", w):
            normalized[i]["clean"] = "well"

    hesitation_words = {"um", "uh", "er", "erm", "like"}
    for i, item in enumerate(normalized):
        w = item["clean"]
        prev_w = normalized[i - 1]["clean"] if i > 0 else ""
        next_w = normalized[i + 1]["clean"] if i < len(normalized) - 1 else ""

        if w == "maybe" and (item["word"].endswith(",") or prev_w in {"think", "guess"}):
            hedging.append({"word": item["word"], "start": item["start"], "end": item["end"], "index": i})
            continue

        if w in {"basically", "actually", "literally", "so", "well"}:
            if next_w in hesitation_words or prev_w in hesitation_words:
                add_filler(i, w)

    # Multi-word filler phrases from Praku's module.
    phrases = [
        ("you", "know", "you know"),
        ("i", "mean", "i mean"),
        ("kind", "of", "kind of"),
        ("sort", "of", "sort of"),
    ]
    for i in range(len(normalized) - 1):
        a, b = normalized[i], normalized[i + 1]
        for x, y, label in phrases:
            if a["clean"] == x and b["clean"] == y:
                if i not in filler_indices and i + 1 not in filler_indices:
                    filler_indices.add(i)
                    filler_indices.add(i + 1)
                    fillers.append({
                        "word": f"{a['word']} {b['word']}",
                        "label": label,
                        "start": a["start"],
                        "end": b["end"],
                        "index": i,
                        "indices": [i, i + 1],
                    })
                break

    fillers.sort(key=lambda x: x["start"])
    hedging.sort(key=lambda x: x["start"])
    return {
        "fillers": fillers,
        "hedging": hedging,
        "filler_count": len(fillers),
        "hedging_count": len(hedging),
    }
