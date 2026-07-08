"""dm8_common 连接逻辑回归测试：验证 JDBC URL 拼接与 preflight 预检。"""

import os
import sys
import argparse
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import dm8_common


def make_args(**over):
    base = dict(host="127.0.0.1", port=5236, user="SYSDBA", password="p",
                database=None, schema=None)
    base.update(over)
    return argparse.Namespace(**base)


class TestJdbcUrlConstruction:
    """验证 get_connection 拼接的 JDBC URL 正确包含 host/port/database/schema。"""

    def _capture_url(self, args):
        """mock jaydebeapi.connect，捕获实际传入的 url 参数。"""
        captured = {}
        def fake_connect(driver_class, url, creds, driver_path):
            captured["url"] = url
            captured["creds"] = creds
            return mock.MagicMock()
        with mock.patch("dm8_common.find_driver", return_value="/fake/driver.jar"), \
             mock.patch.dict(sys.modules, {"jaydebeapi": mock.MagicMock(connect=fake_connect)}):
            dm8_common.get_connection(args)
        return captured

    def test_url_without_database(self):
        cap = self._capture_url(make_args())
        assert cap["url"] == "jdbc:dm://127.0.0.1:5236"

    def test_url_with_database(self):
        """P1 回归：--database 必须拼入 URL。"""
        cap = self._capture_url(make_args(database="DAMENG"))
        assert "DAMENG" in cap["url"], f"database 未拼入 URL: {cap['url']}"

    def test_url_with_database_and_schema(self):
        cap = self._capture_url(make_args(database="DAMENG", schema="SCH"))
        assert "DAMENG" in cap["url"] and "SCH" in cap["url"]


class TestPreflight:
    """P2 回归：preflight 在缺依赖/缺驱动时给出可操作提示。"""

    def test_preflight_passes_when_deps_and_driver_present(self, tmp_path):
        jar = tmp_path / "DmJdbcDriver18.jar"
        jar.write_text("fake")
        fake_jaydebeapi = mock.MagicMock()
        with mock.patch("dm8_common.DRIVER_SEARCH_PATHS", [str(jar)]), \
             mock.patch.dict(sys.modules, {"jaydebeapi": fake_jaydebeapi}):
            # 不抛异常即通过
            dm8_common.preflight()

    def test_preflight_reports_missing_dependency(self):
        """缺 jaydebeapi 时提示 pip install 命令。"""
        with mock.patch.dict(sys.modules, {"jaydebeapi": None}):
            with pytest.raises(dm8_common.PreflightError) as exc:
                dm8_common.preflight()
        assert "pip install jaydebeapi" in str(exc.value)

    def test_preflight_reports_missing_driver(self):
        """缺驱动时提示放置位置。"""
        fake_jaydebeapi = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"jaydebeapi": fake_jaydebeapi}), \
             mock.patch("dm8_common.DRIVER_SEARCH_PATHS", ["/nonexistent/x.jar"]):
            with pytest.raises(dm8_common.PreflightError) as exc:
                dm8_common.preflight()
        assert "DmJdbcDriver18.jar" in str(exc.value)
