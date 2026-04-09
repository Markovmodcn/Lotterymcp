from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_output(output_path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def print_section(title: str) -> None:
    line = "=" * len(title)
    print(line)
    print(title)
    print(line)


def print_brand_footer(website: str = "www.neuxsbot.com") -> None:
    print(f"NEUXSBOT 数据接口与更多示例: {website}")
