from __future__ import annotations

from collections import Counter
from itertools import product
from typing import Any, Iterable


def _build_transition_matrices(records: list[dict[str, Any]], position_count: int, number_range: int) -> list[list[list[int]]]:
    matrices = [[[1 for _ in range(number_range)] for _ in range(number_range)] for _ in range(position_count)]
    for index in range(1, len(records)):
        previous = records[index - 1]["numbers_list"][:position_count]
        current = records[index]["numbers_list"][:position_count]
        if len(previous) != position_count or len(current) != position_count:
            continue
        for position in range(position_count):
            previous_value = int(previous[position])
            current_value = int(current[position])
            if 0 <= previous_value < number_range and 0 <= current_value < number_range:
                matrices[position][previous_value][current_value] += 1
    return matrices


def _position_statistics(records: list[dict[str, Any]], position_count: int) -> dict[str, Any]:
    position_counters = [Counter() for _ in range(position_count)]
    sum_counter = Counter()
    unique_counter = Counter()
    odd_even_counter = Counter()

    for record in records:
        numbers = record["numbers_list"][:position_count]
        if len(numbers) != position_count:
            continue
        for position, number in enumerate(numbers):
            position_counters[position][int(number)] += 1
        sum_counter[sum(numbers)] += 1
        unique_counter[len(set(numbers))] += 1
        odd = sum(number % 2 for number in numbers)
        odd_even_counter[f"{odd}:{position_count - odd}"] += 1

    return {
        "positionCounters": position_counters,
        "sumCounter": sum_counter,
        "uniqueCounter": unique_counter,
        "oddEvenCounter": odd_even_counter,
    }


def _score_numbers(
    numbers: list[int],
    matrices: list[list[list[int]]],
    last_numbers: list[int],
    stats: dict[str, Any],
    total_records: int,
) -> float:
    safe_total = max(total_records, 1)
    markov_score = 0.0
    positional_score = 0.0

    for position, number in enumerate(numbers):
        row = matrices[position][last_numbers[position]]
        row_total = sum(row) or 1
        markov_score += row[number] / row_total
        positional_score += stats["positionCounters"][position][number] / safe_total

    markov_score /= len(numbers)
    positional_score /= len(numbers)
    sum_score = stats["sumCounter"][sum(numbers)] / safe_total
    unique_score = stats["uniqueCounter"][len(set(numbers))] / safe_total
    odd = sum(number % 2 for number in numbers)
    odd_even_score = stats["oddEvenCounter"][f"{odd}:{len(numbers) - odd}"] / safe_total

    return markov_score * 0.4 + positional_score * 0.3 + sum_score * 0.15 + unique_score * 0.1 + odd_even_score * 0.05


def _build_candidates(position_counters: list[Counter], recent_counters: list[Counter], candidate_digits: int) -> list[list[int]]:
    pools: list[list[int]] = []
    for counter, recent_counter in zip(position_counters, recent_counters):
        merged = []
        for number, _ in counter.most_common(candidate_digits):
            if number not in merged:
                merged.append(number)
        for number, _ in recent_counter.most_common(candidate_digits):
            if number not in merged:
                merged.append(number)
        pools.append(merged[:candidate_digits] or [0, 1])

    return [list(candidate) for candidate in product(*pools)]


def _resolve_validation_history_lengths(record_count: int, history_lengths: Iterable[int]) -> list[int]:
    requested: list[int] = []
    for history_length in history_lengths:
        value = int(history_length)
        if value > 0 and value not in requested:
            requested.append(value)

    available = [value for value in requested if record_count > value + 1]
    if available or not requested:
        return available

    max_window = record_count - 2
    if max_window < 2:
        return []

    fallback: list[int] = []
    for candidate in (record_count // 3, record_count // 2, max_window):
        value = min(max(candidate, 2), max_window)
        if record_count > value + 1 and value not in fallback:
            fallback.append(value)
    return fallback


def analyze_positional_records(
    records: list[dict[str, Any]],
    position_count: int,
    number_range: int,
    history_lengths: Iterable[int] = (50, 100, 200),
    top_n: int = 12,
) -> dict[str, Any]:
    if not records:
        return {"recordCount": 0, "message": "当前接口没有返回可分析的位置型彩种历史数据。"}

    normalized = [
        {
            "period": str(record.get("period", "")),
            "numbers_list": [int(number) for number in record.get("numbers_list", [])[:position_count]],
        }
        for record in records
        if len(record.get("numbers_list", [])) >= position_count
    ]
    if not normalized:
        return {"recordCount": 0, "message": "当前接口没有返回可分析的位置型彩种历史数据。"}

    stats = _position_statistics(normalized, position_count)
    recent_stats = _position_statistics(normalized[: min(40, len(normalized))], position_count)
    matrices = _build_transition_matrices(normalized, position_count, number_range)
    latest_numbers = normalized[0]["numbers_list"]

    recommendations = []
    candidates = _build_candidates(stats["positionCounters"], recent_stats["positionCounters"], 3)[:500]
    for candidate in candidates:
        score = _score_numbers(candidate, matrices, latest_numbers, stats, len(normalized))
        recommendations.append(
            {
                "numbers": candidate,
                "score": round(score, 6),
                "sum": sum(candidate),
                "uniqueCount": len(set(candidate)),
            }
        )
    recommendations.sort(key=lambda item: item["score"], reverse=True)

    validation_results = []
    best_history_length = None
    best_hit_count = -1
    for history_length in _resolve_validation_history_lengths(len(normalized), history_lengths):
        if len(normalized) <= history_length + 1:
            continue
        hit_count = 0
        checks = min(20, len(normalized) - history_length - 1)
        for index in range(checks):
            target = normalized[index]["numbers_list"]
            history_slice = normalized[index + 1 : index + 1 + history_length]
            if len(history_slice) < history_length:
                continue
            inner = analyze_positional_records(history_slice, position_count, number_range, history_lengths=(), top_n=20)
            if target in [item["numbers"] for item in inner.get("recommendations", [])]:
                hit_count += 1

        validation_results.append({"historyLength": history_length, "hitCount": hit_count, "checked": checks})
        if hit_count > best_hit_count:
            best_hit_count = hit_count
            best_history_length = history_length

    validation_sample_count = sum(item["checked"] for item in validation_results)
    validation_hit_count = sum(item["hitCount"] for item in validation_results)
    validation_hit_rate = round(validation_hit_count / validation_sample_count * 100, 4) if validation_sample_count else 0.0

    position_summary = []
    for index, counter in enumerate(stats["positionCounters"]):
        recent_counter = recent_stats["positionCounters"][index]
        position_summary.append(
            {
                "position": f"第{index + 1}位",
                "hotDigits": [number for number, _ in counter.most_common(3)],
                "recentHotDigits": [number for number, _ in recent_counter.most_common(3)],
                "coldDigits": [number for number, _ in counter.most_common()[:-4:-1]][:3],
            }
        )

    return {
        "recordCount": len(normalized),
        "latestPeriod": normalized[0]["period"],
        "latestNumbers": latest_numbers,
        "positionSummary": position_summary,
        "sumDistributionTop": [[value, count] for value, count in stats["sumCounter"].most_common(8)],
        "oddEvenDistribution": [[value, count] for value, count in stats["oddEvenCounter"].most_common(8)],
        "uniqueDistribution": [[value, count] for value, count in stats["uniqueCounter"].most_common(8)],
        "recommendations": recommendations[:top_n],
        "validation": {
            "bestHistoryLength": best_history_length,
            "sampleCount": validation_sample_count,
            "hitCount": validation_hit_count,
            "hitRate": validation_hit_rate,
            "historyResults": validation_results,
            "best_history_length": best_history_length,
            "sample_count": validation_sample_count,
            "hit_count": validation_hit_count,
            "hit_rate": validation_hit_rate,
            "history_results": validation_results,
        },
    }
