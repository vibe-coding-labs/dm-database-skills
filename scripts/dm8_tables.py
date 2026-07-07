#!/usr/bin/env python3
"""列出指定 schema 下所有表。"""

from dm8_common import build_arg_parser, get_schema, run_with_connection


def main() -> None:
    parser = build_arg_parser("列出指定 schema 下所有表")
    args = parser.parse_args()
    schema = get_schema(args)

    def handler(conn, args):
        cur = conn.cursor()
        cur.execute(
            "SELECT TABLE_NAME, COMMENTS FROM ALL_TAB_COMMENTS "
            "WHERE OWNER = ? AND TABLE_TYPE = 'TABLE' ORDER BY TABLE_NAME",
            (schema,)
        )
        rows = cur.fetchall()
        cur.close()
        return {
            "schema": schema,
            "count": len(rows),
            "tables": [{"name": r[0], "comment": r[1]} for r in rows],
        }

    run_with_connection(handler, args, "列出表")


if __name__ == "__main__":
    main()
