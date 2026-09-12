// Dev default — no real deploy IP/domain exists yet (deploy/README.md: both
// boxes are bare IP, no TLS). Update once one does; not fabricated here.
const API_BASE_URL = "http://localhost:8000";

interface SearchMessage {
  type: "search";
  title: string;
}

// Runs in the background service worker rather than the content script: a
// content script's fetch is subject to the host page's CSP, which can block
// it on an arbitrary third-party site. A service worker isn't — the standard
// MV3 pattern for a content script calling an external API.
chrome.runtime.onMessage.addListener((message: unknown, _sender, sendResponse) => {
  const request = message as Partial<SearchMessage>;
  if (request?.type !== "search" || typeof request.title !== "string") {
    return false;
  }

  fetch(`${API_BASE_URL}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: request.title }),
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`API ${res.status}`);
      sendResponse({ ok: true, data: await res.json() });
    })
    .catch((err: unknown) => {
      sendResponse({ ok: false, error: String(err) });
    });

  // Keeps the message channel open for the async sendResponse above.
  return true;
});
