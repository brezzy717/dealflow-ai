"""Deduplication via normalized business name + address (coverage ledger 1.8)."""

from __future__ import annotations

import re

# Common entity suffixes stripped before comparison.
_SUFFIXES = {
    "llc", "inc", "incorporated", "corp", "corporation", "co", "company",
    "ltd", "limited", "lp", "llp", "pllc", "group", "holdings", "enterprises",
    "and", "sons", "the",
}
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")
_STREET_ABBR = {
    "street": "st", "avenue": "ave", "boulevard": "blvd", "road": "rd",
    "drive": "dr", "lane": "ln", "court": "ct", "suite": "ste",
}


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation + entity suffixes, collapse whitespace."""
    text = _NON_ALNUM.sub(" ", (name or "").lower())
    tokens = [t for t in _WS.sub(" ", text).split(" ") if t and t not in _SUFFIXES]
    return " ".join(tokens)


def normalize_address(address: str) -> str:
    text = _NON_ALNUM.sub(" ", (address or "").lower())
    tokens = [_STREET_ABBR.get(t, t) for t in _WS.sub(" ", text).split(" ") if t]
    return " ".join(tokens)


def dedup_key(name: str, address: str, state: str) -> str:
    """Stable key for matching the same business across sources/loads."""
    return "|".join(
        (normalize_name(name), normalize_address(address), (state or "").strip().lower())
    )
