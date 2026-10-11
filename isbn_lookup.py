import requests


def lookup_isbn(isbn: str) -> dict:
    clean_isbn = isbn.replace("-", "").strip()

    # 1. Try Google Books
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("totalItems", 0) > 0:
                info = data["items"][0].get("volumeInfo", {})
                return {
                    "title": info.get("title", ""),
                    "author": ", ".join(info.get("authors", [])),
                    "publisher": info.get("publisher", ""),
                    "isbn": clean_isbn,
                }
    except Exception:
        pass

    # 2. Try Open Library
    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            key = f"ISBN:{clean_isbn}"
            if key in data:
                b = data[key]
                authors = [a.get("name") for a in b.get("authors", []) if "name" in a]
                publishers = [p.get("name") for p in b.get("publishers", []) if "name" in p]
                return {
                    "title": b.get("title", ""),
                    "author": ", ".join(authors),
                    "publisher": ", ".join(publishers),
                    "isbn": clean_isbn,
                }
    except Exception:
        pass

    return {"title": "", "author": "", "publisher": "", "isbn": clean_isbn}