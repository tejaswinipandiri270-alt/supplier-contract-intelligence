import re
from pathlib import Path
from pypdf import PdfReader

CLAUSE_PATTERN = re.compile(r"(?im)^(?:CLAUSE\s+\d+\s*[–:-].*|\d+(?:\.\d+)*\s+[A-Z][^\n]{2,})$")

def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def clause_chunks(text: str, metadata: dict, source: str) -> list[dict]:
    # Split on clause headings. A complete SLA clause/table stays together as one chunk.
    lines = [line.strip() for line in text.replace("\r", "").splitlines() if line.strip()]
    sections, current = [], []
    for line in lines:
        if CLAUSE_PATTERN.match(line) and current:
            sections.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append(current)

    chunks = []
    for idx, section in enumerate(sections):
        content = "\n".join(section).strip()
        if len(content) < 35:
            continue
        first = section[0]
        clause = first[:120]
        low = content.lower()
        if "service level" in low or "sla" in low:
            clause_type = "SLA"
        elif "renew" in low:
            clause_type = "Renewal"
        elif "terminat" in low or "notice" in low:
            clause_type = "Termination"
        elif "payment" in low or "value" in low or "fee" in low:
            clause_type = "Commercial"
        else:
            clause_type = "General"
        merged = {**metadata, "source": source, "clause": clause,
                  "clause_type": clause_type, "text": content}
        merged["chunk_id"] = f"{metadata['contract_id']}-{idx:03d}"
        chunks.append(merged)
    return chunks
