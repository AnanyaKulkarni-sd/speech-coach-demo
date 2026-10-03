let selectedAudio = null;
let mediaRecorder = null;
let recordedChunks = [];

function chooseAudio() {
    document.getElementById("audioInput").click();
}

document.getElementById("audioInput").addEventListener("change", function () {
    if (this.files.length > 0) {
        selectedAudio = this.files[0];
        document.getElementById("fileName").textContent = "Selected: " + selectedAudio.name;
        const preview = document.getElementById("audioPreview");
        preview.src = URL.createObjectURL(selectedAudio);
        preview.hidden = false;
    }
});

async function toggleRecording() {
    const button = document.getElementById("recordButton");
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        button.textContent = "● Record";
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = function (event) {
            if (event.data.size > 0) recordedChunks.push(event.data);
        };

        mediaRecorder.onstop = function () {
            const blob = new Blob(recordedChunks, { type: "audio/webm" });
            selectedAudio = new File([blob], "recorded_speech.webm", { type: "audio/webm" });
            const preview = document.getElementById("audioPreview");
            preview.src = URL.createObjectURL(blob);
            preview.hidden = false;
            document.getElementById("fileName").textContent = "Recorded audio ready";
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        button.textContent = "■ Stop Recording";
    } catch (error) {
        alert("Microphone permission was not available.");
        console.error(error);
    }
}

async function analyzeSpeech() {
    const status = document.getElementById("status");
    if (!selectedAudio) {
        status.textContent = "Please choose an audio file or record your speech first.";
        return;
    }

    status.textContent = "Analyzing speech...";
    const formData = new FormData();
    formData.append("audio", selectedAudio);

    try {
        const response = await fetch("/analyze", { method: "POST", body: formData });
        const data = await response.json();
        displayResults(data);
        status.textContent = "Analysis complete!";
    } catch (error) {
        status.textContent = "Something went wrong. Please try again.";
        console.error(error);
    }
}

function displayResults(data) {
    const metrics = data.metrics;
    document.getElementById("results").hidden = false;

    document.getElementById("overallScore").textContent = metrics.overall;
    document.getElementById("totalWords").textContent = metrics.total_words;
    document.getElementById("fillerCount").textContent = metrics.filler_count;
    document.getElementById("fillerPercentage").textContent = metrics.filler_percentage + "%";
    document.getElementById("duration").textContent = metrics.duration + "s";
    document.getElementById("repeatedWords").textContent = metrics.repeated_words;
    document.getElementById("pace").textContent = metrics.pace;
    document.getElementById("volume").textContent = metrics.volume;
    document.getElementById("pausing").textContent = metrics.pausing;

    displayTranscript(data.transcript);
    displayDeliveryRings(metrics);
    displayFeedback(data.feedback);
    document.getElementById("results").scrollIntoView({ behavior: "smooth" });
}

function displayTranscript(words) {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = "";
    words.forEach(item => {
        const span = document.createElement("span");
        span.textContent = item.word;
        span.className = item.filler ? "word filler" : "word";
        transcript.appendChild(span);
    });
}

function displayDeliveryRings(metrics) {
    // All ring values are performance scores: higher = stronger performance.
    setRing("ringPace", "ringPaceValue", metrics.pace);
    setRing("ringVolume", "ringVolumeValue", metrics.volume);
    setRing("ringPausing", "ringPausingValue", metrics.pausing);

    // These two are calculated by the scoring pipeline when real modules are connected.
    // For the current demo, fall back to the existing overall-style values if absent.
    const fillerScore = metrics.filler_score !== undefined
        ? metrics.filler_score
        : Math.max(0, Math.min(100, 100 - Number(metrics.filler_percentage || 0) * 5));
    const repetitionScore = metrics.repetition_score !== undefined
        ? metrics.repetition_score
        : Math.max(0, Math.min(100, 100 - Number(metrics.repeated_words || 0) * 5));

    setRing("ringFiller", "ringFillerValue", fillerScore);
    setRing("ringRepetition", "ringRepetitionValue", repetitionScore);
    setRing("ringOverall", "ringOverallValue", metrics.overall);
}

function setRing(ringId, valueId, value) {
    const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
    const ring = document.getElementById(ringId);
    ring.style.setProperty("--score", safeValue);
    ring.classList.remove("score-red", "score-yellow", "score-green");

    // User-defined score colours:
    // <30 = red, 30–80 = yellow, >80 = green.
    if (safeValue < 30) ring.classList.add("score-red");
    else if (safeValue <= 80) ring.classList.add("score-yellow");
    else ring.classList.add("score-green");

    document.getElementById(valueId).textContent = Math.round(safeValue);
}

function displayFeedback(items) {
    const feedback = document.getElementById("feedback");
    feedback.innerHTML = "";
    items.forEach(item => {
        const div = document.createElement("div");
        div.className = "feedback-item";
        div.textContent = "💡 " + item;
        feedback.appendChild(div);
    });
}

function toggleTheme() {
    const dark = document.body.classList.toggle("dark");
    localStorage.setItem("speechCoachTheme", dark ? "dark" : "light");
    updateThemeButton(dark);
}

function updateThemeButton(dark) {
    document.getElementById("themeIcon").textContent = dark ? "☾" : "☀";
    document.getElementById("themeLabel").textContent = dark ? "Dark" : "Light";
}

(function loadTheme() {
    const dark = localStorage.getItem("speechCoachTheme") === "dark";
    document.body.classList.toggle("dark", dark);
    updateThemeButton(dark);
})();
