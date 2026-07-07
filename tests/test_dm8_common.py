"""dm8_common 单元测试：驱动查找、参数解析、JSON 输出。"""

import json
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from dm8_common import (
    DEFAULT_PORT,
    DEFAULT_USER,
    build_arg_parser,
    find_driver,
    get_schema,
    output_json,
)


class TestFindDriver:
    """驱动查找逻辑。"""

    def test_find_driver_returns_existing_path(self, tmp_path):
        jar = tmp_path / "DmJdbcDriver18.jar"
        jar.write_text("fake")
        with mock.patch("dm8_common.DRIVER_SEARCH_PATHS", [str(jar)]):
            assert find_driver() == str(jar)

    def test_find_driver_raises_when_not_found(self):
        with mock.patch("dm8_common.DRIVER_SEARCH_PATHS", ["/nonexistent/x.jar"]):
            with pytest.raises(FileNotFoundError):
                find_driver()


class TestArgParser:
    """参数解析。"""

    def test_default_values(self):
        parser = build_arg_parser("test")
        args = parser.parse_args(["--password", "secret"])
        assert args.host == "localhost"
        assert args.port == DEFAULT_PORT
        assert args.user == DEFAULT_USER
        assert args.password == "secret"
        assert args.database is None
        assert args.schema is None

    def test_password_required(self):
        parser = build_arg_parser("test")
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_custom_values(self):
        parser = build_arg_parser("test")
        args = parser.parse_args(
            ["--host", "10.0.0.1", "--port", "6236", "--user", "TEST", "--password", "p", "--schema", "SCH"]
        )
        assert args.host == "10.0.0.1"
        assert args.port == 6236
        assert args.user == "TEST"
        assert args.schema == "SCH"


class TestGetSchema:
    """schema 解析优先级。"""

    def test_explicit_schema_wins(self):
        ns = mock.Mock(user="sysdba", schema="MYSCH")
        assert get_schema(ns) == "MYSCH"

    def test_fallback_to_uppercase_user(self):
        ns = mock.Mock(user="sysdba", schema=None)
        assert get_schema(ns) == "SYSDBA"


class TestOutputJson:
    """JSON 输出格式与退出码。"""

    def test_success_output(self, capsys):
        output_json(True, data={"k": 1}, message="ok")
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is True
        assert out["data"] == {"k": 1}
        assert out["message"] == "ok"

    def test_failure_exits_nonzero(self, capsys):
        with pytest.raises(SystemExit) as exc:
            output_json(False, message="err")
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is False
