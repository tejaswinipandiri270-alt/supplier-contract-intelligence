import json, os, tempfile
from pathlib import Path
from app.config import get_settings
from app.chunking import extract_pdf_text, clause_chunks
from app.embeddings import embed_texts
from app.opensearch_store import index_chunks

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DOCS = ROOT / "data" / "contracts"

def metadata_from_text(text: str, fallback: dict) -> dict:
    # Contract fields are read from the first-page text generated in the synthetic PDFs.
    def find(pattern, default):
        m = __import__("re").search(pattern, text, __import__("re").I)
        return m.group(1).strip() if m else default
    supplier = find(r"Supplier\s*:\s*([^\n]+)", fallback.get("supplier", "Unknown"))
    category = find(r"Category\s*:\s*([^\n]+)", fallback.get("category", "Other"))
    start = find(r"Start Date\s*:\s*(\d{4}-\d{2}-\d{2})", fallback.get("start_date", "2026-01-01"))
    end = find(r"End Date\s*:\s*(\d{4}-\d{2}-\d{2})", fallback.get("end_date", "2027-12-31"))
    value = find(r"Contract Value\s*:\s*£?([\d,]+(?:\.\d+)?)", str(fallback.get("contract_value", 0)))
    renew = find(r"Auto Renew\s*:\s*(Yes|No|True|False)", str(fallback.get("auto_renew", False)))
    notice = find(r"Notice Period\s*:\s*(\d+)", str(fallback.get("notice_days", 90)))
    return {
        "contract_id": fallback.get("contract_id", supplier.lower().replace(" ", "-")),
        "supplier": supplier, "category": category, "start_date": start, "end_date": end,
        "contract_value": float(value.replace(",", "")), "auto_renew": renew.lower() in ("yes","true"),
        "notice_days": int(notice)
    }

def _download_s3_documents(bucket: str, prefix: str, target: Path):
    import boto3
    s3 = boto3.client("s3", region_name=get_settings().aws_region)
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".pdf"):
                dest = target / Path(key).name
                s3.download_file(bucket, key, str(dest))

def run_ingestion():
    s = get_settings()
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "contracts" if s.use_s3 else LOCAL_DOCS
        if s.use_s3:
            source_dir.mkdir(parents=True, exist_ok=True)
            if not s.s3_bucket:
                raise ValueError("USE_S3=true but S3_BUCKET is empty")
            _download_s3_documents(s.s3_bucket, s.s3_prefix, source_dir)
        all_chunks = []
        for pdf in sorted(source_dir.glob("*.pdf")):
            text = extract_pdf_text(pdf)
            fallback_path = pdf.with_suffix(".json")
            fallback = json.loads(fallback_path.read_text()) if fallback_path.exists() else {}
            metadata = metadata_from_text(text, fallback)
            chunks = clause_chunks(text, metadata, pdf.name)
            for chunk in chunks:
                chunk["embedding"] = None
            if chunks:
                vectors = embed_texts([c["text"] for c in chunks])
                for c, v in zip(chunks, vectors):
                    c["embedding"] = v
                all_chunks.extend(chunks)
        count = index_chunks(all_chunks)
        manifest = {"documents": len(list(source_dir.glob("*.pdf"))), "chunks_indexed": count}
        (Path(__file__).resolve().parents[1] / "data" / "ingestion_manifest.json").write_text(json.dumps(manifest, indent=2))
        return manifest

if __name__ == "__main__":
    print(run_ingestion())
