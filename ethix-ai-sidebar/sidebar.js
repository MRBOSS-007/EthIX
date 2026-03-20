/**
 * sidebar.js — Ethix AI Sidebar Logic
 *
 * Responsibilities:
 *  - Render welcome screen & conversation history
 *  - Auto-resize textarea
 *  - Send messages to content.js via postMessage (content.js proxies to API)
 *  - Render bot replies with typing animation + lightweight Markdown parsing
 *  - Code block rendering with copy-to-clipboard
 *  - Status bar management
 */

(function () {
  "use strict";

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const chatEl = document.getElementById("ethix-chat");
  const inputEl = document.getElementById("ethix-input");
  const sendBtn = document.getElementById("ethix-send-btn");
  const closeBtn = document.getElementById("ethix-close-btn");
  const clearBtn = document.getElementById("ethix-clear-btn");
  const typingEl = document.getElementById("ethix-typing");
  const statusDot = document.getElementById("ethix-status-dot");
  const statusTxt = document.getElementById("ethix-status-text");

  // ── State ──────────────────────────────────────────────────────────────────
  let isWaiting = false;
  let reqCounter = 0;
  const pendingReq = new Map();   // requestId → { resolve, reject }

  // ── Init ───────────────────────────────────────────────────────────────────
  renderWelcome();
  inputEl.focus();
  autoAnalyzeOnOpen();   // ← NEW: fires proactive analysis on open

  // ── Event listeners ────────────────────────────────────────────────────────
  sendBtn.addEventListener("click", handleSend);
  closeBtn.addEventListener("click", () => {
    window.parent.postMessage({ type: "ETHIX_CLOSE" }, "*");
  });
  clearBtn.addEventListener("click", clearConversation);

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  inputEl.addEventListener("input", autoResize);

  // Listen for API responses from content.js
  window.addEventListener("message", handleIncomingMessage);

  // ── Message handler (content.js → sidebar) ─────────────────────────────────
  function handleIncomingMessage(event) {
    const { type, requestId, payload } = event.data || {};
    const pending = pendingReq.get(requestId);
    if (!pending) return;

    if (type === "ETHIX_RESPONSE") {
      pending.resolve(payload.response);
    } else if (type === "ETHIX_ERROR") {
      pending.reject(new Error(payload.error));
    }
    pendingReq.delete(requestId);
  }

  // ── Core send flow ─────────────────────────────────────────────────────────
  async function handleSend() {
    const text = inputEl.value.trim();
    if (!text || isWaiting) return;

    // Remove welcome if present
    const welcome = chatEl.querySelector(".ethix-welcome");
    if (welcome) welcome.remove();

    // Render user bubble
    appendMessage("user", text);
    inputEl.value = "";
    autoResize();

    setWaiting(true);

    try {
      const response = await sendToAPI(text);
      setWaiting(false);
      await appendBotMessage(response);
    } catch (err) {
      setWaiting(false);
      appendMessage("bot", `⚠ Error: ${err.message}`, true);
    }
  }

  // ── API proxy via postMessage to content.js ────────────────────────────────
  function sendToAPI(message) {
    return new Promise((resolve, reject) => {
      const requestId = ++reqCounter;
      pendingReq.set(requestId, { resolve, reject });

      // Timeout after 30s
      const timer = setTimeout(() => {
        if (pendingReq.has(requestId)) {
          pendingReq.delete(requestId);
          reject(new Error("Request timed out after 30s"));
        }
      }, 30000);

      // Wrap resolve/reject to clear timer
      const origResolve = resolve;
      const origReject = reject;
      pendingReq.set(requestId, {
        resolve: (v) => { clearTimeout(timer); origResolve(v); },
        reject: (e) => { clearTimeout(timer); origReject(e); },
      });

      window.parent.postMessage({
        type: "ETHIX_CHAT",
        requestId,
        payload: { message },
      }, "*");
    });
  }

  // ── NEW: Auto-analyze on open ──────────────────────────────────────────────
  async function autoAnalyzeOnOpen() {
    try {
      const res = await fetch("http://localhost:8000/context");
      if (!res.ok) return;
      const data = await res.json();

      if (data.found) {
        // Remove welcome screen
        const welcome = chatEl.querySelector(".ethix-welcome");
        if (welcome) welcome.remove();

        // Show a synthetic user trigger
        appendMessage("user", "Analyse the dark patterns detected on this page.");
        setWaiting(true);

        try {
          const reply = await sendToAPI("Analyse the dark patterns detected on this page.");
          setWaiting(false);
          await appendBotMessage(reply);
        } catch (err) {
          setWaiting(false);
          appendMessage("bot", `⚠ Error: ${err.message}`, true);
        }
      }
    } catch (_) {
      // Silent fail — server not ready or no data, user can still type manually
    }
  }

  // ── Message rendering ──────────────────────────────────────────────────────
  function appendMessage(role, text, isError = false) {
    const msg = document.createElement("div");
    msg.className = `ethix-msg ethix-${role}`;

    const time = getTimestamp();

    if (role === "user") {
      const bubble = document.createElement("div");
      bubble.className = "ethix-bubble";
      bubble.textContent = text;
      msg.appendChild(bubble);

      const meta = document.createElement("div");
      meta.className = "ethix-msg-meta";
      meta.textContent = `You · ${time}`;
      msg.appendChild(meta);

    } else {
      // Bot layout: avatar + bubble
      const row = document.createElement("div");
      row.className = "ethix-msg-row";

      const avatar = document.createElement("div");
      avatar.className = "ethix-bot-avatar";
      avatar.textContent = "AI";

      const bubble = document.createElement("div");
      bubble.className = isError ? "ethix-bubble ethix-error-bubble" : "ethix-bubble";
      bubble.innerHTML = isError ? escapeHtml(text) : parseMarkdown(text);

      row.appendChild(avatar);
      row.appendChild(bubble);
      msg.appendChild(row);

      const meta = document.createElement("div");
      meta.className = "ethix-msg-meta";
      meta.textContent = `Ethix AI · ${time}`;
      msg.appendChild(meta);
    }

    chatEl.appendChild(msg);
    scrollToBottom();
    return msg;
  }

  // ── Bot message with typewriter animation ──────────────────────────────────
  async function appendBotMessage(fullText) {
    const msg = document.createElement("div");
    msg.className = "ethix-msg ethix-bot";

    const row = document.createElement("div");
    row.className = "ethix-msg-row";

    const avatar = document.createElement("div");
    avatar.className = "ethix-bot-avatar";
    avatar.textContent = "AI";

    const bubble = document.createElement("div");
    bubble.className = "ethix-bubble ethix-cursor";
    bubble.innerHTML = "";

    row.appendChild(avatar);
    row.appendChild(bubble);
    msg.appendChild(row);

    const meta = document.createElement("div");
    meta.className = "ethix-msg-meta";
    meta.textContent = `Ethix AI · ${getTimestamp()}`;
    msg.appendChild(meta);

    chatEl.appendChild(msg);
    scrollToBottom();

    // Split text at code block boundaries to type prose, inject code instantly
    const segments = splitAtCodeBlocks(fullText);

    for (const seg of segments) {
      if (seg.type === "code") {
        // Render code block immediately
        const block = buildCodeBlock(seg.lang, seg.code);
        bubble.appendChild(block);
        scrollToBottom();
      } else {
        // Type prose character by character
        await typeProse(seg.text, bubble);
      }
    }

    // Remove cursor
    bubble.classList.remove("ethix-cursor");
    // Final render pass (handles any markdown outside code)
    const finalHTML = parseMarkdown(fullText);
    bubble.innerHTML = finalHTML;

    // Re-attach code block copy buttons (innerHTML replaced them)
    attachCopyButtons(bubble);
    scrollToBottom();
  }

  async function typeProse(text, container) {
    const CHUNK = 3;       // chars per frame
    const DELAY = 12;      // ms between chunks — adjust for speed

    let i = 0;
    const span = document.createElement("span");
    container.appendChild(span);

    while (i < text.length) {
      span.textContent += text.slice(i, i + CHUNK);
      i += CHUNK;
      scrollToBottom();
      await sleep(DELAY);
    }
  }

  // ── Waiting / typing indicator ─────────────────────────────────────────────
  function setWaiting(state) {
    isWaiting = state;
    sendBtn.disabled = state;
    inputEl.disabled = state;
    typingEl.classList.toggle("ethix-visible", state);

    if (state) {
      statusDot.className = "ethix-status-dot ethix-loading";
      statusTxt.textContent = "Thinking…";
    } else {
      statusDot.className = "ethix-status-dot";
      statusTxt.textContent = "Connected · localhost:8000";
    }
    scrollToBottom();
  }

  // ── Welcome screen ─────────────────────────────────────────────────────────
  function renderWelcome() {
    const el = document.createElement("div");
    el.className = "ethix-welcome";
    el.innerHTML = `
      <div class="ethix-welcome-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#63CAB7" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="#63CAB7" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="#63CAB7" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
      </div>
      <h2>Ethix AI Assistant</h2>
      <p>Ask me anything about this page, write code, debug issues, or explore ideas.</p>
      <div class="ethix-welcome-chips">
        <span class="ethix-chip">Explain this page</span>
        <span class="ethix-chip">Write a script</span>
        <span class="ethix-chip">Debug my code</span>
        <span class="ethix-chip">Summarise content</span>
      </div>
    `;

    // Chips as quick-prompts
    el.querySelectorAll(".ethix-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        inputEl.value = chip.textContent;
        inputEl.focus();
        autoResize();
      });
    });

    chatEl.appendChild(el);
  }

  function clearConversation() {
    chatEl.innerHTML = "";
    renderWelcome();
  }

  // ── Markdown parser (lightweight, no deps) ─────────────────────────────────
  function parseMarkdown(raw) {
    let html = raw;

    // Fenced code blocks — capture lang + body
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      const safeCode = escapeHtml(code.trimEnd());
      const langLabel = lang || "text";
      return `
        <div class="ethix-code-block" data-lang="${escapeHtml(langLabel)}">
          <div class="ethix-code-header">
            <span class="ethix-code-lang">${escapeHtml(langLabel)}</span>
            <button class="ethix-copy-btn" data-code="${encodeURIComponent(code.trimEnd())}">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Copy
            </button>
          </div>
          <pre><code>${safeCode}</code></pre>
        </div>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // Italic
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

    // Headers
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Unordered lists
    html = html.replace(/^\s*[-*] (.+)/gm, "<li>$1</li>");
    html = html.replace(/(<li>[\s\S]+?<\/li>)/g, "<ul>$1</ul>");

    // Numbered lists
    html = html.replace(/^\s*\d+\. (.+)/gm, "<li>$1</li>");

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Paragraphs (wrap plain lines)
    html = html.replace(/\n{2,}/g, "</p><p>");
    html = `<p>${html}</p>`;

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, "");
    html = html.replace(/<p>(<(?:div|ul|ol|h[123]|pre))/g, "$1");
    html = html.replace(/(<\/(?:div|ul|ol|h[123]|pre)>)<\/p>/g, "$1");

    return html;
  }

  // ── Code block builder (used in typing animation path) ────────────────────
  function buildCodeBlock(lang, code) {
    const wrap = document.createElement("div");
    wrap.className = "ethix-code-block";

    const header = document.createElement("div");
    header.className = "ethix-code-header";
    header.innerHTML = `
      <span class="ethix-code-lang">${escapeHtml(lang || "text")}</span>
      <button class="ethix-copy-btn">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
        Copy
      </button>`;

    const pre = document.createElement("pre");
    const codeEl = document.createElement("code");
    codeEl.textContent = code;
    pre.appendChild(codeEl);

    wrap.appendChild(header);
    wrap.appendChild(pre);

    header.querySelector(".ethix-copy-btn").addEventListener("click", () =>
      copyCode(code, header.querySelector(".ethix-copy-btn")));

    return wrap;
  }

  // ── Copy-to-clipboard ──────────────────────────────────────────────────────
  function attachCopyButtons(container) {
    container.querySelectorAll(".ethix-copy-btn[data-code]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const code = decodeURIComponent(btn.dataset.code);
        copyCode(code, btn);
      });
    });
  }

  function copyCode(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      const orig = btn.innerHTML;
      btn.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg> Copied!`;
      btn.classList.add("ethix-copied");
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.classList.remove("ethix-copied");
      }, 2000);
    }).catch(() => {
      btn.textContent = "Failed";
      setTimeout(() => { btn.textContent = "Copy"; }, 2000);
    });
  }

  // ── Segment splitter for typewriter (prose vs code blocks) ───────────────
  function splitAtCodeBlocks(text) {
    const segments = [];
    const regex = /```(\w*)\n?([\s\S]*?)```/g;
    let last = 0;
    let m;
    while ((m = regex.exec(text)) !== null) {
      if (m.index > last) {
        segments.push({ type: "prose", text: text.slice(last, m.index) });
      }
      segments.push({ type: "code", lang: m[1] || "text", code: m[2].trimEnd() });
      last = regex.lastIndex;
    }
    if (last < text.length) {
      segments.push({ type: "prose", text: text.slice(last) });
    }
    return segments;
  }

  // ── Utilities ──────────────────────────────────────────────────────────────
  function autoResize() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
  }

  function scrollToBottom() {
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  function getTimestamp() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

})();