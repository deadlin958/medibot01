/**
 * chat.js — Message rendering, typing indicator, triage progress,
 *            sources accordion, history sidebar, toast notifications.
 */

const Chat = (() => {
  // ── DOM refs ─────────────────────────────────────────────────────
  const messagesEl      = () => document.getElementById('messages');
  const typingEl        = () => document.getElementById('typing-indicator');
  const triageProgressEl= () => document.getElementById('triage-progress');
  const historyListEl   = () => document.getElementById('history-list');
  const toastContainer  = () => document.getElementById('toast-container');

  // Minimal Markdown renderer using marked.js (loaded via CDN)
  function renderMarkdown(text) {
    if (window.marked) {
      return window.marked.parse(text, { breaks: true, gfm: true });
    }
    // Fallback: simple line-break conversion
    return text.replace(/\n/g, '<br>');
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
              .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function formatTime(date = new Date()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // ── Typing indicator ──────────────────────────────────────────────
  function showTyping() {
    const el = typingEl();
    if (el) { el.classList.remove('hidden'); scrollToBottom(); }
  }

  function hideTyping() {
    const el = typingEl();
    if (el) el.classList.add('hidden');
  }

  // ── Scroll to bottom ──────────────────────────────────────────────
  function scrollToBottom() {
    const el = messagesEl();
    if (el) el.scrollTop = el.scrollHeight;
  }

  // ── Sources accordion ─────────────────────────────────────────────
  function buildSourcesHTML(sources) {
    if (!sources || sources.length === 0) return '';
    const cards = sources.map(s => {
      const dec = (s.final_decision || 'maybe').toLowerCase();
      const snippet = escapeHtml(s.snippet || '').slice(0, 220);
      return `
        <div class="source-card">
          <div class="source-header">
            <span class="source-decision ${dec}">${dec}</span>
            <span class="source-pubid">PubMed #${s.pubid}</span>
          </div>
          <div class="source-question">${escapeHtml(s.question || '')}</div>
          <div class="source-snippet">${snippet}${s.snippet && s.snippet.length > 220 ? '…' : ''}</div>
        </div>`;
    }).join('');

    return `
      <div class="sources-section">
        <button class="sources-toggle" onclick="Chat.toggleSources(this)">
          📚 ${sources.length} PubMedQA source${sources.length > 1 ? 's' : ''} &nbsp;
          <i class="chevron">▾</i>
        </button>
        <div class="sources-list">${cards}</div>
      </div>`;
  }

  function toggleSources(btn) {
    btn.classList.toggle('open');
    const list = btn.nextElementSibling;
    list.classList.toggle('open');
  }

  // ── Separate disclaimer from answer body ──────────────────────────
  function splitDisclaimer(text) {
    const marker = 'Disclaimer:';
    const idx = text.lastIndexOf(marker);
    if (idx === -1) return { body: text, disclaimer: '' };
    return {
      body:       text.slice(0, idx).trim(),
      disclaimer: text.slice(idx).trim(),
    };
  }

  // ── Add a text message ────────────────────────────────────────────
  function addMessage(content, role, meta = {}) {
    const container = messagesEl();
    if (!container) return;

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const isEmergency = meta.is_emergency || false;
    const type        = meta.type || 'answer';
    const sources     = meta.sources || [];
    const isBot       = role === 'bot';

    let innerHTML = '';

    if (isBot) {
      // ── Bot bubble ─────────────────────────────────────────────────
      if (isEmergency) {
        innerHTML = `
          <div class="avatar bot">🏥</div>
          <div class="bubble-wrap">
            <div class="emergency-banner">
              <span class="emergency-icon">🚨</span>
              <div class="emergency-text">
                <strong>Medical Emergency Detected</strong>
                ${renderMarkdown(content)}
              </div>
            </div>
            <span class="msg-time">${formatTime()}</span>
          </div>`;
      } else {
        const bubbleClass = type === 'triage' ? 'bot triage' :
                            type === 'greeting' ? 'bot greeting' : 'bot';
        const { body, disclaimer } = splitDisclaimer(content);
        const bodyHtml      = renderMarkdown(body);
        const disclaimerHtml = disclaimer
          ? `<div class="disclaimer-text">${escapeHtml(disclaimer)}</div>` : '';
        const sourcesHtml   = buildSourcesHTML(sources);

        innerHTML = `
          <div class="avatar bot">🏥</div>
          <div class="bubble-wrap">
            <div class="bubble ${bubbleClass}">
              ${bodyHtml}
              ${disclaimerHtml}
              ${sourcesHtml}
            </div>
            <span class="msg-time">${formatTime()}</span>
          </div>`;
      }
    } else {
      // ── User bubble ────────────────────────────────────────────────
      innerHTML = `
        <div class="bubble-wrap">
          <div class="bubble user">${escapeHtml(content)}</div>
          <span class="msg-time">${formatTime()}</span>
        </div>
        <div class="avatar user">👤</div>`;
    }

    row.innerHTML = innerHTML;
    container.appendChild(row);
    scrollToBottom();
    updateHistorySidebar(content, role);
    return row;
  }

  // ── Add an image message (user side) ──────────────────────────────
  function addImageMessage(file, question, role) {
    const container = messagesEl();
    if (!container) return;

    const url = URL.createObjectURL(file);
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    row.innerHTML = `
      <div class="bubble-wrap">
        <div class="bubble user image-bubble">
          <div class="image-user-bubble">
            <img src="${url}" class="img-preview" alt="Uploaded image">
            ${question ? `<span class="img-question">${escapeHtml(question)}</span>` : ''}
          </div>
        </div>
        <span class="msg-time">${formatTime()}</span>
      </div>
      <div class="avatar user">👤</div>`;
    container.appendChild(row);
    scrollToBottom();
    updateHistorySidebar(`[Image] ${question || 'Image uploaded'}`, role);
  }

  // ── Add bot image-analysis response ───────────────────────────────
  function addImageAnalysisResponse(response) {
    const container = messagesEl();
    if (!container) return;

    const { body, disclaimer } = splitDisclaimer(response.content || '');
    const descHtml = response.image_description
      ? `<div class="image-description-card">
           <strong>🔍 Image Analysis</strong>
           ${escapeHtml(response.image_description)}
         </div>` : '';
    const sourcesHtml    = buildSourcesHTML(response.sources || []);
    const disclaimerHtml = disclaimer
      ? `<div class="disclaimer-text">${escapeHtml(disclaimer)}</div>` : '';

    const row = document.createElement('div');
    row.className = 'message-row bot';
    row.innerHTML = `
      <div class="avatar bot">🏥</div>
      <div class="bubble-wrap">
        <div class="bubble bot">
          <span class="image-analysis-badge">🖼 Image analyzed via GPT-4o Vision</span>
          ${descHtml}
          ${renderMarkdown(body)}
          ${disclaimerHtml}
          ${sourcesHtml}
        </div>
        <span class="msg-time">${formatTime()}</span>
      </div>`;
    container.appendChild(row);
    scrollToBottom();
  }

  // ── Triage progress bar ───────────────────────────────────────────
  function updateTriageProgress(step, total) {
    const el = triageProgressEl();
    if (!el) return;

    if (step >= total) {
      el.classList.add('completed');
      return;
    }

    el.classList.remove('completed');
    const dotsEl    = el.querySelector('.triage-dots');
    const fracEl    = el.querySelector('.triage-fraction');

    if (dotsEl) {
      dotsEl.innerHTML = Array.from({ length: total }, (_, i) => {
        const cls = i < step ? 'done' : i === step ? 'current' : '';
        return `<div class="triage-dot ${cls}"></div>`;
      }).join('');
    }
    if (fracEl) fracEl.textContent = `${step}/${total}`;
  }

  // ── History sidebar ───────────────────────────────────────────────
  function updateHistorySidebar(text, role) {
    const list = historyListEl();
    if (!list) return;

    const emptyEl = list.querySelector('.history-empty');
    if (emptyEl) emptyEl.remove();

    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
      <div class="history-item-role ${role}">${role === 'user' ? 'You' : 'Assistant'}</div>
      <div class="history-item-text">${escapeHtml(text.slice(0, 80))}</div>`;
    list.prepend(item);
  }

  function clearHistory() {
    const list = historyListEl();
    if (!list) return;
    list.innerHTML = `
      <div class="history-empty">
        <div class="history-empty-icon">💬</div>
        No conversation yet
      </div>`;
  }

  // ── Toast notifications ───────────────────────────────────────────
  function toast(message, type = 'error', duration = 4000) {
    const container = toastContainer();
    if (!container) return;

    const icons = { error: '❌', success: '✅', warning: '⚠️', info: 'ℹ️' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(message)}</span>`;
    container.appendChild(el);

    setTimeout(() => {
      el.classList.add('removing');
      el.addEventListener('animationend', () => el.remove());
    }, duration);
  }

  return {
    addMessage, addImageMessage, addImageAnalysisResponse,
    showTyping, hideTyping, updateTriageProgress,
    clearHistory, updateHistorySidebar, toast, toggleSources,
    scrollToBottom,
  };
})();

window.Chat = Chat;
