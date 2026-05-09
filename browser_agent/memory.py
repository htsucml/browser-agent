"""Placeholder memory layer.

TODO: persist selector adaptation and site notes across runs.
"""

from __future__ import annotations


class Memory:
    def __init__(self) -> None:
        self.selector_notes: dict[str, str] = {}
