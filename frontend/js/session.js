/**
 * session.js — localStorage-based anonymous session management.
 * Stores only the session UUID — no PII ever saved.
 */

const Session = (() => {
  const KEY = 'clinicalbot_session_id';

  function get() {
    return localStorage.getItem(KEY);
  }

  function set(id) {
    localStorage.setItem(KEY, id);
  }

  function clear() {
    localStorage.removeItem(KEY);
  }

  /**
   * Returns existing session_id or fetches a new one from the server.
   * @returns {Promise<string>}
   */
  async function getOrCreate() {
    let id = get();
    if (id) return id;
    try {
      const res  = await fetch('/api/session/new');
      const data = await res.json();
      id = data.session_id;
      set(id);
      return id;
    } catch (err) {
      // Fallback: generate a local UUID (server won't track it but chat still works)
      id = crypto.randomUUID();
      set(id);
      console.warn('Could not create server session, using local UUID:', id);
      return id;
    }
  }

  function shortId(id) {
    return id ? id.slice(0, 8) + '…' : '—';
  }

  return { get, set, clear, getOrCreate, shortId };
})();

window.Session = Session;
