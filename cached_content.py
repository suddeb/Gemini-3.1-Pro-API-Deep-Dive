from google import genai
from google.genai import types
from dotenv import load_dotenv
import io
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

long_context_pdf_path = "SudiptaDeb_Resume.pdf"

# Retrieve and upload the PDF using the File API
with open(long_context_pdf_path, "rb") as f:
    doc_io = io.BytesIO(f.read())

document = client.files.upload(
  file=doc_io,
  config=dict(mime_type='application/pdf')
)

model_name = "gemini-3.1-pro-preview"
system_instruction = "You are an expert analyzing resume."

# Create a cached content object
cache = client.caches.create(
    model=model_name,
    config=types.CreateCachedContentConfig(
      system_instruction=system_instruction,
      contents=[document],
    )
)

print(f'{cache=}')

response = client.models.generate_content(
  model=model_name,
  contents="Please summarize the key technical expertise of the candidate",
  config=types.GenerateContentConfig(
    cached_content=cache.name
  ))

print(f'{response.usage_metadata=}')

print('\n\n', response.text)