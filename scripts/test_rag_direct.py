import sys
sys.path.insert(0, '.')
from backend.rag.pipeline import run_rag

try:
    print("Running RAG pipeline...")
    res = run_rag("Patient context - Age: 31 | Main symptom: Headache | Duration: 3 days | Severity: moderate\n\nUser question: none", history_string="")
    print("Success:")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
