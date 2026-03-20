from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

app = Flask(__name__)
CORS(app)

# ── Groq client (raw SDK — much faster than LangChain wrapper) ─────────────
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
    timeout=25.0,          # hard timeout — well inside the 30s frontend limit
    max_retries=1,
)
MODEL = "llama-3.3-70b-versatile"

JSON_DATA_PATH = os.path.join(os.path.dirname(__file__), "../chatbot/json/example.json")

# ── JSON reader ────────────────────────────────────────────────────────────
def get_page_context() -> dict | None:
    """Reads the JSON produced by the scraper module. Returns None on any failure."""
    try:
        if os.path.exists(JSON_DATA_PATH):
            with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate minimum expected keys
                if isinstance(data, dict) and "text" in data:
                    return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"[server] JSON read error: {e}")
    return None


# ── Prompt builder ─────────────────────────────────────────────────────────
BASE_SYSTEM_PROMPT = """\
You are Ethix AI — an expert in UX ethics and dark UI pattern detection, \
embedded as a browser-extension assistant.

Tone: clear, concise, non-judgmental. Use Markdown (bold, bullets, code blocks).
Never mention internal JSON keys or raw data structures in your reply.
"""

def build_system_prompt(context: dict | None) -> str:
    if context is None:
        return BASE_SYSTEM_PROMPT + "\n\nNo dark pattern data is available for the current page."

    text              = context.get("text", "")
    label             = context.get("label", "unknown")
    spans             = context.get("highlighted_spans", [])
    span_list         = ", ".join(f'"{s}"' for s in spans) if spans else "none"

    return f"""{BASE_SYSTEM_PROMPT}

## Detected Dark Pattern on Current Page

- **UI text:** "{text}"
- **Pattern category:** {label}
- **Manipulative phrases:** {span_list}

### Your behaviour rules (strictly follow these):

1. **If the user's message is a greeting, "hi", "hello", or asks what dark patterns exist on \
this page** → Proactively analyse the data above and respond with:
   a. A plain-English definition of the pattern category.
   b. Why this specific text qualifies as that pattern.
   c. Which highlighted phrases do the manipulating and how.
   d. The psychological effect on users.
   e. A short, ethical alternative wording.

2. **If the user asks a follow-up question** (e.g. "why is this harmful?", \
"how can I fix it?", "write a script") → Answer directly using the same context above.

3. **Never ask the user to paste or provide context** — you already have it.
"""

def build_no_data_prompt() -> str:
    return BASE_SYSTEM_PROMPT + "\n\nThe scraper found **no dark patterns** on the current page. " \
           "Let the user know the page looks clean, and offer to answer general questions about dark patterns."


# ── /chat endpoint ─────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    body    = request.get_json(force=True, silent=True) or {}
    message = body.get("message", "").strip()

    if not message:
        return jsonify({"response": "Please send a non-empty message."}), 400

    context = get_page_context()

    # If JSON exists but is empty / malformed, treat as no-data
    system_prompt = build_system_prompt(context) if context else build_no_data_prompt()

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.5,        # lower = more deterministic / faster
            max_tokens=900,
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": message},
            ],
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        print(f"[server] Groq error: {e}")
        return jsonify({"response": f"AI error: {str(e)}"}), 500

    return jsonify({"response": reply})


# ── /context endpoint (optional — lets sidebar show detected data) ─────────
@app.route("/context", methods=["GET"])
def context():
    data = get_page_context()
    if data:
        return jsonify({"found": True, "data": data})
    return jsonify({"found": False})


if __name__ == "__main__":
    # threaded=True is CRITICAL — prevents one request blocking the next
    app.run(port=8000, threaded=True, debug=False)