from __future__ import annotations

import hashlib
import re

_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[\W_]+", flags=re.UNICODE)


def normalize_profile_text(text: str) -> str:
    t = text.lower().strip()
    # collapse whitespace
    t = _SPACE_RE.sub(" ", t)
    # collapse punctuation to spaces then collapse whitespace again
    t = _PUNCT_RE.sub(" ", t)
    t = _SPACE_RE.sub(" ", t)
    return t.strip()


def hash_profile_text(text: str) -> str:
    norm = normalize_profile_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()
