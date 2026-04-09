from __future__ import annotations

from html import escape
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent


SCREENSHOTS = {
    "terminal-help.svg": {
        "title": "Lotterymcp CLI",
        "badge": "真实命令输出",
        "command": "npx --yes lotterymcp@latest --help",
        "lines": [
            "临时打开菜单:",
            "  npx --yes lotterymcp@latest",
            "",
            "全局安装:",
            "  npm i -g lotterymcp",
            "",
            "可用命令:",
            "  serve            启动 MCP stdio 服务",
            "  init             生成本地配置文件",
            "  doctor           检查当前配置和网站连通性",
            "  login            打开官网账号页并获取 Token",
            "  analyze          直接运行 Python 分析程序",
            "",
            "官网: www.neuxsbot.com",
            "传输方式: stdio",
            "彩种: 由 AI 对话动态传入，不写死在本地配置",
        ],
    },
    "terminal-fc3d.svg": {
        "title": "福彩3D 示例分析",
        "badge": "示例输出",
        "command": "lotterymcp analyze fc3d --periods 30",
        "lines": [
            "示例数据来源: 仓库内置离线样本",
            "分析期数: 30",
            "有效记录: 30",
            "最新期号: 1",
            "最新号码: 1 2 3",
            "反推命中案例: 4",
            "最佳历史长度: 100",
            "类型分布: group3=2, group6=2",
            "回测验证: 完全命中 1 次 | 两码命中 2 次 | 样本 3 期",
            "",
            "高分推荐:",
            "  号码=123 | 类型=direct | 分数=0.987654 | 和值=6 | 奇偶=2:1",
            "",
            "结果文件: results/fc3d-analysis-demo.json",
        ],
    },
    "terminal-ssq.svg": {
        "title": "双色球 示例分析",
        "badge": "示例输出",
        "command": "lotterymcp analyze ssq --periods 30",
        "lines": [
            "示例数据来源: 仓库内置离线样本",
            "分析期数: 30",
            "有效记录: 3",
            "最新期号: 3",
            "最新红球: 1 2 3 4 5 6",
            "最新蓝球: 7",
            "红球热度 Top5: 1, 2, 3, 4, 5",
            "蓝球热度 Top2: 7, 9",
            "重复概率: 精确 1.693e-07 | 近似 4+ 0.0049008278",
            "",
            "高分推荐:",
            "  红球=1 2 3 4 5 6 | 蓝球=7 | 分数=1.872222",
            "  分区=6-0-0 | 和值=21",
            "",
            "结果文件: results/ssq-analysis-demo.json",
        ],
    },
    "terminal-dlt.svg": {
        "title": "大乐透 示例分析",
        "badge": "示例输出",
        "command": "lotterymcp analyze dlt --periods 30",
        "lines": [
            "示例数据来源: 仓库内置离线样本",
            "分析期数: 30",
            "有效记录: 3",
            "最新期号: 3",
            "最新前区: 1 2 3 4 5",
            "最新后区: 1 2",
            "前区热度 Top5: 1, 2, 3, 5, 7",
            "后区热度 Top3: 1, 2, 3",
            "回测样本: 1 期 | 前区均命中 3.0000 | 后区均命中 1.0000",
            "总均命中: 4.0000",
            "",
            "高分推荐:",
            "  前区=1 2 3 4 5 | 后区=1 2 | 分数=0.740000",
            "  前区分区=5-0-0 | 后区分区=2-0",
        ],
    },
}


def render_terminal_svg(title: str, badge: str, command: str, lines: list[str]) -> str:
    width = 1600
    line_height = 42
    content_top = 184
    content_height = max(680, content_top + (len(lines) + 3) * line_height)
    height = content_height + 80

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">',
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#09111b" />',
        '<stop offset="100%" stop-color="#111b29" />',
        "</linearGradient>",
        '<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#0f1723" />',
        '<stop offset="100%" stop-color="#111827" />',
        "</linearGradient>",
        "</defs>",
        '<rect width="1600" height="100%" fill="url(#bg)" />',
        '<rect x="44" y="40" width="1512" height="{0}" rx="28" fill="url(#panel)" stroke="#223147" stroke-width="2"/>'.format(height - 80),
        '<rect x="44" y="40" width="1512" height="74" rx="28" fill="#0b1220" />',
        '<circle cx="92" cy="77" r="10" fill="#ff5f57" />',
        '<circle cx="124" cy="77" r="10" fill="#febc2e" />',
        '<circle cx="156" cy="77" r="10" fill="#28c840" />',
        f'<text x="220" y="87" fill="#e6edf3" font-size="30" font-family="Consolas, Monaco, \'Courier New\', monospace">{escape(title)}</text>',
        f'<rect x="1260" y="56" width="228" height="40" rx="20" fill="#17314c" stroke="#2d4b69"/>',
        f'<text x="1374" y="82" text-anchor="middle" fill="#8bc5ff" font-size="22" font-family="Consolas, Monaco, \'Courier New\', monospace">{escape(badge)}</text>',
        f'<text x="88" y="154" fill="#7ee787" font-size="28" font-family="Consolas, Monaco, \'Courier New\', monospace">$ {escape(command)}</text>',
    ]

    y = content_top
    for line in lines:
        safe = escape(line)
        color = "#d7e2f0"
        if line.startswith("高分推荐"):
            color = "#8bc5ff"
        if "示例数据来源" in line:
            color = "#f2cc60"
        if "结果文件" in line:
            color = "#7ee787"
        body.append(
            f'<text x="88" y="{y}" fill="{color}" font-size="28" font-family="Consolas, Monaco, \'Courier New\', monospace">{safe}</text>'
        )
        y += line_height

    body.extend(
        [
            f'<text x="88" y="{height - 34}" fill="#5f728c" font-size="22" font-family="Consolas, Monaco, \'Courier New\', monospace">NEUXSBOT • www.neuxsbot.com</text>',
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
