# Kubernetes Failure Test Scenarios

These scenarios can be used to test the AI Kubernetes Agent with real failures.

## Prerequisites

```bash
# Ensure you have a Kubernetes cluster and kubectl configured
kubectl config get-contexts
```

## Scenario 1: CrashLoopBackOff - Missing Environment Variable

```bash
# Create a deployment with missing env var
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crashloop-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crashloop-app
  template:
    metadata:
      labels:
        app: crashloop-app
    spec:
      containers:
      - name: app
        image: nginx:alpine
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: missing-secret
              key: database-url
        ports:
        - containerPort: 80
EOF
```

**Expected AI Diagnosis:**
- Root Cause: Pod in CrashLoopBackOff due to missing Secret `missing-secret` with key `database-url`
- Fix: Create the missing Secret or remove the env var reference
- kubectl: `kubectl create secret generic missing-secret --from-literal=database-url=postgres://...`

---

## Scenario 2: ImagePullBackOff - Wrong Image Tag

```bash
# Create a deployment with non-existent image tag
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: imagepull-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: imagepull-app
  template:
    metadata:
      labels:
        app: imagepull-app
    spec:
      containers:
      - name: app
        image: nginx:nonexistent-tag-12345
        ports:
        - containerPort: 80
EOF
```

**Expected AI Diagnosis:**
- Root Cause: ImagePullBackOff - image `nginx:nonexistent-tag-12345` not found in registry
- Fix: Update deployment to use valid image tag
- kubectl: `kubectl set image deployment/imagepull-app app=nginx:latest`

---

## Scenario 3: OOMKilled - Low Memory Limits

```bash
# Create a deployment with very low memory limit
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oom-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: oom-app
  template:
    metadata:
      labels:
        app: oom-app
    spec:
      containers:
      - name: app
        image: polinux/stress
        args: ["--vm", "1", "--vm-bytes", "256M", "--vm-keep"]
        resources:
          limits:
            memory: "64Mi"
          requests:
            memory: "32Mi"
EOF
```

**Expected AI Diagnosis:**
- Root Cause: Container OOMKilled - memory limit (64Mi) exceeded by stress test
- Fix: Increase memory limits or optimize application memory usage
- kubectl: `kubectl set resources deployment oom-app -c app --limits=memory=256Mi`

---

## Scenario 4: Service Selector Mismatch

```bash
# Create deployment with one label
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: selector-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: selector-app
      version: v1
  template:
    metadata:
      labels:
        app: selector-app
        version: v1
    spec:
      containers:
      - name: app
        image: nginx:alpine
        ports:
        - containerPort: 80
EOF

# Create service with different selector (missing version label)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: selector-service
  namespace: default
spec:
  selector:
    app: selector-app
    # Missing version: v1
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF
```

**Expected AI Diagnosis:**
- Root Cause: Service `selector-service` has no endpoints - selector mismatch (missing `version: v1` label)
- Fix: Update service selector to match pod labels
- kubectl: `kubectl patch service selector-service -p '{"spec":{"selector":{"app":"selector-app","version":"v1"}}}'`

---

## Scenario 5: Pending Pod - Insufficient Resources

```bash
# Create a deployment requesting more resources than available
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pending-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pending-app
  template:
    metadata:
      labels:
        app: pending-app
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: "100"
            memory: "1Ti"
EOF
```

**Expected AI Diagnosis:**
- Root Cause: Pod stuck in Pending - insufficient cluster resources (requests exceed capacity)
- Fix: Reduce resource requests or scale up cluster
- kubectl: `kubectl set resources deployment pending-app -c app --requests=cpu=100m,memory=128Mi`

---

## Cleanup

```bash
# Remove all test resources
kubectl delete deployment crashloop-app imagepull-app oom-app selector-app pending-app --ignore-not-found
kubectl delete service selector-service --ignore-not-found
kubectl delete secret missing-secret --ignore-not-found
```

## Running the AI Agent

1. Start the application:
   ```bash
   docker compose up --build
   ```

2. Open http://localhost:3000
3. Sign in / Sign up
4. Select your cluster from the cluster selector
5. Select namespace (default)
6. Click "Investigate Cluster"
7. Watch the progress and review the diagnosis