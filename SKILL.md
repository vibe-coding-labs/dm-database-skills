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
