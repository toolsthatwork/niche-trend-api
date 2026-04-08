"""
Readability Score API
Uses textstat (offline)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import textstat

router = APIRouter(prefix="/readability", tags=["Readability Score"])

GRADE_LABELS = {
    range(-100, 1): "Professional/Academic",
    range(1, 7): "College Graduate",
    range(7, 10): "College",
    range(10, 13): "High School",
    range(13, 17): "Middle School",
    range(17, 20): "5th–6th Grade",
    range(20, 30): "4th Grade",
    range(30, 100): "3rd Grade or below",
}

def grade_label(score: float) -> str:
    for r, label in GRADE_LABELS.items():
        if int(score) in r:
            return label
    return "Unknown"

class BatchRequest(BaseModel):
    texts: List[str]

@router.get("/", summary="API Info")
def readability_info():
    return {
        "name": "Readability Score API",
        "version": "1.0.0",
        "endpoints": ["/readability/analyze", "/readability/batch", "/readability/grade"],
        "powered_by": "Tools That Work"
    }

@router.get("/analyze", summary="Full readability analysis of text")
def analyze_text(
    text: str = Query(..., description="Text to analyze (min 100 chars recommended)")
):
    if len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text too short for readability analysis")
    try:
        flesch = textstat.flesch_reading_ease(text)
        fk_grade = textstat.flesch_kincaid_grade(text)
        smog = textstat.smog_index(text)
        ari = textstat.automated_readability_index(text)
        cli = textstat.coleman_liau_index(text)
        gunning = textstat.gunning_fog(text)
        consensus = textstat.text_standard(text, float_output=True)

        return {
            "text_length": len(text),
            "word_count": textstat.lexicon_count(text),
            "sentence_count": textstat.sentence_count(text),
            "syllable_count": textstat.syllable_count(text),
            "avg_words_per_sentence": round(textstat.lexicon_count(text) / max(textstat.sentence_count(text), 1), 1),
            "difficult_words": textstat.difficult_words(text),
            "scores": {
                "flesch_reading_ease": round(flesch, 1),
                "flesch_kincaid_grade": round(fk_grade, 1),
                "gunning_fog": round(gunning, 1),
                "smog_index": round(smog, 1),
                "automated_readability_index": round(ari, 1),
                "coleman_liau_index": round(cli, 1),
                "consensus_grade": round(consensus, 1),
            },
            "reading_level": grade_label(consensus),
            "estimated_reading_time_seconds": round(textstat.lexicon_count(text) / 238 * 60),
            "flesch_interpretation": (
                "Very Easy" if flesch >= 90 else
                "Easy" if flesch >= 80 else
                "Fairly Easy" if flesch >= 70 else
                "Standard" if flesch >= 60 else
                "Fairly Difficult" if flesch >= 50 else
                "Difficult" if flesch >= 30 else
                "Very Confusing"
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/grade", summary="Get simple reading grade level")
def grade_level(text: str = Query(..., description="Text to grade")):
    if len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text too short")
    grade = textstat.text_standard(text, float_output=True)
    return {
        "grade_level": round(grade, 1),
        "reading_level": grade_label(grade),
        "word_count": textstat.lexicon_count(text),
    }

@router.post("/batch", summary="Analyze multiple texts (max 20)")
def batch_analyze(req: BatchRequest):
    if len(req.texts) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 texts per request")
    results = []
    for text in req.texts:
        grade = textstat.text_standard(text, float_output=True)
        results.append({
            "text": text[:80] + "..." if len(text) > 80 else text,
            "word_count": textstat.lexicon_count(text),
            "grade_level": round(grade, 1),
            "reading_level": grade_label(grade),
            "flesch_reading_ease": round(textstat.flesch_reading_ease(text), 1),
        })
    return {"results": results, "count": len(results)}
