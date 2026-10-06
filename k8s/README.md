# EKS Migration Assessor - Kubernetes Manifests

Kustomize manifests for deploying the EKS Migration Assessor on Kubernetes (local/kind and EKS).

## Directory Structure

```
k8s/
├── base/
│   ├── namespace.yaml
│   ├── serviceaccount.yaml
│   ├── statefulset.yaml
│   ├── service.yaml
│   ├── networkpolicy.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── local/
│   │   └── kustomization.yaml     # kind (local)
│   └── eks/
│       ├── kustomization.yaml
│       └── storageclass-gp3.yaml  # EBS gp3 for EKS
├── kind-config.yaml               # kind cluster config
└── README.md
```

---

## Quick Start (kind)

### 1. Create the kind cluster

```bash
kind create cluster --config k8s/kind-config.yaml --name eks-assessor
```

### 2. Build the Docker image

```bash
docker build -f docker/Dockerfile -t eks-assessor:dev .
```

### 3. Load the image into kind

```bash
kind load docker-image eks-assessor:dev --name eks-assessor
```

### 4. Deploy to kind (local overlay)

```bash
kubectl apply -k k8s/overlays/local
```

### 5. Verify deployment

```bash
# Check pod is ready
kubectl -n eks-assessor get pods -w

# Check PVC is Bound
kubectl -n eks-assessor get pvc

# Expected output:
# NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# workspace-eks-assessor-0   Bound    pvc-xxxxx   5Gi        RWO            standard       1m
```

### 6. Access the UI

```bash
# Port-forward to access locally
kubectl -n eks-assessor port-forward svc/eks-assessor 8501:80

# Open http://localhost:8501 in your browser
```

### 7. Test data persistence

```bash
# Create a test report via the UI, then delete the pod
kubectl -n eks-assessor delete pod eks-assessor-0

# Watch it come back
kubectl -n eks-assessor get pods -w

# The report files should still exist in /workspace
```

---

## EKS Deployment (Production)

### Prerequisites

- EKS cluster with EBS CSI driver installed
- **EKS Pod Identity** association (replaces IRSA) with appropriate permissions
- AWS Load Balancer Controller for Ingress (optional)

### 1. Create the StorageClass (gp3)

```bash
kubectl apply -k k8s/overlays/eks
```

This creates the `gp3` StorageClass with EBS CSI driver provisioner.

### 2. Create IAM Role for Pod Identity

```bash
# Create IAM role with trust policy for the service account
# Attach policies for: S3, Secrets Manager, CloudWatch Logs, etc.

# The association between the Kubernetes ServiceAccount and the IAM role
# is managed via EKS Pod Identity Association (created by Terraform).
# No service account annotations needed - Pod Identity uses the EKS Pod Identity Agent.
```

### 3. Deploy to EKS

```bash
# Build and push image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag eks-assessor:dev <account>.dkr.ecr.us-east-1.amazonaws.com/eks-assessor:dev
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/eks-assessor:dev

# Update image in statefulset (or use kustomize image tag)
kubectl -n eks-assessor set image statefulset/eks-assessor eks-assessor=<account>.dkr.ecr.us-east-1.amazonaws.com/eks-assessor:dev

# Apply EKS overlay
kubectl apply -k k8s/overlays/eks
```

### 4. Verify

```bash
kubectl -n eks-assessor get pods -w
kubectl -n eks-assessor get pvc
kubectl -n eks-assessor get storageclass
```

---

## Validation

### Render manifests locally

```bash
# Local (kind) overlay
kubectl kustomize k8s/overlays/local

# EKS overlay
kubectl kustomize k8s/overlays/eks
```

### Validate with kubeconform (if available)

```bash
kubectl kustomize k8s/overlays/eks | kubeconform -strict -ignore-missing-schemas
```

---

## Architecture Notes

### Why StatefulSet with replicas=1?

EBS volumes are **ReadWriteOnce** and bound to a single Availability Zone.
A StatefulSet with `replicas: 1` ensures:
- No multi-attach errors
- Stable network identity
- Ordered deployment/scaling
- Persistent storage tied to the pod

For high availability, deploy multiple StatefulSets in different AZs with separate EBS volumes.

### Security Context

The pod runs with:
- `runAsNonRoot: true`, `runAsUser: 10001`, `fsGroup: 10001`
- `allowPrivilegeEscalation: false`
- All capabilities dropped
- `seccompProfile: RuntimeDefault`
- `readOnlyRootFilesystem: true`

### NetworkPolicy

- **Ingress**: Allows traffic from ingress-nginx and same namespace on port 8501
- **Egress**: Only DNS (53/UDP/TCP), HTTPS (443), and EKS Pod Identity agent (169.254.170.23:80)

### volumeClaimTemplates

The StatefulSet uses a `volumeClaimTemplate` named `workspace` with:
- `accessModes: ["ReadWriteOnce"]`
- `resources.requests.storage: 5Gi`
- `storageClassName` patched per overlay (`standard` for kind, `gp3` for EKS)

---

## Pod Identity vs IRSA

This project uses **EKS Pod Identity** instead of IRSA (IAM Roles for Service Accounts):

| Aspect | IRSA | EKS Pod Identity |
|--------|------|------------------|
| Trust policy | OIDC provider + `sts:AssumeRoleWithWebIdentity` | `pods.eks.amazonaws.com` principal + `sts:AssumeRole` + `sts:TagSession` |
| Service Account annotation | `eks.amazonaws.com/role-arn` | **None required** |
| OIDC Provider | Must be created and configured | Not required |
| Association | IAM Role + SA annotation | **Pod Identity Association** (EKS resource) |
| Credential delivery | STS endpoint | EKS Pod Identity Agent (169.254.170.23:80) |

### How Terraform creates the Pod Identity Association

Terraform manages the EKS Pod Identity Association as a resource:

```hcl
resource "aws_eks_pod_identity_association" "assessor" {
  cluster_name    = aws_eks_cluster.main.name
  namespace       = "eks-assessor"
  service_account = "eks-assessor"
  role_arn        = aws_iam_role.assessor.arn
}
```

This creates the EKS Pod Identity Association, which:
1. Links the Kubernetes ServiceAccount `eks-assessor` in namespace `eks-assessor` to the IAM Role
2. The EKS Pod Identity Agent (running on each node at `169.254.170.23:80`) automatically provides credentials
3. No OIDC provider or service account annotations needed

The IAM role trust policy must allow `pods.eks.amazonaws.com`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "pods.eks.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ]
    }
  ]
}
```

### NetworkPolicy for Pod Identity

The NetworkPolicy includes an egress rule to allow the Pod Identity Agent:

```yaml
egress:
  - to:
      - ipBlock:
          cidr: 169.254.170.23/32
    ports:
      - protocol: TCP
        port: 80
```

This allows the pod to reach the EKS Pod Identity Agent at the link-local address `169.254.170.23:80`.

---

## Validation

### Render manifests locally

```bash
# Local (kind) overlay
kubectl kustomize k8s/overlays/local

# EKS overlay
kubectl kustomize k8s/overlays/eks
```

### Validate with kubeconform (if available)

```bash
kubectl kustomize k8s/overlays/eks | kubeconform -strict -ignore-missing-schemas
```

---

## Architecture Notes

### Why StatefulSet with replicas=1?

EBS volumes are **ReadWriteOnce** and bound to a single Availability Zone.
A StatefulSet with `replicas: 1` ensures:
- No multi-attach errors
- Stable network identity
- Ordered deployment/scaling
- Persistent storage tied to the pod

For high availability, deploy multiple StatefulSets in different AZs with separate EBS volumes.

### Security Context

The pod runs with:
- `runAsNonRoot: true`, `runAsUser: 10001`, `fsGroup: 10001`
- `allowPrivilegeEscalation: false`
- All capabilities dropped
- `seccompProfile: RuntimeDefault`
- `readOnlyRootFilesystem: true`

### NetworkPolicy

- **Ingress**: Allows traffic from ingress-nginx and same namespace on port 8501
- **Egress**: Only DNS (53/UDP/TCP), HTTPS (443), and EKS Pod Identity agent (169.254.170.23:80)

### volumeClaimTemplates

The StatefulSet uses a `volumeClaimTemplate` named `workspace` with:
- `accessModes: ["ReadWriteOnce"]`
- `resources.requests.storage: 5Gi`
- `storageClassName` patched per overlay (`standard` for kind, `gp3` for EKS)

---

## Cleanup

```bash
# Delete the kind cluster
kind delete cluster --name eks-assessor

# Or delete the namespace (cascades to all resources)
kubectl delete namespace eks-assessor
```