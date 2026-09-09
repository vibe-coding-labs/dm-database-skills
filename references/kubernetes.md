# 达梦数据库 Kubernetes 部署指引

Kubernetes 部署达梦适合需要多副本、滚动升级、集中监控的场景。达梦官方镜像通常以单容器形态发布，以下为最小可用部署示例。

## 1. 前置

- 已就绪 K8s 集群（RBAC、StorageClass 可用）
- 镜像可由集群访问，建议使用可达镜像源
- 持久化使用 PersistentVolume/PersistentVolumeClaim

## 2. 示例清单

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dm8-config
data:
  CASE_SENSITIVE: "1"
---
apiVersion: v1
kind: Secret
metadata:
  name: dm8-secret
type: Opaque
stringData:
  SYSDBA_PWD: SYSDBA001
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dm8-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: apps/v1
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
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5236
          env:
            - name: CASE_SENSITIVE
              valueFrom:
                configMapKeyRef:
                  name: dm8-config
                  key: CASE_SENSITIVE
            - name: SYSDBA_PWD
              valueFrom:
                secretKeyRef:
                  name: dm8-secret
                  key: SYSDBA_PWD
          volumeMounts:
            - name: dm8-data
              mountPath: /opt/dmdbms/data
          readinessProbe:
            tcpSocket:
              port: 5236
            initialDelaySeconds: 20
            periodSeconds: 10
          livenessProbe:
            tcpSocket:
              port: 5236
            initialDelaySeconds: 30
            periodSeconds: 10
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
      targetPort: 5236
  type: ClusterIP
```

## 3. 部署与验证

```bash
kubectl apply -f dm8.yaml
kubectl get pods -l app=dm8
kubectl port-forward deploy/dm8 5236:5236
```

## 4. 连接

在集群内或通过 port-forward 连接：

```bash
python3 scripts/dm8_connect.py --host 127.0.0.1 --port 5236 --user SYSDBA --password SYSDBA001
```

## 5. 生产建议

- 将镜像密码放入 Secret，勿硬编码
- 按需启用 NodeAffinity/Toleration
- 配置 Backup/Restore 与日志采集
- 如需要多副本，请评估达梦官方高可用方案
