# 达梦数据库 Windows Server 安装流程

本文档适用于 Windows Server 2012/2016/2019/2022/2025。达梦数据库支持在这些系统上以服务方式运行，也可在 PowerShell 中做基础运维。

## 1. 下载与准备

1. 在支持浏览器的环境中打开 https://eco.dameng.com/download/ 并登录账号。
2. 选择 **DM8 开发版（Windows）**，下载安装包，例如 `DM8Install.exe`。
3. 将安装包复制到目标 Windows Server，例如 `C:\temp\DM8Install.exe`。
4. 推荐准备 JDBC 驱动 `DmJdbcDriver18.jar`，后续放入本项目 `assets/`。

## 2. 图形化安装

1. 双击 `DM8Install.exe`，按向导选择安装目录，如 `C:\dmdbms`。
2. 选择安装组件，至少包含：
   - DM8 服务端
   - disql
   - DM 管理工具(DMManager)
3. 完成安装后，通过「数据库配置助手」(dbca) 创建实例：
   - 选择「创建数据库实例」
   - 设置实例名、端口，默认建议 `5236`
   - 设置 SYSDBA 密码，建议至少 9 位且含大小写和数字
4. 实例创建后服务 `DmServiceDMSERVER` 通常自动启动。

## 3. 服务验证

```powershell
# 查看服务状态
Get-Service -Name "DmServiceDMSERVER"

# 启动服务
Start-Service -Name "DmServiceDMSERVER"

# 端口监听
Test-NetConnection -ComputerName localhost -Port 5236
```

## 4. 命令行验证

在安装目录 `bin` 下运行 `disql`：

```powershell
cd C:\dmdbms\bin
.\disql.exe SYSDBA/SYSDBA001@localhost:5236
```

```sql
SQL> SELECT SVR_VERSION FROM V$INSTANCE;
SQL> SELECT STATUS$ FROM V$INSTANCE;
SQL> EXIT;
```

预期：版本号行 + `STATUS$` 为 `4`（OPEN）。

## 5. 防火墙放行

若需远程连接，放行 5236 端口：

```powershell
New-NetFirewallRule -DisplayName "DM8 TCP 5236" -Direction Inbound -Protocol TCP -LocalPort 5236 -Action Allow
```

## 6. 安装后检查清单

- [ ] 服务正常：`Get-Service DmServiceDMSERVER` 为 Running
- [ ] 端口监听：`5236` 可连接
- [ ] disql 可查询版本
- [ ] 已修改默认密码
- [ ] JDBC 驱动已放入 `assets/DmJdbcDriver18.jar`
- [ ] 运行连接测试脚本返回 success=true

## 7. 常见问题

| 问题 | 解决 |
|------|------|
| 安装包报毒/被拦截 | 关闭实时防护或添加白名单，重试安装 |
| 服务无法启动 | 查看事件查看器与应用日志，检查 `dm.ini` 路径 |
| 连接超时 | 检查防火墙、端口、密码、监听地址 |
| 中文显示乱码 | 确认字符集配置与终端编码一致 |
