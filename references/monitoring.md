# 达梦数据库监控指南

本文档提供达梦数据库基础监控方法与告警建议。

## 1. 基础监控项

- 实例状态：`STATUS$` 是否为 `OPEN`
- 会话数：`SELECT COUNT(*) FROM V$SESSIONS;`
- 锁等待：`SELECT * FROM V$LOCK WHERE BLOCKED = 1;`
- 表空间使用率：`SELECT TABLESPACE_NAME, SUM(BYTES)/1024/1024 FROM DBA_FREE_SPACE GROUP BY TABLESPACE_NAME;`

## 2. 日志位置

- 数据库日志：`/opt/dmdbms/data/DAMENG/log/dm.log`
- 告警日志：`/opt/dmdbms/data/DAMENG/log/alert.log`

## 3. 告警建议

- 表空间使用率超过阈值
- 备份失败
- 服务异常停止
- 锁等待持续超过阈值
