// Background service worker: keep the daemon reachable and expose a right-click
// "Capture selection to Seymour Wins" action.
const DAEMON = "http://127.0.0.1:8770";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "capture-selection",
    title: "Capture selection → Seymour Wins",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "capture-selection" || !info.selectionText) return;
  const t = new Date();
  try {
    await fetch(DAEMON + "/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        year: t.getFullYear(), month: t.getMonth() + 1, day: t.getDate(),
        theme: "meme", fact: info.selectionText.trim(),
      }),
    });
  } catch (e) { /* daemon offline; ignore */ }
});
