import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools import is_safe_url, run_tool


def test_blocks_localhost_and_private():
    assert not is_safe_url("http://localhost:8000")
    assert not is_safe_url("http://127.0.0.1/admin")
    assert not is_safe_url("http://192.168.1.1")
    assert not is_safe_url("file:///etc/passwd")


def test_unknown_tool():
    assert "Unknown tool" in run_tool("nope", {})


def test_fetch_refuses_unsafe():
    assert run_tool("fetch_page", {"url": "http://127.0.0.1"}).startswith("Refused")
