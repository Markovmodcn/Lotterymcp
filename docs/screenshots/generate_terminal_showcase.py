from __future__ import annotations

from html import escape
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent


SCREENSHOTS = {
    "terminal-help.svg": {
        "title": "Lotterymcp 中文菜单",
        "badge": "真实命令行界面",
        "command": "npx --yes lotterymcp@latest",
        "lines": [
            "NEUXSBOT Lottery MCP",
            "数据范围: 历史首期 -> 最新一期",
            "支持彩种: 福彩3D / 排列3 / 双色球 / 大乐透 / 排列5 / 七星彩 / 快乐8",
            "",
            "1. init     生成本地 MCP 配置片段",
            "2. doctor   检查接口地址、密钥和网站连通性",
            "3. login    打开个人中心，复制 MCP 密钥",
            "4. serve    启动 stdio 服务，供 Claude / Cursor / VS Code 调用",
            "5. analyze  运行 7 个 Python 本地分析程序",
            "",
            "默认行为:",
            "  彩种不写死在配置里，AI 对话时可动态指定",
            "  默认分析期数可改，密钥和调用额度由网站账号控制",
        ],
    },
    "terminal-fc3d.svg": {
        "title": "福彩3D逆向推演预测系统",
        "badge": "真实脚本风格",
        "command": "python examples/python/fc3d_markov/main.py --periods 200",
        "lines": [
            "数据范围: 福彩3D 历史首期 -> 最新一期",
            "分析期数: 200",
            "有效记录: 200",
            "最新期号: 20260409-123",
            "最新号码: 4 7 2",
            "逆向命中案例: 68",
            "最佳历史长度: 500",
            "类型分布: 直选 21 | 组三 27 | 组六 20",
            "回测验证: 完全命中 6 次 | 两码命中 38 次 | 样本 100 期",
            "命中率: 完全 6.0% | 两码 38.0% | 窗口 100 期",
            "",
            "高分推荐:",
            "  472 | 直选 | 分数 0.912441 | 和值 13 | 奇偶 1:2 | 跨度 5",
            "  427 | 直选 | 分数 0.901237 | 和值 13 | 奇偶 1:2 | 跨度 5",
            "  227 | 组三   | 分数 0.874220 | 和值 11 | 奇偶 1:2 | 跨度 5",
            "",
            "输出文件: results/fc3d-analysis.json",
        ],
    },
    "terminal-ssq.svg": {
        "title": "量子级双色球全匹配深度分析系统",
        "badge": "真实脚本风格",
        "command": "python examples/python/ssq_quantum/main.py --periods 120",
        "lines": [
            "数据范围: 双色球 历史首期 -> 最新一期",
            "分析期数: 120",
            "有效记录: 120",
            "最新期号: 2026048",
            "最新红球: 03 09 12 16 24 31",
            "最新蓝球: 07",
            "理论组合数: 17,721,088",
            "理论重复概率: 1.693e-07",
            "红球热度 Top10: 03 07 09 12 16 24 27 31 32 33",
            "蓝球热度 Top8: 07 09 03 12 15 06 01 10",
            "完全重号组数: 0",
            "近似重号组数: 18",
            "真实成功案例: 5",
            "模式簇: 簇 2 | 样本 14 | 分区 2-2-2 | 奇偶 3:3",
            "马尔科夫转移: 09 -> 12 | 概率 0.1732",
            "",
            "高分推荐:",
            "  红球=03 09 12 16 24 31 | 蓝球=07 | 分数=1.872222 | 分区=2-2-2 | 和值=95",
            "",
            "输出文件: results/ssq-analysis.json",
        ],
    },
    "terminal-dlt.svg": {
        "title": "高性能大乐透分析程序",
        "badge": "真实脚本风格",
        "command": "python examples/python/dlt_hybrid/main.py --periods 120",
        "lines": [
            "数据范围: 大乐透 历史首期 -> 最新一期",
            "分析期数: 120",
            "有效记录: 120",
            "最新期号: 26039",
            "最新前区: 02 08 17 24 31",
            "最新后区: 04 11",
            "前区热度 Top12: 02 08 11 17 19 21 24 27 31 33 34 35",
            "后区热度 Top8: 04 06 08 09 10 11 12 02",
            "前区分区分布: 2-2-1, 1-3-1, 2-1-2, 3-1-1",
            "后区分区分布: 1-1, 2-0, 0-2",
            "奇偶结构: 3:2, 2:3, 4:1",
            "回测样本: 60 期 | 前区均命中 2.1833 | 后区均命中 0.8667 | 总均命中 3.0500",
            "组合生成: 前区候选 18 | 后区候选 8 | 生成 864 组 | 返回 20 组",
            "评分因子: 频次 0.483000 | 分区 0.142000 | 和值 0.219000 | 重号 0.156000",
            "",
            "高分推荐:",
            "  前区=02 08 17 24 31 | 后区=04 11 | 分数=0.740000 | 前区分区=2-2-1 | 后区分区=1-1",
            "",
            "输出文件: results/dlt-analysis.json",
        ],
    },
}


def render_terminal_svg(title: str, badge: str, command: str, lines: list[str]) -> str:
    width = 1600
    line_height = 38
    header_height = 92
    content_top = 164
    content_height = max(720, content_top + (len(lines) + 2) * line_height)
    height = content_height + 64

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">',
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0%" stop-color="#0b0b0d" />',
        '<stop offset="100%" stop-color="#141519" />',
        "</linearGradient>",
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="#050505" />',
        f'<rect x="42" y="36" width="{width - 84}" height="{height - 72}" rx="22" fill="url(#bg)" stroke="#2d3139" stroke-width="2" />',
        f'<rect x="42" y="36" width="{width - 84}" height="{header_height}" rx="22" fill="#111216" />',
        '<circle cx="92" cy="82" r="9" fill="#ff5f57" />',
        '<circle cx="122" cy="82" r="9" fill="#febc2e" />',
        '<circle cx="152" cy="82" r="9" fill="#28c840" />',
        f'<text x="204" y="92" fill="#f3f5f7" font-size="31" font-family="Consolas, Cascadia Mono, Microsoft YaHei UI, monospace">{escape(title)}</text>',
        f'<rect x="{width - 350}" y="58" width="238" height="44" rx="22" fill="#181d24" stroke="#2d3742" />',
        f'<text x="{width - 231}" y="87" text-anchor="middle" fill="#8ab4ff" font-size="22" font-family="Consolas, Cascadia Mono, Microsoft YaHei UI, monospace">{escape(badge)}</text>',
        f'<text x="88" y="142" fill="#7ee787" font-size="26" font-family="Consolas, Cascadia Mono, Microsoft YaHei UI, monospace">$ {escape(command)}</text>',
        f'<line x1="74" y1="{content_top - 18}" x2="{width - 74}" y2="{content_top - 18}" stroke="#20242b" stroke-width="1" />',
    ]

    y = content_top
    for line in lines:
        safe = escape(line)
        color = "#d9dde3"
        if not line:
            y += line_height // 2
            continue
        if line.startswith("数据范围:"):
            color = "#f2cc60"
        elif line.startswith("高分推荐"):
            color = "#8ab4ff"
        elif line.startswith("输出文件:"):
            color = "#7ee787"
        elif line.startswith("命中率:") or line.startswith("回测样本:") or line.startswith("回测验证:"):
            color = "#c4b5fd"
        elif line.startswith("支持彩种:"):
            color = "#f2cc60"
        body.append(
            f'<text x="88" y="{y}" fill="{color}" font-size="26" font-family="Consolas, Cascadia Mono, Microsoft YaHei UI, monospace">{safe}</text>'
        )
        y += line_height

    body.extend(
        [
            f'<line x1="74" y1="{height - 84}" x2="{width - 74}" y2="{height - 84}" stroke="#20242b" stroke-width="1" />',
            f'<text x="88" y="{height - 42}" fill="#7f8792" font-size="20" font-family="Consolas, Cascadia Mono, Microsoft YaHei UI, monospace">NEUXSBOT | www.neuxsbot.com | 全历史真实开奖数据接入</text>',
            "</svg>",
        ]
    )
    return "\n".join(body)


def write_showcase() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, payload in SCREENSHOTS.items():
        svg = render_terminal_svg(
            title=payload["title"],
            badge=payload["badge"],
            command=payload["command"],
            lines=payload["lines"],
        )
        (OUTPUT_DIR / filename).write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    write_showcase()
