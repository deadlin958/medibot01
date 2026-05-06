"""
FastAPI Application Entry Point — clinical chatbot backend.
Serves the frontend SPA at / and API endpoints at /api/*
"""

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.routes.chat_routes  import router as chat_router
from backend.routes.image_routes import router as image_router
from backend.config import STATIC_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Clinical Chatbot API",
    description=(
        "Multimodal clinical chatbot powered by PubMedQA, GPT-4o, "
        "LangChain, and ChromaDB. For general guidance only."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(chat_router,  prefix="/api", tags=["Chat"])
app.include_router(image_router, prefix="/api", tags=["Image"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "clinical-chatbot-backend", "version": "2.0.0"}


# ── Serve frontend SPA ────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def serve_index():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Frontend not found. Run the backend and open /docs."}


# Mount static assets under /static (CSS, JS, images)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    log.info(f"Frontend served from {STATIC_DIR}")
else:
    log.warning(f"Frontend dir not found at {STATIC_DIR}. UI will not be served.")


if __name__ == "__main__":
    import uvicorn
    log.info("Starting Clinical Chatbot Backend on http://localhost:8000")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
