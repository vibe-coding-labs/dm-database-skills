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
