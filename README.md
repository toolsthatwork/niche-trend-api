# Niche Trend & Tag API

Trending keywords, tags, quotes, and design palettes for creators and sellers.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info |
| `GET /health` | Health check |
| `GET /niches` | List all supported niches |
| `GET /trends?niche=productivity` | Trending keywords for a niche |
| `GET /tags?niche=wellness&limit=30` | Hashtags/tags for a niche |
| `GET /quotes?niche=motivation&limit=10` | Curated quotes |
| `GET /design-quotes` | Quotes with color palettes for POD |

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Deploy

Configured for Render.com free tier. See `render.yaml`.

## License

MIT
