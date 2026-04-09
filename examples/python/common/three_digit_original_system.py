from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ThreeDigitConfig:
    lottery_type: str
    display_name: str
    output_path: Path
    history_file: Path
    success_cases_file: Path
    reverse_min_history: int = 100
    reverse_history_lengths: tuple[int, ...] = (100, 200, 500, 1000)
    total_tickets: int = 10
    bet_per_ticket: int = 2
    total_budget: int = 20
    direct_ratio: float = 0.4
    group3_ratio: float = 0.4
    group6_ratio: float = 0.2


def _digits_from_combo(combo: str | list[int]) -> list[int]:
    if isinstance(combo, list):
        return [int(item) for item in combo]
    return [int(digit) for digit in str(combo).zfill(3)]


def _to_native(value: Any) -> Any:
    if isinstance(value, dict):
        return {_to_native(key): _to_native(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_native(item) for item in value]
    if isinstance(value, tuple):
        return [_to_native(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _get_number_type(combo: str | list[int]) -> str:
    digits = _digits_from_combo(combo)
    unique_digits = len(set(digits))
    if unique_digits == 1:
        return "豹子"
    if unique_digits == 2:
        return "组三"
    return "组六"


def _with_prediction_aliases(prediction: dict[str, Any]) -> dict[str, Any]:
    payload = dict(prediction)
    if "oddEven" in payload and "odd_even" not in payload:
        payload["odd_even"] = payload["oddEven"]
    if "pairDigit" in payload and "pair_digit" not in payload:
        payload["pair_digit"] = payload["pairDigit"]
    if "singleDigit" in payload and "single_digit" not in payload:
        payload["single_digit"] = payload["singleDigit"]
    return payload


def _with_success_case_aliases(success_case: dict[str, Any]) -> dict[str, Any]:
    payload = dict(success_case)
    aliases = {
        "targetPeriod": "target_period",
        "targetCombo": "target_combo",
        "targetType": "target_type",
        "historyLength": "history_length",
        "oddEven": "odd_even",
    }
    for modern_key, legacy_key in aliases.items():
        if modern_key in payload and legacy_key not in payload:
            payload[legacy_key] = payload[modern_key]
    return payload


def _with_reverse_analysis_aliases(result: dict[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    aliases = {
        "totalCases": "total_cases",
        "bestHistoryLength": "best_history_length",
        "typeDistribution": "type_distribution",
        "rankDistribution": "rank_distribution",
        "sumDistribution": "sum_distribution",
        "digitDistribution": "digit_distribution",
        "successRate": "success_rate",
        "averageRank": "average_rank",
    }
    for modern_key, legacy_key in aliases.items():
        if modern_key in payload and legacy_key not in payload:
            payload[legacy_key] = payload[modern_key]
    if "successRateByHistory" not in payload:
        payload["successRateByHistory"] = {}
    if "success_rate_by_history" not in payload:
        payload["success_rate_by_history"] = payload["successRateByHistory"]
    return payload


def _build_validation_result(
    exact_hits: int,
    two_digit_hits: int,
    test_count: int,
    group3_hits: int,
    group6_hits: int,
    history_length: int,
) -> dict[str, Any]:
    exact_hit_rate = round(exact_hits / test_count * 100, 4) if test_count else 0.0
    two_digit_hit_rate = round(two_digit_hits / test_count * 100, 4) if test_count else 0.0
    return {
        "historyLength": history_length,
        "windowSize": history_length,
        "testCount": test_count,
        "testedPeriods": test_count,
        "exactHits": exact_hits,
        "twoDigitHits": two_digit_hits,
        "group3Hits": group3_hits,
        "group6Hits": group6_hits,
        "exactRate": exact_hit_rate,
        "twoDigitRate": two_digit_hit_rate,
        "exactHitRate": exact_hit_rate,
        "twoDigitHitRate": two_digit_hit_rate,
        "history_length": history_length,
        "window_size": history_length,
        "test_count": test_count,
        "tested_periods": test_count,
        "exact_hits": exact_hits,
        "two_digit_hits": two_digit_hits,
        "group3_hits": group3_hits,
        "group6_hits": group6_hits,
        "exact_rate": exact_hit_rate,
        "two_digit_rate": two_digit_hit_rate,
        "exact_hit_rate": exact_hit_rate,
        "two_digit_hit_rate": two_digit_hit_rate,
    }


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    normalized_rows = []
    for record in reversed(records):
        numbers = [int(item) for item in record.get("numbers_list", [])[:3]]
        if len(numbers) != 3:
            continue
        normalized_rows.append(
            {
                "期号": str(record.get("period", "")),
                "百位": numbers[0],
                "十位": numbers[1],
                "个位": numbers[2],
            }
        )
    return pd.DataFrame(normalized_rows)


class ReverseAnalyzer:
    def __init__(self, data: pd.DataFrame, config: ThreeDigitConfig):
        self.data = data.reset_index(drop=True)
        self.config = config
        self.total_periods = len(data)
        self.success_cases: list[dict[str, Any]] = []
        self.analysis_results: dict[str, Any] = {}
        self.type_counts = Counter()
        self.history_length_counts = Counter()
        self.rank_counts = Counter()
        self.sum_counts = Counter()
        self.digit_counts = Counter()

    def get_number_type(self, combo: str | list[int]) -> str:
        return _get_number_type(combo)

    def generate_all_combinations(self) -> list[str]:
        return [f"{i}{j}{k}" for i in range(10) for j in range(10) for k in range(10)]

    def get_odd_even_ratio(self, combo: str | list[int]) -> str:
        digits = _digits_from_combo(combo)
        odd_count = sum(digit % 2 for digit in digits)
        return f"{odd_count}:{3 - odd_count}"

    def calculate_combo_score(self, combo: str, historical_data: pd.DataFrame) -> float:
        digits = _digits_from_combo(combo)
        total = sum(digits)
        score = 0.0

        pos_freq = 0.0
        for index, digit in enumerate(digits):
            pos = ["百位", "十位", "个位"][index]
            pos_data = historical_data[pos].values
            pos_freq += np.sum(pos_data == digit) / len(pos_data)
        score += (pos_freq / 3) * 0.25

        sums = historical_data["百位"] + historical_data["十位"] + historical_data["个位"]
        score += (np.sum(sums == total) / len(sums)) * 0.2

        all_digits: list[int] = []
        for pos in ["百位", "十位", "个位"]:
            all_digits.extend(historical_data[pos].values.tolist())
        digit_freq = sum(all_digits.count(digit) / len(all_digits) for digit in digits)
        score += (digit_freq / 3) * 0.2

        odd_even = self.get_odd_even_ratio(combo)
        odd_even_history = []
        for _, row in historical_data.iterrows():
            odd = sum([int(row["百位"]) % 2, int(row["十位"]) % 2, int(row["个位"]) % 2])
            odd_even_history.append(f"{odd}:{3 - odd}")
        score += (odd_even_history.count(odd_even) / len(odd_even_history)) * 0.15

        span = max(digits) - min(digits)
        spans = []
        for _, row in historical_data.iterrows():
            row_digits = [int(row["百位"]), int(row["十位"]), int(row["个位"])]
            spans.append(max(row_digits) - min(row_digits))
        score += (spans.count(span) / len(spans)) * 0.1

        combo_type = self.get_number_type(combo)
        types = []
        for _, row in historical_data.iterrows():
            combo_row = f"{int(row['百位'])}{int(row['十位'])}{int(row['个位'])}"
            types.append(self.get_number_type(combo_row))
        score += (types.count(combo_type) / len(types)) * 0.1
        return score

    def perform_reverse_analysis(self) -> list[dict[str, Any]]:
        for current_idx in range(self.config.reverse_min_history, self.total_periods):
            target_row = self.data.iloc[current_idx]
            target_combo = f"{int(target_row['百位'])}{int(target_row['十位'])}{int(target_row['个位'])}"
            target_type = self.get_number_type(target_combo)
            if target_type == "豹子":
                continue

            for history_length in self.config.reverse_history_lengths:
                if history_length > current_idx:
                    continue
                start_idx = current_idx - history_length
                historical_data = self.data.iloc[start_idx:current_idx]
                scored_combos = []
                for combo in self.generate_all_combinations():
                    scored_combos.append((combo, self.calculate_combo_score(combo, historical_data)))
                scored_combos.sort(key=lambda item: item[1], reverse=True)

                for rank, (combo, score) in enumerate(scored_combos[:100], 1):
                    if combo == target_combo:
                        success_case = {
                            "periodIndex": current_idx,
                            "targetPeriod": str(target_row.get("期号", "")),
                            "targetCombo": target_combo,
                            "targetType": target_type,
                            "historyLength": history_length,
                            "rank": rank,
                            "score": round(score, 6),
                            "sum": sum(int(digit) for digit in target_combo),
                            "oddEven": self.get_odd_even_ratio(target_combo),
                        }
                        period_info = {
                            "period": success_case["targetPeriod"],
                            "historyLength": history_length,
                            "periodIndex": current_idx,
                        }
                        success_case["periodInfo"] = period_info
                        success_case["period_info"] = period_info
                        self.success_cases.append(success_case)
                        self.type_counts[target_type] += 1
                        self.history_length_counts[history_length] += 1
                        self.rank_counts[rank] += 1
                        self.sum_counts[success_case["sum"]] += 1
                        for digit in target_combo:
                            self.digit_counts[int(digit)] += 1
                        break

                if self.success_cases and self.success_cases[-1]["periodIndex"] == current_idx:
                    break

        self.success_cases = [_with_success_case_aliases(case) for case in self.success_cases]
        self.analyze_results()
        return self.success_cases

    def analyze_results(self) -> dict[str, Any]:
        if not self.success_cases:
            self.analysis_results = _with_reverse_analysis_aliases(
                {
                    "totalCases": 0,
                    "bestHistoryLength": None,
                    "typeDistribution": {},
                    "rankDistribution": {},
                    "sumDistribution": {},
                    "digitDistribution": {},
                    "averageRank": 0,
                }
            )
            return self.analysis_results

        total_tested = max(self.total_periods - self.config.reverse_min_history, 1)
        best_history = self.history_length_counts.most_common(1)[0][0] if self.history_length_counts else None
        self.analysis_results = _with_reverse_analysis_aliases(
            {
                "totalCases": len(self.success_cases),
                "bestHistoryLength": best_history,
                "typeDistribution": dict(self.type_counts),
                "rankDistribution": dict(self.rank_counts),
                "sumDistribution": dict(self.sum_counts),
                "digitDistribution": dict(self.digit_counts),
                "successRate": round(len(self.success_cases) / total_tested * 100, 4),
                "averageRank": round(sum(case["rank"] for case in self.success_cases) / len(self.success_cases), 4),
            }
        )
        return self.analysis_results

    def save_analysis(self) -> None:
        payload = _to_native(
            {
                "analysisDate": datetime.now().isoformat(),
                "totalPeriods": self.total_periods,
                "successCases": self.success_cases,
                "analysisResults": self.analysis_results,
            }
        )
        self.config.success_cases_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.success_cases_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class PredictionGenerator:
    def __init__(self, data: pd.DataFrame, config: ThreeDigitConfig, reverse_analysis: dict[str, Any] | None = None):
        self.data = data.reset_index(drop=True)
        self.config = config
        self.total_periods = len(data)
        self.reverse_analysis = reverse_analysis or {}
        self.best_history_length = int(self.reverse_analysis.get("bestHistoryLength") or 500)
        self.type_ratios = self.calculate_type_ratios()

    def calculate_type_ratios(self) -> dict[str, float]:
        type_dist = self.reverse_analysis.get("typeDistribution") or {}
        total = sum(type_dist.values())
        if total == 0:
            return {
                "直选": self.config.direct_ratio,
                "组三": self.config.group3_ratio,
                "组六": self.config.group6_ratio,
            }
        group3_ratio = type_dist.get("组三", 0) / total
        group6_ratio = type_dist.get("组六", 0) / total
        direct_ratio = 1.0 - (group3_ratio + group6_ratio) * 0.5
        total_ratio = direct_ratio + group3_ratio + group6_ratio
        return {
            "直选": direct_ratio / total_ratio,
            "组三": group3_ratio / total_ratio,
            "组六": group6_ratio / total_ratio,
        }

    def get_number_type(self, combo: str | list[int]) -> str:
        return _get_number_type(combo)

    def get_odd_even_ratio(self, combo: str | list[int]) -> str:
        digits = _digits_from_combo(combo)
        odd_count = sum(digit % 2 for digit in digits)
        return f"{odd_count}:{3 - odd_count}"

    def generate_predictions(self) -> list[dict[str, Any]]:
        historical_data = self.data.tail(self.best_history_length)
        direct_count = int(self.config.total_tickets * self.type_ratios["直选"])
        group3_count = int(self.config.total_tickets * self.type_ratios["组三"])
        group6_count = self.config.total_tickets - direct_count - group3_count

        all_predictions = []
        all_predictions.extend(self.generate_direct_predictions(historical_data, direct_count))
        all_predictions.extend(self.generate_group3_predictions(historical_data, group3_count))
        all_predictions.extend(self.generate_group6_predictions(historical_data, group6_count))
        all_predictions.sort(key=lambda item: item["score"], reverse=True)
        return all_predictions[: self.config.total_tickets]

    def generate_direct_predictions(self, historical_data: pd.DataFrame, count: int) -> list[dict[str, Any]]:
        predictions = []
        position_hot: dict[str, list[int]] = {}
        for pos in ["百位", "十位", "个位"]:
            pos_counter = Counter(historical_data[pos].values)
            position_hot[pos] = [num for num, _ in pos_counter.most_common(4)]

        generated = set()
        for hundred in position_hot["百位"]:
            for ten in position_hot["十位"]:
                for unit in position_hot["个位"]:
                    combo = f"{hundred}{ten}{unit}"
                    if combo in generated:
                        continue
                    predictions.append(
                        {
                            "combo": combo,
                            "type": "直选",
                            "score": round(self.score_direct_selection(combo, historical_data), 6),
                            "hundred": hundred,
                            "ten": ten,
                            "unit": unit,
                            "sum": hundred + ten + unit,
                            "oddEven": self.get_odd_even_ratio(combo),
                            "odd_even": self.get_odd_even_ratio(combo),
                        }
                    )
                    generated.add(combo)
        predictions.sort(key=lambda item: item["score"], reverse=True)
        return predictions[:count]

    def generate_group3_predictions(self, historical_data: pd.DataFrame, count: int) -> list[dict[str, Any]]:
        predictions = []
        pair_digits: list[int] = []
        for _, row in historical_data.iterrows():
            combo = f"{int(row['百位'])}{int(row['十位'])}{int(row['个位'])}"
            if self.get_number_type(combo) == "组三":
                digit_counts = Counter(_digits_from_combo(combo))
                for digit, cnt in digit_counts.items():
                    if cnt == 2:
                        pair_digits.append(digit)

        pair_counter = Counter(pair_digits)
        hot_pair_digits = [digit for digit, _ in pair_counter.most_common(8)]
        all_digits: list[int] = []
        for pos in ["百位", "十位", "个位"]:
            all_digits.extend(historical_data[pos].values.tolist())
        digit_counter = Counter(all_digits)
        hot_digits = [digit for digit, _ in digit_counter.most_common(12)]

        generated = set()
        for pair_digit in hot_pair_digits[:5]:
            for single_digit in hot_digits[:10]:
                if single_digit == pair_digit:
                    continue
                combos = [
                    f"{pair_digit}{pair_digit}{single_digit}",
                    f"{pair_digit}{single_digit}{pair_digit}",
                    f"{single_digit}{pair_digit}{pair_digit}",
                ]
                for combo in combos:
                    if combo in generated:
                        continue
                    predictions.append(
                        {
                            "combo": combo,
                            "type": "组三",
                            "score": round(self.score_group3(combo, historical_data), 6),
                            "pairDigit": pair_digit,
                            "singleDigit": single_digit,
                            "sum": sum(int(digit) for digit in combo),
                            "oddEven": self.get_odd_even_ratio(combo),
                            "odd_even": self.get_odd_even_ratio(combo),
                        }
                    )
                    generated.add(combo)

        predictions.sort(key=lambda item: item["score"], reverse=True)
        return predictions[:count]

    def generate_group6_predictions(self, historical_data: pd.DataFrame, count: int) -> list[dict[str, Any]]:
        predictions = []
        all_digits: list[int] = []
        for pos in ["百位", "十位", "个位"]:
            all_digits.extend(historical_data[pos].values.tolist())
        digit_counter = Counter(all_digits)
        hot_digits = [digit for digit, _ in digit_counter.most_common(10)]

        digit_distribution = self.reverse_analysis.get("digitDistribution") or {}
        if digit_distribution:
            reverse_hot_digits = [digit for digit, _ in sorted(digit_distribution.items(), key=lambda item: item[1], reverse=True)[:10]]
            combined_digits = list(dict.fromkeys(hot_digits[:5] + reverse_hot_digits[:5]))
        else:
            combined_digits = hot_digits

        generated = set()
        for i in range(len(combined_digits)):
            for j in range(i + 1, len(combined_digits)):
                for k in range(j + 1, len(combined_digits)):
                    a, b, c = combined_digits[i], combined_digits[j], combined_digits[k]
                    combo = f"{a}{b}{c}"
                    if combo in generated:
                        continue
                    predictions.append(
                        {
                            "combo": combo,
                            "type": "组六",
                            "score": round(self.score_group6(combo, historical_data), 6),
                            "sum": a + b + c,
                            "oddEven": self.get_odd_even_ratio(combo),
                            "odd_even": self.get_odd_even_ratio(combo),
                        }
                    )
                    generated.add(combo)

        predictions.sort(key=lambda item: item["score"], reverse=True)
        return predictions[:count]

    def score_direct_selection(self, combo: str, historical_data: pd.DataFrame) -> float:
        digits = _digits_from_combo(combo)
        score = 0.0

        pos_score = 0.0
        for index, digit in enumerate(digits):
            pos = ["百位", "十位", "个位"][index]
            pos_data = historical_data[pos].values
            pos_score += np.sum(pos_data == digit) / len(pos_data)
        score += (pos_score / 3) * 0.3

        total = sum(digits)
        sums = historical_data["百位"] + historical_data["十位"] + historical_data["个位"]
        score += (np.sum(sums == total) / len(sums)) * 0.2

        combos_history = [
            f"{int(row['百位'])}{int(row['十位'])}{int(row['个位'])}"
            for _, row in historical_data.iterrows()
        ]
        score += (combos_history.count(combo) / len(combos_history)) * 0.2

        odd_even = self.get_odd_even_ratio(combo)
        odd_even_history = []
        for _, row in historical_data.iterrows():
            odd = sum([int(row["百位"]) % 2, int(row["十位"]) % 2, int(row["个位"]) % 2])
            odd_even_history.append(f"{odd}:{3 - odd}")
        score += (odd_even_history.count(odd_even) / len(odd_even_history)) * 0.15

        digit_distribution = self.reverse_analysis.get("digitDistribution") or {}
        sum_distribution = self.reverse_analysis.get("sumDistribution") or {}
        for digit in digits:
            if str(digit) in digit_distribution or digit in digit_distribution:
                score += 0.02
        if str(total) in sum_distribution or total in sum_distribution:
            score += 0.05
        return score

    def score_group3(self, combo: str, historical_data: pd.DataFrame) -> float:
        digits = _digits_from_combo(combo)
        score = 0.0
        digit_counts = Counter(digits)
        pair_digit = None
        single_digit = None
        for digit, count in digit_counts.items():
            if count == 2:
                pair_digit = digit
            else:
                single_digit = digit
        if pair_digit is None or single_digit is None:
            return score

        pair_freq = 0.0
        single_freq = 0.0
        for pos in ["百位", "十位", "个位"]:
            pos_data = historical_data[pos].values
            pair_freq += np.sum(pos_data == pair_digit) / len(pos_data)
            single_freq += np.sum(pos_data == single_digit) / len(pos_data)
        score += (pair_freq / 3) * 0.25
        score += (single_freq / 3) * 0.2

        total = sum(digits)
        sums = historical_data["百位"] + historical_data["十位"] + historical_data["个位"]
        score += (np.sum(sums == total) / len(sums)) * 0.2

        types = [
            self.get_number_type(f"{int(row['百位'])}{int(row['十位'])}{int(row['个位'])}")
            for _, row in historical_data.iterrows()
        ]
        score += (types.count("组三") / len(types)) * 0.15

        digit_distribution = self.reverse_analysis.get("digitDistribution") or {}
        sum_distribution = self.reverse_analysis.get("sumDistribution") or {}
        if str(pair_digit) in digit_distribution or pair_digit in digit_distribution:
            score += 0.1
        if str(total) in sum_distribution or total in sum_distribution:
            score += 0.1
        return score

    def score_group6(self, combo: str, historical_data: pd.DataFrame) -> float:
        digits = _digits_from_combo(combo)
        score = 0.0

        digit_score = 0.0
        for digit in digits:
            freq = 0.0
            for pos in ["百位", "十位", "个位"]:
                pos_data = historical_data[pos].values
                freq += np.sum(pos_data == digit) / len(pos_data)
            digit_score += freq / 3
        score += (digit_score / 3) * 0.3

        total = sum(digits)
        sums = historical_data["百位"] + historical_data["十位"] + historical_data["个位"]
        score += (np.sum(sums == total) / len(sums)) * 0.25

        types = [
            self.get_number_type(f"{int(row['百位'])}{int(row['十位'])}{int(row['个位'])}")
            for _, row in historical_data.iterrows()
        ]
        score += (types.count("组六") / len(types)) * 0.2

        odd_even = self.get_odd_even_ratio(combo)
        odd_even_history = []
        for _, row in historical_data.iterrows():
            odd = sum([int(row["百位"]) % 2, int(row["十位"]) % 2, int(row["个位"]) % 2])
            odd_even_history.append(f"{odd}:{3 - odd}")
        score += (odd_even_history.count(odd_even) / len(odd_even_history)) * 0.15

        digit_distribution = self.reverse_analysis.get("digitDistribution") or {}
        sum_distribution = self.reverse_analysis.get("sumDistribution") or {}
        for digit in digits:
            if str(digit) in digit_distribution or digit in digit_distribution:
                score += 0.03
        if str(total) in sum_distribution or total in sum_distribution:
            score += 0.1
        return score


class HistoryManager:
    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self) -> list[dict[str, Any]]:
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_history(self) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        payload = _to_native(self.history)
        self.history_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_prediction(self, predictions: list[dict[str, Any]], period_info: dict[str, Any] | None = None) -> dict[str, Any]:
        legacy_period_info = dict(period_info or {})
        if "totalPeriods" in legacy_period_info and "total_periods" not in legacy_period_info:
            legacy_period_info["total_periods"] = legacy_period_info["totalPeriods"]
        record = {
            "date": datetime.now().isoformat(),
            "predictions": predictions,
            "periodInfo": legacy_period_info,
            "period_info": legacy_period_info,
        }
        self.history.append(record)
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self.save_history()
        return record

    def get_recent_predictions(self, count: int = 10) -> list[dict[str, Any]]:
        if count <= 0:
            return []
        return self.history[-count:] if self.history else []


class MainSystem:
    def __init__(self, config: ThreeDigitConfig):
        self.config = config
        self.data: pd.DataFrame | None = None
        self.reverse_analysis: dict[str, Any] | None = None
        self.history_manager = HistoryManager(config.history_file)

    def load_records(self, records: list[dict[str, Any]]) -> pd.DataFrame:
        self.data = records_to_dataframe(records)
        if self.data.empty:
            raise ValueError("当前接口没有返回可分析的三位数历史数据。")
        return self.data

    def run_reverse_analysis(self) -> dict[str, Any]:
        if self.data is None:
            raise ValueError("尚未加载历史数据。")
        analyzer = ReverseAnalyzer(self.data, self.config)
        analyzer.perform_reverse_analysis()
        analyzer.save_analysis()
        self.reverse_analysis = analyzer.analysis_results
        return {
            "successCases": analyzer.success_cases,
            "analysisResults": analyzer.analysis_results,
        }

    def generate_predictions(self) -> list[dict[str, Any]]:
        if self.data is None:
            raise ValueError("尚未加载历史数据。")
        generator = PredictionGenerator(self.data, self.config, self.reverse_analysis)
        predictions = [_with_prediction_aliases(prediction) for prediction in generator.generate_predictions()]
        latest_row = self.data.iloc[-1]
        self.history_manager.add_prediction(
            predictions,
            {
                "period": str(latest_row.get("期号", "")),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "totalPeriods": len(self.data),
            },
        )
        return predictions

    def validate_prediction(self) -> dict[str, Any]:
        if self.data is None:
            raise ValueError("尚未加载历史数据。")

        total_periods = len(self.data)
        available_history_lengths = sorted(
            {
                int(length)
                for length in self.config.reverse_history_lengths
                if int(length) > 0 and int(length) < total_periods
            }
        )
        if not available_history_lengths:
            history_length = max(min(total_periods - 1, self.config.reverse_min_history), 1)
        else:
            history_length = int((self.reverse_analysis or {}).get("bestHistoryLength") or available_history_lengths[0])
            if history_length not in available_history_lengths:
                history_length = min(available_history_lengths, key=lambda item: abs(item - history_length))

        test_periods = min(100, max(total_periods - history_length, 0))
        exact_hits = 0
        two_digit_hits = 0
        group3_hits = 0
        group6_hits = 0
        test_count = 0

        for offset in range(1, test_periods + 1):
            current_idx = total_periods - offset
            if current_idx < history_length:
                continue

            target_row = self.data.iloc[current_idx]
            target_combo = f"{int(target_row['百位'])}{int(target_row['十位'])}{int(target_row['个位'])}"
            target_type = _get_number_type(target_combo)
            historical_data = self.data.iloc[current_idx - history_length:current_idx]

            generator = PredictionGenerator(historical_data, self.config, self.reverse_analysis)
            predictions = generator.generate_predictions()

            exact_hit = False
            two_digit_hit = False
            target_digits = set(target_combo)
            for prediction in predictions:
                pred_combo = str(prediction["combo"]).zfill(3)
                if pred_combo == target_combo:
                    exact_hit = True
                    two_digit_hit = True
                    break
                if len(target_digits & set(pred_combo)) >= 2:
                    two_digit_hit = True

            if exact_hit:
                exact_hits += 1
                if target_type == "组三":
                    group3_hits += 1
                elif target_type == "组六":
                    group6_hits += 1

            if two_digit_hit:
                two_digit_hits += 1
            test_count += 1

        return _build_validation_result(
            exact_hits=exact_hits,
            two_digit_hits=two_digit_hits,
            test_count=test_count,
            group3_hits=group3_hits,
            group6_hits=group6_hits,
            history_length=history_length,
        )

    def run_full_analysis(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        data = self.load_records(records)
        reverse_payload = self.run_reverse_analysis()
        predictions = self.generate_predictions()
        validation = self.validate_prediction()
        latest_row = data.iloc[-1]
        type_counts = Counter(pred["type"] for pred in predictions)
        sum_counter = Counter(pred["sum"] for pred in predictions)
        odd_even_counter = Counter(pred["oddEven"] for pred in predictions)
        all_digits = []
        for pred in predictions:
            all_digits.extend(_digits_from_combo(pred["combo"]))
        digit_counter = Counter(all_digits)
        return _to_native(
            {
                "recordCount": len(data),
                "latestPeriod": str(latest_row.get("期号", "")),
                "latestNumbers": [int(latest_row["百位"]), int(latest_row["十位"]), int(latest_row["个位"])],
                "reverseAnalysis": reverse_payload["analysisResults"],
                "successCases": reverse_payload["successCases"],
                "predictions": predictions,
                "recentPredictions": self.history_manager.get_recent_predictions(),
                "ticketPlan": {
                    "totalTickets": self.config.total_tickets,
                    "costPerTicket": self.config.bet_per_ticket,
                    "totalBudget": self.config.total_budget,
                    "totalCost": len(predictions) * self.config.bet_per_ticket,
                    "typeCounts": dict(type_counts),
                    "typeRatios": PredictionGenerator(data, self.config, self.reverse_analysis).type_ratios,
                },
                "predictionStats": {
                    "sumDistribution": dict(sum_counter),
                    "oddEvenDistribution": dict(odd_even_counter),
                    "digitDistribution": dict(digit_counter),
                },
                "validation": validation,
                "historyFiles": {
                    "historyFile": str(self.config.history_file),
                    "successCasesFile": str(self.config.success_cases_file),
                },
            }
        )
