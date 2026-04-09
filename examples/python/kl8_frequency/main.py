from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
PYTHON_ROOT = CURRENT_DIR.parent
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from common.api_client import LotteryApiClient, LotteryApiError
from common.formatters import print_brand_footer, print_section, write_json_output
from common.kl8_analysis import analyze_kl8_records


LOTTERY_TYPE = "kl8"
DISPLAY_NAME = "快乐8"
PROGRAM_NAME = "快乐8频率遗漏分析程序"


def analyze(records: list[dict[str, Any]], periods: int) -> dict[str, Any]:
    result = {
        "lotteryType": LOTTERY_TYPE,
        "displayName": DISPLAY_NAME,
        "programName": PROGRAM_NAME,
        "periods": periods,
    }
    result.update(analyze_kl8_records(records))
    return result


def print_analysis(result: dict[str, Any]) -> None:
    print_section(PROGRAM_NAME)
    print(f"分析期数: {result['periods']}")
    print(f"有效记录: {result['recordCount']}")
    if result.get("recordCount", 0) == 0:
        print(result["message"])
        return

    print(f"最新期号: {result['latestPeriod']}")
    print(f"最新号码: {' '.join(str(item) for item in result['latestNumbers'])}")
    print(f"全期热号 Top12: {result['hotNumbers']}")
    print(f"近30期热号 Top12: {result['recentHotNumbers']}")
    print(f"高遗漏号码 Top12: {result['highOmissionNumbers']}")
    print(f"分区分布: {result['zoneDistribution'][:4]}")
    print(f"奇偶分布: {result['oddEvenDistribution'][:4]}")
    print(f"高低分布: {result['highLowDistribution'][:4]}")
    print(f"连号分布: {result['consecutiveDistribution'][:4]}")
    validation = result.get("validation", {})
    if validation:
        print(
            f"回测样本: {validation.get('sampleCount', 0)} 期 | "
            f"平均命中 {validation.get('avgHitCount', 0.0):.4f} | "
            f"最佳命中 {validation.get('bestHitCount', 0)}"
        )
    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"推荐组合: {recommendations[0]['numbers']}")
    else:
        print(f"推荐组合: {result['balancedPick']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument("--api-base-url", default=os.getenv("NEUXSBOT_API_BASE_URL", "https://www.neuxsbot.com"))
    parser.add_argument("--token", default=os.getenv("NEUXSBOT_TOKEN", ""))
    parser.add_argument("--periods", type=int, default=int(os.getenv("NEUXSBOT_PERIODS", "120")))
    parser.add_argument("--output", default=str(Path(__file__).with_name("analysis_result.json")))
    args = parser.parse_args()

    try:
        client = LotteryApiClient(args.api_base_url, token=args.token)
        records = client.fetch_history_records(LOTTERY_TYPE, periods=args.periods)
        result = analyze(records, periods=args.periods)
        print_analysis(result)
        output_path = write_json_output(args.output, result)
    except LotteryApiError as exc:
        print(f"\u8bf7\u6c42\u5931\u8d25: {exc}")
        return 1
    print("")
    print(f"结果文件: {output_path}")
    print_brand_footer()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
