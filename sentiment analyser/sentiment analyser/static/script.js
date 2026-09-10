const textInput = document.getElementById("text-input");
const charCount = document.getElementById("char-count");
const analyzeBtn = document.getElementById("analyze-btn");
const clearBtn = document.getElementById("clear-btn");
const errorMsg = document.getElementById("error-msg");
const resultBox = document.getElementById("result-box");

const emojiEl = document.getElementById("emoji");
const sentimentLabel = document.getElementById("sentiment-label");
const polarityScore = document.getElementById("polarity-score");
const gaugeFill = document.getElementById("gauge-fill");
const gaugeValue = document.getElementById("gauge-value");
const sliderPointer = document.getElementById("slider-pointer");
const barPos = document.getElementById("bar-pos");
const barNeu = document.getElementById("bar-neu");
const barNeg = document.getElementById("bar-neg");
const pctPos = document.getElementById("pct-pos");
const pctNeu = document.getElementById("pct-neu");
const pctNeg = document.getElementById("pct-neg");

const GAUGE_CIRCUMFERENCE = 283; // approx pi * radius(90)

const EMOJI = { Positive: "😄", Negative: "☹️", Neutral: "😐" };
const COLORS = { Positive: "#34e89e", Negative: "#ff5f6d", Neutral: "#6fa8ff" };

textInput.addEventListener("input", () => {
  charCount.textContent = `${textInput.value.length} / 5000`;
});

textInput.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") analyze();
});

analyzeBtn.addEventListener("click", analyze);

clearBtn.addEventListener("click", () => {
  textInput.value = "";
  charCount.textContent = "0 / 5000";
  hideError();
  resultBox.classList.add("hidden");
});

async function analyze() {
  const text = textInput.value.trim();
  hideError();

  if (!text) {
    showError("Please enter some text to analyze.");
    return;
  }

  setLoading(true);

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Something went wrong.");
      return;
    }

    renderResult(data);
  } catch (err) {
    showError("Could not reach the server. Is it running?");
  } finally {
    setLoading(false);
  }
}

function renderResult(data) {
  const { sentiment, compound, positive, negative, neutral } = data;

  resultBox.classList.remove("hidden");

  emojiEl.textContent = EMOJI[sentiment] || "🙂";
  sentimentLabel.textContent = sentiment;
  sentimentLabel.style.color = COLORS[sentiment] || "#fff";
  polarityScore.textContent = compound.toFixed(2);

  const offset = GAUGE_CIRCUMFERENCE * (1 - (compound + 1) / 2);
  gaugeFill.style.strokeDashoffset = offset;
  gaugeFill.style.stroke = COLORS[sentiment] || "#6fa8ff";
  gaugeValue.textContent = compound.toFixed(2);

  const sliderLeft = ((compound + 1) / 2) * 100;
  sliderPointer.style.left = `${sliderLeft}%`;

  requestAnimationFrame(() => {
    barPos.style.width = `${positive}%`;
    barNeu.style.width = `${neutral}%`;
    barNeg.style.width = `${negative}%`;
  });

  pctPos.textContent = `${positive}%`;
  pctNeu.textContent = `${neutral}%`;
  pctNeg.textContent = `${negative}%`;
}

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.classList.toggle("loading", isLoading);
}

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.classList.add("show");
}

function hideError() {
  errorMsg.textContent = "";
  errorMsg.classList.remove("show");
}
