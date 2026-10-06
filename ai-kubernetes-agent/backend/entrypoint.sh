#!/bin/bash
set -e

# Configure kubectl for kind cluster if not already configured
if ! kubectl config get-clusters | grep -q "kubernetes-demo-cluster"; then
    echo "Configuring kubectl for kind cluster..."
    
    # Create .kube directory
    mkdir -p /root/.kube
    
    # Write simple kubeconfig with insecure-skip-tls-verify
    cat > /root/.kube/config << 'EOF'
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://kubernetes-demo-cluster-control-plane:6443
  name: kubernetes-demo-cluster
contexts:
- context:
    cluster: kubernetes-demo-cluster
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes-demo-cluster
current-context: kubernetes-admin@kubernetes-demo-cluster
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    token: ""
EOF
    echo "kubectl configured for kind cluster"
else
    echo "kubectl already configured"
fi

# Execute the main command
exec "$@"