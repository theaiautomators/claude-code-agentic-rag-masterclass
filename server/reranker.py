from sentence_transformers import CrossEncoder

def get_reranker_model():
    """Lazy load the cross encoder model to save memory."""
    if not hasattr(get_reranker_model, "_model"):
        # We use a lightweight BGE reranker base model
        get_reranker_model._model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return get_reranker_model._model

def rerank_results(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank a list of candidate results using a cross-encoder."""
    if not results:
        return results
        
    reranker = get_reranker_model()
    
    # CrossEncoder expects pairs of (query, document)
    pairs = [[query, doc["content"]] for doc in results]
    
    # Predict relevance scores
    scores = reranker.predict(pairs)
    
    # Inject scores into our result dictionaries
    for score, doc in zip(scores, results):
        doc["reranker_score"] = float(score)
        
    # Sort by the new cross-encoder score descending
    reranked = sorted(results, key=lambda x: x["reranker_score"], reverse=True)
    
    return reranked[:top_k]
