# Security TODOs

The following items contain credentials or sensitive data and require action before this repository can be safely committed or shared:

## Rotate credentials
- **admin.conf**: Contains Kubernetes cluster admin credentials (certificates, tokens, server URLs). Rotate all certificates and tokens immediately.
- **.env / .env.\***: May contain API keys, database passwords, or other secrets. Rotate all values.
- **opencode.json**: May contain API keys or authentication tokens for the OpenCode tool.

## Repository reorganization
- **ai-kubernetes-agent/**: Contains a separate application with its own backend/services. Move this to its own separate repository to avoid credential leakage and maintain separation of concerns.

## Action items
1. [ ] Rotate all credentials in admin.conf (regenerate certificates, tokens)
2. [ ] Rotate all credentials in .env files
3. [ ] Rotate credentials in opencode.json
4. [ ] Move ai-kubernetes-agent/ to its own separate Git repository
5. [ ] Verify no secrets remain in git history (use `git filter-repo` or BFG Repo-Cleaner if needed)
6. [ ] Run `git status` to verify no secrets are staged or tracked