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
from common.dlt_analysis import analyze_dlt_records
from common.formatters import print_brand_footer, print_section, write_json_output


LOTTERY_TYPE = "dlt"
DISPLAY_NAME = "大乐透"
PROGRAM_NAME = "大乐透反推分析程序"


def analyze(records: list[dict[str, Any]], periods: int) -> dict[str, Any]:
    result = {
        "lotteryType": LOTTERY_TYPE,
        "displayName": DISPLAY_NAME,
        "programName": PROGRAM_NAME,
        "periods": periods,
    }
    result.update(analyze_dlt_records(records))
    return result


def print_analysis(result: dict[str, Any]) -> None:
    print_section(PROGRAM_NAME)
    print(f"分析期数: {result['periods']}")
    print(f"有效记录: {result['recordCount']}")
    if result.get("recordCount", 0) == 0:
        print(result["message"])
        return

    print(f"最新期号: {result['latestPeriod']}")
    print(f"最新前区: {' '.join(str(item) for item in result['latestFront'])}")
    print(f"最新后区: {' '.join(str(item) for item in result['latestBack'])}")
    print(f"前区热度 Top12: {result['frontFrequencyTop']}")
    print(f"后区热度 Top8: {result['backFrequencyTop']}")
    print(f"前区分区分布: {result['frontZoneDistribution'][:4]}")
    print(f"后区分区分布: {result['backZoneDistribution'][:4]}")
    print(f"奇偶结构: {result['oddEvenDistribution'][:4]}")

    validation = result.get("validation") or {}
    if validation:
        print(
            "回测样本: "
            f"{validation.get('sampleCount', 0)} 期 | "
            f"前区均命中 {validation.get('avgFrontMatch', 0.0):.4f} | "
            f"后区均命中 {validation.get('avgBackMatch', 0.0):.4f} | "
            f"总均命中 {validation.get('avgTotalMatch', 0.0):.4f}"
        )

    performance_stats = result.get("performanceStats") or {}
    if performance_stats:
        print(
            "组合生成: "
            f"前区候选 {performance_stats.get('frontPoolSize', 0)} | "
            f"后区候选 {performance_stats.get('backPoolSize', 0)} | "
            f"生成 {performance_stats.get('generatedCombinationCount', 0)} 组 | "
            f"返回 {performance_stats.get('returnedCombinationCount', 0)} 组"
        )

    models_performance = result.get("modelsPerformance") or {}
    if models_performance:
        print(
            "评分因子: "
            f"频次 {models_performance.get('frequencyModel', 0.0):.6f} | "
            f"分区 {models_performance.get('zoneModel', 0.0):.6f} | "
            f"和值 {models_performance.get('sumModel', 0.0):.6f} | "
            f"重号 {models_performance.get('repeatModel', 0.0):.6f}"
        )

    recent_cases = validation.get("recentCases") or []
    if recent_cases:
        print(f"最近回测样例: {recent_cases[:3]}")

    print("")
    print("高分推荐:")
    for item in result.get("topCombinations", [])[:5]:
        print(
            f"  前区={item['front']} | 后区={item['back']} | 分数={item['score']:.6f} | "
            f"前区分区={item['frontZonePattern']} | 后区分区={item['backZonePattern']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument("--api-base-url", default=os.getenv("NEUXSBOT_API_BASE_URL", "https://www.neuxsbot.com"))
    parser.add_argument("--token", default=os.getenv("NEUXSBOT_TOKEN", ""))
    parser.add_argument("--periods", type=int, default=int(os.getenv("NEUXSBOT_PERIODS", "120")))
    parser.add_argument("--output", default=str(Path(__file__).with_name("analysis_result.json")))
    args = parser.parse_args()

    try:
        client = LotteryApiClient(args.api_base_url, token=args.token)
        records = client.fetch_history_records(LOTTERY_TYPE, periods=args.periods, page_size=200)
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
