# rad-1password

End-to-end coverage of the 1Password CLI (`op`) — written so Claude can use your secrets *without* you ever pasting plaintext into chat.

## What's inside

### Auto-triggered skills (model-invoked)

Loaded automatically when relevant.

| Skill | Triggers on |
|---|---|
| `1password-cli` | Router. Mention of `op`, 1Password, secret references, biometric unlock for a CLI, `OP_ACCOUNT`/`OP_SERVICE_ACCOUNT_TOKEN` |
| `op-secrets-injection` | `op inject`, `op run`, `op read`, `.env` files with `op://...`, `{{ op://... }}` templates |
| `op-item-management` | `op item` CRUD, all 20 item categories, fields, JSON templates, assignment-statement syntax |
| `op-provisioning` | `op user`, `op group`, `op vault user/group grant/revoke`, onboarding/offboarding, recovery |
| `op-ssh-keys` | SSH key generation, `?ssh-format=openssh`, 1Password SSH agent, signing git commits |
| `op-shell-plugins` | `op plugin init/run` for gh/aws/stripe/doctl/etc. with biometric auth |
| `op-service-accounts` | Service accounts, Connect server, GitHub Actions, K8s 1Password Operator, events-api |

### Slash commands

| Command | Purpose |
|---|---|
| `/op-signin` | Sign in (idempotent), report account |
| `/op-status` | Quick status: version, identity, accessible vaults |
| `/op-find <query>` | Search items by name across all accessible vaults |
| `/op-secret-template <item>` | Generate `KEY=op://...` lines for every field on an item |

## Install

```
/plugin marketplace add RadOrigin-LLC/RAD-Claude-Skills
/plugin install rad-1password@rad-claude-skills
```

## Requirements

- 1Password CLI v2.x — `op --version` (verified against v2.34.0)
- For interactive use: 1Password desktop app with **Settings > Developer > Integrate with 1Password CLI** enabled, plus biometric unlock (Touch ID / Windows Hello / system auth)
- For headless / CI: a service account token in `OP_SERVICE_ACCOUNT_TOKEN`

## Coverage notes

All 8 commands and 11 management commands documented at <https://developer.1password.com/docs/cli/reference/> are covered. `op environment` is **beta-only** and not available in stable v2.x — the skills note this and direct users to in-app management instead. Flag and example info was cross-checked against `op --help` on a v2.34.0 install rather than only against the docs site.

## License

Apache-2.0
