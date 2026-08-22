import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY was not found in the .env file."
    )


print("API key loaded:", bool(api_key))


client = genai.Client(api_key=api_key)


response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Reply with exactly: HEX Gemini connection is working.",
)


print("Gemini response:")
print(response.text)