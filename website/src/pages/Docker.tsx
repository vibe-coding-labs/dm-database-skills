export default function Docker() {
  return (
    <div className="page">
      <h1>Docker 与 Compose</h1>
      <p>容器方式是最快的达梦部署途径。</p>

      <h2>Docker</h2>
      <pre>{`docker run -d --name dm8 -p 5236:5236 -v /opt/dm8/data:/opt/dmdbms/data chillzhuang/dm:8.1.2.128`}</pre>

      <h2>Docker Compose</h2>
      <pre>{`services:
  dm8:
    image: chillzhuang/dm:8.1.2.128
    ports: ["5236:5236"]
    volumes: ["./data:/opt/dmdbms/data"]`}</pre>

      <p>详细内容见：</p>
      <ul>
        <li><a className="link" href="https://github.com/vibe-coding-labs/dm-database-skills/blob/main/references/docker-install.md" target="_blank" rel="noreferrer">docker-install.md</a></li>
        <li><a className="link" href="https://github.com/vibe-coding-labs/dm-database-skills/blob/main/references/docker-compose.md" target="_blank" rel="noreferrer">docker-compose.md</a></li>
      </ul>
    </div>
  )
}
