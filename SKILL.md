---
name: dm-database-skills
description: 达梦数据库(DM8)操作技能。涵盖下载安装部署流程(参考官方 eco.dameng.com/download 产品矩阵)与连接/查询/管理工具集(测试连接、列出表、查看表结构、执行SQL、查看库信息、备份恢复)。当需要安装达梦数据库、操作达梦实例、查询数据、分析表结构、备份恢复时使用此技能。支持 Windows、macOS、Linux 平台，通过命令行参数指定 host/port/user/password/database/schema。可作为 dm8 mcp 服务的替代方案。
---

# 达梦数据库操作 SKILL

提供达梦数据库(DM8)的下载安装引导与连接/查询/管理工具集。

## 能力总览

本 SKILL 分两层：

1. **下载安装层** — 文档化流程，引导从官方下载到完成实例部署，覆盖 Linux、Windows、Windows Server、Docker、Docker Compose、Kubernetes，以及移动端与容器场景
2. **操作工具层** — Python 脚本集，连接已部署实例执行各类操作

## 何时使用

| 场景 | 使用方式 |
|------|---------|
| Linux 物理机安装达梦（Ubuntu/CentOS） | 阅读 `references/install.md`，按流程下载安装并初始化实例 |
| Windows 桌面安装达梦 | 阅读 `references/install.md`，使用图形向导安装并初始化实例 |
| Windows Server 安装达梦 | 阅读 `references/windows-server-install.md`，按服务化方式部署与验证 |
| 容器安装达梦（Docker，推荐快速体验） | 阅读 `references/docker-install.md`，拉取镜像启动容器 |
| Docker Compose 启动达梦 | 阅读 `references/docker-compose.md`，使用 compose 文件一键启停 |
| Kubernetes 部署达梦 | 阅读 `references/kubernetes.md`，按清单部署 Deployment 与 Service |
| 移动端使用达梦（Android/iOS） | 阅读 `references/mobile-install.md`，以远程 JDBC/Web 方式访问 |
| 日常运维、监控、调优、故障排查 | 阅读 `references/operations.md`、`references/monitoring.md` |
| 备份恢复数据库 | 阅读 `references/backup-restore.md` 或使用 dmrman |
| 自动获取 JDBC 驱动（免登录官网） | 运行 `scripts/dm8_get_driver.py`，从容器或已安装目录拷出驱动 |
| 需要测试/连接达梦数据库 | 运行 `scripts/dm8_connect.py` |
| 需要列出某 schema 下所有表 | 运行 `scripts/dm8_tables.py` |
| 需要查看表结构 | 运行 `scripts/dm8_schema.py` |
| 需要执行 SQL 查询 | 运行 `scripts/dm8_query.py` |
| 需要查看数据库信息 | 运行 `scripts/dm8_info.py` |

## 端到端零接触路径（从零到能查询）

AI Agent 从零环境到能执行 SQL 的全自动化路径，优先容器方式（最快、可自主完成）：

```bash
# 1. 启动达梦容器
docker run -d --name dm8 -p 5236:5236 -v /opt/dm8/data:/opt/dmdbms/data chillzhuang/dm:8.1.2.128

# 2. 安装 Python 依赖
pip install jaydebeapi JPype1

# 3. 从容器自动拷出 JDBC 驱动到 assets/（无需登录官网）
python3 scripts/dm8_get_driver.py

# 4. 连接测试（默认 SYSDBA/SYSDBA001）
python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password SYSDBA001

# 5. 执行 SQL
python3 scripts/dm8_query.py --host 127.0.0.1 --user SYSDBA --password SYSDBA001 --query "SELECT SVR_VERSION FROM V\$INSTANCE"
```

完成上述 5 步即可查询达梦数据库。物理机安装路径见 `references/install.md`，容器路径见 `references/docker-install.md`。

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
- `references/windows-server-install.md` — Windows Server 安装与服务化部署
- `references/docker-install.md` — Docker 镜像拉取、启动、连接验证
- `references/docker-compose.md` — Docker Compose 部署与常用操作
- `references/kubernetes.md` — Kubernetes 部署清单与验证
- `references/mobile-install.md` — Android/iOS 使用方式与限制
- `references/backup-restore.md` — 备份恢复操作手册
- `references/operations.md` — 日常运维与故障排查
- `references/monitoring.md` — 监控方法与告警建议
- `references/common_queries.md` — 常用达梦 SQL 查询模板
