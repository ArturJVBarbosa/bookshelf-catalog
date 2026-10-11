import json
import streamlit as st
from google import genai
from google.genai import types


def get_gemini_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)


def extract_books_from_spines(image_bytes: bytes) -> list[dict]:
    client = get_gemini_client()

    prompt = """
    Examine this photo showing book spines on a shelf or stacked together.
    Extract every visible book in natural visual reading order (left-to-right or top-to-bottom).
    Pay attention to titles and authors in Portuguese, English, and other languages.
    Return strictly a JSON list of objects with keys: "title", "author", "publisher".
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    try:
        data = json.loads(response.text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "books" in data:
            return data["books"]
        return []
    except Exception:
        return []