#!/usr/bin/env python3
"""
mac_backup.py - macOS 个人设置备份 & dotfiles 部署

用法:
    python3 mac_backup.py                  # 备份 (system → repo)
    python3 mac_backup.py --dry-run        # 预览备份
    python3 mac_backup.py link             # symlink 部署 (repo → system, macOS + Linux)
    python3 mac_backup.py link --dry-run   # 预览部署

备份目标目录就是本脚本所在的 mac-setup/ 仓库。
敏感文件 (.ssh, .bashrc_private, Personal_AI_Brain) 不会被备份。
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 路径常量 ──────────────────────────────────────────────────────────

HOME = Path.home()
REPO = Path(__file__).resolve().parent  # mac-setup/ 仓库根目录
IS_MACOS = platform.system() == "Darwin"

# ── 颜色输出 ──────────────────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[OK]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[SKIP]{RESET} {msg}")


def error(msg):
    print(f"{RED}[ERR]{RESET} {msg}")


def section(msg):
    print(f"\n{BOLD}{CYAN}{'─' * 60}")
    print(f"  {msg}")
    print(f"{'─' * 60}{RESET}")


# ── 工具函数 ──────────────────────────────────────────────────────────


def run(cmd, **kwargs):
    """运行 shell 命令，返回 (returncode, stdout)"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, **kwargs
    )
    return result.returncode, result.stdout.strip()


def copy_file(src, dst, dry_run=False):
    """复制单个文件，自动创建目标目录"""
    src = Path(src).expanduser()
    dst = Path(dst)
    if not src.exists():
        warn(f"源文件不存在: {src}")
        return False
    if dry_run:
        info(f"[DRY-RUN] {src} -> {dst}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    info(f"{src} -> {dst}")
    return True


def copy_dir(src, dst, dry_run=False):
    """复制整个目录"""
    src = Path(src).expanduser()
    dst = Path(dst)
    if not src.exists():
        warn(f"源目录不存在: {src}")
        return False
    if dry_run:
        count = sum(1 for _ in src.rglob("*") if _.is_file())
        info(f"[DRY-RUN] {src}/ ({count} files) -> {dst}/")
        return True
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    count = sum(1 for _ in dst.rglob("*") if _.is_file())
    info(f"{src}/ ({count} files) -> {dst}/")
    return True


def defaults_export(domain, dst, dry_run=False):
    """导出 macOS defaults 偏好到 plist 文件"""
    dst = Path(dst)
    if dry_run:
        info(f"[DRY-RUN] defaults export {domain} -> {dst}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    rc, _ = run(f'defaults export "{domain}" "{dst}"')
    if rc == 0:
        info(f"defaults export {domain} -> {dst}")
        return True
    else:
        warn(f"defaults export 失败: {domain}")
        return False


# ══════════════════════════════════════════════════════════════════════
#  BACKUP: system → repo
# ══════════════════════════════════════════════════════════════════════


def backup_homebrew(dry_run=False):
    section("1/11 Homebrew (Brewfile)")
    dst = REPO / "Brewfile"
    if dry_run:
        info("[DRY-RUN] brew bundle dump -> Brewfile")
        return
    rc, _ = run(f'brew bundle dump --describe --force --file="{dst}"')
    if rc == 0:
        lines = dst.read_text().splitlines()
        taps = sum(1 for l in lines if l.startswith("tap"))
        brews = sum(1 for l in lines if l.startswith("brew"))
        casks = sum(1 for l in lines if l.startswith("cask"))
        info(f"Brewfile: {taps} taps, {brews} formulas, {casks} casks")
    else:
        error("brew bundle dump 失败")


def backup_fonts(dry_run=False):
    section("2/11 Fonts")
    src = HOME / "Library" / "Fonts"
    dst = REPO / "fonts"
    if not src.exists():
        warn("~/Library/Fonts/ 不存在")
        return
    if dry_run:
        fonts = [f for f in src.rglob("*") if f.is_file() and not f.name.startswith(".")]
        info(f"[DRY-RUN] {len(fonts)} font files")
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in sorted(src.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            rel = f.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            count += 1
    info(f"已备份 {count} 个字体文件")


def backup_configs(dry_run=False):
    section("3/11 Config Files")

    single_files = {
        HOME / ".zshrc": REPO / "configs" / ".zshrc",
        HOME / ".shell_common": REPO / "configs" / ".shell_common",
        HOME / ".gitconfig": REPO / "configs" / ".gitconfig",
        HOME / ".theme_mode": REPO / "configs" / ".theme_mode",
        HOME / ".aerospace.toml": REPO / "configs" / ".aerospace.toml",
        HOME / ".config" / "starship.toml": REPO / "configs" / "starship.toml",
        HOME / ".bash_profile": REPO / "configs" / ".bash_profile",
        HOME / ".bashrc": REPO / "configs" / ".bashrc",
        HOME / ".zprofile": REPO / "configs" / ".zprofile",
        HOME / ".zshenv": REPO / "configs" / ".zshenv",
        HOME / ".hushlogin": REPO / "configs" / ".hushlogin",
    }
    for src, dst in single_files.items():
        copy_file(src, dst, dry_run)

    dir_configs = {
        HOME / ".config" / "ghostty": REPO / "configs" / "ghostty",
        HOME / ".config" / "nvim": REPO / "configs" / "nvim",
        HOME / ".zsh": REPO / "configs" / "zsh",
    }
    for src, dst in dir_configs.items():
        copy_dir(src, dst, dry_run)

    bin_scripts = {
        HOME / ".local" / "bin" / "theme": REPO / "bin" / "theme",
        HOME / ".local" / "bin" / "toggle_app": REPO / "bin" / "toggle_app",
    }
    for src, dst in bin_scripts.items():
        copy_file(src, dst, dry_run)


def backup_defaults(dry_run=False):
    section("4/11 macOS Defaults (系统偏好)")

    domains = {
        "com.apple.dock": "dock",
        "com.apple.finder": "finder",
        "com.apple.symbolichotkeys": "symbolichotkeys",
        "NSGlobalDomain": "NSGlobalDomain",
        "com.apple.universalaccess": "universalaccess",
        "com.apple.AppleMultitouchTrackpad": "trackpad",
        "com.apple.driver.AppleBluetoothMultitouch.trackpad": "trackpad_bt",
        "org.herf.Flux": "org.herf.Flux",
        "com.knollsoft.Hyperkey": "com.knollsoft.Hyperkey",
        "com.apple.TextEdit": "com.apple.TextEdit",
        "abnerworks.Typora": "abnerworks.Typora",
        "bobko.aerospace": "bobko.aerospace",
        "com.anthropic.claudefordesktop": "com.anthropic.claudefordesktop",
        "com.apple.screencapture": "screencapture",
        "com.apple.desktopservices": "desktopservices",
    }

    dst_dir = REPO / "defaults"
    for domain, filename in domains.items():
        defaults_export(domain, dst_dir / f"{filename}.plist", dry_run)

    if not dry_run:
        rc, stdout = run("defaults find NSUserKeyEquivalents 2>/dev/null")
        if rc == 0 and stdout:
            out = dst_dir / "NSUserKeyEquivalents_all.txt"
            out.write_text(stdout)
            info(f"自定义键盘快捷键 -> {out}")


def backup_services(dry_run=False):
    section("5/11 Services (Automator Workflows)")
    src = HOME / "Library" / "Services"
    dst = REPO / "services"
    if not src.exists():
        warn("~/Library/Services/ 不存在")
        return
    if dry_run:
        items = [f for f in src.iterdir() if not f.name.startswith(".")]
        info(f"[DRY-RUN] {len(items)} services")
        return
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in sorted(src.iterdir()):
        if item.name.startswith("."):
            continue
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
        count += 1
    info(f"已备份 {count} 个 Services")


def backup_claude_code(dry_run=False):
    section("6/11 Claude Code")

    claude_dir = HOME / ".claude"
    dst_dir = REPO / "claude"

    global_files = ["CLAUDE.md", "settings.json"]
    for f in global_files:
        copy_file(claude_dir / f, dst_dir / f, dry_run)

    projects_dir = claude_dir / "projects"
    if not projects_dir.exists():
        warn("~/.claude/projects/ 不存在")
        return

    memory_count = 0
    for project in sorted(projects_dir.iterdir()):
        if not project.is_dir():
            continue
        memory_dir = project / "memory"
        memory_md = project / "MEMORY.md"
        claude_md = project / "CLAUDE.md"

        has_memory = memory_dir.exists() or memory_md.exists() or claude_md.exists()
        if not has_memory:
            continue

        project_dst = dst_dir / "projects" / project.name
        if memory_dir.exists():
            copy_dir(memory_dir, project_dst / "memory", dry_run)
            memory_count += 1
        if memory_md.exists():
            copy_file(memory_md, project_dst / "MEMORY.md", dry_run)
        if claude_md.exists():
            copy_file(claude_md, project_dst / "CLAUDE.md", dry_run)

    if not dry_run:
        info(f"共备份 {memory_count} 个项目的 memory 数据")


def backup_typora_themes(dry_run=False):
    section("7/11 Typora Themes")
    src = HOME / "Library" / "Application Support" / "abnerworks.Typora" / "themes"
    dst = REPO / "typora" / "themes"
    copy_dir(src, dst, dry_run)


def backup_shortcuts(dry_run=False):
    section("8/11 Shortcuts (快捷指令列表)")
    dst = REPO / "shortcuts_list.txt"
    if dry_run:
        info("[DRY-RUN] shortcuts list -> shortcuts_list.txt")
        return
    rc, stdout = run("shortcuts list 2>/dev/null")
    if rc == 0 and stdout:
        dst.write_text(stdout)
        count = len(stdout.splitlines())
        info(f"已导出 {count} 个快捷指令名称 -> {dst}")
    else:
        warn("shortcuts 命令不可用或无快捷指令")


def backup_ollama_models(dry_run=False):
    section("9/11 Ollama 模型列表")
    dst = REPO / "ollama_models.txt"
    if dry_run:
        info("[DRY-RUN] ollama list -> ollama_models.txt")
        return
    rc, stdout = run("ollama list 2>/dev/null")
    if rc == 0 and stdout:
        dst.write_text(stdout)
        count = len(stdout.splitlines()) - 1
        info(f"已记录 {count} 个模型 -> {dst}")
    else:
        warn("ollama 未运行或无模型")


def backup_oh_my_zsh_custom(dry_run=False):
    section("10/11 Oh My Zsh Custom Plugins/Themes")
    omz_custom = HOME / ".oh-my-zsh" / "custom"
    dst = REPO / "configs" / "omz-custom"

    if not omz_custom.exists():
        warn("~/.oh-my-zsh/custom/ 不存在")
        return

    for subdir_name in ["plugins", "themes"]:
        src_sub = omz_custom / subdir_name
        if not src_sub.exists():
            continue
        for item in sorted(src_sub.iterdir()):
            if item.name.startswith(".") or item.name.startswith("example"):
                continue
            if (item / ".git").exists():
                rc, url = run(f'git -C "{item}" remote get-url origin 2>/dev/null')
                if rc == 0 and url:
                    if dry_run:
                        info(f"[DRY-RUN] 记录插件 git URL: {item.name} -> {url}")
                        continue
                    list_file = dst / f"{subdir_name}.txt"
                    list_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(list_file, "a") as f:
                        f.write(f"{item.name}\t{url}\n")
                    info(f"记录插件 git URL: {item.name} -> {url}")
            else:
                copy_dir(item, dst / subdir_name / item.name, dry_run)



def cmd_backup(args):
    """执行备份: system → repo"""
    print(f"\n{BOLD}{'=' * 60}")
    print(f"  macOS Backup: system → repo")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  备份目录: {REPO}")
    if args.dry_run:
        print(f"  {YELLOW}*** DRY-RUN 模式 ***{RESET}")
    print(f"{'=' * 60}{RESET}\n")

    rc, _ = run("which brew")
    if rc != 0:
        error("Homebrew 未安装")
        sys.exit(1)

    backup_homebrew(args.dry_run)
    backup_fonts(args.dry_run)
    backup_configs(args.dry_run)
    backup_defaults(args.dry_run)
    backup_services(args.dry_run)
    backup_claude_code(args.dry_run)
    backup_typora_themes(args.dry_run)
    backup_shortcuts(args.dry_run)
    backup_ollama_models(args.dry_run)
    backup_oh_my_zsh_custom(args.dry_run)

    if not args.dry_run:
        ts = REPO / ".last_backup"
        ts.write_text(datetime.now().isoformat())

    print(f"\n{BOLD}{GREEN}{'=' * 60}")
    print(f"  备份完成!")
    print(f"{'=' * 60}{RESET}")
    print(f"\n{YELLOW}提醒: 以下需手动备份:{RESET}")
    print(f"  - ~/.ssh/              (SSH 密钥)")
    print(f"  - ~/.bashrc_private    (API Keys)")
    print(f"  - ~/d/Personal_AI_Brain/")
    print(f"\n下一步: cd {REPO} && git add -A && git commit -m 'backup'")


# ══════════════════════════════════════════════════════════════════════
#  LINK: repo → system (symlink 部署, macOS + Linux)
# ══════════════════════════════════════════════════════════════════════


BACKUP_DIR = None  # 延迟初始化


def _get_backup_dir():
    global BACKUP_DIR
    if BACKUP_DIR is None:
        BACKUP_DIR = HOME / ".dotfiles_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    return BACKUP_DIR


def symlink(src, dst, dry_run=False):
    """创建 symlink，已有的普通文件会备份到 ~/.dotfiles_backup/"""
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        warn(f"源不存在: {src}")
        return False

    # 已是正确的 symlink
    if dst.is_symlink() and dst.resolve() == src.resolve():
        info(f"ok  {dst}")
        return True

    if dry_run:
        info(f"[DRY-RUN] ln -sf {src} -> {dst}")
        return True

    # 备份已有的普通文件
    if dst.exists() and not dst.is_symlink():
        backup_dir = _get_backup_dir()
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(backup_dir / dst.name))
        info(f"bak {dst} -> {backup_dir}/{dst.name}")

    # 删除旧 symlink
    if dst.is_symlink():
        dst.unlink()

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src)
    info(f"ln  {dst} -> {src}")
    return True


def cmd_link(args):
    """Symlink 部署: repo → system (macOS + Linux)"""
    print(f"\n{BOLD}{'=' * 60}")
    print(f"  Dotfiles Link: repo → system")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  源: {REPO}")
    if args.dry_run:
        print(f"  {YELLOW}*** DRY-RUN 模式 ***{RESET}")
    print(f"{'=' * 60}{RESET}")

    configs = REPO / "configs"
    dry = args.dry_run

    # ── Shell config ──
    section("Shell Config")
    shell_files = [
        ".bash_profile", ".bashrc", ".shell_common",
        ".zprofile", ".zshenv", ".zshrc",
        ".hushlogin", ".gitconfig",
    ]
    for f in shell_files:
        symlink(configs / f, HOME / f, dry)

    # ── AeroSpace (macOS only) ──
    if IS_MACOS and (configs / ".aerospace.toml").exists():
        section("AeroSpace")
        symlink(configs / ".aerospace.toml", HOME / ".aerospace.toml", dry)

    # ── Scripts ──
    section("Scripts (bin/)")
    for script in sorted((REPO / "bin").iterdir()):
        if script.is_file():
            symlink(script, HOME / ".local" / "bin" / script.name, dry)

    # ── Starship ──
    section("Starship")
    symlink(configs / "starship.toml", HOME / ".config" / "starship.toml", dry)

    # ── Zsh themes (catppuccin) ──
    section("Zsh Themes")
    for f in ["mocha.zsh", "latte.zsh"]:
        symlink(configs / "zsh" / "catppuccin" / f,
                HOME / ".zsh" / "catppuccin" / f, dry)

    # ── Neovim ──
    section("Neovim")
    for f in ["init.lua", "lazy-lock.json"]:
        src = configs / "nvim" / f
        if src.exists():
            symlink(src, HOME / ".config" / "nvim" / f, dry)

    # ── Ghostty (macOS only) ──
    if IS_MACOS and (configs / "ghostty" / "config").exists():
        section("Ghostty")
        symlink(configs / "ghostty" / "config",
                HOME / ".config" / "ghostty" / "config", dry)

    # ── Theme mode ──
    theme_file = HOME / ".theme_mode"
    if not theme_file.exists():
        if not dry:
            theme_file.write_text("dark")
        info(f"new ~/.theme_mode (dark)")

    # ── Secrets template ──
    private = HOME / ".bashrc_private"
    example = configs / ".bashrc_private.example"
    if not private.exists() and example.exists():
        if not dry:
            shutil.copy2(example, private)
            private.chmod(0o600)
        info("new ~/.bashrc_private (模板 — 请填入真实 API keys)")
    elif private.exists():
        info("~/.bashrc_private 已存在，跳过模板")

    # ── GNOME Terminal (Linux only) ──
    if not IS_MACOS:
        dconf_file = REPO / "docs" / "gnome-terminal-profiles.dconf"
        rc, _ = run("which dconf")
        if rc == 0 and dconf_file.exists():
            section("GNOME Terminal")
            if dry:
                info("[DRY-RUN] dconf load terminal profiles")
            else:
                rc, _ = run(f'dconf load /org/gnome/terminal/legacy/profiles:/ < "{dconf_file}"')
                if rc == 0:
                    info("loaded terminal profiles")

    # ── Summary ──
    backup_dir = _get_backup_dir()
    print(f"\n{BOLD}{GREEN}{'=' * 60}")
    print(f"  Link 完成!")
    print(f"{'=' * 60}{RESET}")
    if backup_dir.exists():
        print(f"\n  旧文件备份在: {backup_dir}")
    print(f"\n{YELLOW}下一步:{RESET}")
    if IS_MACOS:
        print(f"  1. 完整 macOS 恢复: python3 mac_restore.py")
        print(f"  2. 编辑 ~/.bashrc_private 填入 API keys")
        print(f"  3. 新开终端或执行: exec zsh")
    else:
        print(f"  1. 编辑 ~/.bashrc_private 填入 API keys")
        print(f"  2. 新开终端或执行: exec zsh")


# ══════════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="macOS 设置备份 & dotfiles 部署",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 mac_backup.py              备份当前系统设置到仓库
  python3 mac_backup.py --dry-run    预览备份内容
  python3 mac_backup.py link         symlink 部署 dotfiles
  python3 mac_backup.py link --dry-run
""",
    )
    parser.add_argument(
        "command", nargs="?", default="backup",
        choices=["backup", "link"],
        help="backup (默认): system → repo | link: repo → system via symlinks",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="预览操作，不实际执行"
    )
    args = parser.parse_args()

    if args.command == "link":
        cmd_link(args)
    else:
        cmd_backup(args)


if __name__ == "__main__":
    main()
