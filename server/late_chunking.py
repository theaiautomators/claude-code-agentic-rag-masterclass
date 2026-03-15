"""Late chunking via jinaai/jina-embeddings-v2-base-en (768 dims, 8192 token ctx)."""
from __future__ import annotations
import warnings

JINA_MODEL_NAME = "jinaai/jina-embeddings-v2-base-en"
JINA_MAX_TOKENS = 8192


def _get_jina_model():
    """Lazy-load and cache the Jina tokenizer + model."""
    if not hasattr(_get_jina_model, "_cache"):
        from transformers import AutoModel, AutoTokenizer
        import einops  # noqa — verify available
        print("Loading jina-embeddings-v2 model (first run downloads ~500MB)...")
        tokenizer = AutoTokenizer.from_pretrained(JINA_MODEL_NAME, trust_remote_code=True)
        model = AutoModel.from_pretrained(JINA_MODEL_NAME, trust_remote_code=True)
        model.eval()
        _get_jina_model._cache = (tokenizer, model)
    return _get_jina_model._cache


def _build_span_annotations(tokenizer, chunks: list[str]) -> list[tuple[int, int]]:
    """Compute (start, end) token spans for each chunk in the full sequence.
    Layout: [CLS] chunk0_tokens chunk1_tokens ... [SEP]  → chunk0 starts at index 1.
    """
    spans, cursor = [], 1  # offset by 1 for [CLS]
    for chunk in chunks:
        n = len(tokenizer.encode(chunk, add_special_tokens=False))
        spans.append((cursor, cursor + n))
        cursor += n
    return spans


def _mean_pool(hidden_states, start: int, end: int) -> list[float]:
    span = hidden_states[min(start, hidden_states.shape[0]):min(end, hidden_states.shape[0])]
    return (span.mean(dim=0) if span.shape[0] > 0 else hidden_states[0] * 0).tolist()


def late_chunk_embed(full_document: str, chunks: list[str]) -> list[list[float]]:
    """Single forward pass over full_document; pool per-chunk token spans.
    Falls back to CLS-pooling per chunk when document exceeds JINA_MAX_TOKENS."""
    import torch
    tokenizer, model = _get_jina_model()

    full_ids = tokenizer.encode(full_document, add_special_tokens=True)
    if len(full_ids) > JINA_MAX_TOKENS:
        warnings.warn(
            f"Document exceeds {JINA_MAX_TOKENS} tokens ({len(full_ids)}). "
            "Falling back to independent chunk embedding.",
            RuntimeWarning, stacklevel=2,
        )
        return _fallback_embed(tokenizer, model, chunks)

    spans = _build_span_annotations(tokenizer, chunks)
    inputs = tokenizer(full_document, return_tensors="pt", truncation=True,
                       max_length=JINA_MAX_TOKENS, add_special_tokens=True)
    with torch.no_grad():
        hidden = model(**inputs).last_hidden_state[0]  # (seq_len, 768)

    return [_mean_pool(hidden, s, e) for s, e in spans]


def _fallback_embed(tokenizer, model, chunks: list[str]) -> list[list[float]]:
    import torch
    results = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True,
                           max_length=JINA_MAX_TOKENS, add_special_tokens=True)
        with torch.no_grad():
            cls_emb = model(**inputs).last_hidden_state[0, 0, :]
        results.append(cls_emb.tolist())
    return results
