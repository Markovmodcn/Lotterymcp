import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXAMPLES_ROOT = REPO_ROOT / "examples" / "python"
if str(PYTHON_EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_EXAMPLES_ROOT))

from common.api_client import LotteryApiClient, LotteryApiError  # noqa: E402


class FakeResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class ApiClientTests(unittest.TestCase):
    def test_request_json_surfaces_human_readable_rate_limit_message(self):
        def opener(_request):
            raise HTTPError(
                url="https://www.neuxsbot.com/api/v1/mcp/lottery/history",
                code=429,
                msg="Too Many Requests",
                hdrs=None,
                fp=None,
            )

        client = LotteryApiClient("https://www.neuxsbot.com", opener=opener)

        with self.assertRaises(LotteryApiError) as context:
            client.request_json("lottery/history", {"lotteryType": "pl5", "page": 1, "limit": 20})

        message = str(context.exception)
        self.assertIn("429", message)
        self.assertIn("请求过于频繁", message)

    def test_request_json_retries_rate_limit_then_succeeds(self):
        attempts = {"count": 0}

        def opener(_request):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise HTTPError(
                    url="https://www.neuxsbot.com/api/v1/mcp/lottery/history",
                    code=429,
                    msg="Too Many Requests",
                    hdrs={"Retry-After": "0"},
                    fp=None,
                )
            return FakeResponse('{"data":[1],"meta":{"hasMore":false}}')

        client = LotteryApiClient("https://www.neuxsbot.com", opener=opener)
        with patch("common.api_client.time.sleep") as sleep_mock:
            payload = client.request_json("lottery/history", {"lotteryType": "pl5", "page": 1, "limit": 20})

        self.assertEqual(payload["data"], [1])
        self.assertEqual(attempts["count"], 2)
        sleep_mock.assert_called_once()

    def test_request_json_raises_after_rate_limit_retries_exhausted(self):
        def opener(_request):
            raise HTTPError(
                url="https://www.neuxsbot.com/api/v1/mcp/lottery/history",
                code=429,
                msg="Too Many Requests",
                hdrs=None,
                fp=None,
            )

        client = LotteryApiClient("https://www.neuxsbot.com", opener=opener)
        with patch("common.api_client.time.sleep") as sleep_mock:
            with self.assertRaises(LotteryApiError) as context:
                client.request_json("lottery/history", {"lotteryType": "pl5", "page": 1, "limit": 20})

        self.assertIn("429", str(context.exception))
        self.assertGreaterEqual(sleep_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
