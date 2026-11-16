import time
from app.config import get_settings
from app.embeddings import embed_query
from app.opensearch_store import get_client
from app.self_query import parse_filters

def retrieve(question: str):
    s = get_settings()
    client = get_client()
    filters, semantic_query, is_list = parse_filters(question)
    filter_clauses = []
    if filters.get("category"):
        filter_clauses.append({"term": {"category": filters["category"]}})
    if filters.get("supplier"):
        filter_clauses.append({"wildcard": {"supplier": {"value": f"*{filters['supplier']}*", "case_insensitive": True}}})
    if "auto_renew" in filters:
        filter_clauses.append({"term": {"auto_renew": filters["auto_renew"]}})
    if filters.get("end_date_range"):
        filter_clauses.append({"range": {"end_date": filters["end_date_range"]}})

    started = time.perf_counter()
    # Cross-contract/list questions use structured filters and paginate all matching chunks,
    # rather than relying on a small top-k vector result.
    if is_list and filter_clauses:
        body = {"size": 1000, "query": {"bool": {"filter": filter_clauses}}}
        response = client.search(index=s.opensearch_index, body=body)
        hits = response["hits"]["hits"]
        results = [{"_source": h["_source"], "_score": h.get("_score", 1.0)} for h in hits]
    else:
        vector = embed_query(semantic_query or question)
        knn = {"knn": {"embedding": {"vector": vector, "k": max(s.top_k, 30 if is_list else s.top_k)}}}
        query = {"bool": {"must": [knn], "filter": filter_clauses}} if filter_clauses else knn
        response = client.search(index=s.opensearch_index, body={"size": max(s.top_k, 30 if is_list else s.top_k), "query": query})
        results = [{"_source": h["_source"], "_score": h.get("_score", 0.0)} for h in response["hits"]["hits"]]
    elapsed = (time.perf_counter() - started) * 1000
    return results, filters, is_list, elapsed

