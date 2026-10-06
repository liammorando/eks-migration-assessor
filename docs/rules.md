# EKS Migration Assessor - Rule Catalog

This document lists all detection rules used by the EKS Migration Assessor.
Rules are organized by category and include severity, description, and EKS remediation hints.

## Documentation File Handling

The scanner treats certain files as **documentation** and applies special handling:

- **Code-pattern rules** (STATE-001, STATE-002, STATE-003, NET-001, NET-002, LOG-001, LIFE-001) **skip** documentation files entirely to avoid false positives from examples, SQL snippets, or configuration examples in docs.
- **Secret detection (CFG-001)** still runs on documentation files but **downgrades severity by one level** (e.g., CRITICAL → HIGH) since secrets in docs are often placeholders or examples.

Files considered documentation:
- Any file with extension `.md`, `.rst`, `.txt`
- Any file under `docs/`, `doc/`, `examples/`, or `samples/` directories (case-insensitive)
- Special files: `CHANGELOG*`, `LICENSE*`, `NOTICE*`, `README*`, `CONTRIBUTING*`, `AUTHORS*`, `HISTORY*`, `NEWS*`, `CHANGES*`, `TODO*`, `COPYING*` (case-insensitive, with or without extension)

## Rule Summary

| ID | Severity | Category | Title |
|----|----------|----------|-------|
| CFG-001 | 🔴 CRITICAL | `config` | Hardcoded secrets |
| CFG-002 | 🟡 MEDIUM | `config` | No environment variable configuration |
| CMP-001 | 🟠 HIGH | `container` | Host bind mounts in docker-compose |
| CMP-002 | 🔴 CRITICAL | `container` | Privileged or host network mode in docker-compose |
| CMP-003 | 🟢 LOW | `container` | Fixed container_name or depends_on for startup ordering |
| CMP-004 | 🟠 HIGH | `container` | Missing Dockerfile for build context |
| CTR-001 | 🟠 HIGH | `container` | No Dockerfile |
| CTR-002 | 🟡 MEDIUM | `container` | Dockerfile runs as root |
| CTR-003 | 🟡 MEDIUM | `container` | Dockerfile uses :latest tag |
| CTR-004 | 🟡 MEDIUM | `container` | No health check endpoint |
| LIFE-001 | 🟢 LOW | `lifecycle` | No SIGTERM/graceful shutdown handling |
| LOG-001 | 🟡 MEDIUM | `logging` | Logging to files instead of stdout |
| NET-001 | 🟡 MEDIUM | `networking` | Hardcoded IP addresses or localhost |
| NET-002 | 🟢 LOW | `networking` | Hardcoded ports without env override |
| OK-001 | 🔵 INFO | `config` | Positive practice detected |
| STATE-001 | 🟠 HIGH | `state` | Local filesystem writes detected |
| STATE-002 | 🟠 HIGH | `state` | In-memory session/state storage |
| STATE-003 | 🟠 HIGH | `state` | SQLite or local database file |

---

## Detailed Rule Descriptions

### CFG-001: Hardcoded secrets

**Severity:** 🔴 CRITICAL  
**Category:** `config`  

Hardcoded secrets, passwords, API keys, or AWS credentials in source code.

**EKS Remediation:** Use AWS Secrets Manager with Pod Identity, or Kubernetes Secrets; never commit secrets to code

---

### CFG-002: No environment variable configuration

**Severity:** 🟡 MEDIUM  
**Category:** `config`  

Application doesn't use environment variables for configuration (12-factor app violation).

**EKS Remediation:** Use environment variables for configuration (12-factor); use ConfigMap in Kubernetes

---

### CMP-001: Host bind mounts in docker-compose

**Severity:** 🟠 HIGH  
**Category:** `container`  

docker-compose.yml uses host bind mounts (absolute host paths) which are not portable to Kubernetes.

**EKS Remediation:** Replace host bind mounts with PVC volumes in Kubernetes

---

### CMP-002: Privileged or host network mode in docker-compose

**Severity:** 🔴 CRITICAL  
**Category:** `container`  

docker-compose.yml uses privileged: true or network_mode: host, which are not allowed in Kubernetes.

**EKS Remediation:** Remove privileged: true; use securityContext with specific capabilities if needed; remove network_mode: host

---

### CMP-003: Fixed container_name or depends_on for startup ordering

**Severity:** 🟢 LOW  
**Category:** `container`  

docker-compose.yml uses fixed container_name or depends_on for startup ordering, which don't translate to Kubernetes.

**EKS Remediation:** Remove container_name; use initContainers or readiness probes for startup ordering

---

### CMP-004: Missing Dockerfile for build context

**Severity:** 🟠 HIGH  
**Category:** `container`  

docker-compose.yml references build: context but no Dockerfile exists there.

**EKS Remediation:** Create Dockerfile in the build context or fix the build path

---

### CTR-001: No Dockerfile

**Severity:** 🟠 HIGH  
**Category:** `container`  

Project has no Dockerfile, cannot be containerized for Kubernetes.

**EKS Remediation:** Create a Dockerfile to containerize the application

---

### CTR-002: Dockerfile runs as root

**Severity:** 🟡 MEDIUM  
**Category:** `container`  

Dockerfile doesn't specify a non-root USER; container runs as root.

**EKS Remediation:** Add USER directive in Dockerfile; use runAsNonRoot: true in pod securityContext

---

### CTR-003: Dockerfile uses :latest tag

**Severity:** 🟡 MEDIUM  
**Category:** `container`  

Dockerfile uses :latest tag or no tag, making builds non-reproducible.

**EKS Remediation:** Use pinned image tags (e.g., python:3.12-slim) for reproducible builds

---

### CTR-004: No health check endpoint

**Severity:** 🟡 MEDIUM  
**Category:** `container`  

No HEALTHCHECK in Dockerfile and no /health, /healthz, or /ready endpoint in application code.

**EKS Remediation:** Add HEALTHCHECK to Dockerfile and implement /healthz and /ready endpoints in application; configure livenessProbe and readinessProbe in deployment

---

### LIFE-001: No SIGTERM/graceful shutdown handling

**Severity:** 🟢 LOW  
**Category:** `lifecycle`  

Application doesn't handle SIGTERM for graceful shutdown, causing abrupt termination.

**EKS Remediation:** Add signal handler for SIGTERM; set terminationGracePeriodSeconds in pod spec

---

### LOG-001: Logging to files instead of stdout

**Severity:** 🟡 MEDIUM  
**Category:** `logging`  

Application logs to files (FileHandler, /var/log) instead of stdout, preventing log aggregation.

**EKS Remediation:** Log to stdout/stderr; use CloudWatch agent or Fluent Bit for log aggregation in EKS

---

### NET-001: Hardcoded IP addresses or localhost

**Severity:** 🟡 MEDIUM  
**Category:** `networking`  

Application uses hardcoded localhost, 127.0.0.1, or private IP addresses (10.x, 172.16-31.x, 192.168.x) which won't work in Kubernetes.

**EKS Remediation:** Use Kubernetes Service DNS names (e.g., service-name.namespace.svc.cluster.local)

---

### NET-002: Hardcoded ports without env override

**Severity:** 🟢 LOW  
**Category:** `networking`  

Application uses hardcoded port numbers without environment variable override.

**EKS Remediation:** Use environment variable for port (e.g., PORT=8080); Kubernetes injects container port via Service

---

### OK-001: Positive practice detected

**Severity:** 🔵 INFO  
**Category:** `config`  

Good practice found: stdout logging, env config, health endpoint, non-root user, HEALTHCHECK, or pinned tag.

**EKS Remediation:** Good practice - no action needed

---

### STATE-001: Local filesystem writes detected

**Severity:** 🟠 HIGH  
**Category:** `state`  

Application writes to local filesystem (e.g., open() with write mode, os.makedirs on absolute paths) which is ephemeral in Kubernetes.

**EKS Remediation:** Use PVC with EBS CSI Driver, or S3 for object storage

---

### STATE-002: In-memory session/state storage

**Severity:** 🟠 HIGH  
**Category:** `state`  

Application stores session or state in memory (module-level dicts, Flask session without external store) which is not shared across pods.

**EKS Remediation:** Use Redis/ElastiCache or DynamoDB for session storage; run stateless pods

---

### STATE-003: SQLite or local database file

**Severity:** 🟠 HIGH  
**Category:** `state`  

Application uses SQLite or local database files which don't work in distributed Kubernetes environments.

**EKS Remediation:** Use RDS (PostgreSQL/MySQL) or a StatefulSet with PVC

---
