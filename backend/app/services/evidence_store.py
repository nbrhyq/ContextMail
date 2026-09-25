from typing import Iterable, List

from app.models.domain import Evidence


class EvidenceStore:
    """State-scoped evidence utilities; persistence is handled by RunStore."""

    @staticmethod
    def merge(existing: List[Evidence], incoming: Iterable[Evidence]) -> List[Evidence]:
        by_id = {item.id: item for item in existing}
        for item in incoming:
            by_id[item.id] = item
        return list(by_id.values())

    @staticmethod
    def verified(evidence: Iterable[Evidence]) -> List[Evidence]:
        return [item for item in evidence if item.verified]

