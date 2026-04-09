from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any


def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for record in records:
        numbers = record.get("numbers_list", [])
        if len(numbers) < 7:
            continue
        normalized.append(
            {
                "period": str(record.get("period", "")),
                "front": sorted(int(number) for number in numbers[:5]),
                "back": sorted(int(number) for number in numbers[5:7]),
            }
        )
    return normalized


def _build_omission(values_by_record: list[list[int]], number_range: range) -> list[list[int]]:
    omission = {number: len(values_by_record) for number in number_range}
    for index, values in enumerate(values_by_record):
        for number in values:
            omission[int(number)] = min(omission[int(number)], index)
    return [[number, miss] for number, miss in sorted(omission.items(), key=lambda item: (-item[1], item[0]))[:10]]


def _build_recent_repeat_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"front": [], "back": []}

    latest = records[0]
    latest_front = set(latest["front"])
    latest_back = set(latest["back"])
    front_summary = []
    back_summary = []
    for record in records[1:11]:
        front_overlap = len(latest_front & set(record["front"]))
        back_overlap = len(latest_back & set(record["back"]))
        if front_overlap > 0:
            front_summary.append([record["period"], front_overlap])
        if back_overlap > 0:
            back_summary.append([record["period"], back_overlap])

    return {
        "front": front_summary[:6],
        "back": back_summary[:6],
    }


def _build_models_performance(top_combinations: list[dict[str, Any]]) -> dict[str, Any]:
    if not top_combinations:
        return {
            "frequencyModel": 0.0,
            "zoneModel": 0.0,
            "sumModel": 0.0,
            "repeatModel": 0.0,
        }

    average_score = sum(item["score"] for item in top_combinations) / len(top_combinations)
    return {
        "frequencyModel": round(average_score * 0.55, 6),
        "zoneModel": round(average_score * 0.25, 6),
        "sumModel": round(average_score * 0.15, 6),
        "repeatModel": round(average_score * 0.05, 6),
    }


def _build_performance_stats(
    normalized: list[dict[str, Any]],
    top_front_pool: list[int],
    top_back_pool: list[int],
    top_combinations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "recordCount": len(normalized),
        "frontPoolSize": len(top_front_pool),
        "backPoolSize": len(top_back_pool),
        "generatedCombinationCount": len(top_combinations),
        "returnedCombinationCount": min(len(top_combinations), 10),
    }


def _pick_validation_windows(record_count: int) -> list[int]:
    candidates = [1, 3, 5, 10, 20, 30, 50, 80]
    windows = [window for window in candidates if record_count > window + 1]
    if windows:
        return windows
    if record_count > 2:
        return [record_count - 2]
    return []


def _build_validation_case(
    target: dict[str, Any],
    candidate: dict[str, Any],
    history_length: int,
    sequence: int,
) -> dict[str, Any]:
    front_match = len(set(candidate["front"]) & set(target["front"]))
    back_match = len(set(candidate["back"]) & set(target["back"]))
    total_match = front_match + back_match
    case = {
        "targetPeriod": target["period"],
        "targetFront": target["front"],
        "targetBack": target["back"],
        "predictedFront": candidate["front"],
        "predictedBack": candidate["back"],
        "frontMatchCount": front_match,
        "backMatchCount": back_match,
        "totalMatchCount": total_match,
        "historyLength": history_length,
        "score": candidate["score"],
        "target_period": target["period"],
        "target_front": target["front"],
        "target_back": target["back"],
        "predicted_front": candidate["front"],
        "predicted_back": candidate["back"],
        "front_match_count": front_match,
        "back_match_count": back_match,
        "total_match_count": total_match,
        "history_length": history_length,
    }
    case["_sequence"] = sequence
    return case


def _is_better_validation_case(candidate: dict[str, Any], current: dict[str, Any] | None) -> bool:
    if current is None:
        return True
    return (
        candidate["totalMatchCount"],
        candidate["backMatchCount"],
        candidate["frontMatchCount"],
        candidate["score"],
        candidate["historyLength"],
    ) > (
        current["totalMatchCount"],
        current["backMatchCount"],
        current["frontMatchCount"],
        current["score"],
        current["historyLength"],
    )


def _strip_validation_case(case: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in case.items() if not key.startswith("_")}


def _empty_validation() -> dict[str, Any]:
    return {
        "sampleCount": 0,
        "testCount": 0,
        "avgFrontMatch": 0.0,
        "avgBackMatch": 0.0,
        "avgTotalMatch": 0.0,
        "bestTotalMatch": 0,
        "bestCase": {},
        "hitDistribution": {},
        "recentCases": [],
        "historyResults": [],
        "sample_count": 0,
        "test_count": 0,
        "avg_front_match": 0.0,
        "avg_back_match": 0.0,
        "avg_total_match": 0.0,
        "best_total_match": 0,
        "best_case": {},
        "hit_distribution": {},
        "recent_cases": [],
        "history_results": [],
    }


def _build_validation(normalized: list[dict[str, Any]], top_n: int = 10) -> dict[str, Any]:
    validation = _empty_validation()
    if len(normalized) < 3:
        return validation

    total_front_match = 0
    total_back_match = 0
    total_match = 0
    sample_count = 0
    best_case: dict[str, Any] | None = None
    hit_distribution: Counter[str] = Counter()
    best_case_by_period: dict[str, dict[str, Any]] = {}
    history_results = []

    for history_length in _pick_validation_windows(len(normalized)):
        checks = min(10, len(normalized) - history_length - 1)
        if checks <= 0:
            continue

        window_front_match = 0
        window_back_match = 0
        window_total_match = 0
        window_best_match = 0
        window_sample_count = 0

        for index in range(checks):
            target = normalized[index]
            history_slice = normalized[index + 1 : index + 1 + history_length]
            if len(history_slice) < history_length:
                continue

            inner = _analyze_dlt_normalized(history_slice, include_validation=False)
            candidates = inner.get("topCombinations", [])[:top_n]
            if not candidates:
                continue

            case = max(
                (_build_validation_case(target, candidate, history_length, index) for candidate in candidates),
                key=lambda item: (
                    item["totalMatchCount"],
                    item["backMatchCount"],
                    item["frontMatchCount"],
                    item["score"],
                    item["historyLength"],
                ),
            )

            sample_count += 1
            window_sample_count += 1
            total_front_match += case["frontMatchCount"]
            total_back_match += case["backMatchCount"]
            total_match += case["totalMatchCount"]
            window_front_match += case["frontMatchCount"]
            window_back_match += case["backMatchCount"]
            window_total_match += case["totalMatchCount"]
            window_best_match = max(window_best_match, case["totalMatchCount"])
            hit_distribution[f"front{case['frontMatchCount']}_back{case['backMatchCount']}"] += 1

            if _is_better_validation_case(case, best_case):
                best_case = case
            if _is_better_validation_case(case, best_case_by_period.get(case["targetPeriod"])):
                best_case_by_period[case["targetPeriod"]] = case

        if window_sample_count:
            history_results.append(
                {
                    "historyLength": history_length,
                    "sampleCount": window_sample_count,
                    "avgFrontMatch": round(window_front_match / window_sample_count, 4),
                    "avgBackMatch": round(window_back_match / window_sample_count, 4),
                    "avgTotalMatch": round(window_total_match / window_sample_count, 4),
                    "bestTotalMatch": window_best_match,
                    "history_length": history_length,
                    "sample_count": window_sample_count,
                    "avg_front_match": round(window_front_match / window_sample_count, 4),
                    "avg_back_match": round(window_back_match / window_sample_count, 4),
                    "avg_total_match": round(window_total_match / window_sample_count, 4),
                    "best_total_match": window_best_match,
                }
            )

    if sample_count == 0:
        return validation

    recent_cases = [
        _strip_validation_case(case)
        for case in sorted(best_case_by_period.values(), key=lambda item: item["_sequence"])[:6]
    ]
    avg_front_match = round(total_front_match / sample_count, 4)
    avg_back_match = round(total_back_match / sample_count, 4)
    avg_total_match = round(total_match / sample_count, 4)
    best_total_match = best_case["totalMatchCount"] if best_case else 0
    best_case_payload = _strip_validation_case(best_case) if best_case else {}
    hit_distribution_payload = dict(sorted(hit_distribution.items(), key=lambda item: (-item[1], item[0])))

    return {
        "sampleCount": sample_count,
        "testCount": sample_count,
        "avgFrontMatch": avg_front_match,
        "avgBackMatch": avg_back_match,
        "avgTotalMatch": avg_total_match,
        "bestTotalMatch": best_total_match,
        "bestCase": best_case_payload,
        "hitDistribution": hit_distribution_payload,
        "recentCases": recent_cases,
        "historyResults": history_results,
        "sample_count": sample_count,
        "test_count": sample_count,
        "avg_front_match": avg_front_match,
        "avg_back_match": avg_back_match,
        "avg_total_match": avg_total_match,
        "best_total_match": best_total_match,
        "best_case": best_case_payload,
        "hit_distribution": hit_distribution_payload,
        "recent_cases": recent_cases,
        "history_results": history_results,
    }


def _analyze_dlt_normalized(normalized: list[dict[str, Any]], include_validation: bool = True) -> dict[str, Any]:
    if not normalized:
        return {"recordCount": 0, "message": "当前接口没有返回可分析的大乐透历史数据。"}

    front_counter = Counter()
    back_counter = Counter()
    front_zone_counter = Counter()
    back_zone_counter = Counter()
    front_sum_counter = Counter()
    back_sum_counter = Counter()
    odd_even_counter = Counter()

    for record in normalized:
        front = record["front"]
        back = record["back"]
        front_counter.update(front)
        back_counter.update(back)

        front_zone_pattern = (
            sum(1 for number in front if 1 <= number <= 12),
            sum(1 for number in front if 13 <= number <= 24),
            sum(1 for number in front if 25 <= number <= 35),
        )
        back_zone_pattern = (
            sum(1 for number in back if 1 <= number <= 6),
            sum(1 for number in back if 7 <= number <= 12),
        )
        front_zone_counter[front_zone_pattern] += 1
        back_zone_counter[back_zone_pattern] += 1
        front_sum_counter[sum(front)] += 1
        back_sum_counter[sum(back)] += 1
        odd_even_counter[
            f"{sum(number % 2 for number in front)}:{5 - sum(number % 2 for number in front)}"
        ] += 1

    latest = normalized[0]
    top_front_pool = [number for number, _ in front_counter.most_common(10)]
    top_back_pool = [number for number, _ in back_counter.most_common(6)]
    latest_front_set = set(latest["front"])

    top_combinations = []
    for front_combo in combinations(top_front_pool, 5):
        front_list = sorted(front_combo)
        front_zone_pattern = (
            sum(1 for number in front_list if 1 <= number <= 12),
            sum(1 for number in front_list if 13 <= number <= 24),
            sum(1 for number in front_list if 25 <= number <= 35),
        )
        front_zone_score = front_zone_counter[front_zone_pattern] / max(len(normalized), 1)
        front_repeat_score = len(set(front_list) & latest_front_set) / 5
        front_sum_score = front_sum_counter[sum(front_list)] / max(len(normalized), 1)
        front_frequency_score = sum(front_counter[number] for number in front_list) / max(sum(front_counter.values()), 1)

        for back_combo in combinations(top_back_pool, 2):
            back_list = sorted(back_combo)
            back_zone_pattern = (
                sum(1 for number in back_list if 1 <= number <= 6),
                sum(1 for number in back_list if 7 <= number <= 12),
            )
            back_zone_score = back_zone_counter[back_zone_pattern] / max(len(normalized), 1)
            back_sum_score = back_sum_counter[sum(back_list)] / max(len(normalized), 1)
            back_frequency_score = sum(back_counter[number] for number in back_list) / max(sum(back_counter.values()), 1)

            total_score = (
                front_frequency_score * 0.35
                + back_frequency_score * 0.20
                + front_zone_score * 0.15
                + back_zone_score * 0.10
                + front_sum_score * 0.10
                + back_sum_score * 0.05
                + front_repeat_score * 0.05
            )
            top_combinations.append(
                {
                    "front": front_list,
                    "back": back_list,
                    "score": round(total_score, 6),
                    "frontZonePattern": list(front_zone_pattern),
                    "backZonePattern": list(back_zone_pattern),
                }
            )

    top_combinations.sort(key=lambda item: item["score"], reverse=True)
    front_omission_top = _build_omission([record["front"] for record in normalized], range(1, 36))
    back_omission_top = _build_omission([record["back"] for record in normalized], range(1, 13))
    models_performance = _build_models_performance(top_combinations[:10])
    performance_stats = _build_performance_stats(normalized, top_front_pool, top_back_pool, top_combinations)
    result = {
        "recordCount": len(normalized),
        "latestPeriod": latest["period"],
        "latestFront": latest["front"],
        "latestBack": latest["back"],
        "frontFrequencyTop": [[number, count] for number, count in front_counter.most_common(12)],
        "backFrequencyTop": [[number, count] for number, count in back_counter.most_common(8)],
        "frontZoneDistribution": [[list(pattern), count] for pattern, count in front_zone_counter.most_common(6)],
        "backZoneDistribution": [[list(pattern), count] for pattern, count in back_zone_counter.most_common(4)],
        "oddEvenDistribution": [[pattern, count] for pattern, count in odd_even_counter.most_common(6)],
        "frontSumDistributionTop": [[value, count] for value, count in front_sum_counter.most_common(8)],
        "backSumDistributionTop": [[value, count] for value, count in back_sum_counter.most_common(6)],
        "frontOmissionTop": front_omission_top,
        "backOmissionTop": back_omission_top,
        "recentRepeatSummary": _build_recent_repeat_summary(normalized),
        "modelsPerformance": models_performance,
        "performanceStats": performance_stats,
        "topCombinations": top_combinations[:10],
    }
    if include_validation:
        result["validation"] = _build_validation(normalized)
    return result


def analyze_dlt_records(records: list[dict[str, Any]], include_validation: bool = True) -> dict[str, Any]:
    normalized = _normalize_records(records)
    return _analyze_dlt_normalized(normalized, include_validation=include_validation)
