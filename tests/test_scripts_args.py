"""操作脚本参数解析测试（不连接真实数据库）。"""

import json
import os
import sys
import importlib

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS_DIR, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestQueryScriptArgs:
    def test_query_or_file_required(self):
        mod = load_script("dm8_query")
        with pytest.raises(SystemExit):
            sys.argv = ["dm8_query.py", "--password", "p"]
            try:
                mod.main()
            except SystemExit:
                raise
            except Exception:
                pass

    def test_query_and_file_mutually_exclusive(self):
        mod = load_script("dm8_query")
        with pytest.raises(SystemExit):
            sys.argv = ["dm8_query.py", "--password", "p", "--query", "SELECT 1", "--file", "x.sql"]
            try:
                mod.main()
            except SystemExit:
                raise
            except Exception:
                pass


class TestSchemaScriptArgs:
    def test_table_required(self):
        mod = load_script("dm8_schema")
        with pytest.raises(SystemExit):
            sys.argv = ["dm8_schema.py", "--password", "p"]
            try:
                mod.main()
            except SystemExit:
                raise
            except Exception:
                pass


class TestAllScriptsHaveHelp:
    """所有脚本必须可正常解析 --help。"""

    @pytest.mark.parametrize("name", ["dm8_connect", "dm8_tables", "dm8_schema", "dm8_query", "dm8_info"])
    def test_help_exits_zero(self, name, capsys):
        mod = load_script(name)
        with pytest.raises(SystemExit) as exc:
            sys.argv = [f"{name}.py", "--help"]
            mod.main()
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "--password" in out


class TestGetDriverScript:
    """dm8_get_driver.py 参数解析与降级行为（不依赖真实容器）。"""

    def test_help_exits_zero(self, capsys):
        mod = load_script("dm8_get_driver")
        with pytest.raises(SystemExit) as exc:
            sys.argv = ["dm8_get_driver.py", "--help"]
            mod.main()
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "--container" in out

    def test_no_driver_returns_actionable_message(self, capsys, monkeypatch, tmp_path):
        """无容器无安装时，应输出三种可操作替代方案并退出码 1。"""
        mod = load_script("dm8_get_driver")
        # 无已安装路径
        monkeypatch.setattr(mod, "INSTALLED_PATHS", ["/nonexistent/x.jar"])
        # 无 docker
        monkeypatch.setattr(mod.shutil, "which", lambda _: None)
        # assets 指向临时目录避免污染
        monkeypatch.setattr(mod, "ASSETS_DIR", str(tmp_path / "assets"))
        monkeypatch.setattr(mod, "TARGET_PATH", str(tmp_path / "assets" / "DmJdbcDriver18.jar"))

        with pytest.raises(SystemExit) as exc:
            sys.argv = ["dm8_get_driver.py"]
            mod.main()
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["success"] is False
        assert "eco.dameng.com" in out["message"]
