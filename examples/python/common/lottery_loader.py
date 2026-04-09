from __future__ import annotations

from typing import Any


def split_numbers(raw_numbers: str | list[int] | tuple[int, ...]) -> list[int]:
    if isinstance(raw_numbers, (list, tuple)):
        return [int(item) for item in raw_numbers]

    return [
        int(chunk.strip())
        for chunk in str(raw_numbers or "").split(",")
        if str(chunk).strip()
    ]


def parse_history_record(record: dict[str, Any]) -> dict[str, Any]:
    numbers_list = split_numbers(record.get("numbers", ""))
    return {
        **record,
        "numbers_list": numbers_list,
        "number_count": len(numbers_list),
    }


def parse_history_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [parse_history_record(record) for record in records]
