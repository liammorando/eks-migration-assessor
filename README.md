# EKS Migration Assessor

> **Analyze any public GitHub/GitLab repository for EKS migration readiness — free, deterministic, and optionally AI-enhanced.**

![Architecture](architecture.png)

## Descripción en Español

**Evaluador de Preparación para Migración a EKS**: análisis estático determinista de repositorios públicos de GitHub/GitLab para detectar patrones anti-migración a Kubernetes (EKS), con puntuación de preparación (0-100), hallazgos categorizados por severidad, plan de migración por fases con acciones concretas, y reporte ejecutivo opcional mediante LLM local (Ollama).

### Características principales

- **Análisis determinista**: 22+ reglas de detección en 8 categorías (Estado, Configuración, Red, Contenedor, Logging, Ciclo de vida, Docker Compose, Positivos)
- **Puntuación 0-100** con niveles: Ready (≥85), Ready with minor changes (65-84), Needs significant work (40-64), Not ready (<40)
- **Plan de migración** por fases (1-4) con acciones, esfuerzo (S/M/L) y referencias a hallazgos
- **LLM opcional** (Ollama local) para resumen ejecutivo y chat interactivo
- **Interfaz web** (Streamlit) con tema oscuro, i18n (EN/ES), exportación MD/JSON
- **Kubernetes manifests** (Kustomize base + overlays para kind y EKS)
- **Terraform** completo (EKS + VPC + EBS CSI + Pod Identity + ECR + S3)
- **CI/CD gratis** (GitHub Actions: tests, Docker build, K8s validation, Terraform validation)

---

## Features

- **Deterministic static analysis** — 17 detection rules across 7 categories (State, Config, Networking, Container, Logging, Lifecycle, Compose)
- **Scoring & migration plan** — 0-100 readiness score, phased remediation plan with effort estimates
- **Executive summary** — Optional AI-generated summary via local Ollama (free, no API keys)
- **Multi-format reports** — Markdown + JSON output
- **Kubernetes manifests** — Kustomize base + overlays for kind (local) and EKS (production)
- **Terraform** — Complete EKS + VPC + EBS CSI + Pod Identity + ECR + S3 (validated, never applied)
- **Free CI/CD** — GitHub Actions: Python tests, Docker build, K8s validation, Terraform validation
- **AgentCore** — Optional AgentCore adapter for running as a pod in EKS
- **Interactive Web UI** — Streamlit-based interface with real-time progress, tabbed results, history, and agent chat

## UI

The web UI (`app/streamlit_app.py`) provides five tabs for exploring assessment results:

- **Overview** — KPI cards (score gauge, findings severity bar, files scanned, repo info), top priorities, strengths, and executive summary
- **Findings** — Filterable, searchable list with grouped/flat views, severity pills, category filter, and pagination
- **Migration Plan** — Each phase as a card with phase badge, title, effort badge (S/M/L), rationale, action bullets, and related finding ID tags
- **Report** — Full Markdown report in a bordered container with comfortable reading width; download buttons for Markdown and JSON
- **Ask the Agent** — Follow-up Q&A via local Ollama (disabled when repository is not available post-analysis)

Sidebar sections:
- **Settings** — Language selector (EN/ES)
- **Analysis** — Toggle "Use local LLM (Ollama)" with expandable LLM settings (host, model, inline validation status), max repo size input
- **History** — 10 most recent reports of this session with repo name, score badge, relative time, and Load button
- **Environment** (collapsed) — Workspace path, session ID, and security notice

Design system documented in [docs/ui-design.md](docs/ui-design.md). Screenshots: ![Overview](docs/screenshots/overview.png) ![Findings](docs/screenshots/findings.png) ![Plan](docs/screenshots/plan.png) ![Report](docs/screenshots/report.png)

## Quick Start / Inicio Rápido

### Instalación Base
```bash
pip install -e ".[dev]"
```

### Con LLM Local (Ollama)
```bash
pip install -e ".[dev,llm]"
```

### Con Soporte AWS
```bash
pip install -e ".[dev,aws]"
```

### Python Local (CLI)
```bash
eks-migration-assessor scan https://github.com/pallets/flask --no-llm --out ./report
```

### Docker Compose
```bash
docker compose up
# Abre http://localhost:8501
```

### Kubernetes Local (kind)
```bash
kind create cluster --config k8s/kind-config.yaml --name eks-assessor
docker build -f docker/Dockerfile -t eks-assessor:dev .
kind load docker-image eks-assessor:dev --name eks-assessor
kubectl apply -k k8s/overlays/local
kubectl -n eks-assessor port-forward svc/eks-assessor 8501:80
# Abre http://localhost:8501
```

### Despliegue en EKS (producción)
```bash
cd terraform
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
# Luego: terraform init && terraform apply  (requiere credenciales AWS)
```

## Architecture

```mermaid
flowchart TD
    User[User] --> UI[Streamlit UI / CLI]
    UI --> Scanner[Static Scanner]
    Scanner --> Rules[17 Detection Rules]
    Rules --> Scoring[Scoring Engine]
    Scoring --> Plan[Migration Planner]
    Plan --> Report[Markdown + JSON Report]
    
    subgraph Optional["Optional AI Layer"]
        Ollama[Ollama LLM] -.-> Strands[Strands Agent]
        Strands --> Summary[Executive Summary]
        Strands -.-> Chat[Follow-up Q&A]
    end
    
    Optional --> Report
    
    subgraph K8s["Kubernetes (EKS/kind)"]
        Pod[eks-assessor Pod]
        PVC[PVC → EBS CSI → EBS Volume]
        SA[ServiceAccount eks-assessor]
        SA --> PI[Pod Identity Association]
        PI --> IAM[IAM Role: S3 Put/Get/List]
        IAM --> S3[(S3 Reports Bucket)]
        Pod --> PVC
        Pod --> SA
    end
    
    Report --> UI
    
    subgraph AgentCore["AgentCore (Optional)"]
        AgentCore[AgentCore Pod in EKS]
        AgentCore --> K8sAPI[Kubernetes API]
        AgentCore --> Bedrock[Bedrock AgentCore Runtime]
    end
    
    Optional --> Report
    AgentCore --> Report
```

## Why It's Free / Por Qué Es Gratis

| Component | Cost |
|-----------|------|
| Static analysis engine | Pure Python, no external APIs |
| Local LLM | Ollama (runs on your machine) |
| CI/CD | GitHub Actions free tier |
| Container image | Built locally, no registry fees |
| Kubernetes | kind (local) or your existing cluster |
| Terraform | Validated only, never applied |

**No API keys, no cloud accounts, no paid tiers.**
**Sin claves API, sin cuentas en la nube, sin planes de pago.**

## What Is Intentionally Not Deployed

- **No `terraform apply`** — Terraform is validated only (`fmt`, `init -backend=false`, `validate`)
- **No `terraform plan` against AWS** — No credentials configured in CI
- **No `kubectl apply` in CI** — Manifests are validated with `kubeconform` only
- **No production credentials** — All examples use local kind or mock data

## Rule Catalog

See [docs/rules.md](docs/rules.md) for the complete catalog of 17 detection rules.

### Documentation File Handling

The scanner treats certain files as **documentation** to reduce false positives:

- **Code-pattern rules** (STATE-001, STATE-002, STATE-003, NET-001, NET-002, LOG-001, LIFE-001) **skip** documentation files entirely.
- **Secret detection (CFG-001)** still runs on documentation files but **downgrades severity by one level** (e.g., CRITICAL → HIGH).

Files considered documentation: `.md`, `.rst`, `.txt` extensions; files under `docs/`, `doc/`, `examples/`, `samples/`; and special files like `CHANGELOG*`, `LICENSE*`, `NOTICE*`, `README*`, `CONTRIBUTING*`, `AUTHORS*`, `HISTORY*`, `NEWS*`, `CHANGES*`, `TODO*`, `COPYING*`.

| ID | Severity | Category | Title |
|----|----------|----------|-------|
| STATE-001 | 🟠 HIGH | `state` | Local filesystem writes |
| STATE-002 | 🟠 HIGH | `state` | In-memory session/state storage |
| STATE-003 | 🟠 HIGH | `state` | SQLite/local database file |
| CFG-001 | 🔴 CRITICAL | `config` | Hardcoded secrets |
| CFG-002 | 🟡 MEDIUM | `config` | No env var configuration |
| NET-001 | 🟡 MEDIUM | `networking` | Hardcoded IPs/localhost |
| NET-002 | 🟢 LOW | `networking` | Hardcoded ports |
| CTR-001 | 🟠 HIGH | `container` | No Dockerfile |
| CTR-002 | 🟡 MEDIUM | `container` | Runs as root |
| CTR-003 | 🟡 MEDIUM | `container` | :latest tag |
| CTR-004 | 🟡 MEDIUM | `container` | No health check |
| LOG-001 | 🟡 MEDIUM | `logging` | File logging |
| LIFE-001 | 🟢 LOW | `lifecycle` | No SIGTERM handling |
| CMP-001 | 🟠 HIGH | `container` | Host bind mounts |
| CMP-002 | 🔴 CRITICAL | `container` | Privileged/host network |
| CMP-003 | 🟢 LOW | `container` | Fixed container_name/depends_on |
| CMP-004 | 🟠 HIGH | `container` | Missing Dockerfile |
| OK-001 | 🔵 INFO | `config` | Positive practices |

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **StatefulSet with replicas=1** | EBS volumes are ReadWriteOnce (RWO) and bound to a single AZ. A single replica avoids multi-attach errors. For HA, deploy multiple StatefulSets in different AZs. |
| **No Fargate** | Fargate does not support EBS volumes, which are required for PVCs. The assessor needs persistent storage for reports. |
| **Static analysis only** | Never executes analyzed code. Safe for untrusted repositories. |
| **Optional LLM** | Executive summary only. Core analysis is deterministic and works without any LLM. |
| **Pod Identity vs IRSA** | Pod Identity (EKS Pod Identity Agent) is the modern replacement for IRSA. Simpler trust policies, no OIDC provider management, supports tagging. |
| **StatefulSet + PVC** | Reports must survive pod restarts. EBS volumes via CSI provide RWO persistent storage. |
| **Deterministic scoring** | Penalties per severity (critical=25, high=12, medium=5, low=2, info=0), capped at 2x per rule ID to avoid over-penalizing repeated patterns. |

## Limitations & Roadmap

### Limitations
- **Heuristics can produce false positives** — Pattern matching on source code may flag code that's actually fine in context (e.g., test files, commented code).
- **Language coverage** — Rules are biased toward Python, Dockerfile, YAML, docker-compose. Limited support for Go, Java, Node.js, etc.
- **No runtime analysis** — Cannot detect issues that only manifest at runtime (e.g., memory leaks, config loaded from external sources).
- **Single-replica only** — StatefulSet with replicas=1 is a design choice for EBS RWO volumes; HA requires multi-AZ deployment.

### Roadmap
- [ ] Expand language support (Go, Java, JavaScript/TypeScript, .NET)
- [ ] Add more framework-specific rules (Spring Boot, Express, FastAPI, etc.)
- [ ] Improve false positive reduction with context-aware analysis
- [ ] Add SARIF output for GitHub Security tab integration
- [ ] Support for Helm charts and Kustomize in source repos
- [ ] Webhook/API for integration with CI pipelines

## Security Notes

- **No authentication** — This is a single-tenant demo. Production deployment needs OIDC + a Kubernetes Job per analysis with its own ServiceAccount, quotas, and restricted egress.
- **Single-tenant demo** — Not multi-tenant. No tenant isolation.
- **Production needs** — OIDC + a Kubernetes Job per analysis with its own ServiceAccount, quotas, and restricted egress.

## AgentCore

The AgentCore adapter (`src/assessor/agentcore_entrypoint.py`) allows running the assessor as a pod in EKS. The agent runs as a pod in EKS and uses the Bedrock AgentCore runtime. AgentCore is **only an optional adapter** — it is not deployed in this project.

## License

TODO: choose a license