#!/usr/bin/env python3
"""查看数据库实例基本信息。"""

from dm8_common import build_arg_parser, run_with_connection


def main() -> None:
    parser = build_arg_parser("查看数据库实例基本信息")
    args = parser.parse_args()

    def handler(conn, args):
        cur = conn.cursor()
        info = {}

        queries = {
            "instance": "SELECT NAME, SVR_VERSION, STATUS$ FROM V$INSTANCE",
            "database": "SELECT NAME, CREATE_TIME FROM V$DATABASE",
            "port": "SELECT SF_GET_PARA_VALUE(1, 'PORT_NUM')",
            "case_sensitive": "SELECT SF_GET_PARA_VALUE(1, 'COMPATIBLE_MODE')",
        }

        for key, sql in queries.items():
            try:
                cur.execute(sql)
                info[key] = [list(r) for r in cur.fetchall()]
            except Exception as e:
                info[key] = f"查询失败: {e}"

        cur.close()
        return info

    run_with_connection(handler, args, "查看数据库信息")


if __name__ == "__main__":
    main()
