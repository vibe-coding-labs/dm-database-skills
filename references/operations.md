# 达梦数据库运维手册

本文档覆盖日常运维、监控、调优、故障排查与维护窗口建议。

## 1. 日常巡检

- 服务状态：`systemctl status DmServiceDMSERVER`
- 监听端口：`ss -tlnp | grep 5236`
- 实例状态：`SELECT NAME, STATUS$, SVR_VERSION FROM V$INSTANCE;`
- 表空间：`SELECT TABLESPACE_NAME, FILE_NAME, BYTES/1024/1024 AS MB FROM DBA_DATA_FILES;`
- 会话与锁：`SELECT * FROM V$SESSIONS WHERE STATE='ACTIVE';`

## 2. 服务操作

```bash
# 启动
sudo systemctl start DmServiceDMSERVER

# 停止
sudo systemctl stop DmServiceDMSERVER

# 重启
sudo systemctl restart DmServiceDMSERVER

# 查看日志
tail -f /opt/dmdbms/data/DAMENG/log/dm.log
```

## 3. 监控建议

- 操作系统：CPU、内存、磁盘 IO、网络
- 数据库：QPS/TPS、活跃会话、慢查询、表空间增长
- 备份：备份成功/失败、恢复演练周期

## 4. 性能调优

- 合理设置 `PAGE_SIZE` 与缓冲池
- 定期重建索引、收集统计信息
- 控制并发会话与锁等待
- 归档模式开启后注意磁盘增长

## 5. 故障排查

| 现象 | 建议 |
|------|------|
| 服务启动失败 | 检查 `dm.ini`、端口、日志、磁盘空间 |
| 连接超时 | 检查防火墙、监听地址、密码、网络 |
| 慢查询 | 检查执行计划、索引、锁等待 |
| 表空间满 | 扩展数据文件或清理历史数据 |
