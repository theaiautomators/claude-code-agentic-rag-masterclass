from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Split text into overlapping chunks, trying to break at natural boundaries.

    Tries splits in order: double newline, single newline, period+space, space.
    Falls back to hard character split if no separator works.
    """
    if not text or not text.strip():
        return []

    if len(text) <= chunk_size:
        return [text.strip()]

    chunks = []
    start = 0

    while start < len(text):
        # Take a window of chunk_size characters
        end = start + chunk_size

        if end >= len(text):
            # Last chunk — take everything remaining
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Try to find a natural break point within the window
        window = text[start:end]
        break_pos = _find_break_point(window)

        if break_pos > 0:
            chunk = text[start:start + break_pos].strip()
            if chunk:
                chunks.append(chunk)
            # Move forward, applying overlap
            start = start + break_pos - chunk_overlap
            if start < 0:
                start = 0
        else:
            # Hard split at chunk_size
            chunk = window.strip()
            if chunk:
                chunks.append(chunk)
            start = end - chunk_overlap

    return chunks


def _find_break_point(window: str) -> int:
    """Find the best break point in a text window, preferring natural boundaries."""
    separators = ["\n\n", "\n", ". ", " "]

    for sep in separators:
        # Find last occurrence of separator
        pos = window.rfind(sep)
        if pos > 0:
            # Include the separator in the chunk (except trailing spaces)
            return pos + len(sep)

    # No good break point found
    return 0
