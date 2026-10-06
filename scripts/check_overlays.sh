#!/bin/bash
# Check that kustomize overlays render correctly and contain expected values
# Run from repository root: ./scripts/check_overlays.sh

set -euo pipefail

echo "Checking kustomize overlays..."

# Check that kubectl kustomize works
echo "Testing kubectl kustomize for local overlay..."
LOCAL_OUTPUT=$(kubectl kustomize k8s/overlays/local)
if [ $? -ne 0 ]; then
    echo "FAIL: kubectl kustomize k8s/overlays/local failed"
    exit 1
fi

echo "Testing kubectl kustomize for eks overlay..."
EKS_OUTPUT=$(kubectl kustomize k8s/overlays/eks)
if [ $? -ne 0 ]; then
    echo "FAIL: kubectl kustomize k8s/overlays/eks failed"
    exit 1
fi

# Check local overlay has storageClassName: standard
echo "Checking local overlay has storageClassName: standard..."
if ! echo "$LOCAL_OUTPUT" | grep -q "storageClassName: standard"; then
    echo "FAIL: local overlay missing 'storageClassName: standard'"
    exit 1
fi
echo "OK: local overlay has storageClassName: standard"

# Check eks overlay has storageClassName: gp3
echo "Checking eks overlay has storageClassName: gp3..."
if ! echo "$EKS_OUTPUT" | grep -q "storageClassName: gp3"; then
    echo "FAIL: eks overlay missing 'storageClassName: gp3'"
    exit 1
fi
echo "OK: eks overlay has storageClassName: gp3"

# Check eks overlay has StorageClass kind
echo "Checking eks overlay has StorageClass kind..."
if ! echo "$EKS_OUTPUT" | grep -q "kind: StorageClass"; then
    echo "FAIL: eks overlay missing 'kind: StorageClass'"
    exit 1
fi
echo "OK: eks overlay has StorageClass"

# Check neither output contains template syntax
echo "Checking neither output contains template syntax..."
if echo "$LOCAL_OUTPUT" | grep -q '{{'; then
    echo "FAIL: local output contains template syntax '{{'"
    exit 1
fi
if echo "$EKS_OUTPUT" | grep -q '{{'; then
    echo "FAIL: eks output contains template syntax '{{'"
    exit 1
fi
echo "OK: no template syntax found"

# Check eks output does NOT contain role-arn
echo "Checking eks output does NOT contain role-arn..."
if echo "$EKS_OUTPUT" | grep -q "role-arn"; then
    echo "FAIL: eks output contains 'role-arn' (IRSA leftover)"
    exit 1
fi
echo "OK: no role-arn found in eks output"

echo ""
echo "All checks passed!"
exit 0