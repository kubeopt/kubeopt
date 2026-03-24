# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it privately:

**Email**: security@kubeopt.com

Do not open public GitHub issues for security vulnerabilities.

We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest main branch | Yes |
| Older versions | No |

## Security Design

- All API endpoints require JWT authentication (except /health)
- Cloud credentials are never stored in the application database
- License validation is enforced for paid features (plan generation, AI chat)
- Input validation on all user-facing endpoints (XSS, SQL injection, path traversal protection)
- Rate limiting per IP and per license tier
- CORS restricted to configured origins in production
