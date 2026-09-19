from collections import defaultdict

from inference_gateway.models import UsageRecord


class Meter:
    def __init__(self) -> None:
        self.records: list[UsageRecord] = []

    def record(self, record: UsageRecord) -> None:
        self.records.append(record)

    def tenant_summary(self, tenant_id: str) -> dict:
        records = [record for record in self.records if record.tenant_id == tenant_id]
        tokens = sum(record.usage.total_tokens for record in records)
        return {
            "tenant": tenant_id,
            "requests": len(records),
            "tokens": tokens,
            "estimated_cost_usd": round(tokens / 1_000_000 * 0.80, 6),
            "note": "estimate only; not a billing record",
        }

    def by_model(self) -> dict[str, int]:
        totals: dict[str, int] = defaultdict(int)
        for record in self.records:
            totals[record.model] += record.usage.total_tokens
        return dict(totals)
