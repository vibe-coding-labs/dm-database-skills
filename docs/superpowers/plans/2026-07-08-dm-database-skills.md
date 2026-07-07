# 达梦数据库操作 SKILLS 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`
> Steps use checkbox (`- [ ]`) syntax.

**Goal:** 创建一个达梦数据库(DM8)操作 SKILLS，覆盖「下载安装」全流程文档与「连接/查询/管理」工具集脚本，使 Claude 能自主完成达梦数据库的部署与日常操作。

**Architecture:** 下载安装流程以 markdown 文档形式呈现（参考 eco.dameng.com/download/ 的官方产品矩阵：服务端安装包 Win/Linux、客户端工具 disql/DM Manager、JDBC 驱动、DEM），由 SKILL.md 在用户需要安装时引导阅读；工具集脚本采用 Python + JayDeBeApi + JDBC 驱动方案（继承 huangzt/dm8-tools 的架构），提供 connect/tables/schema/query/info/rman 六个脚本，统一 `--host/--port/--user/--password/--database/--schema` 连接参数，输出 JSON，跨平台。两层结合：先按 `references/install.md` 部署达梦实例，再用 `scripts/*.py` 操作它。设计理由：JDBC 驱动是达梦官方推荐的连接方式，兼容性最好；文档与脚本分离便于按需加载，避免 SKILL.md 过长。

**Tech Stack:** Python 3.8+, JayDeBeApi 1.6, JPype1 1.4, DM8 JDBC Driver 18 (DmJdbcDriver18.jar), 达梦 DM8 服务端 (Linux/Windows), disql/dmrman/dminit 命令行工具, Bash/Shell

**Risks:**
- Task 1 创建的 SKILL.md 引用了 Task 3 才创建的脚本 → 缓解：Task 1 先写脚本路径占位说明，Task 3 必须严格使用相同文件名
- Task 4 安装文档中的下载链接需登录账号才能获取 → 缓解：文档明确标注「需登录 eco.dameng.com 账号」，并提供手动下载 + 命令行校验两套方案
- Task 5 的脚本依赖 JDBC 驱动 jar，不同环境驱动路径不同 → 缓解：驱动查找顺序覆盖项目内置/assets/环境变量/系统默认四个位置
- 无现有测试覆盖 → 缓解：Task 6 补充脚本参数解析与输出的单元测试（用 mock，不依赖真实数据库）

---

### Task 1: 创建 SKILL.md 主入口文档 — 定义 SKILL 的能力清单与使用引导

**Depends on:** None
**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: 创建 SKILL.md — 达梦数据库操作技能的主入口，声明能力清单、连接参数、使用引导**

```markdown
---
name: dm-database-skills
description: 达梦数据库(DM8)操作技能。涵盖下载安装部署流程(参考官方 eco.dameng.com/download 产品矩阵)与连接/查询/管理工具集(测试连接、列出表、查看表结构、执行SQL、查看库信息、备份恢复)。当需要安装达梦数据库、操作达梦实例、查询数据、分析表结构、备份恢复时使用此技能。支持 Windows、macOS、Linux 平台，通过命令行参数指定 host/port/user/password/database/schema。可作为 dm8 mcp 服务的替代方案。
---

# 达梦数据库操作 SKILL

提供达梦数据库(DM8)的下载安装引导与连接/查询/管理工具集。

## 能力总览

本 SKILL 分两层：

1. **下载安装层** — 文档化流程，引导从官方下载到完成实例部署
2. **操作工具层** — Python 脚本集，连接已部署实例执行各类操作

## 何时使用

| 场景 | 使用方式 |
|------|---------|
| 用户需要安装达梦数据库 | 阅读 `references/install.md`，按流程下载安装并初始化实例 |
| 需要测试/连接达梦数据库 | 运行 `scripts/dm8_connect.py` |
| 需要列出某 schema 下所有表 | 运行 `scripts/dm8_tables.py` |
| 需要查看表结构 | 运行 `scripts/dm8_schema.py` |
| 需要执行 SQL 查询 | 运行 `scripts/dm8_query.py` |
| 需要查看数据库信息 | 运行 `scripts/dm8_info.py` |
| 需要备份恢复数据库 | 阅读 `references/backup-restore.md` 或使用 dmrman |

## 快速开始

### 前置要求

安装 Python 依赖：

```bash
pip install jaydebeapi JPype1
```

> 工具层使用 JDBC 驱动连接达梦数据库，驱动查找顺序见下方「驱动位置」。

### 连接参数

所有脚本支持以下统一参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 数据库主机地址 | localhost |
| `--port` | 数据库端口 | 5236 |
| `--user` | 数据库用户名 | SYSDBA |
| `--password` | 数据库密码 | 必填 |
| `--database` | 数据库名称 | 可选 |
| `--schema` | Schema 名称 | 用户默认 Schema |

### 驱动位置

脚本按以下顺序查找 `DmJdbcDriver18.jar`：

1. `assets/DmJdbcDriver18.jar`（推荐，项目内置）
2. 环境变量 `DM_HOME` 指向的 `drivers/jdbc/` 子目录
3. 系统默认安装位置（Linux: `/opt/dmdbms/drivers/jdbc/`，Windows: `C:\dmdbms\drivers\jdbc\`）

## 输出格式

所有脚本输出 JSON：

```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

## 达梦数据库特有注意事项

- 使用 Schema 概念（类似 Oracle）
- 系统视图使用 `DBA_*`、`ALL_*`、`USER_*` 命名
- 支持 PL/SQL 语法
- 默认端口为 5236
- 默认管理员用户为 SYSDBA / 密码 SYSDBA001（安装后应立即修改）

## 参考文档

- `references/install.md` — 下载安装与实例初始化完整流程
- `references/backup-restore.md` — 备份恢复操作手册
- `references/common_queries.md` — 常用达梦 SQL 查询模板
```

- [ ] **Step 2: 验证 SKILL.md 格式**
Run: `test -f SKILL.md && head -1 SKILL.md | grep -q '^---' && echo "PASS"`
Expected:
  - Exit code: 0
  - Output contains: "PASS"

- [ ] **Step 3: 提交**
Run: `git add SKILL.md && git commit -m "docs(skill): add dm-database-skills SKILL.md entry with capability overview"`

---

### Task 2: 创建公共连接模块 — 统一 JDBC 连接与参数解析逻辑

**Depends on:** Task 1
**Files:**
- Create: `scripts/dm8_common.py`

- [ ] **Step 1: 创建 dm8_common.py — 封装参数解析、驱动查找、JDBC 连接、JSON 输出，供所有脚本复用**

```python
#!/usr/bin/env python3
"""达梦数据库公共模块：参数解析、驱动查找、JDBC 连接、统一 JSON 输出。"""

import argparse
import json
import os
import sys
from typing import Any, Optional


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
```

- [ ] **Step 2: 验证模块可导入**
Run: `python3 -c "import sys; sys.path.insert(0, 'scripts'); import dm8_common; print(dm8_common.DEFAULT_PORT)"`
Expected:
  - Exit code: 0
  - Output contains: "5236"

- [ ] **Step 3: 提交**
Run: `git add scripts/dm8_common.py && git commit -m "feat(scripts): add dm8_common shared module for JDBC connection and args parsing"`

---

### Task 3: 创建操作工具脚本集 — 连接/列表/结构/查询/信息五个脚本

**Depends on:** Task 2
**Files:**
- Create: `scripts/dm8_connect.py`
- Create: `scripts/dm8_tables.py`
- Create: `scripts/dm8_schema.py`
- Create: `scripts/dm8_query.py`
- Create: `scripts/dm8_info.py`

- [ ] **Step 1: 创建 dm8_connect.py — 测试数据库连接是否可用**

```python
#!/usr/bin/env python3
"""测试达梦数据库连接。"""

import argparse
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
```

- [ ] **Step 2: 创建 dm8_tables.py — 列出指定 schema 下所有表**

```python
#!/usr/bin/env python3
"""列出指定 schema 下所有表。"""

import argparse
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
```

- [ ] **Step 3: 创建 dm8_schema.py — 查看指定表结构（列、类型、注释）**

```python
#!/usr/bin/env python3
"""查看指定表结构。"""

import argparse
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
```

- [ ] **Step 4: 创建 dm8_query.py — 执行任意 SQL 查询并返回结果**

```python
#!/usr/bin/env python3
"""执行 SQL 查询。"""

import argparse
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
```

- [ ] **Step 5: 创建 dm8_info.py — 查看数据库实例基本信息**

```python
#!/usr/bin/env python3
"""查看数据库实例基本信息。"""

import argparse
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
```

- [ ] **Step 6: 验证所有脚本可执行且参数解析正常**
Run: `for s in connect tables schema query info; do python3 scripts/dm8_${s}.py --help >/dev/null 2>&1 && echo "dm8_${s}.py OK" || echo "dm8_${s}.py FAIL"; done`
Expected:
  - Exit code: 0
  - Output contains: "dm8_connect.py OK" and "dm8_query.py OK" and "dm8_info.py OK"

- [ ] **Step 7: 提交**
Run: `git add scripts/dm8_connect.py scripts/dm8_tables.py scripts/dm8_schema.py scripts/dm8_query.py scripts/dm8_info.py && git commit -m "feat(scripts): add dm8 connect/tables/schema/query/info operation scripts"`

---

### Task 4: 创建下载安装文档 — 完整的达梦下载与实例初始化流程

**Depends on:** Task 1
**Files:**
- Create: `references/install.md`

- [ ] **Step 1: 创建 install.md — 达梦数据库下载安装与实例初始化完整流程文档**

```markdown
# 达梦数据库下载安装流程

本文档引导从官方下载达梦数据库到完成实例部署。来源：[达梦在线服务平台](https://eco.dameng.com/download/)。

## 1. 下载

### 1.1 访问下载页

打开 https://eco.dameng.com/download/ ，登录达梦社区账号（未注册需先注册）。

### 1.2 选择产品

达梦官方下载页提供以下产品（以页面实际展示为准）：

| 产品 | 说明 | 适用场景 |
|------|------|---------|
| DM8 开发版（Windows） | Windows 安装包 `.exe` | 本地开发、Windows 服务 |
| DM8 开发版（Linux） | Linux 安装包 `.bin`（含 rpm/iso 形式） | 服务器部署、信创环境 |
| DM8 客户端工具 | disql、DM 管理工具(DMManager) | 远程连接、图形化管理 |
| DM8 JDBC 驱动 | `DmJdbcDriver18.jar` 等 | Java/Python 应用连接 |
| DM8 Python 驱动 | dmPython | Python 原生连接 |
| DEM (达梦企业管理器) | Web 管理平台 | 集中监控管理 |
| 达梦文档 | 安装/管理/SQL/开发手册 | 参考资料 |

> **重要**：下载页为单页应用(SPA)，实际下载链接需登录后由页面动态生成。本 SKILL 的工具脚本所需的 JDBC 驱动，请从下载页获取 `DmJdbcDriver18.jar` 并放置于本项目的 `assets/` 目录。

### 1.3 获取 JDBC 驱动（工具脚本必需）

```bash
# 下载页登录后下载 DmJdbcDriver18.jar，放入项目 assets 目录
mkdir -p assets
cp /path/to/downloaded/DmJdbcDriver18.jar assets/
# 校验文件存在且为有效 jar
unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class
```

## 2. Linux 安装

### 2.1 创建专用用户

达梦官方建议使用非 root 专用用户安装运行：

```bash
# 创建 dmsa 用户组与用户
groupadd dinstall
useradd -g dinstall -m -d /home/dmsa dmsa
passwd dmsa
# 创建安装目录并授权
mkdir -p /opt/dmdbms
chown -R dmsa:dinstall /opt/dmdbms
```

### 2.2 配置系统参数

```bash
# 调整最大文件句柄数（root 执行）
cat >> /etc/security/limits.conf <<'EOF'
dmsa soft nofile 65536
dmsa hard nofile 65536
EOF

# 检查
su - dmsa -c "ulimit -n"
```

### 2.3 挂载并安装

```bash
# 切到 dmsa 用户
su - dmsa
# 赋予安装包执行权限
chmod +x /path/to/DM8Install.bin
# 静默安装（-q 静默模式）
./DM8Install.bin -i
# 按提示选择安装目录 /opt/dmdbms，完成安装
```

## 3. 初始化数据库实例

### 3.1 使用 dminit 创建实例

```bash
# 切到安装目录的 bin
cd /opt/dmdbms/bin
# 初始化实例到 /opt/dmdbms/data
./dminit PATH=/opt/dmdbms/data DB_NAME=DAMENG INSTANCE_NAME=DMSERVER PORT_NUM=5236 SYSDBA_PWD=SYSDBA001
```

关键参数说明：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `PATH` | 实例数据目录 | `/opt/dmdbms/data` |
| `DB_NAME` | 数据库名 | `DAMENG` |
| `INSTANCE_NAME` | 实例名 | `DMSERVER` |
| `PORT_NUM` | 监听端口 | `5236` |
| `SYSDBA_PWD` | SYSDBA 密码 | `SYSDBA001`（至少 9 位，含大小写数字） |
| `PAGE_SIZE` | 页大小（可选） | `16` |
| `CASE_SENSITIVE` | 大小写敏感 | `Y`（默认） |
| `CHARSET` | 字符集 | `1`（UTF-8）/ `0`（GB18030） |

### 3.2 注册并启动服务

```bash
# 以 root 注册服务（脚本位于安装目录 script/root）
su - root
cd /opt/dmdbms/script/root
./dm_service_installer.sh -t dmserver -p DMSERVER -dm_ini /opt/dmdbms/data/DAMENG/dm.ini

# 启动服务
systemctl start DmServiceDMSERVER
systemctl enable DmServiceDMSERVER
systemctl status DmServiceDMSERVER
```

### 3.3 验证实例

```bash
# 使用 disql 连接（安装目录 bin 下）
cd /opt/dmdbms/bin
./disql SYSDBA/SYSDBA001@localhost:5236

# 在 disql 提示符下执行
SQL> SELECT SVR_VERSION FROM V$INSTANCE;
SQL> SELECT STATUS$ FROM V$INSTANCE;
SQL> EXIT;
```

预期输出：版本号行 + `STATUS$` 为 `OPEN`（值 4 表示 OPEN）。

## 4. Windows 安装

1. 双击 `DM8Install.exe`，按图形向导选择安装目录（如 `C:\dmdbms`）
2. 安装完成后，运行「数据库配置助手」(dbca) 创建实例
3. 选择「创建数据库实例」，设置端口 5236、SYSDBA 密码
4. 完成后服务 `DmServiceDMSERVER` 自动启动
5. 验证：打开「DM 管理工具」或 `disql SYSDBA/SYSDBA001@localhost:5236`

## 5. 安装后检查清单

- [ ] 服务正常运行（Linux: `systemctl status DmServiceDMSERVER`）
- [ ] 端口 5236 监听（`ss -tlnp | grep 5236` 或 `netstat -an | findstr 5236`）
- [ ] disql 可连接并查询版本
- [ ] 已修改 SYSDBA 默认密码（生产环境）
- [ ] JDBC 驱动已放入 `assets/DmJdbcDriver18.jar`
- [ ] 运行 `python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password <新密码>` 返回 success=true

## 6. 常见问题

| 问题 | 解决 |
|------|------|
| 下载页空白/无法下载 | 登录账号；浏览器禁用拦截；SPA 页面需 JS 启用 |
| `dminit` 提示权限不足 | 用 dmsa 用户执行，目录已 chown |
| 服务启动失败 | 检查 `dm.ini` 路径、端口占用、`logs/` 日志 |
| disql 连接被拒 | 检查防火墙、`PORT_NUM`、SYSDBA 密码 |
| 找不到 JDBC 驱动 | 按 SKILL.md「驱动位置」放置 jar 或设 `DM_HOME` |
```

- [ ] **Step 2: 验证文档存在且含关键章节**
Run: `grep -c '^## ' references/install.md | xargs -I{} test {} -ge 6 && echo "PASS"`
Expected:
  - Exit code: 0
  - Output contains: "PASS"

- [ ] **Step 3: 提交**
Run: `git add references/install.md && git commit -m "docs(references): add DM8 download and installation workflow guide"`

---

### Task 5: 创建备份恢复与常用 SQL 参考文档 — 补充运维与查询模板

**Depends on:** Task 1
**Files:**
- Create: `references/backup-restore.md`
- Create: `references/common_queries.md`

- [ ] **Step 1: 创建 backup-restore.md — 达梦数据库备份恢复操作手册**

```markdown
# 达梦数据库备份恢复手册

## 1. 概述

达梦支持物理备份（dmrman）与逻辑备份（dexp/dimp）两类方式。

| 方式 | 工具 | 适用场景 |
|------|------|---------|
| 物理备份 | dmrman | 全库/增量脱机备份，恢复快 |
| 逻辑备份 | dexp/dimp | 按用户/表导出导入，跨库迁移 |
| 在线备份 | SQL `BACKUP` | 服务运行中备份，需归档开启 |

## 2. 开启归档（在线备份前提）

```bash
./disql SYSDBA/SYSDBA001@localhost:5236
```

```sql
-- 修改数据库为归档模式
ALTER DATABASE MOUNT;
ALTER DATABASE ARCHIVELOG;
ALTER DATABASE ADD ARCHIVELOG 'DEST=/opt/dmdbms/data/arch, TYPE=LOCAL, FILE_SIZE=128, SPACE_LIMIT=2048';
ALTER DATABASE OPEN;
-- 确认
SELECT ARCH_MODE FROM V$DATABASE;
```

## 3. 物理备份（dmrman）

### 3.1 全量脱机备份

需先停止服务：

```bash
systemctl stop DmServiceDMSERVER
cd /opt/dmdbms/bin
./dmrman
```

```
RMAN> BACKUP DATABASE '/opt/dmdbms/data/DAMENG/dm.ini' FULL TO "FULL_BAK" BACKUPSET '/opt/dmdbms/data/bak/FULL_BAK';
RMAN> EXIT;
```

### 3.2 增量备份

```
RMAN> BACKUP DATABASE '/opt/dmdbms/data/DAMENG/dm.ini' INCREMENT WITH BACKUPDIR '/opt/dmdbms/data/bak' TO "INCR_BAK" BACKUPSET '/opt/dmdbms/data/bak/INCR_BAK';
```

### 3.3 恢复

```
RMAN> RESTORE DATABASE '/opt/dmdbms/data/DAMENG/dm.ini' FROM BACKUPSET '/opt/dmdbms/data/bak/FULL_BAK';
RMAN> RECOVER DATABASE '/opt/dmdbms/data/DAMENG/dm.ini' FROM BACKUPSET '/opt/dmdbms/data/bak/FULL_BAK';
RMAN> RECOVER DATABASE '/opt/dmdbms/data/DAMENG/dm.ini' UPDATE DB_MAGIC;
```

恢复后启动服务：`systemctl start DmServiceDMSERVER`。

## 4. 逻辑备份（dexp/dimp）

### 4.1 导出

```bash
# 全库导出
./dexp SYSDBA/SYSDBA001@localhost:5236 FILE=/tmp/full.dmp LOG=/tmp/full.log FULL=Y

# 按用户/表导出
./dexp SYSDBA/SYSDBA001@localhost:5236 FILE=/tmp/user.dmp OWNER=SCHEMA_NAME LOG=/tmp/user.log
./dexp SYSDBA/SYSDBA001@localhost:5236 FILE=/tmp/tbl.dmp TABLES=SCHEMA_NAME.TABLE_NAME LOG=/tmp/tbl.log
```

### 4.2 导入

```bash
./dimp SYSDBA/SYSDBA001@localhost:5236 FILE=/tmp/full.dmp LOG=/tmp/imp.log FULL=Y IGNORE=Y
```

## 5. 在线 SQL 备份

```sql
-- 全量在线备份
BACKUP DATABASE FULL TO "ONLINE_FULL" BACKUPSET '/opt/dmdbms/data/bak/ONLINE_FULL';
-- 增量在线备份
BACKUP DATABASE INCREMENT WITH BACKUPDIR '/opt/dmdbms/data/bak' TO "ONLINE_INCR" BACKUPSET '/opt/dmdbms/data/bak/ONLINE_INCR';
```

## 6. 备份检查清单

- [ ] 归档已开启（`ARCH_MODE` 为 Y）
- [ ] 备份目录有足够空间
- [ ] 定期验证备份可恢复（演练）
- [ ] 关键变更前先做全量备份
```

- [ ] **Step 2: 创建 common_queries.md — 常用达梦 SQL 查询模板**

```markdown
# 达梦常用 SQL 查询模板

> 本文档供 `scripts/dm8_query.py --query "..."` 或 disql 直接使用。

## 1. 实例与版本

```sql
-- 数据库版本
SELECT SVR_VERSION FROM V$INSTANCE;
SELECT * FROM V$VERSION;
-- 实例状态（4=OPEN）
SELECT NAME, STATUS$, STATUS$ DESC FROM V$INSTANCE;
```

## 2. 表与 Schema

```sql
-- 当前用户所有表
SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME;
-- 指定 schema 所有表（含注释）
SELECT TABLE_NAME, COMMENTS FROM ALL_TAB_COMMENTS WHERE OWNER = 'SCHEMA_NAME' AND TABLE_TYPE = 'TABLE';
-- 表结构
SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE FROM ALL_TAB_COLUMNS WHERE OWNER = 'SCHEMA_NAME' AND TABLE_NAME = 'TABLE_NAME' ORDER BY COLUMN_ID;
```

## 3. 表空间

```sql
-- 表空间使用情况
SELECT TABLESPACE_NAME, FILE_NAME, BYTES/1024/1024 AS MB FROM DBA_DATA_FILES ORDER BY TABLESPACE_NAME;
-- 表空间剩余
SELECT TABLESPACE_NAME, SUM(BYTES)/1024/1024 AS FREE_MB FROM DBA_FREE_SPACE GROUP BY TABLESPACE_NAME;
```

## 4. 用户与权限

```sql
-- 所有用户
SELECT USERNAME FROM DBA_USERS ORDER BY USERNAME;
-- 用户权限
SELECT * FROM DBA_SYS_PRIVS WHERE GRANTEE = 'USERNAME';
```

## 5. 会话与锁

```sql
-- 当前会话
SELECT SESSID, SQL_TEXT, STATE, CREATE_TIME FROM V$SESSIONS WHERE STATE = 'ACTIVE';
-- 锁等待
SELECT * FROM V$LOCK WHERE BLOCKED = 1;
```

## 6. 分页查询（达梦 ROWNUM 方式）

```sql
-- 前 10 条
SELECT * FROM TABLE_NAME WHERE ROWNUM <= 10;
-- 分页：第 2 页（每页 10）
SELECT * FROM (SELECT T.*, ROWNUM RN FROM TABLE_NAME T WHERE ROWNUM <= 20) WHERE RN > 10;
-- TOP 写法（兼容模式）
SELECT TOP 10 * FROM TABLE_NAME;
```

## 7. 序列

```sql
CREATE SEQUENCE SEQ_NAME START WITH 1 INCREMENT BY 1 NOCACHE;
SELECT SEQ_NAME.NEXTVAL FROM DUAL;
SELECT SEQ_NAME.CURRVAL FROM DUAL;
```

## 8. 常用函数差异（相对 Oracle/MySQL）

| 需求 | 达梦写法 |
|------|---------|
| 当前时间 | `SELECT SYSDATE FROM DUAL;` 或 `SELECT CURRENT_TIMESTAMP;` |
| 字符串拼接 | `SELECT 'a' || 'b' FROM DUAL;` |
| 空值处理 | `SELECT NVL(COL, 0) FROM T;` |
| 类型转换 | `SELECT CAST(COL AS VARCHAR(100)) FROM T;` |
```

- [ ] **Step 3: 验证两份文档章节完整**
Run: `test $(grep -c '^## ' references/backup-restore.md) -ge 5 && test $(grep -c '^## ' references/common_queries.md) -ge 6 && echo "PASS"`
Expected:
  - Exit code: 0
  - Output contains: "PASS"

- [ ] **Step 4: 提交**
Run: `git add references/backup-restore.md references/common_queries.md && git commit -m "docs(references): add backup-restore and common-queries SQL templates"`

---

### Task 6: 创建单元测试 — 覆盖公共模块的参数解析与驱动查找逻辑

**Depends on:** Task 2, Task 3
**Files:**
- Create: `tests/test_dm8_common.py`
- Create: `tests/test_scripts_args.py`
- Modify: `requirements.txt`（新建，声明运行依赖）

- [ ] **Step 1: 创建 requirements.txt — 声明运行依赖与测试依赖**

```text
# 达梦数据库操作 SKILLS 运行依赖
jaydebeapi>=1.6.0
JPype1>=1.4.0

# 测试依赖
pytest>=7.0.0
```

- [ ] **Step 2: 创建 test_dm8_common.py — 测试驱动查找、参数解析、JSON 输出（用 mock，不依赖真实数据库）**

```python
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
```

- [ ] **Step 3: 创建 test_scripts_args.py — 测试各脚本的参数解析（--query/--file 互斥、--table 必填）**

```python
"""操作脚本参数解析测试（不连接真实数据库）。"""

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
    def test_query_or_file_required(self, capsys):
        mod = load_script("dm8_query")
        with pytest.raises(SystemExit):
            mod.main.__wrapped__ if hasattr(mod.main, "__wrapped__") else None
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
```

- [ ] **Step 4: 验证测试通过**
Run: `python3 -m pytest tests/ -v --no-header 2>&1 | tail -20`
Expected:
  - Exit code: 0
  - Output contains: "passed"
  - Output does NOT contain: "FAILED" or "ERROR"

- [ ] **Step 5: 提交**
Run: `git add requirements.txt tests/test_dm8_common.py tests/test_scripts_args.py && git commit -m "test: add unit tests for dm8_common args parsing, driver finding, and script args"`

---

### Task 7: 创建 assets 占位与 README — 补全项目骨架与使用说明

**Depends on:** Task 3
**Files:**
- Create: `assets/README.md`
- Create: `README.md`
- Create: `.gitignore`

- [ ] **Step 1: 创建 assets/README.md — 说明如何放置 JDBC 驱动**

```markdown
# assets 目录

本目录用于存放达梦 JDBC 驱动 `DmJdbcDriver18.jar`，供 `scripts/` 下的工具脚本连接数据库使用。

## 获取方式

1. 访问 https://eco.dameng.com/download/ （需登录达梦社区账号）
2. 下载「DM8 JDBC 驱动」
3. 将 `DmJdbcDriver18.jar` 放入本目录

## 校验

```bash
unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class
```

> 该目录的 jar 文件不纳入版本控制（见 `.gitignore`），请各环境自行放置。
```

- [ ] **Step 2: 创建 .gitignore — 忽略驱动 jar、Python 缓存、虚拟环境**

```text
# 达梦 JDBC 驱动（各环境自行下载放置）
assets/*.jar

# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.venv/
venv/

# IDE
.vscode/
.idea/

# 系统
.DS_Store
Thumbs.db
```

- [ ] **Step 3: 创建 README.md — 项目总览与快速使用**

```markdown
# 达梦数据库操作 SKILLS

达梦数据库(DM8)操作技能集合，提供下载安装引导与连接/查询/管理工具集。

## 功能

- **下载安装**：`references/install.md` 涵盖从官方下载到实例部署全流程
- **连接测试**：`scripts/dm8_connect.py`
- **列出表**：`scripts/dm8_tables.py`
- **查看表结构**：`scripts/dm8_schema.py`
- **执行 SQL**：`scripts/dm8_query.py`
- **查看库信息**：`scripts/dm8_info.py`
- **备份恢复**：`references/backup-restore.md`
- **常用 SQL**：`references/common_queries.md`

## 快速使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 放置 JDBC 驱动到 assets/（见 assets/README.md）

# 3. 测试连接
python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password YOUR_PASSWORD

# 4. 列出表
python3 scripts/dm8_tables.py --host 127.0.0.1 --user SYSDBA --password YOUR_PASSWORD --schema SCH_NAME

# 5. 执行查询
python3 scripts/dm8_query.py --host 127.0.0.1 --user SYSDBA --password YOUR_PASSWORD --query "SELECT * FROM T WHERE ROWNUM <= 10"
```

## 目录结构

```
.
├── SKILL.md                  # 技能入口（能力清单与引导）
├── scripts/                  # 操作工具脚本
│   ├── dm8_common.py         # 公共连接模块
│   ├── dm8_connect.py        # 测试连接
│   ├── dm8_tables.py         # 列出表
│   ├── dm8_schema.py         # 查看表结构
│   ├── dm8_query.py          # 执行 SQL
│   └── dm8_info.py           # 查看库信息
├── references/               # 参考文档
│   ├── install.md            # 下载安装流程
│   ├── backup-restore.md     # 备份恢复手册
│   └── common_queries.md     # 常用 SQL 模板
├── assets/                   # JDBC 驱动（不入库）
├── tests/                    # 单元测试
└── requirements.txt          # 依赖
```

## 测试

```bash
python3 -m pytest tests/ -v
```

## 平台兼容

✅ Windows ✅ macOS ✅ Linux

## 参考

- [达梦在线服务平台](https://eco.dameng.com/download/)
- [达梦技术文档](https://eco.dameng.com/document/dm/zh-cn/start)
```

- [ ] **Step 4: 验证项目骨架完整**
Run: `for f in SKILL.md README.md .gitignore assets/README.md references/install.md references/backup-restore.md references/common_queries.md scripts/dm8_common.py scripts/dm8_connect.py scripts/dm8_tables.py scripts/dm8_schema.py scripts/dm8_query.py scripts/dm8_info.py requirements.txt tests/test_dm8_common.py tests/test_scripts_args.py; do test -f "$f" && echo "OK $f" || echo "MISSING $f"; done | grep -c MISSING | xargs -I{} test {} -eq 0 && echo "ALL FILES PRESENT"`
Expected:
  - Exit code: 0
  - Output contains: "ALL FILES PRESENT"

- [ ] **Step 5: 提交**
Run: `git add assets/README.md README.md .gitignore && git commit -m "docs: add project README, assets placeholder, and gitignore"`
