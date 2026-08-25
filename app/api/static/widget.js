/**
 * widget.js
 *
 * Embeddable support chat widget for Verve Athletics. Drop this script
 * tag onto any page and it injects a floating chat launcher + panel,
 * talks to chat_api.py, and persists a session ID in localStorage so a
 * returning visitor's conversation state carries over within the
 * browser session.
 *
 * No build step, no dependencies - vanilla JS/CSS, works by just
 * including this file with a <script> tag.
 */

(function () {
  const API_BASE = window.VERVE_CHAT_API || "http://localhost:5001";
  const SESSION_KEY = "verve_chat_session_id";

  function getSessionId() {
    let id = localStorage.getItem(SESSION_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(SESSION_KEY, id);
    }
    return id;
  }

  const styles = `
    :root {
      --verve-ink: #10151F;
      --verve-navy: #1B2438;
      --verve-navy-light: #26314A;
      --verve-amber: #F5A623;
      --verve-amber-dark: #D98C0F;
      --verve-cream: #F6F4EF;
      --verve-line: #313D57;
    }

    #verve-launcher {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 18px;
      background: var(--verve-navy);
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 24px rgba(16, 21, 31, 0.35);
      z-index: 999998;
      transition: transform 0.15s ease;
    }
    #verve-launcher:hover { transform: translateY(-2px); }

    #verve-launcher::before {
      content: "";
      position: absolute;
      inset: -4px;
      border-radius: 22px;
      border: 2px solid var(--verve-amber);
      opacity: 0;
      animation: verve-pulse 2.4s ease-out infinite;
    }
    @keyframes verve-pulse {
      0% { opacity: 0.55; transform: scale(0.92); }
      70% { opacity: 0; transform: scale(1.12); }
      100% { opacity: 0; transform: scale(1.12); }
    }

    #verve-launcher svg { width: 26px; height: 26px; }

    #verve-panel {
      position: fixed;
      bottom: 98px;
      right: 24px;
      width: 360px;
      max-width: calc(100vw - 32px);
      height: 520px;
      max-height: calc(100vh - 140px);
      background: var(--verve-cream);
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(16, 21, 31, 0.28);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    #verve-panel.open { display: flex; }

    #verve-header {
      background: var(--verve-navy);
      color: var(--verve-cream);
      padding: 18px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    #verve-header-title {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }
    #verve-header-sub {
      font-size: 12px;
      color: #A9B3C9;
      margin-top: 2px;
      font-weight: 400;
      text-transform: none;
      letter-spacing: normal;
    }
    #verve-close {
      background: none;
      border: none;
      color: var(--verve-cream);
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
      opacity: 0.7;
      padding: 4px;
    }
    #verve-close:hover { opacity: 1; }

    #verve-messages {
      flex: 1;
      overflow-y: auto;
      padding: 18px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .verve-msg {
      max-width: 82%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 13.5px;
      line-height: 1.45;
      white-space: pre-wrap;
    }
    .verve-msg.user {
      align-self: flex-end;
      background: var(--verve-navy);
      color: var(--verve-cream);
      border-bottom-right-radius: 4px;
    }
    .verve-msg.bot {
      align-self: flex-start;
      background: #fff;
      color: var(--verve-ink);
      border: 1px solid #E6E1D6;
      border-bottom-left-radius: 4px;
    }
    .verve-msg.escalated {
      border-left: 3px solid var(--verve-amber);
    }
    .verve-msg.typing {
      align-self: flex-start;
      background: #fff;
      border: 1px solid #E6E1D6;
      display: flex;
      gap: 4px;
      padding: 12px 14px;
    }
    .verve-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #B7BFCF;
      animation: verve-bounce 1.2s infinite ease-in-out;
    }
    .verve-dot:nth-child(2) { animation-delay: 0.15s; }
    .verve-dot:nth-child(3) { animation-delay: 0.3s; }
    @keyframes verve-bounce {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
      30% { transform: translateY(-4px); opacity: 1; }
    }

    #verve-input-row {
      display: flex;
      gap: 8px;
      padding: 14px;
      border-top: 1px solid #E6E1D6;
      background: #fff;
    }
    #verve-input {
      flex: 1;
      border: 1px solid #DAD4C6;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 13.5px;
      font-family: inherit;
      resize: none;
      outline: none;
    }
    #verve-input:focus { border-color: var(--verve-amber); }
    #verve-send {
      background: var(--verve-amber);
      border: none;
      border-radius: 10px;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
    }
    #verve-send:hover { background: var(--verve-amber-dark); }
    #verve-send:disabled { opacity: 0.5; cursor: default; }
    #verve-send svg { width: 16px; height: 16px; }
  `;

  function injectStyles() {
    const styleTag = document.createElement("style");
    styleTag.textContent = styles;
    document.head.appendChild(styleTag);
  }

  function buildDOM() {
    const launcher = document.createElement("button");
    launcher.id = "verve-launcher";
    launcher.setAttribute("aria-label", "Open support chat");
    launcher.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 5h16v10H8l-4 4V5z" stroke="#F5A623" stroke-width="1.8" stroke-linejoin="round"/>
        <circle cx="9" cy="10" r="1" fill="#F5A623"/>
        <circle cx="12" cy="10" r="1" fill="#F5A623"/>
        <circle cx="15" cy="10" r="1" fill="#F5A623"/>
      </svg>
    `;

    const panel = document.createElement("div");
    panel.id = "verve-panel";
    panel.innerHTML = `
      <div id="verve-header">
        <div>
          <div id="verve-header-title">Verve Support</div>
          <div id="verve-header-sub">Usually replies in seconds</div>
        </div>
        <button id="verve-close" aria-label="Close chat">&times;</button>
      </div>
      <div id="verve-messages"></div>
      <div id="verve-input-row">
        <textarea id="verve-input" rows="1" placeholder="Ask about an order or a policy..."></textarea>
        <button id="verve-send" aria-label="Send">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 11l18-7-7 18-2.5-7L3 11z" fill="#10151F"/>
          </svg>
        </button>
      </div>
    `;

    document.body.appendChild(launcher);
    document.body.appendChild(panel);
    return { launcher, panel };
  }

  function addMessage(container, text, role, escalated) {
    const el = document.createElement("div");
    el.className = `verve-msg ${role}` + (escalated ? " escalated" : "");
    el.textContent = text;
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
    return el;
  }

  function addTyping(container) {
    const el = document.createElement("div");
    el.className = "verve-msg typing";
    el.innerHTML = `<span class="verve-dot"></span><span class="verve-dot"></span><span class="verve-dot"></span>`;
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
    return el;
  }

  async function sendMessage(text, messagesEl) {
    addMessage(messagesEl, text, "user");
    const typingEl = addTyping(messagesEl);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: getSessionId() })
      });
      const data = await res.json();
      typingEl.remove();
      addMessage(messagesEl, data.answer, "bot", data.escalated);
    } catch (err) {
      typingEl.remove();
      addMessage(messagesEl, "Sorry, I couldn't reach support right now - please try again in a moment.", "bot", true);
    }
  }

  function init() {
    injectStyles();
    const { launcher, panel } = buildDOM();
    const messagesEl = panel.querySelector("#verve-messages");
    const inputEl = panel.querySelector("#verve-input");
    const sendBtn = panel.querySelector("#verve-send");
    const closeBtn = panel.querySelector("#verve-close");

    let greeted = false;

    launcher.addEventListener("click", () => {
      panel.classList.toggle("open");
      if (panel.classList.contains("open") && !greeted) {
        addMessage(messagesEl, "Hi! I'm the Verve Athletics support assistant. Ask me about an order, shipping, returns, or anything else.", "bot");
        greeted = true;
      }
    });
    closeBtn.addEventListener("click", () => panel.classList.remove("open"));

    function handleSend() {
      const text = inputEl.value.trim();
      if (!text) return;
      inputEl.value = "";
      sendMessage(text, messagesEl);
    }

    sendBtn.addEventListener("click", handleSend);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
