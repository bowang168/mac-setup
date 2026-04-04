# mac-setup

macOS backup & restore automation for a keyboard-driven, eye-friendly, minimal setup.

**Scenario**: MacBook Pro M3 Pro — primary volume + clean macOS setup, backup & restore.

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

Available steps: `prereqs`, `brew`, `fonts`, `configs`, `omz`, `defaults`, `services`, `claude`, `typora`, `ollama`, `hidefolders`

## What's Included

| Directory / File | Content |
|------------------|---------|
| `mac_backup.py` | Automated backup: dotfiles, defaults, fonts, services, etc. |
| `mac_restore.py` | Automated restore: Homebrew, configs, defaults, Claude Code, etc. |
| `mac_backup_restore_steps.md` | Manual steps, verification checklist, eye health tips |
| `Brewfile` | Homebrew packages and casks |
| `configs/` | Dotfiles: zshrc, gitconfig, nvim, ghostty, aerospace, starship |
| `defaults/` | macOS system preferences (plist exports) |
| `claude/` | Claude Code settings and memory |
| `services/` | Automator workflows |
| `fonts/` | Custom fonts (recursive backup) |
| `typora/` | Typora themes |
| `bin/` | Custom scripts (theme toggle, app toggle) |
| `docs/` | Reference docs (eye health guide, shortcuts, etc.) |

## Key Tools

**Terminal & Shell**: Ghostty, zsh + Oh My Zsh, Starship, Neovim

**CLI**: bat, eza, fd, fzf, ripgrep, lazygit, git-delta, yazi, zoxide

**Window Management**: AeroSpace (i3-style tiling)

**Keyboard**: HyperKey (CapsLock = Hyper/Esc)

**Eye Health**: f.lux, Time Out (20-20-20 rule)

**AI**: Claude Code, Ollama (local LLMs)

## What Requires Manual Setup

Some macOS settings are protected and cannot be restored via `defaults import`:

- **Accessibility**: Reduce transparency, Reduce motion, three-finger drag
- **Privacy & Security**: Accessibility/Full Disk Access permissions for apps
- **Other**: Night Shift, default browser, Touch ID, Finder extensions for Shortcuts

See `mac_backup_restore_steps.md` for the full checklist.

## License

MIT - Bo Wang
