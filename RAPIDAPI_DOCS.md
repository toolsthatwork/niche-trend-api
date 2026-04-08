# Niche Trend and Tag API — Documentation

## Overview

Get instant access to curated trending data across 10 profitable niches. Built for Etsy sellers, print-on-demand designers, YouTube/TikTok creators, and developers building tools for the creator economy.

**Base URL:** `https://niche-trend-api.onrender.com`

**Authentication:** Pass your RapidAPI key via the `X-RapidAPI-Key` header (handled automatically by RapidAPI).

---

## Supported Niches

| Niche | Description |
|-------|-------------|
| `productivity` | Focus, time management, deep work |
| `wellness` | Mental health, self-care, mindfulness |
| `motivation` | Inspirational quotes, mindset, growth |
| `fitness` | Exercise, nutrition, healthy habits |
| `gaming` | Video games, streaming, esports |
| `pets` | Dogs, cats, pet care, accessories |
| `finance` | Budgeting, investing, passive income |
| `nature` | Outdoors, plants, sustainability |
| `reading` | Books, literacy, learning |
| `parenting` | Family, kids, education |

---

## Endpoints

### GET `/niches`
Returns all supported niche categories with seed keywords.

**Example Response:**
```json
{
  "niches": ["productivity", "wellness", "motivation", ...],
  "count": 10
}
```

---

### GET `/trends`
Returns trending keywords for a given niche. Data refreshes every 6 hours.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `niche` | string | No | `productivity` | One of the 10 supported niches |

**Example Request:**
```
GET /trends?niche=wellness
```

**Example Response:**
```json
{
  "niche": "wellness",
  "keywords": ["morning routine", "anxiety relief", "self care sunday", "mental health tips"],
  "cached": false,
  "source": "scraped"
}
```

---

### GET `/tags`
Returns optimized hashtags and listing tags for a niche. Perfect for Etsy listings, Instagram, TikTok, and Pinterest.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `niche` | string | No | `productivity` | One of the 10 supported niches |
| `limit` | integer | No | `20` | Number of tags (max 50) |

**Example Request:**
```
GET /tags?niche=fitness&limit=30
```

**Example Response:**
```json
{
  "niche": "fitness",
  "tags": ["#fitness", "#workout", "#gym", "#fitnessmotivation", ...],
  "count": 30
}
```

---

### GET `/quotes`
Returns curated quotes for a niche. Great for social media posts, content creation, and POD designs.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `niche` | string | No | `motivation` | One of the 10 supported niches |
| `limit` | integer | No | `10` | Number of quotes (max 50) |

**Example Request:**
```
GET /quotes?niche=motivation&limit=5
```

**Example Response:**
```json
{
  "niche": "motivation",
  "quotes": [
    "Start before you're ready.",
    "Small steps compound into massive results.",
    ...
  ],
  "count": 5
}
```

---

### GET `/design-quotes`
Returns quotes bundled with matching color palettes. Ready-to-use for print-on-demand designers.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `limit` | integer | No | `5` | Number of designs (max 20) |

**Example Request:**
```
GET /design-quotes?limit=3
```

**Example Response:**
```json
{
  "designs": [
    {
      "quote": "Focus is a superpower.",
      "palette": {
        "name": "Midnight Blue",
        "background": "#1a1a2e",
        "text": "#e0e0e0",
        "accent": "#4cc9f0"
      }
    }
  ],
  "count": 3
}
```

---

### GET `/health`
Health check endpoint. Returns `200 OK` when the API is running.

---

## Rate Limits

| Plan | Requests/Month | Rate Limit |
|------|---------------|------------|
| Basic (Free) | 100 | 1,000/hour |
| Pro | 1,000 | 1,000/hour |
| Ultra | 10,000 | 1,000/hour |
| Mega | 100,000 | 1,000/hour |

---

## Notes

- The free tier spins down after inactivity (Render free plan). First request may take 10-30 seconds to wake up. Paid plans respond instantly.
- Trend data is cached for 6 hours and sourced from live Etsy search data with curated fallbacks.
- All endpoints return JSON.
