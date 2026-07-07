#!/usr/bin/env python3
"""测试达梦数据库连接。"""

from dm8_common import build_arg_parser, run_with_connection


def main() -> None:
    parser = build_arg_parser("测试达梦数据库连接")
    args = parser.parse_args()

    def handler(conn, args):
        cur = conn.cursor()
        cur.execute("SELECT SVR_VERSION FROM V$INSTANCE")
        version_row = cur.fetchone()
        cur.execute("SELECT USER FROM DUAL")
        user_row = cur.fetchone()
        cur.close()
        return {
            "host": args.host,
            "port": args.port,
            "user": args.user,
            "version": version_row[0] if version_row else None,
            "current_user": user_row[0] if user_row else None,
        }

    run_with_connection(handler, args, "连接测试")


if __name__ == "__main__":
    main()
