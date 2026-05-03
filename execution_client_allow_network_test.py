import json
from unittest.mock import patch

from client import ExecutionEngineClient


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps({"stdout": "ok", "stderr": "", "exit_code": 0}).encode("utf-8")


def test_run_code_forwards_allow_network() -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    with patch("client.request.urlopen", fake_urlopen):
        result = ExecutionEngineClient("http://engine.test").run_code("print('ok')", allow_network=True)

    assert result["stdout"] == "ok"
    assert captured["payload"] == {"code": "print('ok')", "allow_network": True}


if __name__ == "__main__":
    test_run_code_forwards_allow_network()
    print("execution client allow_network tests passed")
