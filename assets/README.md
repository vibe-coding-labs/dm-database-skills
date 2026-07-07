# assets 目录

本目录用于存放达梦 JDBC 驱动 `DmJdbcDriver18.jar`，供 `scripts/` 下的工具脚本连接数据库使用。

## 获取方式

1. 访问 https://eco.dameng.com/download/ （需登录达梦社区账号）
2. 下载「DM8 JDBC 驱动」
3. 将 `DmJdbcDriver18.jar` 放入本目录

## 校验

```bash
unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class
```

> 该目录的 jar 文件不纳入版本控制（见 `.gitignore`），请各环境自行放置。
