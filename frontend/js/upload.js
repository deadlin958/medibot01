/**
 * upload.js — Drag-and-drop image upload, file validation, preview strip.
 */

const Upload = (() => {
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp'];
  const MAX_SIZE_MB   = 10;

  let _pendingFile = null;

  function getPendingFile()   { return _pendingFile; }
  function clearPendingFile() {
    _pendingFile = null;
    hidePreviewStrip();
    const trigger = document.getElementById('upload-trigger');
    if (trigger) trigger.classList.remove('has-image');
  }

  function validate(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      Chat.toast(`Unsupported file type: ${file.type}. Use JPG, PNG, WebP, GIF, or BMP.`, 'error');
      return false;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      Chat.toast(`File too large. Maximum size is ${MAX_SIZE_MB} MB.`, 'error');
      return false;
    }
    return true;
  }

  function formatSize(bytes) {
    if (bytes < 1024)        return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function showPreviewStrip(file) {
    const strip = document.getElementById('image-preview-strip');
    if (!strip) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      strip.innerHTML = `
        <div class="preview-card">
          <img src="${e.target.result}" class="preview-thumbnail" alt="Preview">
          <div class="preview-info">
            <div class="preview-name">${file.name}</div>
            <div class="preview-meta">${formatSize(file.size)} · ${file.type.split('/')[1].toUpperCase()}</div>
          </div>
          <button class="preview-remove" onclick="Upload.clear()" title="Remove image">✕</button>
        </div>`;
      strip.classList.add('visible');
    };
    reader.readAsDataURL(file);
  }

  function hidePreviewStrip() {
    const strip = document.getElementById('image-preview-strip');
    if (strip) { strip.classList.remove('visible'); strip.innerHTML = ''; }
  }

  function setFile(file) {
    if (!validate(file)) return false;
    _pendingFile = file;
    showPreviewStrip(file);
    const trigger = document.getElementById('upload-trigger');
    if (trigger) trigger.classList.add('has-image');
    return true;
  }

  function clear() { clearPendingFile(); }

  // ── Drag & Drop ───────────────────────────────────────────────────
  function initDragDrop() {
    const overlay = document.getElementById('drop-overlay');
    let dragCounter = 0;

    document.addEventListener('dragenter', (e) => {
      if (e.dataTransfer.types.includes('Files')) {
        dragCounter++;
        if (overlay) overlay.classList.add('active');
      }
    });

    document.addEventListener('dragleave', () => {
      dragCounter--;
      if (dragCounter <= 0 && overlay) {
        dragCounter = 0;
        overlay.classList.remove('active');
      }
    });

    document.addEventListener('dragover', (e) => e.preventDefault());

    document.addEventListener('drop', (e) => {
      e.preventDefault();
      dragCounter = 0;
      if (overlay) overlay.classList.remove('active');
      const file = e.dataTransfer.files[0];
      if (file) setFile(file);
    });
  }

  // ── File input change ─────────────────────────────────────────────
  function initFileInput() {
    const input   = document.getElementById('file-input');
    const trigger = document.getElementById('upload-trigger');
    if (!input || !trigger) return;
    trigger.addEventListener('click', () => input.click());
    input.addEventListener('change', () => {
      if (input.files[0]) setFile(input.files[0]);
      input.value = '';   // allow re-selecting same file
    });
  }

  function init() {
    initDragDrop();
    initFileInput();
  }

  return { init, setFile, clear, getPendingFile, clearPendingFile };
})();

window.Upload = Upload;
