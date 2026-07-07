#!/usr/bin/env python3
"""查看指定表结构。"""

from dm8_common import build_arg_parser, get_schema, run_with_connection


def main() -> None:
    parser = build_arg_parser("查看指定表结构")
    parser.add_argument("--table", required=True, help="表名 (必填)")
    args = parser.parse_args()
    schema = get_schema(args)

    def handler(conn, args):
        cur = conn.cursor()
        cur.execute(
            "SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, COMMENTS "
            "FROM ALL_TAB_COLUMNS C "
            "LEFT JOIN ALL_COL_COMMENTS M "
            "ON C.OWNER = M.OWNER AND C.TABLE_NAME = M.TABLE_NAME AND C.COLUMN_NAME = M.COLUMN_NAME "
            "WHERE C.OWNER = ? AND C.TABLE_NAME = ? "
            "ORDER BY C.COLUMN_ID",
            (schema, args.table.upper())
        )
        rows = cur.fetchall()
        cur.close()
        return {
            "schema": schema,
            "table": args.table.upper(),
            "columns": [
                {
                    "name": r[0],
                    "type": r[1],
                    "length": r[2],
                    "nullable": r[3] == "Y",
                    "comment": r[4],
                }
                for r in rows
            ],
        }

    run_with_connection(handler, args, "查看表结构")


if __name__ == "__main__":
    main()
