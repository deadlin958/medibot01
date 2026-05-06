/**
 * api.js — All fetch calls to the FastAPI backend.
 * Every function returns the parsed JSON response or throws on error.
 */

const API = (() => {
  const BASE = '';  // Same origin (FastAPI serves both API + frontend)

  async function _request(url, options = {}) {
    const res = await fetch(BASE + url, options);
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        errMsg = body.detail || body.message || errMsg;
      } catch (_) { /* ignore */ }
      throw new Error(errMsg);
    }
    return res.json();
  }

  /** POST /api/greet — start a session and get the greeting */
  function greet(sessionId) {
    return _request('/api/greet', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId }),
    });
  }

  /** POST /api/chat — send a text message */
  function sendMessage(sessionId, message) {
    return _request('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId, message }),
    });
  }

  /** POST /api/image-query — upload image + optional question */
  function uploadImage(sessionId, file, question = '') {
    const form = new FormData();
    form.append('image',      file);
    form.append('question',   question);
    form.append('session_id', sessionId);
    return _request('/api/image-query', { method: 'POST', body: form });
  }

  /** POST /api/reset — reset session triage + memory */
  function resetSession(sessionId) {
    return _request('/api/reset', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId }),
    });
  }

  /** GET /api/history — fetch conversation history */
  function getHistory(sessionId) {
    return _request(`/api/history?session_id=${encodeURIComponent(sessionId)}`);
  }

  /** GET /health */
  function health() {
    return _request('/health');
  }

  return { greet, sendMessage, uploadImage, resetSession, getHistory, health };
})();

window.API = API;
