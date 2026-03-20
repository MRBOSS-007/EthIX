/**
 * background.js — Service Worker (Manifest V3)
 *
 * Listens for toolbar icon clicks and injects / toggles the sidebar
 * into the active tab via chrome.scripting.executeScript.
 */

chrome.action.onClicked.addListener(async (tab) => {
  // Guard: cannot inject into chrome:// or edge:// pages
  if (!tab.id || !tab.url || tab.url.startsWith("chrome://") || tab.url.startsWith("edge://")) {
    console.warn("[Ethix] Cannot inject sidebar into this page:", tab.url);
    return;
  }

  try {
    // Inject content.js into the active tab.
    // If it's already injected, content.js will toggle the sidebar.
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
  } catch (err) {
    console.error("[Ethix] Failed to inject content script:", err);
  }
});
