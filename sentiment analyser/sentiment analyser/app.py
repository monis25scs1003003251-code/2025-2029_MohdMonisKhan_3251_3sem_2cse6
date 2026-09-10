from flask import Flask, render_template, request, jsonify
from textblob import TextBlob

app = Flask(__name__)


def classify(polarity: float) -> str:
    if polarity > 0.05:
        return "Positive"
    elif polarity < -0.05:
        return "Negative"
    return "Neutral"


def breakdown(polarity: float):
    """Approximate pos/neu/neg percentages from a single polarity score,
    since TextBlob only returns one polarity value (not VADER-style buckets)."""
    if polarity > 0:
        positive = polarity * 100
        negative = 0
        neutral = 100 - positive
    elif polarity < 0:
        negative = abs(polarity) * 100
        positive = 0
        neutral = 100 - negative
    else:
        positive = 0
        negative = 0
        neutral = 100
    return round(positive, 1), round(neutral, 1), round(negative, 1)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Please enter some text to analyze."}), 400

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    sentiment = classify(polarity)
    positive, neutral, negative = breakdown(polarity)

    return jsonify({
        "sentiment": sentiment,
        "compound": round(polarity, 4),
        "subjectivity": round(subjectivity, 4),
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
    })


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
