from __future__ import annotations

from collections import Counter
from itertools import product
from typing import Any


def combo_type(digits: list[int]) -> str:
    unique_count = len(set(digits))
    if unique_count == 1:
        return "豹子"
    if unique_count == 2:
        return "组三"
    return "组六"


def odd_even_pattern(digits: list[int]) -> str:
    odd = sum(number % 2 for number in digits)
    return f"{odd}:{len(digits) - odd}"


def build_transition_matrices(records: list[dict[str, Any]]) -> list[list[list[int]]]:
    matrices = [[[1 for _ in range(10)] for _ in range(10)] for _ in range(3)]
    for index in range(1, len(records)):
        previous = records[index - 1]["numbers_list"]
        current = records[index]["numbers_list"]
        if len(previous) != 3 or len(current) != 3:
            continue
        for position in range(3):
            matrices[position][previous[position]][current[position]] += 1
    return matrices


def build_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    position_counters = [Counter() for _ in range(3)]
    sum_counter = Counter()
    span_counter = Counter()
    pattern_counter = Counter()
    type_counter = Counter()
    digit_counter = Counter()

    for record in records:
        digits = record["numbers_list"][:3]
        if len(digits) != 3:
            continue
        for position, digit in enumerate(digits):
            position_counters[position][digit] += 1
            digit_counter[digit] += 1
        sum_counter[sum(digits)] += 1
        span_counter[max(digits) - min(digits)] += 1
        pattern_counter[odd_even_pattern(digits)] += 1
        type_counter[combo_type(digits)] += 1

    return {
        "positionCounters": position_counters,
        "sumCounter": sum_counter,
        "spanCounter": span_counter,
        "patternCounter": pattern_counter,
        "typeCounter": type_counter,
        "digitCounter": digit_counter,
    }


def score_combo(combo: list[int], matrices: list[list[list[int]]], last_digits: list[int], stats: dict[str, Any], total_records: int) -> float:
    safe_total = max(total_records, 1)

    markov_score = 0.0
    for position, digit in enumerate(combo):
        previous_digit = last_digits[position]
        row = matrices[position][previous_digit]
        row_total = sum(row) or 1
        markov_score += row[digit] / row_total
    markov_score /= 3

    positional_score = 0.0
    for position, digit in enumerate(combo):
        positional_score += stats["positionCounters"][position][digit] / safe_total
    positional_score /= 3

    combo_sum = sum(combo)
    combo_span = max(combo) - min(combo)
    pattern = odd_even_pattern(combo)
    type_name = combo_type(combo)

    sum_score = stats["sumCounter"][combo_sum] / safe_total
    span_score = stats["spanCounter"][combo_span] / safe_total
    pattern_score = stats["patternCounter"][pattern] / safe_total
    type_score = stats["typeCounter"][type_name] / safe_total

    return (
        markov_score * 0.35
        + positional_score * 0.25
        + sum_score * 0.15
        + span_score * 0.10
        + pattern_score * 0.10
        + type_score * 0.05
    )


def build_position_summary(stats: dict[str, Any]) -> list[dict[str, Any]]:
    summary = []
    for index, counter in enumerate(stats["positionCounters"]):
        hot = [item[0] for item in counter.most_common(3)]
        cold = [item[0] for item in counter.most_common()[:-4:-1]]
        summary.append(
            {
                "position": f"第{index + 1}位",
                "hotDigits": hot,
                "coldDigits": cold[:3],
            }
        )
    return summary


def allocate_ticket_plan(type_counter: Counter, total_tickets: int = 10, budget_per_ticket: int = 2) -> dict[str, Any]:
    total = sum(type_counter.values())
    if total <= 0:
        weights = {"直选": 0.4, "组三": 0.4, "组六": 0.2}
    else:
        group3_ratio = type_counter.get("组三", 0) / total
        group6_ratio = type_counter.get("组六", 0) / total
        direct_ratio = 1.0 - (group3_ratio + group6_ratio) * 0.5
        weight_total = direct_ratio + group3_ratio + group6_ratio
        weights = {
            "直选": direct_ratio / weight_total,
            "组三": group3_ratio / weight_total,
            "组六": group6_ratio / weight_total,
        }

    raw_counts = {name: weights[name] * total_tickets for name in weights}
    allocated = {name: int(raw_counts[name]) for name in raw_counts}
    remainder = total_tickets - sum(allocated.values())
    ranking = sorted(raw_counts, key=lambda name: (raw_counts[name] - allocated[name], weights[name]), reverse=True)
    for index in range(remainder):
        allocated[ranking[index % len(ranking)]] += 1

    return {
        "totalTickets": total_tickets,
        "budget": total_tickets * budget_per_ticket,
        "costPerTicket": budget_per_ticket,
        "typeWeights": {name: round(value, 4) for name, value in weights.items()},
        "typeCounts": allocated,
    }


def build_grouped_recommendations(
    recommendations: list[dict[str, Any]],
    stats: dict[str, Any],
    top_n: int = 6,
) -> dict[str, list[dict[str, Any]]]:
    grouped = {"直选": [], "组三": [], "组六": []}

    grouped["直选"] = recommendations[:top_n]

    position_counters = stats["positionCounters"]
    digit_counter = stats["digitCounter"]
    safe_total = max(sum(digit_counter.values()), 1)
    generated_group3: list[dict[str, Any]] = []
    generated_group6: list[dict[str, Any]] = []

    hot_digits = [digit for digit, _ in digit_counter.most_common(8)]
    if not hot_digits:
        hot_digits = list(range(10))

    for pair_digit in hot_digits[:5]:
        for single_digit in hot_digits[:8]:
            if single_digit == pair_digit:
                continue
            for combo in (
                [pair_digit, pair_digit, single_digit],
                [pair_digit, single_digit, pair_digit],
                [single_digit, pair_digit, pair_digit],
            ):
                pair_freq = digit_counter[pair_digit] / safe_total
                single_freq = digit_counter[single_digit] / safe_total
                positional_score = sum(
                    position_counters[index][digit] / max(sum(position_counters[index].values()), 1)
                    for index, digit in enumerate(combo)
                ) / 3
                total_score = pair_freq * 0.45 + single_freq * 0.20 + positional_score * 0.35
                generated_group3.append(
                    {
                        "numbers": combo,
                        "score": round(total_score, 6),
                        "type": "组三",
                        "sum": sum(combo),
                        "span": max(combo) - min(combo),
                        "oddEven": odd_even_pattern(combo),
                    }
                )

    seen_group3 = set()
    deduped_group3 = []
    for item in sorted(generated_group3, key=lambda row: row["score"], reverse=True):
        key = tuple(item["numbers"])
        if key in seen_group3:
            continue
        seen_group3.add(key)
        deduped_group3.append(item)
        if len(deduped_group3) >= top_n:
            break
    grouped["组三"] = deduped_group3

    unique_triplets = set()
    for first in hot_digits[:7]:
        for second in hot_digits[:7]:
            for third in hot_digits[:7]:
                combo = [first, second, third]
                if len(set(combo)) != 3:
                    continue
                canonical = tuple(sorted(combo))
                if canonical in unique_triplets:
                    continue
                unique_triplets.add(canonical)
                score = sum(digit_counter[digit] for digit in combo) / safe_total
                positional_score = sum(
                    position_counters[index][digit] / max(sum(position_counters[index].values()), 1)
                    for index, digit in enumerate(combo)
                ) / 3
                generated_group6.append(
                    {
                        "numbers": combo,
                        "score": round(score * 0.55 + positional_score * 0.45, 6),
                        "type": "组六",
                        "sum": sum(combo),
                        "span": max(combo) - min(combo),
                        "oddEven": odd_even_pattern(combo),
                    }
                )

    generated_group6.sort(key=lambda row: row["score"], reverse=True)
    grouped["组六"] = generated_group6[:top_n]
    return grouped


def reverse_validate(records: list[dict[str, Any]], history_lengths: tuple[int, ...] = (100, 200, 500), top_n: int = 100) -> dict[str, Any]:
    successful_cases = 0
    tested_cases = 0
    best_history_length = None
    best_hits = -1
    history_results = []

    for history_length in history_lengths:
        if len(records) <= history_length + 5:
            continue

        hits = 0
        checks = min(30, len(records) - history_length - 1)
        for index in range(checks):
            target = records[index]["numbers_list"][:3]
            history_slice = records[index + 1 : index + 1 + history_length]
            if len(history_slice) < history_length:
                continue
            analysis = analyze_three_digit_records(history_slice, top_n=top_n, include_validation=False)
            candidates = [item["numbers"] for item in analysis["recommendations"][:top_n]]
            tested_cases += 1
            if target in candidates:
                hits += 1
                successful_cases += 1

        history_results.append({"historyLength": history_length, "hitCount": hits, "checked": checks})
        if hits > best_hits:
            best_hits = hits
            best_history_length = history_length

    return {
        "testedCases": tested_cases,
        "successfulCases": successful_cases,
        "bestHistoryLength": best_history_length,
        "historyResults": history_results,
    }


def analyze_three_digit_records(records: list[dict[str, Any]], top_n: int = 20, include_validation: bool = True) -> dict[str, Any]:
    if not records:
        return {}

    matrices = build_transition_matrices(records)
    stats = build_statistics(records)
    last_digits = records[0]["numbers_list"][:3]

    recommendations = []
    for combo in product(range(10), repeat=3):
        digits = list(combo)
        score = score_combo(digits, matrices, last_digits, stats, len(records))
        recommendations.append(
            {
                "numbers": digits,
                "score": round(score, 6),
                "type": combo_type(digits),
                "sum": sum(digits),
                "span": max(digits) - min(digits),
                "oddEven": odd_even_pattern(digits),
            }
        )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    validation = reverse_validate(records) if include_validation else {}
    grouped_recommendations = build_grouped_recommendations(recommendations, stats)
    ticket_plan = allocate_ticket_plan(stats["typeCounter"])

    return {
        "recordCount": len(records),
        "latestPeriod": records[0]["period"],
        "latestNumbers": records[0]["numbers_list"][:3],
        "positionSummary": build_position_summary(stats),
        "digitFrequencyTop": [list(item) for item in stats["digitCounter"].most_common(10)],
        "oddEvenDistribution": [list(item) for item in stats["patternCounter"].most_common(6)],
        "sumDistributionTop": [list(item) for item in stats["sumCounter"].most_common(5)],
        "spanDistributionTop": [list(item) for item in stats["spanCounter"].most_common(5)],
        "typeDistribution": dict(stats["typeCounter"]),
        "recommendations": recommendations[:top_n],
        "groupedRecommendations": grouped_recommendations,
        "ticketPlan": ticket_plan,
        "validation": validation,
    }
