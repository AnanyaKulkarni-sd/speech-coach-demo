import re

print("AI SPEECH EVALUATOR")

speech = input("Enter your speech: ")

# Convert speech to lowercase
text = speech.lower()

# -----------------------------------
# 1. Detect UM / UHH variations
# -----------------------------------

found_fillers = []
found_hedging = []

# Detect um, umm, ummm, ummmm...
um_matches = re.findall(r"\b(?:u+m+)\b", text)
found_fillers.extend(um_matches)

# Detect uh, uhh, uhhh, uhhhhh...
uh_matches = re.findall(r"\b(?:u+h+)\b", text)
found_fillers.extend(uh_matches)

# Detect er, err, erm, ermmm...
er_matches = re.findall(r"\b(?:e+r+|e+r+m+)\b", text)
found_fillers.extend(er_matches)


# -----------------------------------
# 2. Detect filler phrases
# -----------------------------------

# "you know"
you_know_matches = re.findall(
    r"\byou know\b",
    text
)
found_fillers.extend(
    ["you know"] * len(you_know_matches)
)

# "i mean"
i_mean_matches = re.findall(
    r"\bi mean\b",
    text
)
found_fillers.extend(
    ["i mean"] * len(i_mean_matches)
)

# "kind of"
kind_of_matches = re.findall(
    r"\bkind of\b",
    text
)
found_fillers.extend(
    ["kind of"] * len(kind_of_matches)
)

# "sort of"
sort_of_matches = re.findall(
    r"\bsort of\b",
    text
)
found_fillers.extend(
    ["sort of"] * len(sort_of_matches)
)


# -----------------------------------
# 3. Split speech into words
# -----------------------------------

words = re.findall(r"\b[\w']+[.,!?;:]*", text)


# -----------------------------------
# 4. Detect ambiguous words
# -----------------------------------

# Recognizes:
# um, umm, ummmm...
# uh, uhh, uhhhh...
# er, err, errr...
# erm, ermm, ermmm...
# like

hesitation_pattern = r"(?:u+m+|u+h+|e+r+|e+r+m+|like)"


for i, word in enumerate(words):

    clean_word = word.strip(".,!?;:")

    # Allow stretched versions of ambiguous words
    ambiguous_word = clean_word

    if re.fullmatch(r"basicallyy*", clean_word):
        ambiguous_word = "basically"

    elif re.fullmatch(r"actuallyy*", clean_word):
        ambiguous_word = "actually"

    elif re.fullmatch(r"literallyy*", clean_word):
        ambiguous_word = "literally"

    elif re.fullmatch(r"so+", clean_word):
        ambiguous_word = "so"

    elif re.fullmatch(r"wel+l+", clean_word):
        ambiguous_word = "well"

    # Get previous word
    previous_word = ""
    if i>0:
        previous_word=words[i-1].strip(".,!?;:")

    next_word=""
    if i<len(words)-1:
        next_word=words[i+1].strip(".,!?;:")

    # ==================================================
    # LIKE
    # ==================================================

    if re.fullmatch(r"like+", clean_word):
        # Normal uses
        if previous_word in [
            "would",
            "could",
            "should",
            "really",
            "i",
            "we",
            "they",
            "you"
        ]:
            continue

        if next_word in [
            "coffee",
            "tea",
            "music",
            "food",
            "chocolate",
            "pizza",
            "this",
            "that",
            "it",
            "him",
            "her",
            "them"
        ]:
            continue

        # Filler uses
        if word.endswith(","):
            found_fillers.append("like")
            continue

        if next_word in [
            "really",
            "very",
            "so",
            "just",
            "actually",
            "literally"
        ]:
            found_fillers.append("like")
            continue

        if previous_word in [
            "without",
            "with",
            "and",
            "so",
            "but",
            "then"
        ]:
            found_fillers.append("like")
            continue


    # ==================================================
    # MAYBE
    # ==================================================

    if re.fullmatch(r"maybe+", clean_word):
        # Maybe is uncertainty/hedging,
        # NOT a filler.

        if word.endswith(","):
            found_hedging.append("maybe")
            continue

        if previous_word in [
            "think",
            "guess"
        ]:
            found_hedging.append("maybe")
            continue
    # ==================================================
    # BASICALLY
    # ==================================================

    if ambiguous_word == "basically":

        if re.fullmatch(hesitation_pattern, next_word):
            found_fillers.append("basically")
            continue

        if re.fullmatch(hesitation_pattern, previous_word):
            found_fillers.append("basically")
            continue


    # ==================================================
    # ACTUALLY
    # ==================================================

    if ambiguous_word == "actually":

        if re.fullmatch(hesitation_pattern, next_word):
            found_fillers.append("actually")
            continue

        if re.fullmatch(hesitation_pattern, previous_word):
            found_fillers.append("actually")
            continue


    # ==================================================
    # LITERALLY
    # ==================================================

    if ambiguous_word == "literally":

        if re.fullmatch(hesitation_pattern, next_word):
            found_fillers.append("literally")
            continue

        if re.fullmatch(hesitation_pattern, previous_word):
            found_fillers.append("literally")
            continue


    # ==================================================
    # SO
    # ==================================================

    if ambiguous_word == "so":

        if re.fullmatch(hesitation_pattern, next_word):
            found_fillers.append("so")
            continue

        if re.fullmatch(hesitation_pattern, previous_word):
            found_fillers.append("so")
            continue


    # ==================================================
    # WELL
    # ==================================================

    if ambiguous_word == "well":

        if re.fullmatch(hesitation_pattern, next_word):
            found_fillers.append("well")
            continue

        if re.fullmatch(hesitation_pattern, previous_word):
            found_fillers.append("well")
            continue


# -----------------------------------
# DISPLAY RESULTS
# -----------------------------------

print()
print("Speech Analysis")
print("----------------")

print(
    "Number of words:",
    len(words)
)

print(
    "Filler words found:",
    len(found_fillers)
)

print(
    "Hedging words found:",
    len(found_hedging)
)


if found_fillers:

    print(
        "Detected fillers:",
        ", ".join(found_fillers)
    )

else:

    print(
        "No common filler words detected."
    )


if found_hedging:

    print(
        "Detected hedging:",
        ", ".join(found_hedging)
    )


# -----------------------------------
# SCORE
# -----------------------------------

number_of_fillers = len(found_fillers)

if number_of_fillers == 0:

    filler_score = 10

elif number_of_fillers <= 2:

    filler_score = 8

elif number_of_fillers <= 4:

    filler_score = 6

elif number_of_fillers <= 6:

    filler_score = 4

else:

    filler_score = 2


print(
    "Filler word score:",
    filler_score,
    "/10"
)
