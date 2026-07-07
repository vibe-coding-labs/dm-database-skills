#!/usr/bin/env python3
"""执行 SQL 查询。"""

from dm8_common import build_arg_parser, run_with_connection


def main() -> None:
    parser = build_arg_parser("执行 SQL 查询")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", help="要执行的 SQL 语句")
    group.add_argument("--file", help="包含 SQL 的文件路径")
    args = parser.parse_args()

    sql = args.query
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            sql = f.read().strip()

    is_select = sql.lstrip().upper().startswith("SELECT")

    def handler(conn, args):
        cur = conn.cursor()
        cur.execute(sql)
        if is_select:
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            cur.close()
            return {
                "sql": sql,
                "columns": columns,
                "row_count": len(rows),
                "rows": [list(r) for r in rows],
            }
        else:
            conn.commit()
            rowcount = cur.rowcount
            cur.close()
            return {"sql": sql, "affected_rows": rowcount}

    run_with_connection(handler, args, "执行查询")


if __name__ == "__main__":
    main()
