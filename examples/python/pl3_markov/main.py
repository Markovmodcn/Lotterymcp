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
from common.three_digit_original_system import MainSystem, ThreeDigitConfig


LOTTERY_TYPE = "pl3"
DISPLAY_NAME = "排列3"
PROGRAM_NAME = "排列3逆向分析程序"
DEFAULT_OUTPUT = "results/pl3_analysis_program.json"
RUNTIME_DIR = CURRENT_DIR / "runtime"


def build_config(output_path: str | Path | None = None) -> ThreeDigitConfig:
    target_output = Path(output_path) if output_path else Path(DEFAULT_OUTPUT)
    return ThreeDigitConfig(
        lottery_type=LOTTERY_TYPE,
        display_name=DISPLAY_NAME,
        output_path=target_output,
        history_file=RUNTIME_DIR / "prediction_history.json",
        success_cases_file=RUNTIME_DIR / "success_cases.json",
    )


def build_empty_result(periods: int) -> dict[str, Any]:
    return {
        "lotteryType": LOTTERY_TYPE,
        "displayName": DISPLAY_NAME,
        "programName": PROGRAM_NAME,
        "periods": periods,
        "recordCount": 0,
        "message": "当前接口没有返回可分析的三位数历史数据。",
        "reverseAnalysis": {},
        "successCases": [],
        "predictions": [],
        "recentPredictions": [],
        "ticketPlan": {},
        "predictionStats": {},
        "validation": {},
        "historyFiles": {},
    }


def analyze(records: list[dict[str, Any]], periods: int, output_path: str | Path | None = None) -> dict[str, Any]:
    result = {
        "lotteryType": LOTTERY_TYPE,
        "displayName": DISPLAY_NAME,
        "programName": PROGRAM_NAME,
        "periods": periods,
    }
    if not records:
        result.update(build_empty_result(periods))
        return result

    system = MainSystem(build_config(output_path=output_path))
    result.update(system.run_full_analysis(records))
    return result


def print_analysis(result: dict[str, Any]) -> None:
    print_section(PROGRAM_NAME)
    print(f"分析期数: {result['periods']}")
    print(f"有效记录: {result['recordCount']}")
    if result.get("recordCount", 0) == 0:
        print(result["message"])
        return

    reverse = result.get("reverseAnalysis", {})
    ticket_plan = result.get("ticketPlan", {})
    print(f"最新期号: {result['latestPeriod']}")
    print(f"最新号码: {' '.join(str(item) for item in result['latestNumbers'])}")
    print(f"反推命中案例: {reverse.get('totalCases', 0)}")
    print(f"最佳历史长度: {reverse.get('bestHistoryLength')}")
    print(f"类型分布: {reverse.get('typeDistribution', {})}")
    print(f"选号方案: {ticket_plan.get('typeCounts', {})}")
    validation = result.get("validation", {})
    if validation:
        print(
            f"回测验证: 完全命中 {validation.get('exactHits', 0)} 次 | "
            f"两码命中 {validation.get('twoDigitHits', 0)} 次（命中2个数字） | "
            f"样本 {validation.get('testCount', 0)} 期"
        )
        print(
            f"命中率: 完全 {validation.get('exactRate', 0)}% | "
            f"两码 {validation.get('twoDigitRate', 0)}% | "
            f"窗口 {validation.get('windowSize', 0)} 期"
        )
    print("")
    print("推荐方案:")
    for item in result.get("predictions", [])[:5]:
        print(
            f"  号码={item['combo']} | 类型={item['type']} | 分数={item['score']:.6f} | "
            f"和值={item['sum']} | 奇偶={item['oddEven']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument("--api-base-url", default=os.getenv("NEUXSBOT_API_BASE_URL", "https://www.neuxsbot.com"))
    parser.add_argument("--token", default=os.getenv("NEUXSBOT_TOKEN", ""))
    parser.add_argument("--periods", type=int, default=int(os.getenv("NEUXSBOT_PERIODS", "200")))
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        client = LotteryApiClient(args.api_base_url, token=args.token)
        records = client.fetch_history_records(LOTTERY_TYPE, periods=args.periods, page_size=200)
        result = analyze(records, periods=args.periods, output_path=args.output)
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
