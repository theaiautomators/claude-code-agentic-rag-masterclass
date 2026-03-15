def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Combine vector and keyword results using Reciprocal Rank Fusion (RRF).
    
    Args:
        vector_results: List of dictionaries from vector similarity search
        keyword_results: List of dictionaries from BM25 keyword search
        k: Smoothing parameter for RRF (default 60 is standard)
        
    Returns:
        A new list of merged dictionaries, augmented with 'rrf_score',
        sorted descending by the fused score.
    """
    
    # Track the best (lowest) rank for each chunk ID across both sets
    # Ranks are 1-indexed for the RRF formula: 1 / (k + rank)
    fused_scores = {}
    
    # Store the actual object data so we can rebuild the final list
    chunk_data = {}
    
    # Process vector results
    for rank, item in enumerate(vector_results, start=1):
        chunk_id = item["id"]
        # Save the original item payload
        if chunk_id not in chunk_data:
            chunk_data[chunk_id] = item.copy()
            # Ensure we track the baseline vector params
            chunk_data[chunk_id]["vector_similarity"] = item.get("similarity", 0.0)
            chunk_data[chunk_id]["keyword_rank"] = 0.0
            
        score = 1.0 / (k + rank)
        fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + score
        
    # Process keyword results
    for rank, item in enumerate(keyword_results, start=1):
        chunk_id = item["id"]
        
        # Save the original item payload if not seen in vector results
        if chunk_id not in chunk_data:
            chunk_data[chunk_id] = item.copy()
            chunk_data[chunk_id]["vector_similarity"] = 0.0
            
        # Ensure we track the baseline keyword rank
        chunk_data[chunk_id]["keyword_rank"] = item.get("rank", 0.0)
            
        score = 1.0 / (k + rank)
        fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + score
        
    # Rebuild final merged array and attach the RRF metric
    final_results = []
    for chunk_id, total_score in fused_scores.items():
        doc = chunk_data[chunk_id]
        doc["rrf_score"] = total_score
        final_results.append(doc)
        
    # Sort primarily by the RRF score
    final_results.sort(key=lambda x: x["rrf_score"], reverse=True)
    return final_results
