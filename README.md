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
