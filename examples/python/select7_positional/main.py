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
from common.positional_sequence_analysis import analyze_positional_records


LOTTERY_TYPE = "select7"
DISPLAY_NAME = "七星彩"
PROGRAM_NAME = "七星彩位置趋势分析程序"


def detect_number_range(records: list[dict[str, Any]], position_count: int, fallback: int = 10) -> int:
    max_number = fallback - 1
    for record in records:
        for number in record.get("numbers_list", [])[:position_count]:
            max_number = max(max_number, int(number))
    return max_number + 1


def analyze(records: list[dict[str, Any]], periods: int) -> dict[str, Any]:
    number_range = detect_number_range(records, position_count=7)
    result = {
        "lotteryType": LOTTERY_TYPE,
        "displayName": DISPLAY_NAME,
        "programName": PROGRAM_NAME,
        "periods": periods,
        "detectedNumberRange": number_range,
    }
    result.update(analyze_positional_records(records, position_count=7, number_range=number_range, history_lengths=(20, 30, 50), top_n=12))
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
    print(f"检测号码范围: 0 - {result['detectedNumberRange'] - 1}")
    print("")
    for item in result.get("positionSummary", []):
        print(
            f"{item['position']} | 热号: {item['hotDigits']} | "
            f"近热: {item['recentHotDigits']} | 冷号: {item['coldDigits']}"
        )
    print("")
    print(f"和值分布 Top8: {result['sumDistributionTop']}")
    print(f"奇偶分布 Top8: {result['oddEvenDistribution']}")
    print(f"重号分布 Top8: {result['uniqueDistribution']}")
    print("推荐组合:")
    for item in result.get("recommendations", [])[:8]:
        print(
            f"  {item['numbers']} | 分数={item['score']:.6f} | "
            f"和值={item['sum']} | 不同数字数={item['uniqueCount']}"
        )
    validation = result.get("validation", {})
    if validation:
        if validation.get("sampleCount", 0):
            print(
                f"回测样本: {validation.get('sampleCount', 0)} 期 | 命中 {validation.get('hitCount', 0)} 次 | "
                f"命中率 {validation.get('hitRate', 0.0):.4f}% | 最佳历史长度 {validation.get('bestHistoryLength')}"
            )
        else:
            print("回测摘要: 当前样本不足，暂时无法生成有效回测结果")


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
