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
# 校验文件存在且为有效 jar（成功输出 DmDriver.class 行；无驱动时该命令返回非零，属正常提示缺失）
unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class
```

> 若 `unzip` 未安装：`sudo apt install unzip`（Debian/Ubuntu）或 `sudo yum install unzip`（RHEL/CentOS）。

> 驱动就位后，脚本会在连接前自动 preflight 检查（见 scripts/dm8_common.py 的 preflight 函数），缺失时输出可操作的安装提示而非技术性报错。

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
# 调整最大文件句柄数（root 执行）——写入独立文件，便于回滚
sudo tee /etc/security/limits.d/dmsa.conf > /dev/null <<'EOF'
dmsa soft nofile 65536
dmsa hard nofile 65536
EOF

# 检查（需重新登录或新会话生效）
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

## 7. 可执行性测试

本安装指引附自动化测试，验证各步骤命令可执行。运行：

```bash
# 安装测试依赖
pip3 install --user jaydebeapi JPype1 pytest

# 运行安装指引可执行性测试（需 sudo 用于用户/limits 步骤）
python3 -m pytest tests/integration/test_install_guide.py -v
```

测试覆盖范围：

| 测试类 | 覆盖 install.md 章节 | 说明 |
|--------|---------------------|------|
| TestEnvironmentBaseline | 前提条件 | Java/unzip/Python 可用 |
| TestCreateUser | 2.1 | groupadd/useradd/chown 链可执行 |
| TestSystemParams | 2.2 | limits 独立文件可写入 |
| TestJdbcDriverAcquisition | 1.3 | 驱动校验命令在无驱动时正确失败 |
| TestInstallationPackageAcquisition | 2.3/3 | 安装包获取渠道探测（无包时 skip） |

> **阻塞说明**：达梦安装包（`DM8Install.bin`）与 JDBC 驱动（`DmJdbcDriver18.jar`）需登录 [eco.dameng.com](https://eco.dameng.com/download/) 账号手动下载，公开渠道无法自动获取。完整安装测试在无安装包时自动跳过，属预期行为。
