# Terraform: Infraestructura EKS Migration Assessor

Este directorio contiene la configuración de Terraform para desplegar la infraestructura necesaria para el **EKS Migration Assessor** en AWS.

## ⚠️ IMPORTANTE: Solo Validación

**NO se debe ejecutar `terraform apply` ni `terraform plan` contra AWS.**  
Esta configuración está diseñada para **validación estática únicamente**. Los únicos comandos permitidos son:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

Estos comandos no requieren credenciales AWS ni conexión a internet (salvo para descargar proveedores).

---

## ¿Qué crea esta configuración?

### 1. VPC (`vpc.tf`)
- VPC con CIDR configurable (default `10.0.0.0/16`)
- 2 AZs para alta disponibilidad
- Subredes públicas y privadas **explícitas** (usando `cidrsubnet`)
- **Single NAT Gateway** (tradeoff de costo: ~$45/mes ahorrados, pero dependencia de AZ)

### 2. EKS Cluster (`eks.tf`)
- Cluster EKS versión configurable (default **1.30** - versión STANDARD support actual)
- **Un managed node group en subredes privadas**
- **NO Fargate profile**: Fargate no soporta volúmenes EBS (necesarios para PVCs del assessor)
- Endpoint público y privado habilitado
- `enable_cluster_creator_admin_permissions = true`
- **Node AMI**: `AL2023_x86_64_STANDARD` (Amazon Linux 2023 - AL2 está en mantenimiento)
- **api_allowed_cidrs**: Acceso al endpoint público restringido (sin default a 0.0.0.0/0)

### 3. Addons (`addons.tf`)
- **eks-pod-identity-agent**: Para Pod Identity (reemplaza IRSA)
- **aws-ebs-csi-driver**: Para PVCs con EBS (requiere IAM role via Pod Identity)
- **vpc-cni**, **coredns**, **kube-proxy**: Addons core de EKS
- **Versiones de addons**: Usan `data "aws_eks_addon_version"` con `most_recent = true`
- **EBS CSI Driver**: Sin `service_account_role_arn` (usa Pod Identity)
- **vpc-cni**: Config `enableNetworkPolicy = "true"`
- **depends_on = [module.eks]** en todos los addons

### 4. Pod Identity (`pod_identity.tf`)
- **EBS CSI Driver** → ServiceAccount `ebs-csi-controller-sa` en `kube-system` → Role con `AmazonEBSCSIDriverPolicy`
- **App (eks-assessor)** → ServiceAccount `eks-assessor` en namespace `eks-assessor` → Role con política S3 de mínimo privilegio (solo bucket de reportes)
- Variable renombrada: `create_app_pod_identity` (antes `enable_irsa_for_app`) - Pod Identity no requiere OIDC

### 4. ECR (`ecr.tf`)
- Repositorio con **scan on push** e **immutable tags**
- Lifecycle policy: conserva últimas 10 imágenes, elimina untagged > 7 días
- **tagPatternList**: `["v*", "sha-*"]` (patrón semver `v1.2.3` y git SHA `sha-abc123`)

### 5. S3 (`s3.tf`)
- Bucket privado, versionado, encriptado (AES256), acceso público bloqueado
- **Bucket ownership controls**: `BucketOwnerEnforced` (requerido para Pod Identity)
- Lifecycle: transición a Glacier a 90 días, expiración a 365 días
- **Bucket policy**: SOLO deniega requests donde `aws:SecureTransport` es false (HTTPS obligatorio)
- **Ownership controls**: `BucketOwnerEnforced` (requerido para Pod Identity)

### 6. Outputs (`outputs.tf`)
- Sin outputs hardcoded - derivados del módulo EKS
- `node_group_name` derivado de `module.eks.eks_managed_node_group_names["assessor"]`

---

## Cómo se conectan las piezas

```
┌─────────────────┐     Pod Identity      ┌──────────────────┐
│  eks-assessor   │◄─────────────────────►│  IAM Role (App)  │
│  (ServiceAccount)│  Association          │  (S3: reports   │
│  namespace:      │                       │   bucket only)   │
│  eks-assessor    │                       └──────────────────┘
└─────────────────┘
         │
         │ PVC (EBS via CSI)
         ▼
┌─────────────────┐     Pod Identity      ┌──────────────────────┐
│  EBS CSI Driver │◄─────────────────────►│  IAM Role (CSI)    │
│  (ServiceAccount)│  Association          │  AmazonEBSCSI...   │
│  namespace: kube-│                       │  (Managed Policy)  │
│  system          │                       └──────────────────────┘
└─────────────────┘
```

1. **Pod Identity** asocia ServiceAccounts de Kubernetes a Roles IAM
2. **App** usa su rol para `s3:PutObject/GetObject/ListBucket` **solo** en el bucket de reportes
3. **EBS CSI Driver** usa su rol para crear/adjuntar volúmenes EBS para PVCs
4. **S3 Bucket** tiene política que deniega acceso a cualquier principal que no sea un rol del cluster (`${cluster_name}-*`)

---

## ⚡ Advertencia de Costos (Aproximados)

| Componente | Costo estimado (us-east-1) |
|------------|---------------------------|
| EKS Control Plane | ~$0.10/hora ($73/mes) |
| NAT Gateway (1) | ~$0.045/hora ($33/mes) + datos |
| EC2 t3.medium (1) | ~$0.0416/hora ($30/mes) |
| EBS gp3 5GiB | ~$0.50/mes |
| ECR (scan + storage) | ~$0.10/GB/mes |
| S3 (reports) | < $1/mes típico |

**Total estimado: ~$140-180/mes** para entorno de desarrollo con 1 nodo.

> **Nota**: El control plane EKS es el costo fijo principal. Para reducir costos en dev, considerar apagar el cluster fuera de horario laboral.

---

## Validación Local

```bash
cd terraform

# Formato
terraform fmt -check -recursive

# Inicializar (sin backend)
terraform init -backend=false

# Validar sintaxis y referencias
terraform validate

# Opcional: tflint (si está instalado)
# tflint --init && tflint

# Opcional: checkov (si está instalado)
# checkov -d .
```

---

## Despliegue Real (Cuando esté listo)

```bash
# 1. Configurar credenciales AWS
aws configure

# 2. Inicializar con backend (S3 + DynamoDB para state locking)
terraform init

# 2. Planificar
terraform plan -out=tfplan

# 3. Aplicar (requiere aprobación)
terraform apply tfplan

# 4. Actualizar kubeconfig
aws eks update-kubeconfig --name eks-assessor --region us-east-1

# 5. Verificar
kubectl get nodes
kubectl -n eks-assessor get pods
```

---

## Limpieza

```bash
# Destruir todo (¡CUIDADO: elimina todo!)
terraform destroy
```

---

## Configuración de Backend Remoto (para uso real)

Ver `backend.tf.example` - copiar a `backend.tf` y configurar bucket S3 + DynamoDB para state locking.