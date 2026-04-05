---
layout: default
title: mac-setup
---

# mac-setup

macOS backup & restore automation for a keyboard-driven, eye-friendly, minimal setup.

**Scenario**: MacBook Pro M3 Pro — clean macOS setup, backup & restore.

---

## Quick Start

### Backup (current system)

```bash
python3 mac_backup.py              # full backup
python3 mac_backup.py --dry-run    # preview only
```

### Restore (new system)

```bash
git clone https://github.com/bowang168/mac-setup.git ~/dev/mac-setup
cd ~/dev/mac-setup

python3 mac_restore.py              # interactive (recommended)
python3 mac_restore.py --yes        # skip confirmations
python3 mac_restore.py --only brew configs defaults
```

Available steps: `prereqs`, `brew`, `configs`, `omz`, `defaults`, `services`, `claude`, `typora`, `ollama`, `hidefolders`

---

## What's Included

| Directory / File | Content |
|------------------|---------|
| `mac_backup.py` | Automated backup: dotfiles, defaults, services, etc. |
| `mac_restore.py` | Automated restore: Homebrew, configs, defaults, Claude Code, etc. |
| `human_step_guide.md` | Manual steps (incl. fonts backup/restore), verification checklist, eye health tips |
| `Brewfile` | Homebrew packages and casks |
| `configs/` | Dotfiles: zshrc, gitconfig, nvim, ghostty, aerospace, starship |
| `defaults/` | macOS system preferences (plist exports) |
| `claude/` | Claude Code settings and memory |
| `services/` | Automator workflows |
| `docs/` | Reference docs (font guide, eye health, etc.) |
| `typora/` | Typora themes |
| `bin/` | Custom scripts (theme toggle, app toggle) |
| `docs/` | Reference docs (eye health guide, shortcuts, etc.) |

---

## Key Tools

**Terminal & Shell**: Ghostty, zsh + Oh My Zsh, Starship, Neovim

**CLI**: bat, eza, fd, fzf, ripgrep, lazygit, git-delta, yazi, zoxide

**Window Management**: AeroSpace (i3-style tiling)

**Keyboard**: HyperKey (CapsLock = Hyper/Esc)

**Eye Health**: f.lux, Time Out (20-20-20 rule)

**AI**: Claude Code, Ollama (local LLMs)

---

## Manual Setup Guide

Some macOS settings are protected and cannot be restored via `defaults import`. See the full manual step guide for:

- Backup & restore of sensitive files
- macOS installation on a new volume
- Post-restore verification checklist
- Eye health & display settings
- Multi-volume startup tips

**[Read the Full Manual Step Guide](step-guide)**

---

## About the Author

**Bo Wang** — Principal Technical Support Engineer, based in Auckland, New Zealand.

- [GitHub](https://github.com/bowang168)
- [LinkedIn](https://linkedin.com/in/bowang168)
- [Website](https://bowang168.github.io)

---

## Support This Project

If this setup saved you time, consider:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow?style=flat-square&logo=buy-me-a-coffee)](https://buymeacoffee.com/bowang168)
[![Sponsor](https://img.shields.io/badge/GitHub%20Sponsors-sponsor-ea4aaa?style=flat-square&logo=github-sponsors)](https://github.com/sponsors/bowang168)

---

## License

[MIT](https://github.com/bowang168/mac-setup/blob/main/LICENSE) — Bo Wang
