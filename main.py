#!/usr/bin/env python3
"""
Niche Trend & Tag API — powered by Tools That Work
====================================================
Endpoints:
  GET  /trends              — trending keywords for a niche (Etsy-sourced)
  GET  /tags                — optimized tags for POD / YouTube / SEO
  GET  /quotes              — curated productivity & wellness quotes
  GET  /design-quotes       — quote + color palette combo (ready for design gen)
  GET  /niches              — list available seed niches
  GET  /health              — health check

Deploy to Render.com → list on RapidAPI.
"""

import json
import os
import random
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Routers ──────────────────────────────────────────────────────────────────
from routers import currency, qrcode_api, email_validator, weather, ip_geo
from routers import phone_validator, sentiment, domain_lookup, crypto

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Tools That Work — API Suite",
    description=(
        "A suite of powerful utility APIs: currency exchange, QR codes, "
        "email validation, weather, IP geolocation, phone validation, "
        "sentiment analysis, domain lookup, crypto prices, and niche trends. "
        "Powered by Tools That Work."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include all routers
app.include_router(currency.router)
app.include_router(qrcode_api.router)
app.include_router(email_validator.router)
app.include_router(weather.router)
app.include_router(ip_geo.router)
app.include_router(phone_validator.router)
app.include_router(sentiment.router)
app.include_router(domain_lookup.router)
app.include_router(crypto.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ───────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Niche seed keywords — expand as needed
NICHE_SEEDS: dict[str, list[str]] = {
    "productivity": [
        "productivity sticker", "habit tracker design", "daily planner design",
        "time management print", "goal setting journal", "minimalist planner",
    ],
    "wellness": [
        "mental health quote", "self care quote", "mindfulness print",
        "anxiety relief", "wellness journal", "positive affirmation sticker",
    ],
    "motivation": [
        "motivational sticker", "inspirational quote print", "hustle culture design",
        "entrepreneur quote", "boss lady sticker", "grind mindset",
    ],
    "fitness": [
        "gym motivation sticker", "workout planner", "fitness journal",
        "yoga print", "running quote design", "gym rat sticker",
    ],
    "gaming": [
        "gaming sticker", "gamer quote print", "retro gaming design",
        "controller art print", "esports poster", "pixel art sticker",
    ],
    "pets": [
        "dog lover sticker", "cat mom design", "pet portrait print",
        "funny cat quote", "dog dad sticker", "paw print design",
    ],
    "finance": [
        "budget planner design", "invest sticker", "financial freedom print",
        "money mindset quote", "savings tracker", "crypto design",
    ],
    "nature": [
        "nature print", "botanical illustration", "plant mom sticker",
        "mountain art print", "ocean wave design", "hiking quote sticker",
    ],
    "reading": [
        "bookish sticker", "book lover design", "reading quote print",
        "library print", "book club poster", "literature sticker",
    ],
    "parenting": [
        "mom life sticker", "dad joke design", "new parent gift print",
        "baby milestone design", "funny parenting quote", "toddler mom sticker",
    ],
}

# Base tags per niche for the optimizer
NICHE_BASE_TAGS: dict[str, list[str]] = {
    "productivity": [
        "productivity", "planner", "habit tracker", "minimalist",
        "goal setting", "time management", "organize",
    ],
    "wellness": [
        "wellness", "mental health", "self care", "mindfulness",
        "positive vibes", "healing", "calm",
    ],
    "motivation": [
        "motivation", "inspirational", "hustle", "entrepreneur",
        "boss", "grind", "success",
    ],
    "fitness": [
        "fitness", "gym", "workout", "yoga", "running",
        "health", "active",
    ],
    "gaming": [
        "gaming", "gamer", "retro", "pixel art", "esports",
        "controller", "video games",
    ],
    "pets": [
        "pets", "dog lover", "cat mom", "animals", "paw print",
        "fur baby", "rescue",
    ],
    "finance": [
        "finance", "budget", "invest", "money mindset",
        "savings", "wealth", "financial freedom",
    ],
    "nature": [
        "nature", "botanical", "plant mom", "mountain",
        "ocean", "hiking", "outdoor",
    ],
    "reading": [
        "bookish", "book lover", "reading", "library",
        "literature", "book club", "reader",
    ],
    "parenting": [
        "parenting", "mom life", "dad", "baby",
        "toddler", "family", "kids",
    ],
}

# ── In-memory cache (TTL-based) ─────────────────────────────────────────────

_trend_cache: dict[str, dict] = {}
CACHE_TTL = timedelta(hours=6)


# ── Scraper logic (adapted from trend_scraper.py) ───────────────────────────

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "it", "as", "be",
    "this", "that", "are", "was", "were", "been", "have", "has",
    "do", "did", "will", "would", "could", "should", "may", "might",
    "i", "you", "me", "my", "your", "our", "their", "its",
    "not", "no", "just", "about", "up", "so", "all", "more",
    "also", "than", "very", "can", "into", "some", "other",
    "new", "one", "two", "any", "each", "only", "over", "such",
    "after", "before", "between", "back", "out", "most", "own",
    "same", "how", "here", "there", "when", "where", "what", "which",
    "who", "whom", "then", "now", "down", "these", "those",
    "free", "shipping", "sale", "off", "svg", "png", "digital",
    "download", "file", "instant", "printable", "template",
}


def _scrape_etsy(keyword: str) -> list[str]:
    url = f"https://www.etsy.com/search?q={requests.utils.quote(keyword)}&ref=search_bar"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        titles = []
        for el in soup.select("h3.v2-listing-card__title")[:20]:
            t = el.get_text(strip=True)
            if t:
                titles.append(t)
        return titles
    except Exception:
        return []


def _extract_keywords(titles: list[str], top_n: int = 30) -> list[str]:
    words: list[str] = []
    for title in titles:
        for word in title.lower().split():
            clean = word.strip(".,!?\"'()-|/\\&*#@[]{}~`:;")
            if len(clean) > 3 and clean not in STOP_WORDS and not clean.isdigit():
                words.append(clean)
    counter = Counter(words)
    return [word for word, _ in counter.most_common(top_n)]


FALLBACK_TRENDS: dict[str, list[str]] = {
    "productivity": [
        "planner", "habit", "tracker", "journal", "sticker", "minimalist",
        "goals", "focus", "organize", "routine", "schedule", "notebook",
        "weekly", "monthly", "bullet", "time", "block", "priority",
    ],
    "wellness": [
        "self-care", "mental", "health", "anxiety", "mindfulness", "calm",
        "meditation", "healing", "therapy", "breathe", "gratitude", "journal",
        "affirmation", "peace", "balance", "yoga", "stress", "relief",
    ],
    "motivation": [
        "hustle", "grind", "success", "boss", "inspire", "dream",
        "believe", "ambition", "growth", "mindset", "discipline", "power",
        "strong", "resilient", "fearless", "champion", "unstoppable", "warrior",
    ],
    "fitness": [
        "gym", "workout", "gains", "protein", "cardio", "lift",
        "strength", "muscle", "training", "running", "marathon", "yoga",
        "crossfit", "bench", "deadlift", "squat", "health", "active",
    ],
    "gaming": [
        "gamer", "controller", "retro", "pixel", "arcade", "console",
        "level", "respawn", "achievement", "quest", "multiplayer", "stream",
        "esports", "headset", "keyboard", "mouse", "nerd", "geek",
    ],
    "pets": [
        "puppy", "kitten", "rescue", "adopt", "pawprint", "dogmom",
        "catmom", "furry", "treats", "collar", "leash", "veterinary",
        "breed", "shelter", "companion", "cuddle", "loyal", "bestfriend",
    ],
    "finance": [
        "budget", "invest", "savings", "wealth", "portfolio", "stocks",
        "crypto", "retire", "compound", "dividends", "income", "passive",
        "debt-free", "frugal", "money", "rich", "millionaire", "freedom",
    ],
    "nature": [
        "botanical", "forest", "mountain", "ocean", "hiking", "wildflower",
        "sunset", "landscape", "garden", "fern", "succulent", "cactus",
        "trail", "river", "waterfall", "meadow", "bloom", "earthtone",
    ],
    "reading": [
        "bookworm", "novel", "library", "chapter", "fiction", "author",
        "literary", "bookmark", "spine", "shelf", "reader", "paperback",
        "hardcover", "genre", "classic", "bestseller", "story", "pages",
    ],
    "parenting": [
        "momlife", "dadlife", "toddler", "newborn", "milestone", "nursery",
        "diaper", "sleepless", "family", "firstday", "lunchbox", "schoolrun",
        "bedtime", "playdate", "tantrum", "snack", "sippy", "stroller",
    ],
}


def _get_trends(niche: str) -> dict:
    now = datetime.utcnow()

    # Check cache
    if niche in _trend_cache:
        cached = _trend_cache[niche]
        if now - cached["_fetched_at"] < CACHE_TTL:
            return {k: v for k, v in cached.items() if k != "_fetched_at"}

    seeds = NICHE_SEEDS.get(niche, NICHE_SEEDS["productivity"])
    all_titles: list[str] = []
    by_seed: dict[str, list[str]] = {}

    for kw in seeds:
        titles = _scrape_etsy(kw)
        by_seed[kw] = titles
        all_titles.extend(titles)
        time.sleep(random.uniform(1.5, 3.0))

    top_keywords = _extract_keywords(all_titles)

    # Fallback: if scraping returned nothing, use curated keyword lists
    source = "live"
    if not top_keywords:
        top_keywords = FALLBACK_TRENDS.get(niche, FALLBACK_TRENDS["productivity"])
        source = "curated"

    result = {
        "niche": niche,
        "updated": now.isoformat() + "Z",
        "top_keywords": top_keywords,
        "sample_titles": random.sample(all_titles, min(10, len(all_titles))),
        "seed_count": {kw: len(titles) for kw, titles in by_seed.items()},
        "source": source,
    }

    _trend_cache[niche] = {**result, "_fetched_at": now}
    return result


# ── Quotes (bundled data) ───────────────────────────────────────────────────

QUOTES = [
    "Done is better than perfect.",
    "Progress, not perfection.",
    "One task at a time.",
    "Rest is productive.",
    "Small steps compound.",
    "Focus is a superpower.",
    "Slow down to speed up.",
    "Do less. Do it better.",
    "Clarity before action.",
    "Begin before you're ready.",
    "Consistency beats intensity.",
    "Your attention is your asset.",
    "Less, but better.",
    "Make it simple. Then simpler.",
    "Start before you feel ready.",
    "The work is the reward.",
    "Rest without guilt.",
    "Habits are votes for who you're becoming.",
    "Two-minute rule: do it now.",
    "Discipline is self-love.",
    "Ship it.",
    "Plant seeds. Trust the season.",
    "Automate the repetitive. Focus on the creative.",
    "Plan the work. Work the plan.",
    "The best time was then. The next best is now.",
    "Single-tasking is a skill.",
    "Deep work, deep life.",
    "Morning pages, evening wins.",
    "Structure creates freedom.",
    "Context switching is expensive.",
    "Write it down. Get it done.",
    "Track it, change it.",
    "Systems over willpower.",
    "Version one beats version none.",
    "Energy follows attention.",
    "One priority per day.",
    "Start ugly, refine later.",
    "Finish what you started.",
    "What gets measured gets managed.",
    "Show up, even small.",
    "Calm is a choice.",
    "Long game wins.",
    "Deep focus compounds.",
    "Build it before you need it.",
    "Focus on the signal, not the noise.",
    "Build the life, then live it.",
    "No notifications. Just work.",
    "Eat the frog first.",
    "Ruthlessly prioritize.",
    "Your best work requires your best hours.",
]

COLOR_PALETTES = [
    {"bg": "#F5F0E8", "text": "#2D2D2D", "accent": "#C9A87C", "name": "warm-sand"},
    {"bg": "#1A1A2E", "text": "#E0E0E0", "accent": "#E94560", "name": "dark-coral"},
    {"bg": "#FFFFFF", "text": "#333333", "accent": "#4ECDC4", "name": "clean-teal"},
    {"bg": "#FFF8E7", "text": "#2C3E50", "accent": "#E67E22", "name": "cream-amber"},
    {"bg": "#F0F4F8", "text": "#1A202C", "accent": "#5A67D8", "name": "slate-indigo"},
    {"bg": "#2D3436", "text": "#DFE6E9", "accent": "#00B894", "name": "dark-mint"},
    {"bg": "#FAF3E0", "text": "#2C3E50", "accent": "#D35400", "name": "paper-rust"},
    {"bg": "#0D1117", "text": "#C9D1D9", "accent": "#58A6FF", "name": "github-dark"},
    {"bg": "#FDF2F8", "text": "#831843", "accent": "#EC4899", "name": "blush-pink"},
    {"bg": "#ECFDF5", "text": "#064E3B", "accent": "#10B981", "name": "fresh-green"},
]


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Niche Trend & Tag API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": ["/trends", "/tags", "/quotes", "/design-quotes", "/niches", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}


@app.get("/niches")
def list_niches():
    """List all available niches with their seed keyword counts."""
    return {
        "niches": [
            {"name": n, "seed_keywords": len(seeds)}
            for n, seeds in NICHE_SEEDS.items()
        ]
    }


@app.get("/trends")
def get_trends(
    niche: str = Query(
        default="productivity",
        description="Niche to get trends for. Use /niches to see available options.",
    ),
    limit: int = Query(default=20, ge=1, le=50, description="Max keywords to return"),
):
    """
    Get real-time trending keywords for a niche, scraped from Etsy listings.
    Results are cached for 6 hours per niche.
    """
    niche = niche.lower().strip()
    if niche not in NICHE_SEEDS:
        available = list(NICHE_SEEDS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown niche '{niche}'. Available: {available}",
        )

    data = _get_trends(niche)
    data["top_keywords"] = data["top_keywords"][:limit]
    return data


@app.get("/tags")
def get_tags(
    niche: str = Query(default="productivity", description="Niche for tag optimization"),
    platform: str = Query(
        default="general",
        description="Target platform: general, youtube, etsy, pod",
    ),
    count: int = Query(default=15, ge=5, le=30, description="Number of tags to return"),
    keyword: Optional[str] = Query(default=None, description="Optional focus keyword to prioritize"),
):
    """
    Get optimized tags for a niche + platform combo.
    Combines evergreen base tags with current trending keywords.
    """
    niche = niche.lower().strip()
    if niche not in NICHE_SEEDS:
        raise HTTPException(status_code=400, detail=f"Unknown niche. Use /niches for options.")

    base = list(NICHE_BASE_TAGS.get(niche, []))

    # Platform-specific additions
    platform_tags: dict[str, list[str]] = {
        "youtube": ["tutorial", "tips", "how to", "guide", "2026"],
        "etsy": ["sticker", "print", "digital download", "printable", "gift"],
        "pod": ["sticker", "t-shirt design", "poster", "mug design", "print"],
        "general": [],
    }
    extras = platform_tags.get(platform.lower(), [])

    # Try to pull trending keywords (use cache if available)
    trending: list[str] = []
    if niche in _trend_cache:
        cached = _trend_cache[niche]
        if datetime.utcnow() - cached["_fetched_at"] < CACHE_TTL:
            trending = cached.get("top_keywords", [])[:10]

    # Build final tag list
    all_tags = []
    if keyword:
        all_tags.append(keyword.lower().strip())
    all_tags.extend(base)
    all_tags.extend(extras)
    all_tags.extend(trending)

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for tag in all_tags:
        if tag not in seen:
            seen.add(tag)
            unique.append(tag)

    final = unique[:count]

    return {
        "niche": niche,
        "platform": platform,
        "tags": final,
        "tag_count": len(final),
        "includes_trending": len(trending) > 0,
        "tip": "Call /trends first to populate trending data for better tag results.",
    }


@app.get("/quotes")
def get_quotes(
    count: int = Query(default=5, ge=1, le=20, description="Number of quotes"),
    category: str = Query(default="all", description="all, productivity, mindset, rest"),
):
    """Get curated productivity & wellness quotes for content creation."""
    pool = list(QUOTES)

    # Simple category filtering by keyword
    if category != "all":
        filters: dict[str, list[str]] = {
            "productivity": ["task", "focus", "work", "plan", "system", "priority", "finish", "start", "ship"],
            "mindset": ["compound", "consistency", "discipline", "habit", "vote", "build", "long game"],
            "rest": ["rest", "calm", "slow", "guilt", "gentle"],
        }
        keywords = filters.get(category.lower(), [])
        if keywords:
            pool = [q for q in pool if any(k in q.lower() for k in keywords)] or pool

    selected = random.sample(pool, min(count, len(pool)))
    return {
        "quotes": selected,
        "count": len(selected),
        "categories": ["all", "productivity", "mindset", "rest"],
    }


@app.get("/design-quotes")
def get_design_quotes(
    count: int = Query(default=3, ge=1, le=10, description="Number of design combos"),
):
    """
    Get quote + color palette combos ready for design generation.
    Each result includes a quote, background/text/accent colors, and palette name.
    Perfect for POD design automation.
    """
    selected_quotes = random.sample(QUOTES, min(count, len(QUOTES)))
    combos = []
    for quote in selected_quotes:
        palette = random.choice(COLOR_PALETTES)
        combos.append({
            "quote": quote,
            "palette": palette,
            "suggested_filename": (
                quote.lower()
                .replace(" ", "-")
                .replace(".", "")
                .replace(",", "")
                .replace("'", "")[:50]
            ),
        })

    return {"designs": combos, "count": len(combos)}


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
