import json, re, statistics, time
from pathlib import Path
from app.retrieval import retrieve
from app.generation import generate_answer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "evaluation.json"

def reciprocal_rank(hits, expected_supplier=None, expected_clause=None):
    for rank, hit in enumerate(hits, start=1):
        src = hit["_source"]
        supplier_ok = not expected_supplier or src.get("supplier","").lower() == expected_supplier.lower()
        clause_ok = not expected_clause or expected_clause.lower() in src.get("clause","").lower() or expected_clause.lower() in src.get("clause_type","").lower()
        if supplier_ok and clause_ok:
            return 1.0 / rank
    return 0.0

def main():
    rows = json.loads(DATA.read_text())
    rr, exact, exact_n, list_recalls, latencies = [], [], [], [], []
    for item in rows:
        t0 = time.perf_counter()
        hits, filters, is_list, retrieval_ms = retrieve(item["question"])
        answer = generate_answer(item["question"], hits) if hits else "I don't know"
        latencies.append((time.perf_counter()-t0)*1000)
        if item.get("answerable", True):
            rr.append(reciprocal_rank(hits, item.get("expected_supplier"), item.get("expected_clause")))
            expected = str(item.get("expected_value","")).lower()
            if expected:
                exact_n.append(expected in answer.lower())
        else:
            exact_n.append(not hits or "don't know" in answer.lower())
        if "expected_suppliers" in item:
            found = {h["_source"].get("supplier","").lower() for h in hits}
            expected_set = {x.lower() for x in item["expected_suppliers"]}
            list_recalls.append(len(found & expected_set) / max(1, len(expected_set)))
    report = {
        "questions": len(rows),
        "MRR": round(sum(rr)/len(rr), 4) if rr else 0,
        "exact_match_accuracy": round(sum(exact_n)/len(exact_n), 4) if exact_n else 0,
        "list_recall": round(sum(list_recalls)/len(list_recalls), 4) if list_recalls else None,
        "p95_latency_ms": round(sorted(latencies)[min(len(latencies)-1, int(0.95*len(latencies)))], 2) if latencies else 0,
        "note": "Exact-match checks answer text for expected values; run with Azure configured for generated-answer evaluation."
    }
    out = ROOT / "data" / "evaluation_results.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
