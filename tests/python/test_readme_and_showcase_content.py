import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
SHOWCASE_MODULE_PATH = REPO_ROOT / "docs" / "screenshots" / "generate_terminal_showcase.py"

EXPECTED_KEYWORDS = [
    "福彩3D",
    "排列3",
    "双色球",
    "大乐透",
    "排列5",
    "七星彩",
    "快乐8",
]

BANNED_README_TEXT = "不包含网站后台、账号系统、数据采集系统和桌面端源码。"


def load_showcase_module():
    spec = importlib.util.spec_from_file_location("terminal_showcase", SHOWCASE_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReadmeAndShowcaseContentTests(unittest.TestCase):
    def test_readme_contains_all_lottery_keywords(self):
        readme = README_PATH.read_text(encoding="utf-8")
        for keyword in EXPECTED_KEYWORDS:
            self.assertIn(keyword, readme)

    def test_readme_does_not_include_banned_sentence(self):
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertNotIn(BANNED_README_TEXT, readme)

    def test_showcase_uses_human_readable_chinese_titles(self):
        module = load_showcase_module()

        self.assertEqual(module.SCREENSHOTS["terminal-fc3d.svg"]["title"], "福彩3D逆向推演预测系统")
        self.assertEqual(module.SCREENSHOTS["terminal-ssq.svg"]["title"], "量子级双色球全匹配深度分析系统")
        self.assertEqual(module.SCREENSHOTS["terminal-dlt.svg"]["title"], "高性能大乐透分析程序")
        self.assertEqual(module.SCREENSHOTS["terminal-help.svg"]["badge"], "真实命令行界面")


if __name__ == "__main__":
    unittest.main()
