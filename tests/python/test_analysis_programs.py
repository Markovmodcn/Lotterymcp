import importlib.util
import json
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXAMPLES_ROOT = REPO_ROOT / "examples" / "python"
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(PYTHON_EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_EXAMPLES_ROOT))


def load_module(relative_path: str):
    module_path = REPO_ROOT / relative_path
    module_name = "test_" + relative_path.replace("\\", "_").replace("/", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_three_digit_records(count: int = 30) -> list[dict[str, object]]:
    return [
        {
            "period": str(count - index),
            "numbers_list": [index % 10, (index + 3) % 10, (index + 6) % 10],
        }
        for index in range(count)
    ]


def build_three_digit_validation_records(periods: int = 60) -> list[dict[str, object]]:
    target_combo = [1, 2, 3]
    records: list[dict[str, object]] = []
    for index in range(periods - 1):
        numbers = target_combo if index % 3 == 0 else [
            (index + 2) % 10,
            (index + 5) % 10,
            (index + 7) % 10,
        ]
        records.append({"period": str(periods - index), "numbers_list": numbers})
    records.append({"period": "1", "numbers_list": target_combo})
    return records


def build_three_digit_program_payload(record_count: int) -> dict[str, object]:
    return {
        "recordCount": record_count,
        "latestPeriod": "1",
        "latestNumbers": [1, 2, 3],
        "reverseAnalysis": {
            "totalCases": 4,
            "bestHistoryLength": 100,
            "typeDistribution": {"group3": 2, "group6": 2},
        },
        "successCases": [
            {
                "targetPeriod": "1",
                "targetCombo": "123",
                "historyLength": 100,
                "rank": 5,
            }
        ],
        "predictions": [
            {
                "combo": "123",
                "type": "direct",
                "score": 0.987654,
                "sum": 6,
                "oddEven": "2:1",
                "odd_even": "2:1",
            }
        ],
        "ticketPlan": {
            "totalTickets": 1,
            "costPerTicket": 2,
            "totalBudget": 2,
            "totalCost": 2,
            "typeCounts": {"direct": 1},
        },
        "predictionStats": {
            "sumDistribution": {6: 1},
            "oddEvenDistribution": {"2:1": 1},
            "digitDistribution": {1: 1, 2: 1, 3: 1},
        },
        "validation": {
            "exactHits": 1,
            "twoDigitHits": 2,
            "testCount": 3,
            "exact_hits": 1,
            "two_digit_hits": 2,
            "test_count": 3,
        },
        "historyFiles": {
            "historyFile": "runtime/prediction_history.json",
            "successCasesFile": "runtime/success_cases.json",
        },
    }


def run_three_digit_program_main(relative_path: str, periods: int = 30) -> dict[str, object]:
    module = load_module(relative_path)
    records = build_three_digit_records(periods)
    output_path = Path("results") / f"{module.LOTTERY_TYPE}-program-test.json"
    captured: dict[str, object] = {}

    client = Mock()
    client.fetch_history_records.return_value = records
    original_print_section = module.print_section

    def capture_write_json(target_path, payload):
        captured["output_path"] = Path(target_path)
        captured["payload"] = payload
        return Path(target_path)

    with (
        patch.object(module, "LotteryApiClient", return_value=client),
        patch.object(module, "MainSystem") as main_system_cls,
        patch.object(module, "write_json_output", side_effect=capture_write_json),
        patch.object(module, "print_section", side_effect=original_print_section) as print_section_mock,
        patch.object(
            sys,
            "argv",
            [
                "main.py",
                "--api-base-url",
                "https://api.test",
                "--token",
                "token-123",
                "--periods",
                str(periods),
                "--output",
                str(output_path),
            ],
        ),
    ):
        main_system_cls.return_value.run_full_analysis.return_value = build_three_digit_program_payload(len(records))
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = module.main()

    return {
        "module": module,
        "exit_code": exit_code,
        "stdout": stdout.getvalue(),
        "payload": captured["payload"],
        "output_path": captured["output_path"],
        "client": client,
        "print_section_mock": print_section_mock,
        "config": main_system_cls.call_args[0][0],
    }


class AnalysisProgramTests(unittest.TestCase):
    def test_fc3d_program_main_writes_original_system_payload(self):
        program = run_three_digit_program_main("examples/python/fc3d_markov/main.py")
        module = program["module"]
        result = program["payload"]

        self.assertEqual(program["exit_code"], 0)
        self.assertEqual(result["lotteryType"], "fc3d")
        self.assertEqual(result["displayName"], module.DISPLAY_NAME)
        self.assertEqual(result["programName"], module.PROGRAM_NAME)
        self.assertEqual(result["periods"], 30)
        self.assertIn("reverseAnalysis", result)
        self.assertIn("successCases", result)
        self.assertIn("predictions", result)
        self.assertIn("ticketPlan", result)
        self.assertIn("validation", result)
        self.assertIn("exact_hits", result["validation"])
        self.assertIn("odd_even", result["predictions"][0])
        json.dumps(result, ensure_ascii=False)
        self.assertEqual(program["config"].output_path, program["output_path"])
        program["client"].fetch_history_records.assert_called_once_with("fc3d", periods=30, page_size=200)
        program["print_section_mock"].assert_called_once_with(module.PROGRAM_NAME)
        self.assertIn(module.PROGRAM_NAME, program["stdout"])
        self.assertIn("完全命中", program["stdout"])
        self.assertIn("两码命中", program["stdout"])

    def test_three_digit_system_returns_validation_and_legacy_fields(self):
        from common.three_digit_original_system import MainSystem, ReverseAnalyzer, ThreeDigitConfig

        records = build_three_digit_validation_records(periods=40)
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        base = TEST_TMP_ROOT / "analysis-programs-three-digit"
        shutil.rmtree(base, ignore_errors=True)
        base.mkdir(parents=True, exist_ok=True)
        try:
            config = ThreeDigitConfig(
                lottery_type="fc3d",
                display_name="福彩3D",
                output_path=base / "analysis.json",
                history_file=base / "prediction_history.json",
                success_cases_file=base / "success_cases.json",
                reverse_min_history=5,
                reverse_history_lengths=(5, 10),
                total_tickets=6,
            )
            with patch.object(ReverseAnalyzer, "generate_all_combinations", lambda self: ["123"]):
                result = MainSystem(config).run_full_analysis(records)
        finally:
            shutil.rmtree(base, ignore_errors=True)

        self.assertGreaterEqual(result["recordCount"], len(records))
        self.assertGreater(len(result["successCases"]), 0)
        validation = result["validation"]
        self.assertIn("exactHits", validation)
        self.assertIn("group3Hits", validation)
        self.assertIn("group6Hits", validation)
        self.assertIn("odd_even", result["predictions"][0])
        self.assertEqual(result["predictions"][0]["odd_even"], result["predictions"][0]["oddEven"])
        self.assertIn("targetPeriod", result["successCases"][0])
        self.assertIn("target_period", result["successCases"][0])

    def test_pl3_program_main_writes_original_system_payload(self):
        program = run_three_digit_program_main("examples/python/pl3_markov/main.py")
        module = program["module"]
        result = program["payload"]

        self.assertEqual(program["exit_code"], 0)
        self.assertEqual(result["lotteryType"], "pl3")
        self.assertEqual(result["displayName"], module.DISPLAY_NAME)
        self.assertEqual(result["programName"], module.PROGRAM_NAME)
        self.assertEqual(result["periods"], 30)
        self.assertIn("reverseAnalysis", result)
        self.assertIn("successCases", result)
        self.assertIn("predictions", result)
        self.assertIn("ticketPlan", result)
        self.assertIn("validation", result)
        self.assertIn("exact_hits", result["validation"])
        self.assertIn("odd_even", result["predictions"][0])
        json.dumps(result, ensure_ascii=False)
        self.assertEqual(program["config"].output_path, program["output_path"])
        program["client"].fetch_history_records.assert_called_once_with("pl3", periods=30, page_size=200)
        program["print_section_mock"].assert_called_once_with(module.PROGRAM_NAME)
        self.assertIn(module.PROGRAM_NAME, program["stdout"])
        self.assertIn("完全命中", program["stdout"])
        self.assertIn("两码命中", program["stdout"])

    def test_ssq_program_returns_enriched_metadata(self):
        module = load_module("examples/python/ssq_quantum/main.py")
        records = [
            {"period": "3", "numbers_list": [1, 2, 3, 4, 5, 6, 7]},
            {"period": "2", "numbers_list": [1, 2, 3, 4, 5, 6, 7]},
            {"period": "1", "numbers_list": [1, 2, 3, 4, 5, 8, 9]},
        ]

        result = module.analyze(records, periods=30)

        self.assertEqual(result["lotteryType"], "ssq")
        self.assertEqual(result["displayName"], "双色球")
        self.assertEqual(result["programName"], "双色球全匹配深度分析程序")
        self.assertEqual(result["recordCount"], 3)
        self.assertGreaterEqual(len(result["topRecommendations"]), 1)
        self.assertIn("exactMatches", result)
        self.assertIn("nearMatches", result)
        self.assertIn("trueSuccessCases", result)
        self.assertIn("probabilityModel", result)
        self.assertIn("markovTransitionsTop", result)
        self.assertIn("clusterSummary", result)
        self.assertIn("clusterStats", result)
        self.assertIn("simulationResults", result)
        self.assertIn("evolutionaryPattern", result)
        self.assertIn("markovTransitionsTop", result)
        self.assertIn("trueSuccessCases", result)

    def test_dlt_program_returns_ranked_combinations(self):
        module = load_module("examples/python/dlt_hybrid/main.py")
        records = [
            {"period": "3", "numbers_list": [1, 2, 3, 4, 5, 1, 2]},
            {"period": "2", "numbers_list": [1, 2, 3, 7, 8, 1, 3]},
            {"period": "1", "numbers_list": [1, 2, 5, 7, 9, 2, 3]},
        ]

        result = module.analyze(records, periods=30)

        self.assertEqual(result["lotteryType"], "dlt")
        self.assertEqual(result["displayName"], "大乐透")
        self.assertEqual(result["programName"], "大乐透反推分析程序")
        self.assertEqual(result["recordCount"], 3)
        self.assertGreaterEqual(len(result["topCombinations"]), 1)
        self.assertIn("frontZoneDistribution", result)
        self.assertIn("modelsPerformance", result)
        self.assertIn("performanceStats", result)
        self.assertIn("validation", result)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("avgTotalMatch", result["validation"])
        self.assertIn("hitDistribution", result["validation"])
        self.assertIn("recentCases", result["validation"])

    def test_dlt_program_prints_validation_and_score_summary(self):
        module = load_module("examples/python/dlt_hybrid/main.py")
        records = [
            {"period": "3", "numbers_list": [1, 2, 3, 4, 5, 1, 2]},
            {"period": "2", "numbers_list": [1, 2, 3, 7, 8, 1, 3]},
            {"period": "1", "numbers_list": [1, 2, 5, 7, 9, 2, 3]},
        ]

        result = module.analyze(records, periods=30)
        stdout = StringIO()
        with redirect_stdout(stdout):
            module.print_analysis(result)

        output = stdout.getvalue()
        self.assertIn("回测样本", output)
        self.assertIn("评分因子", output)

    def test_pailie5_program_uses_positional_validation(self):
        module = load_module("examples/python/pailie5_positional/main.py")
        records = [
            {
                "period": str(120 - index),
                "numbers_list": [index % 10, (index + 1) % 10, (index + 2) % 10, (index + 3) % 10, (index + 4) % 10],
            }
            for index in range(40)
        ]

        result = module.analyze(records, periods=120)

        self.assertEqual(result["lotteryType"], "pl5")
        self.assertEqual(result["displayName"], "排列5")
        self.assertEqual(result["programName"], "排列5位置趋势分析程序")
        self.assertEqual(result["recordCount"], 40)
        self.assertGreaterEqual(len(result["recommendations"]), 1)
        self.assertIn("validation", result)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("hitCount", result["validation"])
        self.assertIn("hitRate", result["validation"])

    def test_pailie5_program_uses_fallback_validation_for_small_samples(self):
        module = load_module("examples/python/pailie5_positional/main.py")
        records = [
            {
                "period": str(60 - index),
                "numbers_list": [index % 10, (index + 1) % 10, (index + 2) % 10, (index + 3) % 10, (index + 4) % 10],
            }
            for index in range(20)
        ]

        result = module.analyze(records, periods=20)

        self.assertIn("validation", result)
        self.assertIsNotNone(result["validation"]["bestHistoryLength"])
        self.assertGreaterEqual(len(result["validation"]["historyResults"]), 1)
        self.assertGreater(result["validation"]["sampleCount"], 0)

    def test_pailie5_program_prints_validation_summary(self):
        module = load_module("examples/python/pailie5_positional/main.py")
        records = [
            {
                "period": str(60 - index),
                "numbers_list": [index % 10, (index + 1) % 10, (index + 2) % 10, (index + 3) % 10, (index + 4) % 10],
            }
            for index in range(20)
        ]

        result = module.analyze(records, periods=20)
        stdout = StringIO()
        with redirect_stdout(stdout):
            module.print_analysis(result)

        output = stdout.getvalue()
        self.assertIn("\u56de\u6d4b\u6837\u672c", output)
        self.assertNotIn("\u56de\u6d4b\u7ed3\u679c:", output)

    def test_pailie5_program_main_returns_nonzero_on_api_error(self):
        from common.api_client import LotteryApiError

        module = load_module("examples/python/pailie5_positional/main.py")
        client = Mock()
        client.fetch_history_records.side_effect = LotteryApiError(
            "请求网站接口失败: HTTP 429 请求过于频繁，请稍后重试或降低调用频率"
        )

        with (
            patch.object(module, "LotteryApiClient", return_value=client),
            patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--api-base-url",
                    "https://api.test",
                    "--periods",
                    "20",
                ],
            ),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = module.main()

        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("请求失败", output)
        self.assertIn("429", output)

    def test_select7_program_allows_two_digit_positions(self):
        module = load_module("examples/python/select7_positional/main.py")
        records = [
            {
                "period": str(80 - index),
                "numbers_list": [13 + (index % 2), 14 + (index % 3), 7 + (index % 4), 4 + (index % 5), 8, 9, 10 + (index % 3)],
            }
            for index in range(35)
        ]

        result = module.analyze(records, periods=80)

        self.assertEqual(result["lotteryType"], "select7")
        self.assertEqual(result["displayName"], "七星彩")
        self.assertEqual(result["programName"], "七星彩位置趋势分析程序")
        self.assertEqual(result["recordCount"], 35)
        self.assertEqual(len(result["latestNumbers"]), 7)
        self.assertGreaterEqual(len(result["recommendations"]), 1)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("hitCount", result["validation"])
        self.assertIn("hitRate", result["validation"])

    def test_kl8_program_returns_distribution_summary(self):
        module = load_module("examples/python/kl8_frequency/main.py")
        records = [
            {"period": "2", "numbers_list": list(range(1, 21))},
            {"period": "1", "numbers_list": list(range(11, 31))},
        ]

        result = module.analyze(records, periods=30)

        self.assertEqual(result["lotteryType"], "kl8")
        self.assertEqual(result["displayName"], "快乐8")
        self.assertEqual(result["programName"], "快乐8频率遗漏分析程序")
        self.assertEqual(result["recordCount"], 2)
        self.assertGreaterEqual(len(result["balancedPick"]), 1)
        self.assertIn("recommendations", result)
        self.assertIn("validation", result)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("avgHitCount", result["validation"])
        self.assertIn("zoneDistribution", result)
        self.assertIn("highOmissionNumbers", result)


if __name__ == "__main__":
    unittest.main()
