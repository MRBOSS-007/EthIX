/**
 * content.js — Content Script
 *
 * Injected into the host page by background.js on every icon click.
 * Handles:
 *   - One-time sidebar creation (iframe + overlay)
 *   - Toggle open/close on subsequent clicks
 *   - Host page layout nudge (body margin)
 *   - Message bridge: sidebar ↔ background ↔ API
 */

(function () {
  const SIDEBAR_ID      = "__ethix_sidebar__";
  const OVERLAY_ID      = "__ethix_overlay__";
  const SIDEBAR_WIDTH   = "400px";
  const OPEN_CLASS      = "__ethix_open__";

  // ── If already mounted, just toggle ────────────────────────────────────────
  const existing = document.getElementById(SIDEBAR_ID);
  if (existing) {
    _toggle(existing);
    return;
  }

  // ── Build host-page style tag (isolated namespace) ─────────────────────────
  const hostStyle = document.createElement("style");
  hostStyle.id = "__ethix_host_style__";
  hostStyle.textContent = `
    #${SIDEBAR_ID} {
      position: fixed !important;
      top: 0 !important;
      right: 0 !important;
      width: ${SIDEBAR_WIDTH} !important;
      height: 100vh !important;
      z-index: 2147483647 !important;
      border: none !important;
      transform: translateX(100%) !important;
      transition: transform 0.32s cubic-bezier(0.4, 0, 0.2, 1) !important;
      box-shadow: -8px 0 40px rgba(0,0,0,0.6), -1px 0 0 rgba(99,202,183,0.3) !important;
      border-radius: 0 !important;
    }
    #${SIDEBAR_ID}.${OPEN_CLASS} {
      transform: translateX(0) !important;
    }
    #${OVERLAY_ID} {
      position: fixed !important;
      inset: 0 !important;
      z-index: 2147483646 !important;
      background: rgba(0,0,0,0) !important;
      pointer-events: none !important;
      transition: background 0.32s ease !important;
    }
    #${OVERLAY_ID}.${OPEN_CLASS} {
      background: rgba(0,0,0,0.25) !important;
      backdrop-filter: blur(2px) !important;
      pointer-events: auto !important;
    }
    body.__ethix_pushed__ {
      margin-right: ${SIDEBAR_WIDTH} !important;
      transition: margin-right 0.32s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
  `;
  document.head.appendChild(hostStyle);

  // ── Create backdrop overlay ────────────────────────────────────────────────
  const overlay = document.createElement("div");
  overlay.id = OVERLAY_ID;
  document.body.appendChild(overlay);

  // ── Create iframe ──────────────────────────────────────────────────────────
  const iframe = document.createElement("iframe");
  iframe.id    = SIDEBAR_ID;
  iframe.src   = chrome.runtime.getURL("sidebar.html");
  iframe.allow = "clipboard-write";
  iframe.setAttribute("aria-label", "Ethix AI Assistant");
  document.body.appendChild(iframe);

  // Open immediately after mount (next frame so transition fires)
  requestAnimationFrame(() => requestAnimationFrame(() => _open(iframe)));

  // ── Overlay click → close ──────────────────────────────────────────────────
  overlay.addEventListener("click", () => _close(iframe));

  // ── Message bridge: iframe → content → API → content → iframe ─────────────
  window.addEventListener("message", async (event) => {
    // Only accept messages from our own iframe
    if (event.source !== iframe.contentWindow) return;

    const { type, payload, requestId } = event.data || {};

    if (type === "ETHIX_CLOSE") {
      _close(iframe);
      return;
    }

    if (type === "ETHIX_CHAT") {
      const { message } = payload;
      try {
        const res = await fetch("http://localhost:8000/chat", {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ message }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();

        iframe.contentWindow.postMessage({
          type:      "ETHIX_RESPONSE",
          requestId,
          payload:   { response: data.response },
        }, "*");

      } catch (err) {
        iframe.contentWindow.postMessage({
          type:      "ETHIX_ERROR",
          requestId,
          payload:   { error: err.message },
        }, "*");
      }
    }
  });

  // ── Helper functions ───────────────────────────────────────────────────────
  function _open(el) {
    el.classList.add(OPEN_CLASS);
    overlay.classList.add(OPEN_CLASS);
    document.body.classList.add("__ethix_pushed__");
  }

  function _close(el) {
    el.classList.remove(OPEN_CLASS);
    overlay.classList.remove(OPEN_CLASS);
    document.body.classList.remove("__ethix_pushed__");
  }

  function _toggle(el) {
    if (el.classList.contains(OPEN_CLASS)) {
      _close(el);
    } else {
      _open(el);
    }
  }
})();
