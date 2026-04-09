import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXAMPLES_ROOT = REPO_ROOT / "examples" / "python"
if str(PYTHON_EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_EXAMPLES_ROOT))

from common.dlt_analysis import analyze_dlt_records  # noqa: E402
from common.formatters import print_brand_footer  # noqa: E402
from common.kl8_analysis import analyze_kl8_records  # noqa: E402
from common.positional_sequence_analysis import analyze_positional_records  # noqa: E402
from common.ssq_analysis import analyze_ssq_records  # noqa: E402
from common.three_digit_analysis import analyze_three_digit_records  # noqa: E402


class AnalysisHelpersTests(unittest.TestCase):
    def test_ssq_analysis_detects_exact_and_near_matches(self):
        records = [
            {
                "period": str(36 - index),
                "numbers_list": [1, 2, 3, 4, 5, 6 + (index % 3), 7 + (index % 2)],
            }
            for index in range(18)
        ]
        records.extend(
            [
                {"period": "3", "numbers_list": [1, 2, 3, 4, 5, 6, 7]},
                {"period": "2", "numbers_list": [1, 2, 3, 4, 5, 6, 7]},
                {"period": "1", "numbers_list": [1, 2, 3, 4, 5, 8, 9]},
            ]
        )
        result = analyze_ssq_records(records)

        self.assertEqual(result["recordCount"], len(records))
        self.assertGreaterEqual(len(result["exactMatches"]), 1)
        self.assertGreaterEqual(len(result["nearMatches"]), 1)
        self.assertIn("patternEvolution", result)
        self.assertIn("successCaseSamples", result)
        self.assertIn("trueSuccessCases", result)
        self.assertIn("probabilityModel", result)
        self.assertIn("markovTransitionsTop", result)
        self.assertIn("clusterSummary", result)
        self.assertIn("clusterStats", result)
        self.assertIn("simulationResults", result)
        self.assertIn("evolutionaryPattern", result)
        self.assertIn("markovTransitionsTop", result)
        self.assertIn("trueSuccessCases", result)

    def test_dlt_analysis_returns_ranked_combinations(self):
        records = [
            {"period": "3", "numbers_list": [1, 2, 3, 4, 5, 1, 2]},
            {"period": "2", "numbers_list": [1, 2, 3, 7, 8, 1, 3]},
            {"period": "1", "numbers_list": [1, 2, 5, 7, 9, 2, 3]},
        ]
        result = analyze_dlt_records(records)

        self.assertEqual(result["recordCount"], 3)
        self.assertGreaterEqual(len(result["topCombinations"]), 1)
        self.assertIn("frontZoneDistribution", result)
        self.assertIn("frontOmissionTop", result)
        self.assertIn("recentRepeatSummary", result)
        self.assertIn("modelsPerformance", result)
        self.assertIn("performanceStats", result)
        self.assertIn("validation", result)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("avgTotalMatch", result["validation"])
        self.assertIn("hitDistribution", result["validation"])
        self.assertIn("recentCases", result["validation"])

    def test_three_digit_analysis_returns_grouped_recommendations_and_ticket_plan(self):
        records = [
            {"period": str(60 - idx), "numbers_list": [idx % 10, (idx + 1) % 10, (idx + 2) % 10]}
            for idx in range(40)
        ]
        result = analyze_three_digit_records(records, top_n=12, include_validation=False)

        self.assertEqual(result["recordCount"], 40)
        self.assertIn("groupedRecommendations", result)
        self.assertIn("ticketPlan", result)
        self.assertIn("直选", result["groupedRecommendations"])
        self.assertIn("组三", result["groupedRecommendations"])
        self.assertIn("组六", result["groupedRecommendations"])
        self.assertEqual(result["ticketPlan"]["totalTickets"], 10)

    def test_positional_analysis_runs_backtest_and_recommendations(self):
        records = [
            {"period": str(100 - idx), "numbers_list": [idx % 10, (idx + 1) % 10, (idx + 2) % 10]}
            for idx in range(25)
        ]
        result = analyze_positional_records(records, position_count=3, number_range=10, history_lengths=(10, 15))

        self.assertEqual(result["recordCount"], 25)
        self.assertGreaterEqual(len(result["recommendations"]), 1)
        self.assertIn("validation", result)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("hitCount", result["validation"])
        self.assertIn("hitRate", result["validation"])

    def test_positional_analysis_falls_back_to_shorter_validation_window(self):
        records = [
            {"period": str(40 - idx), "numbers_list": [idx % 10, (idx + 1) % 10, (idx + 2) % 10]}
            for idx in range(20)
        ]
        result = analyze_positional_records(records, position_count=3, number_range=10, history_lengths=(30, 50))

        self.assertIn("validation", result)
        self.assertIsNotNone(result["validation"]["bestHistoryLength"])
        self.assertGreaterEqual(len(result["validation"]["historyResults"]), 1)
        self.assertGreater(result["validation"]["sampleCount"], 0)

    def test_kl8_analysis_returns_zone_and_omission_summary(self):
        records = [
            {"period": "2", "numbers_list": list(range(1, 21))},
            {"period": "1", "numbers_list": list(range(21, 41))},
        ]
        result = analyze_kl8_records(records)

        self.assertEqual(result["recordCount"], 2)
        self.assertEqual(len(result["balancedPick"]), 10)
        self.assertIn("zoneDistribution", result)
        self.assertIn("recommendations", result)
        self.assertIn("validation", result)
        self.assertIn("sampleCount", result["validation"])
        self.assertIn("avgHitCount", result["validation"])

    def test_brand_footer_uses_soft_single_line_notice(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            print_brand_footer()

        output = buffer.getvalue().strip()
        self.assertIn("NEUXSBOT", output)
        self.assertIn("www.neuxsbot.com", output)
        self.assertNotIn("升级", output)
        self.assertNotIn("会员", output)


if __name__ == "__main__":
    unittest.main()
