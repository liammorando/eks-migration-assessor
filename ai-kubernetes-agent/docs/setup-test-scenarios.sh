#!/bin/bash
# Test scenario setup script for AI Kubernetes Agent
# Run with: bash docs/setup-test-scenarios.sh [scenario_number]

set -e

SCENARIO=${1:-"all"}

echo "Setting up Kubernetes test scenarios for AI Kubernetes Agent..."

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl first."
    exit 1
fi

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster. Check your kubeconfig."
    exit 1
fi

echo "Connected to cluster: $(kubectl config current-context)"

setup_crashloop() {
    echo "=== Scenario 1: CrashLoopBackOff (Missing Env Var) ==="
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
    echo "Created crashloop-app deployment. Pod should enter CrashLoopBackOff."
}

setup_imagepull() {
    echo "=== Scenario 2: ImagePullBackOff (Wrong Image Tag) ==="
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
    echo "Created imagepull-app deployment. Pod should enter ImagePullBackOff."
}

setup_oom() {
    echo "=== Scenario 3: OOMKilled (Low Memory Limits) ==="
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
    echo "Created oom-app deployment. Pod should get OOMKilled."
}

setup_selector_mismatch() {
    echo "=== Scenario 4: Service Selector Mismatch ==="
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

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: selector-service
  namespace: default
spec:
  selector:
    app: selector-app
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF
    echo "Created selector-app deployment and selector-service with mismatched selector."
}

setup_pending() {
    echo "=== Scenario 5: Pending Pod (Insufficient Resources) ==="
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
    echo "Created pending-app deployment. Pod should stay Pending."
}

cleanup_all() {
    echo "=== Cleaning up all test resources ==="
    kubectl delete deployment crashloop-app imagepull-app oom-app selector-app pending-app --ignore-not-found=true
    kubectl delete service selector-service --ignore-not-found=true
    kubectl delete secret missing-secret --ignore-not-found=true
    echo "Cleanup complete."
}

case $SCENARIO in
    1)
        setup_crashloop
        ;;
    2)
        setup_imagepull
        ;;
    3)
        setup_oom
        ;;
    4)
        setup_selector_mismatch
        ;;
    5)
        setup_pending
        ;;
    "all")
        setup_crashloop
        setup_imagepull
        setup_oom
        setup_selector_mismatch
        setup_pending
        ;;
    "cleanup")
        cleanup_all
        ;;
    *)
        echo "Usage: $0 [1|2|3|4|5|all|cleanup]"
        echo "  1 - CrashLoopBackOff (Missing Env Var)"
        echo "  2 - ImagePullBackOff (Wrong Image Tag)"
        echo "  3 - OOMKilled (Low Memory Limits)"
        echo "  4 - Service Selector Mismatch"
        echo "  5 - Pending Pod (Insufficient Resources)"
        echo "  all - Create all scenarios"
        echo "  cleanup - Remove all test resources"
        exit 1
        ;;
esac

echo ""
echo "Test scenario setup complete!"
echo "Open http://localhost:3000 and click 'Investigate Cluster' to test."