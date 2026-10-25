import json
import time
from google import genai
from google.genai import errors, types
import streamlit as st


def get_gemini_client():
  api_key = st.secrets["GEMINI_API_KEY"]
  return genai.Client(api_key=api_key)


def extract_books_from_spines(
    image_bytes: bytes, max_retries: int = 4
) -> list[dict]:
  client = get_gemini_client()

  prompt = """
    Examine this photo showing book spines on a shelf or stacked together.
    Extract every visible book in natural visual reading order (left-to-right or top-to-bottom).
    Pay attention to titles and authors in Portuguese, English, and other languages.
    Return strictly a JSON list of objects with keys: "title", "author", "publisher".
    """

  contents = [
      types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
      prompt,
  ]

  config = types.GenerateContentConfig(
      response_mime_type="application/json",
      temperature=0.1,
  )

  # Exponential backoff parameters
  delay = 2  # initial wait in seconds (2s -> 4s -> 8s -> 16s)
  response = None

  for attempt in range(max_retries):
    try:
      response = client.models.generate_content(
          model="gemini-3.8-flash",
          contents=contents,
          config=config,
      )
      break  # Request succeeded, exit retry loop
    except errors.ServerError as e:
      # Catch 503 high demand or transient server errors
      if attempt == max_retries - 1:
        st.error(
            "Gemini is currently experiencing very high demand. Please try"
            " again in a moment."
        )
        return []

      time.sleep(delay)
      delay *= 2
    except errors.APIError as e:
      # Non-transient API errors (e.g. 400 Bad Request, 401 Auth) should fail immediately
      st.error(f"API Error: {e.message}")
      return []
    except Exception as e:
      st.error(f"Unexpected error: {e}")
      return []

  if not response or not response.text:
    return []

  try:
    data = json.loads(response.text)
    if isinstance(data, list):
      return data
    elif isinstance(data, dict) and "books" in data:
      return data["books"]
    return []
  except Exception:
    return []