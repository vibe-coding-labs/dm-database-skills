export default function K8s() {
  return (
    <div className="page">
      <h1>Kubernetes 部署</h1>
      <p>最小可用清单：Deployment + Service + PVC。</p>
      <pre>{`apiVersion: apps/v1
kind: Deployment
metadata:
  name: dm8
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dm8
  template:
    metadata:
      labels:
        app: dm8
    spec:
      containers:
        - name: dm8
          image: chillzhuang/dm:8.1.2.128
          ports:
            - containerPort: 5236
          volumeMounts:
            - name: dm8-data
              mountPath: /opt/dmdbms/data
      volumes:
        - name: dm8-data
          persistentVolumeClaim:
            claimName: dm8-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: dm8
spec:
  selector:
    app: dm8
  ports:
    - port: 5236
      targetPort: 5236`}</pre>

      <p>详细内容见：</p>
      <ul>
        <li><a className="link" href="https://github.com/vibe-coding-labs/dm-database-skills/blob/main/references/kubernetes.md" target="_blank" rel="noreferrer">kubernetes.md</a></li>
      </ul>
    </div>
  )
}
