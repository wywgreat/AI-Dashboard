from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from collectors.registry import registry
from collectors.sources.market import MarketSource
from collectors.sources.news import NewsSource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "normalized_record.schema.json"


TYPE_MAP: dict[str, tuple[type[Any], ...]] = {
    "string": (str,),
    "object": (dict,),
}


def ensure_registered_sources() -> None:
    if not registry.list_sources():
        registry.register(NewsSource())
        registry.register(MarketSource())


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    properties: dict[str, Any] = schema.get("properties", {})

    for field in required:
        if field not in record:
            errors.append(f"missing required field: {field}")

    for field, rules in properties.items():
        if field not in record:
            continue
        expected_type = rules.get("type")
        python_types = TYPE_MAP.get(expected_type)
        if python_types and not isinstance(record[field], python_types):
            errors.append(f"field {field} expected {expected_type}")

    return errors


def main() -> None:
    ensure_registered_sources()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    snapshot, _ = registry.fetch_all()

    for source_name, records in snapshot.items():
        for index, raw_record in enumerate(records):
            if not isinstance(raw_record, dict):
                raise ValueError(f"{source_name}[{index}] must be object")
            record = raw_record
            errors = validate_record(record, schema)
            if errors:
                raise ValueError(f"{source_name}[{index}] schema invalid: {'; '.join(errors)}")

    print("schema validation passed")


if __name__ == "__main__":
    main()
