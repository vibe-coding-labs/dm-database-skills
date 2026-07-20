# 达梦数据库容器（Docker）安装流程

容器方式是最快的达梦部署途径，适合开发测试与 CI/CD。本文档覆盖拉取镜像、启动容器、初始化、连接验证全流程。

## 前提

- 已安装 Docker（`docker --version` 有输出）
- 守护进程运行中（`systemctl status docker` 或 `docker info`）
- 当前用户在 `docker` 组或可用 sudo（`docker ps` 无报错）

> 若 Docker 未安装：`curl -fsSL https://get.docker.com | sh` 然后 `sudo usermod -aG docker $USER`（重新登录生效）。

## 1. 选择镜像

达梦生态有以下常用镜像（任选其一，按可用性与维护活跃度排序）：

| 镜像 | 说明 | 推荐场景 |
|------|------|---------|
| `chillzhuang/dm:8.1.x.x` | 达梦官方推出的 DM8 Docker 镜像 | 生产、长期使用 |
| `webcenter/dmdb:latest` | 社区维护的 DM8 开发版封装 | 快速体验、开发测试 |

> 镜像版本号会随达梦发布更新，以 `docker search` 或镜像仓库实际 tag 为准。

## 2. 拉取与启动

### 2.1 拉取镜像

```bash
docker pull chillzhuang/dm:8.1.2.128
# 或社区版
docker pull webcenter/dmdb:latest
```

### 2.2 启动容器

```bash
docker run -d \
  --name dm8 \
  --restart=unless-stopped \
  -p 5236:5236 \
  -e CASE_SENSITIVE=1 \
  -v /opt/dm8/data:/opt/dmdbms/data \
  chillzhuang/dm:8.1.2.128
```

参数说明：

| 参数 | 说明 |
|------|------|
| `-d` | 后台运行 |
| `--name dm8` | 容器名 `dm8` |
| `--restart=unless-stopped` | 开机自启（崩溃自动重启） |
| `-p 5236:5236` | 映射达梦默认端口到宿主机 |
| `-e CASE_SENSITIVE=1` | 大小写敏感（1=敏感，0=不敏感） |
| `-v /opt/dm8/data:/opt/dmdbms/data` | 数据持久化到宿主机目录 |

> 首次启动会自动 `dminit` 初始化实例，默认 SYSDBA 密码 `SYSDBA001`，约需 10-30 秒。

### 2.3 确认容器运行

```bash
docker ps --filter name=dm8
# 查看启动日志，等待 "database is ready" 或端口监听
docker logs -f dm8
# Ctrl+C 退出日志查看（不影响容器）
```

## 3. 连接验证

### 3.1 进入容器用 disql 验证

```bash
docker exec -it dm8 /opt/dmdbms/bin/disql SYSDBA/SYSDBA001@localhost:5236
```

在 disql 提示符下：

```sql
SQL> SELECT SVR_VERSION FROM V$INSTANCE;
SQL> SELECT STATUS$ FROM V$INSTANCE;
SQL> EXIT;
```

预期：版本号行 + `STATUS$` 为 `4`（OPEN）。

### 3.2 从宿主机用本 SKILL 脚本验证

```bash
# 1. 取出容器内 JDBC 驱动到 assets（容器方式无需登录官网下载）
docker cp dm8:/opt/dmdbms/drivers/jdbc/DmJdbcDriver18.jar assets/
unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class

# 2. 安装 Python 依赖
pip install jaydebeapi JPype1

# 3. 连接测试
python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password SYSDBA001
```

预期输出 `"success": true` 与版本号。

> **关键优势**：容器方式可直接从容器内拷出 JDBC 驱动，**无需登录 eco.dameng.com 账号手动下载**，AI Agent 可全自主完成。

## 4. 修改 SYSDBA 密码

首次启动后应立即修改默认密码：

```bash
docker exec -it dm8 /opt/dmdbms/bin/disql SYSDBA/SYSDBA001@localhost:5236
```

```sql
SQL> ALTER USER SYSDBA IDENTIFIED BY "<新密码>";
SQL> EXIT;
```

## 5. 数据持久化与备份

容器数据已通过 `-v /opt/dm8/data` 持久化到宿主机。备份见 `backup-restore.md`，容器内执行 dmrman：

```bash
docker exec -it dm8 /opt/dmdbms/bin/dmrman
```

## 6. 停止、重启、删除

```bash
# 停止
docker stop dm8
# 启动
docker start dm8
# 重启
docker restart dm8
# 删除容器（保留宿主机数据卷）
docker rm -f dm8
# 彻底清理（连数据卷一起删，谨慎！）
docker rm -f dm8 && sudo rm -rf /opt/dm8/data
```

## 7. 常见问题

| 问题 | 解决 |
|------|------|
| `docker pull` 报 EOF/超时 | 网络受限或 Docker Hub 被墙，配置国内镜像加速器或换 `chillzhuang` 仓库源 |
| 容器启动后立即退出 | `docker logs dm8` 看日志，多为数据目录权限/初始化失败 |
| 端口 5236 被占用 | 改 `-p 5237:5236`，连接时用新端口 |
| `docker cp` 找不到驱动路径 | 不同镜像驱动路径可能不同，`docker exec dm8 find /opt/dmdbms -name "DmJdbcDriver*.jar"` 定位 |
| disql 连接被拒 | 确认容器 `docker ps` 在运行、SYSDBA 密码、防火墙未拦 5236 |
| 镜像拉取太慢 | 配置 `/etc/docker/daemon.json` 加 registry-mirrors |
