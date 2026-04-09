import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXAMPLES_ROOT = REPO_ROOT / "examples" / "python"
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(PYTHON_EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_EXAMPLES_ROOT))

from common.three_digit_original_system import MainSystem, ReverseAnalyzer, ThreeDigitConfig  # noqa: E402


def build_records(count: int = 18) -> list[dict[str, object]]:
    return [
        {
            "period": str(count - index),
            "numbers_list": [index % 10, (index * 2) % 10, (index * 3) % 10],
        }
        for index in range(count)
    ]


class ThreeDigitOriginalSystemTests(unittest.TestCase):
    def test_run_full_analysis_returns_validation_and_legacy_fields(self):
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmp_path = TEST_TMP_ROOT / "three-digit-original-fields"
        shutil.rmtree(tmp_path, ignore_errors=True)
        tmp_path.mkdir(parents=True, exist_ok=True)
        try:
            config = ThreeDigitConfig(
                lottery_type="fc3d",
                display_name="福彩3D",
                output_path=tmp_path / "result.json",
                history_file=tmp_path / "history.json",
                success_cases_file=tmp_path / "success_cases.json",
                reverse_min_history=5,
                reverse_history_lengths=(5,),
                total_tickets=6,
                total_budget=12,
            )

            result = MainSystem(config).run_full_analysis(build_records())

            self.assertIn("validation", result)
            self.assertIn("exactHits", result["validation"])
            self.assertIn("exact_hits", result["validation"])
            self.assertIn("exactRate", result["validation"])
            self.assertIn("exact_rate", result["validation"])
            self.assertIn("twoDigitHits", result["validation"])
            self.assertIn("two_digit_hits", result["validation"])
            self.assertGreaterEqual(result["validation"]["testCount"], 1)

            first_prediction = result["predictions"][0]
            self.assertIn("oddEven", first_prediction)
            self.assertIn("odd_even", first_prediction)
            self.assertEqual(first_prediction["odd_even"], first_prediction["oddEven"])

            self.assertIn("recentPredictions", result)
            self.assertEqual(len(result["recentPredictions"]), 1)
            self.assertIn("periodInfo", result["recentPredictions"][0])
            self.assertIn("period_info", result["recentPredictions"][0])
            self.assertEqual(
                result["recentPredictions"][0]["period_info"],
                result["recentPredictions"][0]["periodInfo"],
            )
            self.assertIn("total_periods", result["recentPredictions"][0]["period_info"])
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)

    def test_run_full_analysis_keeps_full_success_cases_and_recent_history(self):
        repeated_records = [
            {"period": str(40 - index), "numbers_list": [1, 2, 3]}
            for index in range(40)
        ]
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmp_path = TEST_TMP_ROOT / "three-digit-original-history"
        shutil.rmtree(tmp_path, ignore_errors=True)
        tmp_path.mkdir(parents=True, exist_ok=True)
        try:
            config = ThreeDigitConfig(
                lottery_type="fc3d",
                display_name="福彩3D",
                output_path=tmp_path / "result.json",
                history_file=tmp_path / "history.json",
                success_cases_file=tmp_path / "success_cases.json",
                reverse_min_history=5,
                reverse_history_lengths=(5,),
                total_tickets=6,
                total_budget=12,
            )

            with patch.object(ReverseAnalyzer, "generate_all_combinations", lambda self: ["123"]):
                result = MainSystem(config).run_full_analysis(repeated_records)

            self.assertGreater(result["reverseAnalysis"]["totalCases"], 20)
            self.assertEqual(len(result["successCases"]), result["reverseAnalysis"]["totalCases"])
            self.assertIn("recentPredictions", result)
            self.assertEqual(len(result["recentPredictions"]), 1)
            self.assertIn("period_info", result["recentPredictions"][0])
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
