import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

HARD_PROBLEM = """
A startup has 3 engineers. Each can build a feature in 6 days working alone.
They need to build 5 features. Features 3 and 4 cannot start until feature 2
is complete. Feature 5 requires features 1 and 4 to be done.
What is the minimum number of days to ship all 5 features?
Assume engineers can split tasks across days and work in parallel.
"""

MODEL_ID = "gemini-3.1-pro-preview"

response = client.models.generate_content(
    model=MODEL_ID,
    contents=HARD_PROBLEM,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.LOW  # For faster and lower-latency responses
        )
    ),
)

print(response.text)