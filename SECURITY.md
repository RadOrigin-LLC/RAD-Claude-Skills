# Security Policy

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in this project, please report it responsibly using one of these methods:

### Preferred: GitHub Private Vulnerability Reporting

1. Go to the [Security tab](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/security) of this repository
2. Click **"Report a vulnerability"**
3. Fill out the form with details about the vulnerability

This creates a private advisory where we can discuss the issue and develop a fix before any public disclosure.

### Alternative: Email

If you prefer email, contact the maintainer directly at the email address listed on the [GitHub profile](https://github.com/RadOrigin-LLC).

## What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Which files or skills are affected
- Potential impact (what could an attacker do?)
- Suggested fix, if you have one

## Response Timeline

- **Acknowledgment:** Within 48 hours of your report
- **Assessment:** Within 1 week, I'll confirm whether it's a valid vulnerability
- **Fix:** Security patches are prioritized and released as soon as possible
- **Disclosure:** After the fix is released, the vulnerability will be publicly disclosed with credit to the reporter (unless you prefer anonymity)

## Scope

This security policy covers:

- All plugin code and skill definitions in this repository
- Configuration files and templates
- Installation scripts

### Out of Scope

- Vulnerabilities in Claude Code itself (report to [Anthropic](https://www.anthropic.com/responsible-disclosure))
- Vulnerabilities in third-party tools or services referenced by skills
- Issues that require physical access to a user's machine

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Yes |
| Older commits | Best-effort |

## Security Best Practices for Users

When using plugins and skills from this repository:

1. **Review before installing** — Read the skill files before adding them to your Claude Code setup
2. **Keep updated** — Pull the latest version regularly for security fixes
3. **Don't commit secrets** — Never add API keys, tokens, or credentials to skill files
4. **Report issues** — If something looks wrong, report it using the methods above

Thank you for helping keep this project and its users safe.
