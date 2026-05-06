"""
Data Cleaner — parses pubmedqa.csv and outputs cleaned_pubmedqa.jsonl.

Raw `context` column is a stringified Python dict:
  {'contexts': [...], 'labels': [...], 'meshes': [...]}

We parse it, flatten the context sections into a single string,
and write one JSON object per line to CLEANED_JSONL.
"""

import ast
import json
import logging
from pathlib import Path

import pandas as pd

from backend.config import RAW_CSV, CLEANED_JSONL

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def _parse_context(raw: str) -> dict:
    """Convert the stringified context dict into a Python dict safely."""
    try:
        return ast.literal_eval(raw)
    except Exception:
        return {"contexts": [raw], "labels": [], "meshes": []}


def _build_full_context(parsed: dict) -> str:
    """
    Combine labelled sections into a single readable text block.
    E.g.:  OBJECTIVE: ... \nMETHODS: ... \nRESULTS: ...
    """
    contexts = parsed.get("contexts", [])
    labels   = parsed.get("labels", [])

    # Pair each section with its label (if available)
    parts = []
    for i, text in enumerate(contexts):
        label = labels[i] if i < len(labels) else f"SECTION_{i+1}"
        parts.append(f"{label}: {text.strip()}")

    return "\n".join(parts)


def _normalize_decision(raw: str) -> str:
    """Ensure final_decision is one of yes / no / maybe."""
    val = str(raw).strip().lower()
    return val if val in {"yes", "no", "maybe"} else "maybe"


def clean_dataset(
    csv_path: Path = RAW_CSV,
    output_path: Path = CLEANED_JSONL,
) -> int:
    """
    Read the raw CSV, clean & normalize every row, write to JSONL.

    Returns the number of records written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Reading raw dataset from {csv_path} …")
    df = pd.read_csv(csv_path)

    records_written = 0
    skipped = 0

    with output_path.open("w", encoding="utf-8") as fout:
        for _, row in df.iterrows():
            try:
                parsed   = _parse_context(row["context"])
                full_ctx = _build_full_context(parsed)

                record = {
                    "pubid":          int(row["pubid"]),
                    "question":       str(row["question"]).strip(),
                    "full_context":   full_ctx,
                    "long_answer":    str(row["long_answer"]).strip(),
                    "final_decision": _normalize_decision(row["final_decision"]),
                    "mesh_terms":     list(parsed.get("meshes", [])),
                }

                # Basic quality gate — skip if core fields are empty
                if not record["question"] or not record["full_context"]:
                    skipped += 1
                    continue

                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                records_written += 1

            except Exception as exc:
                log.warning(f"Skipping pubid={row.get('pubid', '?')}: {exc}")
                skipped += 1

    log.info(
        f"Cleaning complete — {records_written} records written, "
        f"{skipped} skipped → {output_path}"
    )
    return records_written


if __name__ == "__main__":
    clean_dataset()
