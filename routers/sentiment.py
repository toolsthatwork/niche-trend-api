"""
Sentiment & Text Analysis API
Uses TextBlob (lightweight, no GPU, no API key)
"""
from fastapi import APIRouter, HTTPException, Query, Body
from textblob import TextBlob
import re
from typing import List

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])

def analyze(text: str) -> dict:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity      # -1 to 1
    subjectivity = blob.sentiment.subjectivity  # 0 to 1

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    if subjectivity > 0.6:
        tone = "subjective"
    elif subjectivity < 0.4:
        tone = "objective"
    else:
        tone = "balanced"

    # Word count stats
    words = text.split()
    sentences = [str(s) for s in blob.sentences]

    return {
        "text": text[:200] + "..." if len(text) > 200 else text,
        "sentiment": label,
        "polarity": round(polarity, 4),
        "subjectivity": round(subjectivity, 4),
        "tone": tone,
        "confidence": round(abs(polarity), 4),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(len(words) / max(len(sentences), 1), 1)
    }

@router.get("/", summary="API Info")
def sentiment_info():
    return {
        "name": "Sentiment & Text Analysis API",
        "version": "1.0.0",
        "endpoints": ["/sentiment/analyze", "/sentiment/batch", "/sentiment/keywords"],
        "powered_by": "Tools That Work"
    }

@router.get("/analyze", summary="Analyze sentiment of a text")
def analyze_sentiment(
    text: str = Query(..., description="Text to analyze (max 5000 characters)", max_length=5000)
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return analyze(text)

@router.post("/batch", summary="Analyze sentiment of multiple texts (max 50)")
def batch_sentiment(
    texts: List[str] = Body(..., description="List of texts to analyze (max 50)")
):
    if len(texts) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 texts per request")
    results = []
    for i, text in enumerate(texts):
        try:
            results.append({"index": i, **analyze(text)})
        except Exception:
            results.append({"index": i, "error": "Analysis failed"})

    positive = sum(1 for r in results if r.get("sentiment") == "positive")
    negative = sum(1 for r in results if r.get("sentiment") == "negative")
    neutral = sum(1 for r in results if r.get("sentiment") == "neutral")

    return {
        "total": len(texts),
        "summary": {"positive": positive, "negative": negative, "neutral": neutral},
        "results": results
    }

@router.get("/keywords", summary="Extract keywords from text")
def extract_keywords(
    text: str = Query(..., description="Text to extract keywords from", max_length=5000),
    limit: int = Query(10, ge=1, le=50, description="Max keywords to return")
):
    blob = TextBlob(text)
    # Extract noun phrases as keywords
    noun_phrases = list(set([np.lower() for np in blob.noun_phrases if len(np) > 2]))
    # Also get most common words (filtered)
    stop_words = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","from","is","are","was","were","be","been","have","has","had","do","does","did","will","would","could","should","may","might","this","that","these","those","it","its","they","their","we","our","you","your","he","she","his","her"}
    words = [w.lower() for w in text.split() if w.lower() not in stop_words and len(w) > 3 and w.isalpha()]
    from collections import Counter
    word_freq = Counter(words).most_common(limit)

    return {
        "text_length": len(text),
        "noun_phrases": noun_phrases[:limit],
        "top_words": [{"word": w, "count": c} for w, c in word_freq],
        "sentence_count": len(blob.sentences)
    }
