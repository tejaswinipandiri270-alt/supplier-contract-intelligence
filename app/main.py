from fastapi import FastAPI, HTTPException
from app.schemas import QueryRequest, QueryResponse, Citation
from app.retrieval import retrieve
from app.generation import generate_answer
from app.config import get_settings
import logging
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
        logging.info("Starting supplier contract query")

        # Stage 1: Retrieve evidence from OpenSearch
        try:
            logging.info("Stage 1: Starting retrieval")
            hits, filters, is_list, retrieval_ms = retrieve(request.question)
            logging.info("Stage 1 completed: retrieved %s chunks", len(hits))
        except Exception:
            logging.exception("RETRIEVAL FAILED")
            raise

        settings = get_settings()

        if not hits:
            return QueryResponse(
                answer="I don't know. No supporting contract evidence was found for this question.",
                citations=[],
                scores={"retrieval_ms": round(retrieval_ms, 2), "max_score": 0},
                filters_applied=filters,
                retrieved_chunks=0
            )

        max_score = max(float(h.get("_score") or 0) for h in hits)

        if not is_list and not filters and max_score < settings.min_retrieval_score:
            return QueryResponse(
                answer="I don't know. The retrieved evidence did not meet the confidence threshold.",
                citations=[],
                scores={
                    "retrieval_ms": round(retrieval_ms, 2),
                    "max_score": max_score
                },
                filters_applied=filters,
                retrieved_chunks=len(hits)
            )

        # Stage 2: Generate answer using Azure OpenAI
        try:
            logging.info("Stage 2: Starting answer generation")
            answer = generate_answer(request.question, hits)
            logging.info("Stage 2 completed: answer generated")
        except Exception:
            logging.exception("ANSWER GENERATION FAILED")
            raise

        # Stage 3: Build citations
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
            answer=answer,
            citations=citations,
            scores={
                "retrieval_ms": round(retrieval_ms, 2),
                "max_score": round(max_score, 4)
            },
            filters_applied=filters,
            retrieved_chunks=len(hits)
        )

    except HTTPException:
        raise

    except Exception:
        logging.exception("SUPPLIER CONTRACT QUERY FAILED")
        raise HTTPException(
            status_code=500,
            detail="Query failed. Check the API logs for details."
        )
