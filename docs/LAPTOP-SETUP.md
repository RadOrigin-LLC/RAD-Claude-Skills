# Laptop Setup Guide — Mirror of Desktop (radesjardins)

**Generated:** 2026-04-21 from live scan of desktop (Windows 11 Pro, PowerShell 7.6).
**Target:** Identical dev environment on travel laptop, conflict-free sync with desktop via GitHub.

---

## 0. Prerequisites

- Windows 10/11 on laptop
- Admin rights for installs
- Log in to laptop as same Windows user (or mirror home dir path — your desktop uses `C:\Users\RAD`; the guide assumes the laptop also uses `C:\Users\RAD` for drop-in compatibility of absolute paths in configs)

Open **PowerShell 7 as Administrator** for the install phase. Run everything from `C:\` unless noted.

---

## 1. Install Core CLIs (via winget)

Run as admin. One block, copy-paste:

```powershell
# Core
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli -e
winget install --id Microsoft.PowerShell -e
winget install --id Python.Python.3.13 -e
winget install --id Notepad++.Notepad++ -e
winget install --id Docker.DockerDesktop -e

# Node toolchain (Volta manages node + global JS CLIs on your desktop)
winget install --id Volta.Volta -e

# Editor (VS Code — optional but likely needed)
winget install --id Microsoft.VisualStudioCode -e
```

**Restart PowerShell** after the above (PATH refresh).

### Node via Volta (matches desktop exactly)

```powershell
volta install node@24.14.0
volta install npm@11.9.0
volta install pnpm@10.32.1
volta install bun
volta install wrangler
volta install @openai/codex
volta install happy-coder
volta install resend-cli
```

### Supabase CLI (you have it on desktop)

```powershell
winget install --id Supabase.CLI -e
# OR via scoop if winget fails:
# scoop install supabase
```

### Google Workspace CLI (`gws`) — manual install

You have this at `C:\gws\gws.exe` on desktop (not in winget). On laptop:

```powershell
# Download latest from https://github.com/taylorotwell/gws/releases (or wherever you got it)
# Adjust URL to the release ZIP you used. Then:
New-Item -ItemType Directory -Force -Path C:\gws
# Place gws.exe inside C:\gws\
# Add C:\gws to PATH:
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\gws", "User")
```

Restart PowerShell after PATH change.

---

## 2. Global Git Configuration

Exact copy of desktop settings:

```powershell
git config --global user.name "radesjardins"
git config --global user.email "ryan@ryandesjardins.com"
git config --global core.autocrlf true
git config --global core.editor "'C:\Program Files\Notepad++\notepad++.exe' -multiInst -nosession"
git config --global core.excludesfile "C:/Users/RAD/.gitignore_global"
git config --global pull.rebase false
git config --global fetch.prune true
git config --global init.defaultBranch main

# Git LFS (installed with Git for Windows, just needs init)
git lfs install
```

Copy your `.gitignore_global` from desktop to `C:\Users\RAD\.gitignore_global` (sync via OneDrive, USB, or just recreate it).

---

## 3. Authenticate GitHub CLI

```powershell
gh auth login
# Choose: GitHub.com → HTTPS → Yes authenticate Git → Login with web browser
# Scopes you currently have: gist, read:org, repo, workflow
gh auth status   # verify
```

---

## 4. Clone All Repos

Create the folder structure and clone. This mirrors `C:\Dev\` exactly:

```powershell
New-Item -ItemType Directory -Force -Path C:\Dev
Set-Location C:\Dev

# rad-skills-repo (plugins — needed for Coolify MCP path)
gh repo clone RadOrigin-LLC/RAD-Claude-Skills rad-skills-repo

# RadOrigin projects
New-Item -ItemType Directory -Force -Path `
  "C:\Dev\RadOrigin\APIs", `
  "C:\Dev\RadOrigin\Applications", `
  "C:\Dev\RadOrigin\Chrome Extensions", `
  "C:\Dev\RadOrigin\Web-and-Mobile-Apps", `
  "C:\Dev\RadOrigin\Websites"

gh repo clone radesjardins/pdxhomevet-api                "C:\Dev\RadOrigin\APIs\pdxhomevet-api"
gh repo clone radesjardins/phrase-cache-windows-app      "C:\Dev\RadOrigin\Applications\phrase-cache-windows-app"
gh repo clone radesjardins/super-nano-chrome-extension   "C:\Dev\RadOrigin\Chrome Extensions\super-nano"
gh repo clone radesjardins/soulcat-app                   "C:\Dev\RadOrigin\Web-and-Mobile-Apps\SoulcatApp"
gh repo clone radesjardins/wildplanner-web-app           "C:\Dev\RadOrigin\Web-and-Mobile-Apps\WildPlannerApp"
gh repo clone radesjardins/pdxhomevet-website            "C:\Dev\RadOrigin\Websites\pdxhomevet-website"
gh repo clone radesjardins/radorigin-website             "C:\Dev\RadOrigin\Websites\radorigin-website"
gh repo clone radesjardins/soulcat-website               "C:\Dev\RadOrigin\Websites\soulcat-website"
```

### Active feature branches to check out (on desktop you're on these, not `main`)

```powershell
git -C "C:\Dev\RadOrigin\Chrome Extensions\super-nano" checkout feat/phase2-visual-knowledge-base
git -C "C:\Dev\RadOrigin\Web-and-Mobile-Apps\SoulcatApp" checkout phase-3/m1-ai-foundation
```

### ⚠️ `ryandesjardins-website` is NOT on GitHub

Your desktop copy at `C:\Dev\RadOrigin\Websites\ryandesjardins-website` has no `origin` remote. **Before you travel**, push it up so the laptop can pull it. From desktop:

```powershell
Set-Location "C:\Dev\RadOrigin\Websites\ryandesjardins-website"
gh repo create radesjardins/ryandesjardins-website --private --source=. --remote=origin --push
```

Then on laptop: `gh repo clone radesjardins/ryandesjardins-website "C:\Dev\RadOrigin\Websites\ryandesjardins-website"`

### Local-only files you may want (NOT in git)

These live under `C:\Dev\` on desktop and aren't tracked: `CLAUDE.md`, `HANDOFF.md`, `IDEAS.md`, the entire `plans/` folder. Copy via OneDrive, Dropbox, or a private gist. Suggestion: put them in a private GitHub repo (`radesjardins/dev-notes`) so they sync like everything else.

---

## 5. Install Claude Code

```powershell
# Via npm (Volta will manage it)
npm install -g @anthropic-ai/claude-code

# OR via winget if you prefer:
# winget install --id Anthropic.ClaudeCode -e

claude --version   # confirm
claude login       # web auth — use the same Anthropic account as desktop
```

### Add plugin marketplaces

```powershell
claude
# inside the Claude Code TUI:
/plugin marketplace add anthropics/claude-plugins-official
/plugin marketplace add RadOrigin-LLC/RAD-Claude-Skills
```

### Enable plugins (matches your desktop enabled list)

Inside Claude Code, run `/plugin` and enable each. Or edit `C:\Users\RAD\.claude\settings.json` directly — easier to just copy the `enabledPlugins` block from your desktop. Currently 22 plugins (7 official + 15 rad-claude-skills):

**From `claude-plugins-official`:** `frontend-design`, `skill-creator`, `claude-code-setup`, `plugin-dev`, `microsoft-docs`, `remember`, `mcp-server-dev`

**From `rad-claude-skills`:** `rad-a11y`, `rad-1password`, `rad-brainstormer`, `rad-chrome-extension`, `rad-code-review`, `rad-context-prompter`, `rad-coolify-orchestrator`, `rad-explain`, `rad-gws-core`, `rad-para-second-brain`, `rad-planner`, `rad-seo-optimizer`, `rad-session`, `rad-supabase`

> Archived plugins (`rad-astro`, `rad-fastify`, `rad-google-workspace`, `rad-nextjs`, `rad-react`, `rad-stack-guide`, `rad-stripe-fastify-webhooks`, `rad-typescript`, `rad-zod`) are preserved under [`archive/`](../archive/) but are no longer in the marketplace. Remove them from your laptop's `enabledPlugins` if they were there from a prior install.

Fastest path — copy `C:\Users\RAD\.claude\settings.json` from desktop to laptop after Claude Code is installed. Also copy `C:\Users\RAD\.gitignore_global` if you have one.

---

## 6. Add MCP Servers (user scope — persists across projects)

Your desktop has three user-scope MCPs. Run these in any shell:

```powershell
# desktop-commander (filesystem/process control)
claude mcp add desktop-commander --scope user -- cmd /c npx -y @wonderwhy-er/desktop-commander

# coolify (your self-hosted PaaS — requires the rad-skills-repo cloned in step 4)
claude mcp add coolify --scope user `
  --env COOLIFY_URL=https://coolify.radesjardins.cloud `
  --env COOLIFY_API_TOKEN=<YOUR_COOLIFY_TOKEN> `
  -- node C:/Dev/rad-skills-repo/packages/coolify-mcp/index.js

# supabase (HTTP — OAuth on first use)
claude mcp add supabase --transport http --scope user https://mcp.supabase.com/mcp
```

**Coolify token:** read your current token from the desktop's `C:\Users\RAD\.claude.json` (search for `COOLIFY_API_TOKEN`) and paste on laptop, OR rotate in the Coolify dashboard and update both machines. Never commit this to git.

**Plugin-provided MCPs (automatic, no setup needed):**
- `plugin:microsoft-docs:microsoft-learn` — enabled when the `microsoft-docs` plugin is on
- `plugin:rad-coolify-orchestrator:coolify` — enabled when the `rad-coolify-orchestrator` plugin is on

**Claude.ai account-level connectors (Gmail, Google Calendar, Google Drive, Stripe, TickTick, Context7, Fireflies):** these auto-follow your Anthropic account. Once you `claude login` on the laptop they'll appear in `claude mcp list`. You may need to re-authorize Google Drive (it was showing "Needs authentication" on your desktop too).

### Verify everything

```powershell
claude mcp list
```

Should show ~12 servers, all ✓ except maybe Google Drive needing auth.

### Note on desktop-commander

On your current desktop it shows `✗ Failed to connect`. If you don't actually use it, skip the `claude mcp add desktop-commander` line and remove it from desktop too with `claude mcp remove desktop-commander`.

---

## 7. Claude Desktop App (optional)

You don't have `claude_desktop_config.json` on the desktop — so you're not using the Claude desktop app's MCPs. If you later install it on the laptop, the config file lives at `%APPDATA%\Claude\claude_desktop_config.json` and uses the same JSON shape as the `mcpServers` block in `.claude.json`.

---

## 8. Daily Sync Workflow (the part that prevents conflicts)

**Golden rule:** treat GitHub as the source of truth. Never have both machines editing the same branch without pushing first.

### End of session on laptop (before heading home)

```powershell
# From each repo you touched:
git status                        # see what changed
git add -A
git commit -m "wip: <description>"
git push
# If on a feature branch that doesn't exist on remote yet:
git push -u origin <branch-name>
```

Quick "push everything" helper — drop this into your PowerShell `$PROFILE`:

```powershell
function Sync-AllRepos {
    param([string]$Root = "C:\Dev")
    Get-ChildItem -Path $Root -Recurse -Directory -Filter ".git" -Force -Depth 4 |
      ForEach-Object {
        $repo = $_.Parent.FullName
        Write-Host "`n=== $repo ===" -ForegroundColor Cyan
        Push-Location $repo
        git status -s
        Pop-Location
      }
}
```

Run `Sync-AllRepos` to scan every repo for uncommitted changes before closing the lid.

### Start of session on desktop (when you get home)

```powershell
# For each repo you worked on:
Set-Location C:\Dev\<repo>
git fetch --all --prune
git status                        # check local vs remote
git pull                          # or git pull --ff-only to reject non-FF
```

If the desktop has uncommitted local changes from a prior session that you forgot to push — **stash first**:

```powershell
git stash push -m "desktop-local-$(Get-Date -Format yyyyMMdd)"
git pull
git stash pop                     # reapply; resolve conflicts if any
```

### Avoid the classic conflict: the "I edited both" trap

- Only edit on one machine at a time
- Always `git push` before switching machines
- Always `git fetch && git status` when starting on the other machine — if it says "behind origin by N commits", pull before editing
- If you forgot and there are conflicting edits on both sides, `git pull` will tell you. Resolve normally (edit conflicted files, `git add`, `git commit`).

### Feature branches for anything >1 hour of work

```powershell
git checkout -b feat/what-im-doing
# work, commit often, push often:
git push -u origin feat/what-im-doing
```

When done on that machine and you want to switch, `git push`, then on the other machine `git fetch && git checkout feat/what-im-doing && git pull`.

### The `rad-session` plugin helps

You already have it enabled. At session end run `/wrapup` — writes `HANDOFF.md` + `.claude/session-log.md`, auto-commits both, and prompts to push (`y` to push to origin). At session start on the other machine run `/startup` — it fetches origin, lists incoming session commits, and prompts to pull before reading anything. The briefing leads with `Continuing from <other-host>` so you immediately see you're on a cross-machine handoff.

Flag overrides for this workflow:
- `/wrapup --push` (no prompt, push immediately) and `/wrapup --no-push` (commit locally only)
- `/startup --auto-pull` (no prompt, fast-forward silently) and `/startup --no-pull` (skip sync, read local with stale warning)

Cross-machine sync requires the project to have a git remote and `HANDOFF.md` + `.claude/session-log.md` to be tracked — `/init` Step 7.5 handles the gitignore exception automatically. No `dev-notes` repo workaround needed.

---

## 9. Post-setup Verification Checklist

Run these on the laptop after everything above:

```powershell
git --version                                 # 2.53+
gh auth status                                # logged in as radesjardins
node --version                                # v24.14.0
volta list                                    # shows pnpm, bun, wrangler, etc.
claude --version                              # 2.1.116+
claude mcp list                               # shows ~12 servers, mostly ✓
Set-Location C:\Dev\rad-skills-repo
git status                                    # clean, on main
```

Then open Claude Code in `C:\Dev\rad-skills-repo`, type `/plugin` — should list your 30 plugins all enabled.

---

## 10. Things That Need Manual Attention

1. **Push `ryandesjardins-website` to GitHub from desktop first** (§4 above) — it has no remote.
2. **Copy `.gitignore_global`** from desktop `C:\Users\RAD\.gitignore_global` to laptop.
3. **Copy `.claude\settings.json`** from desktop to laptop after Claude Code is installed (shortcut for plugin enable list).
4. **Copy the Coolify API token** — read it from desktop `.claude.json` or rotate in Coolify UI.
5. **Local-only notes** (`CLAUDE.md`, `HANDOFF.md`, `IDEAS.md`, `plans/`) — put in a private `dev-notes` repo so they sync.
6. **Fix or remove `desktop-commander` MCP** — currently failing on desktop; decide if you need it.
7. **Re-auth Google Drive MCP** — shows "Needs authentication" on desktop and will on laptop.
8. **VS Code settings + extensions** — use the built-in Settings Sync (sign in with GitHub) to mirror automatically.
9. **SSH keys** — you use HTTPS + gh auth, so SSH isn't required. If you ever switch to SSH, copy `~/.ssh/` via encrypted USB.
10. **Shell profile** — copy your PowerShell `$PROFILE` (`$PROFILE` points to the path) if you have custom aliases/functions.
