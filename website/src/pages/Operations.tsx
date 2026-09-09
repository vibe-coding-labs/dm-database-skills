export default function Operations() {
  return (
    <div className="page">
      <h1>运维与监控</h1>
      <p>日常巡检、服务操作、性能调优、备份恢复与监控告警。</p>

      <h2>日常巡检</h2>
      <ul>
        <li>服务状态：<code>systemctl status DmServiceDMSERVER</code></li>
        <li>端口监听：<code>ss -tlnp | grep 5236</code></li>
        <li>实例状态：<code>SELECT NAME, STATUS$, SVR_VERSION FROM V$INSTANCE;</code></li>
      </ul>

      <h2>日志</h2>
      <ul>
        <li>数据库日志：<code>/opt/dmdbms/data/DAMENG/log/dm.log</code></li>
        <li>告警日志：<code>/opt/dmdbms/data/DAMENG/log/alert.log</code></li>
      </ul>

      <p>详细内容见：</p>
      <ul>
        <li><a className="link" href="https://github.com/vibe-coding-labs/dm-database-skills/blob/main/references/operations.md" target="_blank" rel="noreferrer">operations.md</a></li>
        <li><a className="link" href="https://github.com/vibe-coding-labs/dm-database-skills/blob/main/references/monitoring.md" target="_blank" rel="noreferrer">monitoring.md</a></li>
        <li><a className="link" href="https://github.com/vibe-coding-labs/dm-database-skills/blob/main/references/backup-restore.md" target="_blank" rel="noreferrer">backup-restore.md</a></li>
      </ul>
    </div>
  )
}
