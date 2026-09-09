# 达梦数据库 Docker Compose 部署

Docker Compose 适合单机多容器或快速启动达梦实例。本文档提供常用 compose 配置与操作命令。

## 1. 目录结构

```text
dm8-compose/
├── docker-compose.yml
├── .env
└── data/                # 宿主机持久化目录
```

## 2. 基础配置

`docker-compose.yml`

```yaml
services:
  dm8:
    image: chillzhuang/dm:8.1.2.128
    container_name: dm8
    restart: unless-stopped
    ports:
      - "5236:5236"
    environment:
      - CASE_SENSITIVE=1
      - SYSDBA_PWD=SYSDBA001
    volumes:
      - ./data:/opt/dmdbms/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5236"]
      interval: 10s
      timeout: 5s
      retries: 5
```

`.env`

```env
IMAGE_TAG=8.1.2.128
HOST_PORT=5236
CONTAINER_PORT=5236
DATA_DIR=./data
CASE_SENSITIVE=1
SYSDBA_PWD=SYSDBA001
```

## 3. 启动与验证

```bash
docker compose up -d
docker compose ps
docker compose logs -f dm8
```

## 4. 常用命令

```bash
# 重启
docker compose restart dm8

# 查看日志
docker compose logs --tail=100 dm8

# 停止并保留数据
docker compose down

# 停止并删除数据卷
docker compose down -v
```

## 5. 连接验证

```bash
docker cp dm8:/opt/dmdbms/drivers/jdbc/DmJdbcDriver18.jar assets/
python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password SYSDBA001
```

## 6. 生产建议

- 使用具名卷或绑定宿主机目录持久化数据
- 配置资源限制与健康检查
- 修改默认密码
- 开启日志轮转
