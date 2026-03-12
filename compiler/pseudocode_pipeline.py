import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PseudocodeSummary:
    consolidated_total: int
    consolidated_used: int
    inline_used: int
    missing: list[tuple[str, str]] = field(default_factory=list)
    empty: list[tuple[str, str]] = field(default_factory=list)

    @property
    def consolidated_unused(self) -> int:
        return max(0, self.consolidated_total - self.consolidated_used)

    def preview(self, items: list[tuple[str, str]], limit: int = 5) -> str:
        label = ", ".join(card_no for card_no, _ in items[:limit])
        if len(items) > limit:
            label += ", ..."
        return label


class PseudocodeResolver:
    def __init__(self, consolidated: dict[str, object] | None = None):
        self.consolidated = consolidated or {}
        self.reset()

    @classmethod
    def from_file(cls, path: str) -> "PseudocodeResolver":
        file_path = Path(path)
        if not file_path.exists():
            return cls()
        print(f"Loading consolidated ability mappings from {path}")
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(data)

    def reset(self) -> None:
        self._consolidated_used: set[str] = set()
        self._inline_used: set[str] = set()
        self._missing: list[tuple[str, str]] = []
        self._empty: list[tuple[str, str]] = []

    def resolve(self, card_kind: str, card_no: str, data: dict, error_sink: list[str]) -> str:
        raw_jp = str(data.get("ability", "")).strip()
        inline_pseudocode = str(data.get("pseudocode", "")).strip()

        if not raw_jp:
            return inline_pseudocode

        if raw_jp in self.consolidated:
            pseudocode = self._extract_pseudocode(self.consolidated[raw_jp])
            if pseudocode:
                self._consolidated_used.add(raw_jp)
                return pseudocode

            self._append_unique(self._empty, card_no, raw_jp)
            error_sink.append(
                f"[{card_kind}] {card_no}: Consolidated pseudocode entry is empty for ability: {raw_jp[:80]}..."
            )
            return ""

        if inline_pseudocode:
            self._inline_used.add(card_no)
            return inline_pseudocode

        self._append_unique(self._missing, card_no, raw_jp)
        error_sink.append(f"[{card_kind}] {card_no}: Missing pseudocode for ability: {raw_jp[:80]}...")
        return ""

    def summary(self) -> PseudocodeSummary:
        return PseudocodeSummary(
            consolidated_total=len(self.consolidated),
            consolidated_used=len(self._consolidated_used),
            inline_used=len(self._inline_used),
            missing=list(self._missing),
            empty=list(self._empty),
        )

    @staticmethod
    def _extract_pseudocode(entry: object) -> str:
        if isinstance(entry, dict):
            value = entry.get("pseudocode", "")
        elif isinstance(entry, str):
            value = entry
        else:
            value = ""
        return str(value).strip()

    @staticmethod
    def _append_unique(items: list[tuple[str, str]], card_no: str, raw_jp: str) -> None:
        entry = (card_no, raw_jp)
        if entry not in items:
            items.append(entry)