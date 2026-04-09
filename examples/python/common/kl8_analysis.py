from __future__ import annotations

from collections import Counter
from typing import Any


def _build_omission(records: list[dict[str, Any]]) -> dict[int, int]:
    omission = {number: len(records) for number in range(1, 81)}
    for index, record in enumerate(records):
        for number in record.get("numbers_list", []):
            omission[int(number)] = min(omission[int(number)], index)
    return omission


def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "period": str(record.get("period", "")),
            "numbers_list": [int(number) for number in record.get("numbers_list", [])[:20]],
        }
        for record in records
        if len(record.get("numbers_list", [])) >= 20
    ]


def _pick_validation_windows(record_count: int) -> list[int]:
    candidates = [10, 20, 30, 50]
    available = [window for window in candidates if record_count > window + 1]
    if available:
        return available
    if record_count > 2:
        return [record_count - 2]
    return []


def _build_empty_validation() -> dict[str, Any]:
    return {
        "sampleCount": 0,
        "avgHitCount": 0.0,
        "bestHitCount": 0,
        "hitDistribution": {},
        "recentCases": [],
        "sample_count": 0,
        "avg_hit_count": 0.0,
        "best_hit_count": 0,
        "hit_distribution": {},
        "recent_cases": [],
    }


def _analyze_kl8_normalized(normalized: list[dict[str, Any]], include_validation: bool = True) -> dict[str, Any]:
    if not normalized:
        return {"recordCount": 0, "message": "当前接口没有返回可分析的快乐8历史数据。"}

    total_counter = Counter()
    recent_counter = Counter()
    zone_counter = Counter()
    odd_even_counter = Counter()
    high_low_counter = Counter()
    consecutive_counter = Counter()

    for record in normalized:
        numbers = sorted(record["numbers_list"])
        total_counter.update(numbers)
        zone_counter[
            (
                sum(1 for number in numbers if 1 <= number <= 20),
                sum(1 for number in numbers if 21 <= number <= 40),
                sum(1 for number in numbers if 41 <= number <= 60),
                sum(1 for number in numbers if 61 <= number <= 80),
            )
        ] += 1
        odd = sum(number % 2 for number in numbers)
        odd_even_counter[f"{odd}:{20 - odd}"] += 1
        high_low_counter[
            (
                sum(1 for number in numbers if 1 <= number <= 40),
                sum(1 for number in numbers if 41 <= number <= 80),
            )
        ] += 1
        consecutive_counter[sum(1 for left, right in zip(numbers, numbers[1:]) if right - left == 1)] += 1

    for record in normalized[: min(30, len(normalized))]:
        recent_counter.update(record["numbers_list"])

    omission = _build_omission(normalized)
    omission_top = [number for number, _ in sorted(omission.items(), key=lambda item: (-item[1], item[0]))[:12]]
    hot_top = [number for number, _ in total_counter.most_common(12)]
    recent_hot_top = [number for number, _ in recent_counter.most_common(12)]

    balanced_pick = []
    for pool in (hot_top, recent_hot_top, omission_top):
        for number in pool:
            if number not in balanced_pick:
                balanced_pick.append(number)
            if len(balanced_pick) >= 10:
                break
        if len(balanced_pick) >= 10:
            break

    balanced_pick = sorted(balanced_pick[:10])
    result = {
        "recordCount": len(normalized),
        "latestPeriod": normalized[0]["period"],
        "latestNumbers": normalized[0]["numbers_list"],
        "hotNumbers": hot_top,
        "recentHotNumbers": recent_hot_top,
        "highOmissionNumbers": omission_top,
        "zoneDistribution": [[list(pattern), count] for pattern, count in zone_counter.most_common(8)],
        "oddEvenDistribution": [[pattern, count] for pattern, count in odd_even_counter.most_common(8)],
        "highLowDistribution": [[list(pattern), count] for pattern, count in high_low_counter.most_common(8)],
        "consecutiveDistribution": [[value, count] for value, count in consecutive_counter.most_common(8)],
        "balancedPick": balanced_pick,
        "recommendations": [
            {
                "name": "balancedPick",
                "numbers": balanced_pick,
                "source": "hot+recent+omission",
            }
        ],
    }
    if include_validation:
        result["validation"] = _build_kl8_validation(normalized)
    return result


def _build_kl8_validation(normalized: list[dict[str, Any]]) -> dict[str, Any]:
    validation = _build_empty_validation()
    if len(normalized) < 3:
        return validation

    sample_count = 0
    total_hits = 0
    best_hit_count = 0
    hit_distribution: Counter[int] = Counter()
    recent_cases: list[dict[str, Any]] = []

    for history_length in _pick_validation_windows(len(normalized)):
        checks = min(10, len(normalized) - history_length - 1)
        if checks <= 0:
            continue
        for index in range(checks):
            target = normalized[index]
            history_slice = normalized[index + 1 : index + 1 + history_length]
            if len(history_slice) < history_length:
                continue
            inner = _analyze_kl8_normalized(history_slice, include_validation=False)
            prediction = inner.get("balancedPick", [])
            hit_count = len(set(prediction) & set(target["numbers_list"]))
            sample_count += 1
            total_hits += hit_count
            best_hit_count = max(best_hit_count, hit_count)
            hit_distribution[hit_count] += 1
            if len(recent_cases) < 6:
                recent_cases.append(
                    {
                        "targetPeriod": target["period"],
                        "hitCount": hit_count,
                        "predictedNumbers": prediction,
                        "target_period": target["period"],
                        "hit_count": hit_count,
                        "predicted_numbers": prediction,
                    }
                )

    if sample_count == 0:
        return validation

    avg_hit_count = round(total_hits / sample_count, 4)
    hit_distribution_payload = {str(key): value for key, value in sorted(hit_distribution.items())}
    return {
        "sampleCount": sample_count,
        "avgHitCount": avg_hit_count,
        "bestHitCount": best_hit_count,
        "hitDistribution": hit_distribution_payload,
        "recentCases": recent_cases,
        "sample_count": sample_count,
        "avg_hit_count": avg_hit_count,
        "best_hit_count": best_hit_count,
        "hit_distribution": hit_distribution_payload,
        "recent_cases": recent_cases,
    }


def analyze_kl8_records(records: list[dict[str, Any]], include_validation: bool = True) -> dict[str, Any]:
    normalized = _normalize_records(records)
    return _analyze_kl8_normalized(normalized, include_validation=include_validation)
