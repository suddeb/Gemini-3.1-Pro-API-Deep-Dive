# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

This project uses a local virtual environment (`venv/`) with Python 3.14.

```bash
# Activate the virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -U google-genai python-dotenv
```

The `GEMINI_API_KEY` must be set in a `.env` file (already gitignored):
```
GEMINI_API_KEY=your_key_here
```

## Running Scripts

Each Python file is a standalone demo script — run them directly:

```bash
python connection_check.py     # Verify API connectivity
python thinking_level.py       # Demo thinking/reasoning config
python cached_content.py       # Demo File API upload + content caching
python custom_tool.py          # Demo agentic tool-calling loop
```

## Architecture

This is a collection of standalone Gemini 3.1 Pro API exploration scripts. All scripts share the same bootstrap pattern:

```python
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
```

**Scripts and what they demonstrate:**

- `connection_check.py` — Basic `generate_content` call; sanity-check for API access.
- `thinking_level.py` — `ThinkingConfig` with `ThinkingLevel.LOW/MEDIUM/HIGH`; trades latency vs. reasoning depth.
- `cached_content.py` — Two-step workflow: upload a file via `client.files.upload()`, then create a cache with `client.caches.create()` and pass `cached_content=cache.name` in subsequent requests to avoid re-processing large context.
- `custom_tool.py` — Full agentic loop: declare tools as `FunctionDeclaration` objects, pass them in `GenerateContentConfig`, then loop — checking `function_call` parts in each response, dispatching to local Python functions via `TOOL_REGISTRY`, and feeding `FunctionResponse` parts back — until Gemini returns a plain text response.

**Model endpoints:**
- `gemini-3.1-pro-preview` — standard model used in most scripts
- `gemini-3.1-pro-preview-customtools` — dedicated endpoint required for custom tool use (`custom_tool.py`)
