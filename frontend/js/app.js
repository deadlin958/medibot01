/**
 * app.js — Main orchestrator: initialises session, wires all events,
 *           handles send flow for text + image, manages sidebar toggle.
 */

let _sessionId  = null;
let _isBusy     = false;   // prevent double-sends while waiting for API

// ── DOM helpers ────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const el = {
  input:       () => $('msg-input'),
  sendBtn:     () => $('send-btn'),
  sidebarBtn:  () => $('sidebar-toggle'),
  sidebar:     () => $('sidebar'),
  newChatBtn:  () => $('new-chat-btn'),
  sessionBadge:() => $('session-badge'),
};

// ── UI state helpers ───────────────────────────────────────────────
function setBusy(busy) {
  _isBusy = busy;
  const btn = el.sendBtn();
  if (btn) btn.disabled = busy;
  const input = el.input();
  if (input) input.disabled = busy;
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 140) + 'px';
}

function updateSessionBadge(id) {
  const badge = el.sessionBadge();
  if (badge) badge.textContent = Session.shortId(id);
}

// ── Send text message ──────────────────────────────────────────────
async function handleSend() {
  if (_isBusy) return;

  const inputEl   = el.input();
  const message   = (inputEl?.value || '').trim();
  const imageFile = Upload.getPendingFile();

  if (!message && !imageFile) return;

  setBusy(true);
  inputEl.value = '';
  inputEl.style.height = 'auto';

  try {
    if (imageFile) {
      // ── Image + optional question ────────────────────────────────
      Chat.addImageMessage(imageFile, message, 'user');
      Upload.clearPendingFile();
      Chat.showTyping();

      const response = await API.uploadImage(_sessionId, imageFile, message);
      Chat.hideTyping();

      if (response.is_emergency) {
        Chat.addMessage(response.content, 'bot', response);
      } else {
        Chat.addImageAnalysisResponse(response);
      }

    } else {
      // ── Text only ────────────────────────────────────────────────
      Chat.addMessage(message, 'user');
      Chat.showTyping();

      const response = await API.sendMessage(_sessionId, message);
      Chat.hideTyping();

      Chat.addMessage(response.content, 'bot', response);
      Chat.updateTriageProgress(response.triage_step || 0, response.triage_total || 6);
    }

  } catch (err) {
    Chat.hideTyping();
    Chat.toast(err.message || 'Could not reach the server. Is the backend running?', 'error');
    console.error('Send error:', err);
  } finally {
    setBusy(false);
    inputEl?.focus();
  }
}

// ── New chat / reset ───────────────────────────────────────────────
async function handleNewChat() {
  if (_isBusy) return;
  try {
    await API.resetSession(_sessionId);
  } catch (_) { /* ignore if backend unreachable */ }

  Session.clear();
  Chat.clearHistory();
  Upload.clear();
  $('messages').innerHTML = '';
  $('triage-progress')?.classList.remove('completed');

  // Reinitialise
  await init();
}

// ── Sidebar toggle ─────────────────────────────────────────────────
function toggleSidebar() {
  const sb = el.sidebar();
  if (sb) sb.classList.toggle('collapsed');
}

// ── Keyboard handling ─────────────────────────────────────────────
function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

// ── Initialise app ─────────────────────────────────────────────────
async function init() {
  setBusy(true);

  try {
    _sessionId = await Session.getOrCreate();
    updateSessionBadge(_sessionId);

    Chat.updateTriageProgress(0, 6);

    const greeting = await API.greet(_sessionId);
    Chat.addMessage(greeting.content, 'bot', greeting);
    Chat.updateTriageProgress(greeting.triage_step || 0, greeting.triage_total || 6);

  } catch (err) {
    Chat.toast(
      'Could not connect to the backend. Make sure "python backend/app.py" is running.',
      'error',
      8000
    );
    console.error('Init error:', err);
  } finally {
    setBusy(false);
    el.input()?.focus();
  }
}

// ── Wire events after DOM ready ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Input textarea
  const inputEl = el.input();
  if (inputEl) {
    inputEl.addEventListener('keydown', handleKeyDown);
    inputEl.addEventListener('input',   () => autoResize(inputEl));
  }

  // Send button
  el.sendBtn()?.addEventListener('click', handleSend);

  // Sidebar toggle
  el.sidebarBtn()?.addEventListener('click', toggleSidebar);

  // New chat
  el.newChatBtn()?.addEventListener('click', handleNewChat);

  // Upload module init (drag-drop + file input)
  Upload.init();

  // Start the app
  init();
});

window.App = { init, handleSend, handleNewChat, toggleSidebar };
