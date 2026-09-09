export default function Home() {
  return (
    <div className="page home">
      <section className="hero">
        <h1>达梦数据库(DM8)操作技能</h1>
        <p>覆盖下载安装、Docker/K8s/Compose 部署、运维监控、备份恢复与连接查询工具集。</p>
        <div className="actions">
          <a className="btn primary" href="/install">开始安装</a>
          <a className="btn" href="/docker">容器部署</a>
          <a className="btn" href="https://github.com/vibe-coding-labs/dm-database-skills" target="_blank" rel="noreferrer">GitHub</a>
        </div>
      </section>

      <section className="features">
        <div className="feature">
          <h3>📦 多平台安装</h3>
          <p>Linux、Windows、Windows Server、Android、iOS。</p>
        </div>
        <div className="feature">
          <h3>🐳 容器化部署</h3>
          <p>Docker、Docker Compose、Kubernetes 快速上手。</p>
        </div>
        <div className="feature">
          <h3>🔧 运维监控</h3>
          <p>日常巡检、性能调优、备份恢复、监控告警。</p>
        </div>
        <div className="feature">
          <h3>🧰 连接工具</h3>
          <p>Python 脚本连接达梦实例，统一 JSON 输出。</p>
        </div>
      </section>

      <section className="quickstart">
        <h2>快速开始</h2>
        <pre>{`# 安装依赖
pip install -r requirements.txt

# 放置 JDBC 驱动到 assets/
cp DmJdbcDriver18.jar assets/

# 测试连接
python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password YOUR_PASSWORD

# 执行查询
python3 scripts/dm8_query.py --host 127.0.0.1 --user SYSDBA --password YOUR_PASSWORD --query "SELECT SVR_VERSION FROM V\\$INSTANCE"`}</pre>
      </section>
    </div>
  )
}
