#!/usr/bin/env python3
"""达梦数据库公共模块：参数解析、驱动查找、JDBC 连接、统一 JSON 输出。"""

import argparse
import json
import os
import sys
from typing import Any


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5236
DEFAULT_USER = "SYSDBA"
DEFAULT_SCHEMA = "SYSDBA"

DRIVER_CLASS = "dm.jdbc.driver.DmDriver"
JDBC_URL_TEMPLATE = "jdbc:dm://{host}:{port}"

# 驱动查找顺序（与 SKILL.md 文档一致）
DRIVER_SEARCH_PATHS = [
    # 1. 项目内置 assets 目录
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "DmJdbcDriver18.jar"),
    # 2. 环境变量 DM_HOME 指向的 drivers/jdbc/
    os.path.join(os.environ.get("DM_HOME", ""), "drivers", "jdbc", "DmJdbcDriver18.jar"),
    # 3. Linux 系统默认安装位置
    "/opt/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
    # 4. macOS Homebrew 风格
    "/usr/local/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
]


def find_driver() -> str:
    """按优先级查找 DmJdbcDriver18.jar，找不到则抛异常。"""
    for path in DRIVER_SEARCH_PATHS:
        if path and os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "未找到 DmJdbcDriver18.jar。请将驱动放置于 assets/ 目录，"
        "或设置 DM_HOME 环境变量，或安装达梦客户端。查找位置: "
        + " | ".join(p for p in DRIVER_SEARCH_PATHS if p)
    )


def build_arg_parser(description: str) -> argparse.ArgumentParser:
    """构建统一的连接参数解析器。"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"数据库主机地址 (默认: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"数据库端口 (默认: {DEFAULT_PORT})")
    parser.add_argument("--user", default=DEFAULT_USER, help=f"数据库用户名 (默认: {DEFAULT_USER})")
    parser.add_argument("--password", required=True, help="数据库密码 (必填)")
    parser.add_argument("--database", default=None, help="数据库名称 (可选)")
    parser.add_argument("--schema", default=None, help="Schema 名称 (默认: 用户名)")
    return parser


def get_connection(args: argparse.Namespace):
    """建立 JDBC 连接，返回 connection 对象。"""
    import jaydebeapi

    driver_path = find_driver()
    jdbc_url = JDBC_URL_TEMPLATE.format(host=args.host, port=args.port)
    if args.database:
        jdbc_url = f"{jdbc_url}?schema={args.schema or args.user}" if args.schema else jdbc_url

    conn = jaydebeapi.connect(
        DRIVER_CLASS,
        jdbc_url,
        [args.user, args.password],
        driver_path,
    )
    return conn


def get_schema(args: argparse.Namespace) -> str:
    """返回实际使用的 schema（参数优先，否则用用户名）。"""
    return args.schema or args.user.upper()


def output_json(success: bool, data: Any = None, message: str = "") -> None:
    """统一 JSON 输出，确保脚本退出码反映成功与否。"""
    print(json.dumps({"success": success, "data": data, "message": message}, ensure_ascii=False, indent=2))
    if not success:
        sys.exit(1)


def run_with_connection(handler, args: argparse.Namespace, action_desc: str) -> None:
    """通用执行模板：连接 -> 执行 handler(conn, args) -> 输出结果 -> 关闭连接。"""
    try:
        conn = get_connection(args)
        try:
            result = handler(conn, args)
            output_json(True, data=result, message=f"{action_desc}成功")
        finally:
            conn.close()
    except FileNotFoundError as e:
        output_json(False, message=str(e))
    except Exception as e:
        output_json(False, message=f"{action_desc}失败: {type(e).__name__}: {e}")
