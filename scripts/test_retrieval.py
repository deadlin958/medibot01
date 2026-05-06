import sys
sys.path.insert(0, '.')
from backend.rag.retriever import retrieve

results = retrieve('Are ILC2s increased in chronic rhinosinusitis with nasal polyps?', k=3)
for i, r in enumerate(results):
    dist = r['distance']
    meta = r['metadata']
    print(f"--- Hit {i+1} (distance={dist:.4f}) ---")
    print(f"Question  : {meta['question'][:100]}")
    print(f"Decision  : {meta['final_decision']}")
    print(f"Mesh terms: {meta['mesh_terms'][:80]}")
    print()

print("Retrieval smoke test PASSED")
