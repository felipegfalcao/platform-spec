# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| latest (main) | ✅ |
| < 0.1.0 | ❌ |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in Platform Spec, please report it via [GitHub Private Vulnerability Reporting](https://github.com/felipegfalcao/platform-spec/security/advisories/new) or by emailing <felipegfalcao.dev@gmail.com>.

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 72 hours. We will coordinate a fix and disclosure timeline with you.

## Scope

Platform Spec is a framework of templates, schemas, and documentation. The primary security concern is:

- **Template injection**: if a template or context file includes content that could cause an AI agent to execute unintended commands
- **CLI command injection**: if `pspec` CLI commands pass unsanitized user input to shell commands
- **Sensitive data in examples**: if examples accidentally include real credentials, endpoints, or internal information

Out of scope: vulnerabilities in dependencies that do not affect Platform Spec's security posture directly (report those to the respective upstream projects).
