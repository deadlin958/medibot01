import sys
sys.path.insert(0, '.')
from backend.memory.store import add_turn, get_history_as_prompt_string, get_history
from backend.session.manager import create_session, touch_session
from backend.triage.flow import TRIAGE_STEPS, get_triage_status, NUM_STEPS
from backend.prompts.templates import RAG_PROMPT, build_rag_prompt_vars
from backend.rag.pipeline import run_rag
from backend.llm.vision import analyze_image
from backend.routes.chat_routes import router as cr
from backend.routes.image_routes import router as ir
from backend.app import app

print("All Phase 2 backend imports OK")
print(f"Triage steps: {NUM_STEPS}")
step_keys = [s['key'] for s in TRIAGE_STEPS]
print(f"Step keys: {step_keys}")
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print(f"Routes: {routes}")
