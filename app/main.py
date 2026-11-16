from fastapi import FastAPI, HTTPException
from app.schemas import QueryRequest, QueryResponse, Citation
from app.retrieval import retrieve
from app.generation import generate_answer
from app.config import get_settings

app = FastAPI(
    title="Supplier Contract Intelligence Assistant",
    version="1.0.0",
    description="RAG assistant for supplier contracts: clause retrieval, metadata filtering and cited answers."
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "supplier-contract-intelligence"}

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        hits, filters, is_list, retrieval_ms = retrieve(request.question)
        settings = get_settings()
        if not hits:
            return QueryResponse(
                answer="I don't know. No supporting contract evidence was found for this question.",
                citations=[], scores={"retrieval_ms": round(retrieval_ms, 2), "max_score": 0},
                filters_applied=filters, retrieved_chunks=0
            )
        max_score = max(float(h.get("_score") or 0) for h in hits)
        # OpenSearch score scales vary by query type; apply threshold only to semantic queries.
        if not is_list and not filters and max_score < settings.min_retrieval_score:
            return QueryResponse(
                answer="I don't know. The retrieved evidence did not meet the confidence threshold.",
                citations=[], scores={"retrieval_ms": round(retrieval_ms, 2), "max_score": max_score},
                filters_applied=filters, retrieved_chunks=len(hits)
            )
        answer = generate_answer(request.question, hits)
        citations = []
        for h in hits[:10]:
            src = h["_source"]
            citations.append(Citation(
                source=src.get("source", "unknown"),
                supplier=src.get("supplier", "unknown"),
                clause=src.get("clause", "unknown"),
                chunk_id=src.get("chunk_id", "unknown"),
                score=round(float(h.get("_score") or 0), 4),
                excerpt=src.get("text", "")[:350]
            ))
        return QueryResponse(
            answer=answer, citations=citations,
            scores={"retrieval_ms": round(retrieval_ms, 2), "max_score": round(max_score, 4)},
            filters_applied=filters, retrieved_chunks=len(hits)
        )
    
    except HTTPException:
        raise

    except Exception:
        import logging
        logging.exception("Supplier contract query failed")
        raise HTTPException(
            status_code=500,
            detail="Query failed. Check the API logs for details."
        )
