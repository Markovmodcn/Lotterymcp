from __future__ import annotations

import math
from collections import Counter
from itertools import combinations
from typing import Any


TOTAL_SSQ_COMBINATIONS = math.comb(33, 6) * 16
PRIME_REDS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}


def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for record in records:
        numbers = record.get("numbers_list", [])
        if len(numbers) < 7:
            continue
        reds = sorted(int(number) for number in numbers[:6])
        blue = int(numbers[6])
        normalized.append(
            {
                "period": str(record.get("period", "")),
                "reds": reds,
                "blue": blue,
            }
        )
    return normalized


def _repeat_probability(sample_size: int) -> float:
    if sample_size <= 1:
        return 0.0

    probability_no_repeat = 1.0
    for index in range(sample_size):
        probability_no_repeat *= max(TOTAL_SSQ_COMBINATIONS - index, 1) / TOTAL_SSQ_COMBINATIONS
    return max(0.0, 1.0 - probability_no_repeat)


def _red_overlap_probability(min_overlap: int) -> float:
    denominator = math.comb(33, 6)
    probability = 0.0
    for overlap in range(min_overlap, 7):
        probability += math.comb(6, overlap) * math.comb(27, 6 - overlap) / denominator
    return probability


def _find_exact_matches(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index_by_key: dict[tuple[tuple[int, ...], int], dict[str, Any]] = {}
    matches: list[dict[str, Any]] = []

    for record in records:
        key = (tuple(record["reds"]), record["blue"])
        previous = index_by_key.get(key)
        if previous:
            matches.append(
                {
                    "period1": previous["period"],
                    "period2": record["period"],
                    "reds": record["reds"],
                    "blue": record["blue"],
                }
            )
        else:
            index_by_key[key] = record
    return matches


def _find_near_matches(records: list[dict[str, Any]], threshold: int = 4) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for left_index in range(len(records)):
        left = records[left_index]
        left_reds = set(left["reds"])
        for right_index in range(left_index + 1, len(records)):
            right = records[right_index]
            red_overlap = len(left_reds & set(right["reds"]))
            if red_overlap < threshold:
                continue
            blue_match = int(left["blue"] == right["blue"])
            matches.append(
                {
                    "period1": left["period"],
                    "period2": right["period"],
                    "redOverlap": red_overlap,
                    "blueMatch": blue_match,
                    "totalOverlap": red_overlap + blue_match,
                }
            )

    matches.sort(key=lambda item: (item["redOverlap"], item["blueMatch"]), reverse=True)
    return matches[:10]


def _build_pattern_evolution(records: list[dict[str, Any]]) -> dict[str, Any]:
    tail_diversity_counter = Counter()
    prime_ratio_counter = Counter()
    span_counter = Counter()
    recent_red_counter = Counter()
    previous_red_counter = Counter()

    recent_slice = records[: min(20, len(records))]
    previous_slice = records[min(20, len(records)) : min(60, len(records))]

    for record in records:
        reds = record["reds"]
        tail_diversity_counter[len({red % 10 for red in reds})] += 1
        prime_ratio_counter[sum(1 for red in reds if red in PRIME_REDS)] += 1
        span_counter[max(reds) - min(reds)] += 1

    for record in recent_slice:
        recent_red_counter.update(record["reds"])
    for record in previous_slice:
        previous_red_counter.update(record["reds"])

    hot_shift = []
    candidates = set(recent_red_counter) | set(previous_red_counter)
    for number in candidates:
        shift = recent_red_counter[number] - previous_red_counter[number]
        if shift != 0:
            hot_shift.append([number, shift])
    hot_shift.sort(key=lambda item: abs(item[1]), reverse=True)

    return {
        "tailDiversityDistribution": [[value, count] for value, count in tail_diversity_counter.most_common(6)],
        "primeRatioDistribution": [[value, count] for value, count in prime_ratio_counter.most_common(6)],
        "spanDistributionTop": [[value, count] for value, count in span_counter.most_common(8)],
        "recentHotShift": hot_shift[:10],
    }


def _find_success_case_samples(records: list[dict[str, Any]], min_red_matches: int = 4) -> list[dict[str, Any]]:
    if len(records) < 6:
        return []

    success_cases = []
    window_size = min(20, max(5, len(records) // 3))
    for index in range(len(records) - window_size - 1):
        history_slice = records[index + 1 : index + 1 + window_size]
        target = records[index]
        red_counter = Counter()
        blue_counter = Counter()
        for record in history_slice:
            red_counter.update(record["reds"])
            blue_counter.update([record["blue"]])

        predicted_reds = [number for number, _ in red_counter.most_common(10)]
        predicted_blues = [number for number, _ in blue_counter.most_common(3)]
        red_matches = len(set(predicted_reds) & set(target["reds"]))
        blue_hit = target["blue"] in predicted_blues
        if red_matches >= min_red_matches:
            success_cases.append(
                {
                    "targetPeriod": target["period"],
                    "windowSize": window_size,
                    "redMatches": red_matches,
                    "blueIncluded": blue_hit,
                    "predictedRedPool": predicted_reds[:10],
                }
            )
        if len(success_cases) >= 8:
            break
    return success_cases


def _find_true_success_cases(records: list[dict[str, Any]], min_red_matches: int = 4) -> list[dict[str, Any]]:
    if len(records) < 8:
        return []

    success_cases = []
    window_size = min(20, max(6, len(records) // 3))
    for index in range(len(records) - window_size - 1):
        history_slice = records[index + 1 : index + 1 + window_size]
        target = records[index]
        red_counter = Counter()
        blue_counter = Counter()
        for record in history_slice:
            red_counter.update(record["reds"])
            blue_counter.update([record["blue"]])

        predicted_red_pool = [number for number, _ in red_counter.most_common(10)]
        predicted_blue_pool = [number for number, _ in blue_counter.most_common(3)]
        red_matches = len(set(predicted_red_pool) & set(target["reds"]))
        blue_hit = target["blue"] in predicted_blue_pool
        if red_matches >= min_red_matches:
            success_cases.append(
                {
                    "method": "time-series-window",
                    "targetPeriod": target["period"],
                    "windowSize": window_size,
                    "redMatches": red_matches,
                    "blueIncluded": blue_hit,
                    "predictedRedPool": predicted_red_pool,
                    "predictedBluePool": predicted_blue_pool,
                }
            )
        if len(success_cases) >= 10:
            break
    return success_cases


def _build_probability_model(records: list[dict[str, Any]], near_matches: list[dict[str, Any]]) -> dict[str, Any]:
    pair_count = max(len(records) * (len(records) - 1) // 2, 1)
    near_match_rate = round(len(near_matches) / pair_count, 10)
    return {
        "exactRepeatProbability": round(_repeat_probability(len(records)), 10),
        "redOverlap4PlusProbability": round(_red_overlap_probability(4), 10),
        "redOverlap5PlusProbability": round(_red_overlap_probability(5), 10),
        "blueMatchProbability": round(1 / 16, 10),
        "historicalNearMatchRate": near_match_rate,
    }


def _build_markov_transitions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transition_counter = Counter()
    source_counter = Counter()
    for record in records:
        reds = record["reds"]
        for left, right in zip(reds, reds[1:]):
            transition_counter[(left, right)] += 1
            source_counter[left] += 1
    transitions = []
    for (source, target), count in transition_counter.items():
        probability = count / max(source_counter[source], 1)
        transitions.append(
            {
                "from": source,
                "to": target,
                "count": count,
                "probability": round(probability, 6),
            }
        )
    transitions.sort(key=lambda item: (item["probability"], item["count"]), reverse=True)
    return transitions[:10]


def _build_cluster_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cluster_map: dict[tuple[tuple[int, int, int], str], list[dict[str, Any]]] = {}
    for record in records:
        reds = record["reds"]
        zone_pattern = (
            sum(1 for red in reds if 1 <= red <= 11),
            sum(1 for red in reds if 12 <= red <= 22),
            sum(1 for red in reds if 23 <= red <= 33),
        )
        odd_count = sum(red % 2 for red in reds)
        odd_even = f"{odd_count}:{6 - odd_count}"
        cluster_map.setdefault((zone_pattern, odd_even), []).append(record)

    clusters = []
    for index, ((zone_pattern, odd_even), items) in enumerate(
        sorted(cluster_map.items(), key=lambda item: len(item[1]), reverse=True)[:8],
        1,
    ):
        red_counter = Counter()
        for item in items:
            red_counter.update(item["reds"])
        clusters.append(
            {
                "clusterId": index,
                "size": len(items),
                "zonePattern": list(zone_pattern),
                "oddEven": odd_even,
                "topReds": [number for number, _ in red_counter.most_common(5)],
                "samplePeriods": [item["period"] for item in items[:5]],
            }
        )
    return clusters


def _build_cluster_stats(cluster_summary: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        str(item["clusterId"]): {
            "size": item["size"],
            "topReds": item["topReds"],
            "samplePeriods": item["samplePeriods"],
            "zonePattern": item["zonePattern"],
            "oddEven": item["oddEven"],
        }
        for item in cluster_summary
    }


def _build_simulation_results(probability_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "exactMatches": probability_model["exactRepeatProbability"],
        "fivePlusMatches": probability_model["redOverlap5PlusProbability"],
        "fourPlusMatches": probability_model["redOverlap4PlusProbability"],
        "blueMatchProbability": probability_model["blueMatchProbability"],
    }


def _build_evolutionary_pattern(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) < 2:
        return {
            "closestPeriods": [],
            "intersection": 0,
            "union": 0,
            "jaccardSimilarity": 0.0,
            "mutationNumbers": [],
        }

    best_pair = None
    best_score = -1.0
    for left_index in range(len(records) - 1):
        left = set(records[left_index]["reds"])
        for right_index in range(left_index + 1, len(records)):
            right = set(records[right_index]["reds"])
            union = left | right
            if not union:
                continue
            intersection = left & right
            score = len(intersection) / len(union)
            if score > best_score:
                best_score = score
                best_pair = (left_index, right_index, intersection, union)

    if best_pair is None:
        return {
            "closestPeriods": [],
            "intersection": 0,
            "union": 0,
            "jaccardSimilarity": 0.0,
            "mutationNumbers": [],
        }

    left_index, right_index, intersection, union = best_pair
    left_reds = set(records[left_index]["reds"])
    right_reds = set(records[right_index]["reds"])
    mutation_numbers = sorted(left_reds.symmetric_difference(right_reds))
    return {
        "closestPeriods": [records[left_index]["period"], records[right_index]["period"]],
        "intersection": len(intersection),
        "union": len(union),
        "jaccardSimilarity": round(best_score, 6),
        "mutationNumbers": mutation_numbers,
    }


def analyze_ssq_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = _normalize_records(records)
    if not normalized:
        return {"recordCount": 0, "message": "当前接口没有返回可分析的双色球历史数据。"}

    red_counter = Counter()
    blue_counter = Counter()
    zone_counter = Counter()
    odd_even_counter = Counter()
    sum_counter = Counter()

    for record in normalized:
        reds = record["reds"]
        red_counter.update(reds)
        blue_counter.update([record["blue"]])

        zone_pattern = (
            sum(1 for red in reds if 1 <= red <= 11),
            sum(1 for red in reds if 12 <= red <= 22),
            sum(1 for red in reds if 23 <= red <= 33),
        )
        zone_counter[zone_pattern] += 1
        odd_count = sum(red % 2 for red in reds)
        odd_even_counter[f"{odd_count}:{6 - odd_count}"] += 1
        sum_counter[sum(reds)] += 1

    recent_red_sets = [set(record["reds"]) for record in normalized[:10]]
    top_red_pool = [number for number, _ in red_counter.most_common(10)]
    top_blue_pool = [number for number, _ in blue_counter.most_common(4)]

    recommendations = []
    for red_combo in combinations(top_red_pool, 6):
        red_list = sorted(red_combo)
        zone_pattern = (
            sum(1 for red in red_list if 1 <= red <= 11),
            sum(1 for red in red_list if 12 <= red <= 22),
            sum(1 for red in red_list if 23 <= red <= 33),
        )
        zone_score = zone_counter[zone_pattern] / max(len(normalized), 1)
        overlap_score = sum(len(set(red_list) & recent) for recent in recent_red_sets) / max(len(recent_red_sets), 1)
        red_score = sum(red_counter[number] for number in red_list) / max(sum(red_counter.values()), 1)

        for blue in top_blue_pool:
            blue_score = blue_counter[blue] / max(sum(blue_counter.values()), 1)
            total_score = red_score * 0.5 + zone_score * 0.2 + overlap_score * 0.2 + blue_score * 0.1
            recommendations.append(
                {
                    "reds": red_list,
                    "blue": blue,
                    "score": round(total_score, 6),
                    "zonePattern": list(zone_pattern),
                    "sum": sum(red_list),
                }
            )

    recommendations.sort(key=lambda item: item["score"], reverse=True)

    exact_matches = _find_exact_matches(normalized)
    near_matches = _find_near_matches(normalized)
    true_success_cases = _find_true_success_cases(normalized)
    probability_model = _build_probability_model(normalized, near_matches)
    cluster_summary = _build_cluster_summary(normalized)
    latest = normalized[0]
    return {
        "recordCount": len(normalized),
        "latestPeriod": latest["period"],
        "latestReds": latest["reds"],
        "latestBlue": latest["blue"],
        "theoreticalCombinations": TOTAL_SSQ_COMBINATIONS,
        "theoreticalRepeatProbability": round(_repeat_probability(len(normalized)), 10),
        "exactMatches": exact_matches,
        "nearMatches": near_matches,
        "patternEvolution": _build_pattern_evolution(normalized),
        "successCaseSamples": _find_success_case_samples(normalized),
        "trueSuccessCases": true_success_cases,
        "probabilityModel": probability_model,
        "markovTransitionsTop": _build_markov_transitions(normalized),
        "clusterSummary": cluster_summary,
        "clusterStats": _build_cluster_stats(cluster_summary),
        "simulationResults": _build_simulation_results(probability_model),
        "evolutionaryPattern": _build_evolutionary_pattern(normalized),
        "redFrequencyTop": [[number, count] for number, count in red_counter.most_common(10)],
        "blueFrequencyTop": [[number, count] for number, count in blue_counter.most_common(8)],
        "zoneDistribution": [[list(pattern), count] for pattern, count in zone_counter.most_common(8)],
        "oddEvenDistribution": [[pattern, count] for pattern, count in odd_even_counter.most_common(6)],
        "sumDistributionTop": [[value, count] for value, count in sum_counter.most_common(8)],
        "topRecommendations": recommendations[:8],
    }
