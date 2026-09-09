export default function Install() {
  return (
    <div className="page install">
      <h1>安装指南</h1>
      <p>本页面汇总多平台安装与验证要点，详细步骤见仓库文档。</p>

      <div className="grid">
        <div className="card">
          <h3>Ubuntu</h3>
          <ul>
            <li>创建专用用户：<code>groupadd / useradd</code></li>
            <li>limits 独立文件：<code>/etc/security/limits.d/dmsa.conf</code></li>
            <li>防火墙：<code>ufw allow 5236/tcp</code></li>
            <li>安装包：<code>DM8Install.bin</code></li>
          </ul>
          <a className="link" href="/references/install.md">查看 install.md</a>
        </div>

        <div className="card">
          <h3>CentOS/RHEL</h3>
          <ul>
            <li>包管理：<code>yum install unzip</code></li>
            <li>防火墙：<code>firewall-cmd --add-port=5236/tcp --permanent</code></li>
            <li>limits 配置与 Ubuntu 相同</li>
          </ul>
          <a className="link" href="/references/install.md">查看 install.md</a>
        </div>

        <div className="card">
          <h3>Windows</h3>
          <ul>
            <li>图形安装：<code>DM8Install.exe</code></li>
            <li>实例配置：<code>dbca</code></li>
            <li>服务：<code>DmServiceDMSERVER</code></li>
            <li>验证：<code>disql</code></li>
          </ul>
          <a className="link" href="/references/install.md">查看 install.md</a>
        </div>

        <div className="card">
          <h3>Windows Server</h3>
          <ul>
            <li>服务化部署与自启</li>
            <li>PowerShell：<code>Get-Service / Start-Service</code></li>
            <li>防火墙：<code>New-NetFirewallRule</code></li>
          </ul>
          <a className="link" href="/references/windows-server-install.md">查看 windows-server-install.md</a>
        </div>

        <div className="card">
          <h3>Docker</h3>
          <ul>
            <li>镜像：<code>chillzhuang/dm:8.1.2.128</code></li>
            <li>启动：映射 <code>5236</code> 并持久化数据</li>
            <li>驱动：<code>docker cp</code> 从容器拷出</li>
          </ul>
          <a className="link" href="/references/docker-install.md">查看 docker-install.md</a>
        </div>

        <div className="card">
          <h3>Docker Compose</h3>
          <ul>
            <li>单机 compose 一键启停</li>
            <li>环境变量与健康检查</li>
            <li>数据卷持久化</li>
          </ul>
          <a className="link" href="/references/docker-compose.md">查看 docker-compose.md</a>
        </div>

        <div className="card">
          <h3>Kubernetes</h3>
          <ul>
            <li>Deployment + Service</li>
            <li>PVC 持久化</li>
            <li>readiness/liveness 探针</li>
          </ul>
          <a className="link" href="/references/kubernetes.md">查看 kubernetes.md</a>
        </div>

        <div className="card">
          <h3>Android / iOS</h3>
          <ul>
            <li>远程 JDBC/ODBC 访问</li>
            <li>不建议直连生产库</li>
            <li>优先 API/Web 管理入口</li>
          </ul>
          <a className="link" href="/references/mobile-install.md">查看 mobile-install.md</a>
        </div>
      </div>
    </div>
  )
}
