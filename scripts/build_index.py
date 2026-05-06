"""
build_index.py — one-time script to clean → chunk → embed → index the
PubMedQA dataset into ChromaDB.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --reset   # wipe and rebuild the index
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.data_pipeline.cleaner import clean_dataset
from backend.data_pipeline.indexer import build_index
from backend.config import CLEANED_JSONL, CHROMA_DB_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build the PubMedQA ChromaDB index")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the ChromaDB collection",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip data cleaning if cleaned_pubmedqa.jsonl already exists",
    )
    args = parser.parse_args()

    t0 = time.time()

    # ── Step 1: Clean the raw CSV ─────────────────────────────────────────────
    if args.skip_clean and CLEANED_JSONL.exists():
        log.info(f"Skipping cleaning — using existing {CLEANED_JSONL}")
    else:
        log.info("=== Step 1/2: Cleaning raw dataset ===")
        n_records = clean_dataset()
        log.info(f"Cleaned {n_records} records → {CLEANED_JSONL}")

    # ── Step 2: Build the ChromaDB index ─────────────────────────────────────
    log.info("=== Step 2/2: Building ChromaDB vector index ===")
    n_vectors = build_index(jsonl_path=CLEANED_JSONL, reset=args.reset)
    log.info(f"Index built with {n_vectors} vectors → {CHROMA_DB_DIR}")

    elapsed = time.time() - t0
    log.info(f"=== Done in {elapsed:.1f}s ===")


if __name__ == "__main__":
    main()
