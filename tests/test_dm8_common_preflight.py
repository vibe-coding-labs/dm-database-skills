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
