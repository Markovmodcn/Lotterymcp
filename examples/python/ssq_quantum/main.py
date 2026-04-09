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
from common.ssq_analysis import analyze_ssq_records


LOTTERY_TYPE = "ssq"
DISPLAY_NAME = "双色球"
PROGRAM_NAME = "双色球全匹配深度分析程序"


def analyze(records: list[dict[str, Any]], periods: int) -> dict[str, Any]:
    result = {
        "lotteryType": LOTTERY_TYPE,
        "displayName": DISPLAY_NAME,
        "programName": PROGRAM_NAME,
        "periods": periods,
    }
    result.update(analyze_ssq_records(records))
    return result


def print_analysis(result: dict[str, Any]) -> None:
    print_section(PROGRAM_NAME)
    print(f"分析期数: {result['periods']}")
    print(f"有效记录: {result['recordCount']}")
    if result.get("recordCount", 0) == 0:
        print(result["message"])
        return

    print(f"最新期号: {result['latestPeriod']}")
    print(f"最新红球: {' '.join(str(item) for item in result['latestReds'])}")
    print(f"最新蓝球: {result['latestBlue']}")
    print(f"理论组合数: {result['theoreticalCombinations']}")
    print(f"理论重复概率: {result['theoreticalRepeatProbability']}")
    print(f"红球热度 Top10: {result['redFrequencyTop']}")
    print(f"蓝球热度 Top8: {result['blueFrequencyTop']}")
    print(f"完全重号组数: {len(result['exactMatches'])}")
    print(f"近似重号组数: {len(result['nearMatches'])}")
    print(f"真实成功案例: {len(result.get('trueSuccessCases', []))}")
    probability_model = result.get("probabilityModel", {})
    if probability_model:
        print(
            "概率模型: "
            f"精确重复={probability_model.get('exactRepeatProbability')} | "
            f"4红以上={probability_model.get('redOverlap4PlusProbability')} | "
            f"5红以上={probability_model.get('redOverlap5PlusProbability')}"
        )
    cluster_summary = result.get("clusterSummary", [])
    if cluster_summary:
        top_cluster = cluster_summary[0]
        print(
            "模式簇: "
            f"簇#{top_cluster['clusterId']} | 样本={top_cluster['size']} | "
            f"分区={top_cluster['zonePattern']} | 奇偶={top_cluster['oddEven']}"
        )
    markov_transitions = result.get("markovTransitionsTop", [])
    if markov_transitions:
        top_transition = markov_transitions[0]
        print(
            "马尔科夫转移: "
            f"{top_transition['from']:02d} -> {top_transition['to']:02d} | "
            f"概率={top_transition['probability']}"
        )
    print("")
    print("高分推荐:")
    for item in result.get("topRecommendations", [])[:5]:
        print(
            f"  红球={item['reds']} | 蓝球={item['blue']} | 分数={item['score']:.6f} | "
            f"分区={item['zonePattern']} | 和值={item['sum']}"
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
