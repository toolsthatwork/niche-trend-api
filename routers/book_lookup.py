"""
Book / ISBN Lookup API
Uses OpenLibrary.org (free, no key)
"""
from fastapi import APIRouter, HTTPException, Query
import requests
import re

router = APIRouter(prefix="/book", tags=["Book Lookup"])
BASE = "https://openlibrary.org"

def clean_isbn(isbn: str) -> str:
    return re.sub(r"[^0-9X]", "", isbn.upper())

@router.get("/", summary="API Info")
def book_info():
    return {
        "name": "Book and ISBN Lookup API",
        "version": "1.0.0",
        "endpoints": ["/book/isbn", "/book/search", "/book/author"],
        "data_source": "OpenLibrary.org",
        "powered_by": "Tools That Work"
    }

@router.get("/isbn", summary="Look up a book by ISBN-10 or ISBN-13")
def lookup_isbn(
    isbn: str = Query(..., description="ISBN-10 or ISBN-13 (with or without dashes)")
):
    isbn_clean = clean_isbn(isbn)
    if len(isbn_clean) not in (10, 13):
        raise HTTPException(status_code=400, detail="Invalid ISBN length. Must be 10 or 13 digits.")
    try:
        r = requests.get(f"{BASE}/api/books", params={
            "bibkeys": f"ISBN:{isbn_clean}",
            "format": "json",
            "jscmd": "data"
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        key = f"ISBN:{isbn_clean}"
        if key not in data:
            raise HTTPException(status_code=404, detail=f"No book found for ISBN: {isbn_clean}")
        book = data[key]
        return {
            "isbn": isbn_clean,
            "title": book.get("title"),
            "subtitle": book.get("subtitle"),
            "authors": [a.get("name") for a in book.get("authors", [])],
            "publishers": [p.get("name") for p in book.get("publishers", [])],
            "publish_date": book.get("publish_date"),
            "number_of_pages": book.get("number_of_pages"),
            "subjects": [s.get("name") for s in book.get("subjects", [])][:10],
            "cover_url": book.get("cover", {}).get("large") or book.get("cover", {}).get("medium"),
            "openlibrary_url": book.get("url"),
            "identifiers": book.get("identifiers", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Lookup failed: {str(e)}")

@router.get("/search", summary="Search books by title or author")
def search_books(
    query: str = Query(..., description="Search query (title, author, keyword)"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    author: str = Query(None, description="Filter by author name"),
    subject: str = Query(None, description="Filter by subject"),
):
    try:
        params = {"q": query, "limit": limit, "fields": "key,title,author_name,first_publish_year,isbn,number_of_pages_median,subject,cover_edition_key"}
        if author: params["author"] = author
        if subject: params["subject"] = subject
        r = requests.get(f"{BASE}/search.json", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        books = []
        for doc in data.get("docs", []):
            books.append({
                "title": doc.get("title"),
                "authors": doc.get("author_name", []),
                "first_published": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [None])[0] if doc.get("isbn") else None,
                "pages": doc.get("number_of_pages_median"),
                "subjects": doc.get("subject", [])[:5],
                "cover_url": f"https://covers.openlibrary.org/b/olid/{doc['cover_edition_key']}-M.jpg" if doc.get("cover_edition_key") else None,
            })
        return {"query": query, "total": data.get("numFound", 0), "results": books, "count": len(books)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Search failed: {str(e)}")
