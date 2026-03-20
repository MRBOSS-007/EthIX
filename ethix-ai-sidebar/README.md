# Ethix AI Sidebar — Chrome Extension

A VS Code Copilot / Cursor-style AI assistant sidebar that injects into any webpage.

---

## Folder Structure

```
ethix-ai-sidebar/
├── manifest.json       ← Extension manifest (MV3)
├── background.js       ← Service worker — handles icon click, injects content.js
├── content.js          ← Injected into host page — mounts iframe, bridges API calls
├── sidebar.html        ← The sidebar UI (runs inside iframe)
├── sidebar.css         ← All sidebar styles (namespaced, no host-page conflicts)
├── sidebar.js          ← Chat logic, Markdown rendering, typewriter animation
├── icons/
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

---

## Installation

1. Open Chrome and navigate to `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select this `ethix-ai-sidebar/` folder
5. The Ethix icon will appear in your toolbar

---

## Usage

1. Start your backend server on `http://localhost:8000`

   Expected endpoint:
   ```
   POST /chat
   Body:     { "message": "<user_message>" }
   Response: { "response": "<bot_reply>" }
   ```

2. Navigate to any webpage
3. Click the **Ethix** toolbar icon to open the sidebar
4. Click again (or press ✕) to close it

---

## Architecture

```
[Toolbar click]
      ↓
background.js  (service worker)
      ↓  chrome.scripting.executeScript
content.js     (injected into host page)
      ↓  creates <iframe src="sidebar.html">
sidebar.html / sidebar.css / sidebar.js   (runs in isolated iframe context)
      ↓  window.postMessage({ type: "ETHIX_CHAT", ... })
content.js     (receives message, makes fetch() to localhost:8000)
      ↓  window.postMessage({ type: "ETHIX_RESPONSE", ... })
sidebar.js     (renders reply with typewriter animation)
```

### Why iframe?

The sidebar runs inside a sandboxed `<iframe>` so its CSS and JS are **completely
isolated** from the host page. No style leakage. No JS conflicts. The host page's
layout is gently nudged (`margin-right: 400px`) so the sidebar doesn't overlap content.

---

## Customisation

| What                    | Where                     |
|-------------------------|---------------------------|
| Sidebar width           | `content.js` → `SIDEBAR_WIDTH` |
| API endpoint            | `content.js` → `fetch(...)` URL |
| Typewriter speed        | `sidebar.js` → `CHUNK` / `DELAY` |
| Color theme             | `sidebar.css` → `:root` variables |
| Quick-prompt chips      | `sidebar.js` → `renderWelcome()` |

---

## Backend (minimal Flask example)

```python
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "")
    # Replace with your LLM call
    reply = f"You said: {message}"
    return jsonify({"response": reply})

if __name__ == "__main__":
    app.run(port=8000)
```

---

## Features

- ✅ Manifest V3 compliant
- ✅ Toggle open/close (single instance only)
- ✅ Smooth slide-in animation from right
- ✅ Host page nudged, not covered
- ✅ Backdrop blur overlay
- ✅ Fenced code blocks with copy-to-clipboard
- ✅ Typewriter animation for bot replies
- ✅ Inline Markdown rendering (bold, italic, headers, lists, links, code)
- ✅ Auto-resize textarea
- ✅ Enter to send / Shift+Enter for newline
- ✅ Loading/typing dots indicator
- ✅ Status bar with connection state
- ✅ Clear conversation button
- ✅ Timeout & error handling
- ✅ Quick-prompt chips on welcome screen
