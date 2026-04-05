#!/usr/bin/env python3
"""
mac_restore.py - macOS 个人设置一键恢复脚本

用法:
    python3 mac_restore.py              # 执行恢复 (交互确认每步)
    python3 mac_restore.py --dry-run    # 预览恢复内容，不实际操作
    python3 mac_restore.py --yes        # 跳过确认，全部执行
    python3 mac_restore.py --only brew  # 只执行指定步骤
    python3 mac_restore.py --pull-ollama-models  # 只拉取 Ollama 模型

前置条件:
    1. 已从目标卷启动新 macOS
    2. 本仓库已 clone 到新系统
    脚本会自动检测并安装: Xcode CLT, Homebrew, Oh My Zsh, Claude Code
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 路径常量 ──────────────────────────────────────────────────────────

HOME = Path.home()
REPO = Path(__file__).resolve().parent

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
    """运行 shell 命令"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, **kwargs
    )
    return result.returncode, result.stdout.strip()


def run_visible(cmd):
    """运行命令并实时显示输出"""
    return subprocess.run(cmd, shell=True).returncode


def has_cmd(name):
    """检查命令是否在 PATH 中"""
    rc, _ = run(f"which {name}")
    return rc == 0


def ensure_brew_path():
    """确保 Homebrew 在当前进程的 PATH 中 (Apple Silicon)"""
    brew_bin = "/opt/homebrew/bin"
    if os.path.isdir(brew_bin) and brew_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{brew_bin}:{os.environ.get('PATH', '')}"


def confirm(msg, auto_yes=False):
    """确认是否继续"""
    if auto_yes:
        return True
    answer = input(f"\n{YELLOW}[?]{RESET} {msg} [Y/n] ").strip().lower()
    return answer in ("", "y", "yes")


def copy_file(src, dst, dry_run=False):
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        warn(f"备份文件不存在: {src}")
        return False
    if dry_run:
        info(f"[DRY-RUN] {src} -> {dst}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    info(f"{src} -> {dst}")
    return True


def copy_dir(src, dst, dry_run=False):
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        warn(f"备份目录不存在: {src}")
        return False
    if dry_run:
        count = sum(1 for _ in src.rglob("*") if _.is_file())
        info(f"[DRY-RUN] {src}/ ({count} files) -> {dst}/")
        return True
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    count = sum(1 for _ in dst.rglob("*") if _.is_file())
    info(f"恢复 {count} 个文件 -> {dst}/")
    return True


def defaults_import(domain, src, dry_run=False):
    src = Path(src)
    if not src.exists():
        warn(f"plist 不存在: {src}")
        return False
    if dry_run:
        info(f"[DRY-RUN] defaults import {domain} <- {src}")
        return True
    rc, _ = run(f'defaults import "{domain}" "{src}"')
    if rc == 0:
        info(f"defaults import {domain} <- {src}")
        return True
    else:
        error(f"defaults import 失败: {domain}")
        return False


# ── 恢复任务 ──────────────────────────────────────────────────────────

STEPS = {}


def step(name, label):
    """注册恢复步骤的装饰器"""
    def decorator(func):
        STEPS[name] = (label, func)
        return func
    return decorator


# ── 0. Prerequisites ─────────────────────────────────────────────────


@step("prereqs", "0/9 Prerequisites (Xcode CLT + Homebrew)")
def restore_prereqs(dry_run=False, **_):
    section("0/9 Prerequisites")

    # ── Xcode Command Line Tools ──
    rc, _ = run("xcode-select -p")
    if rc != 0:
        info("安装 Xcode Command Line Tools...")
        if dry_run:
            info("[DRY-RUN] xcode-select --install")
        else:
            rc = run_visible("xcode-select --install")
            if rc != 0:
                error("Xcode CLT 安装失败，请手动运行: xcode-select --install")
                return
            info("Xcode CLT 安装完成 (如弹出 GUI 对话框，请先完成安装再继续)")
    else:
        info("Xcode Command Line Tools 已安装")

    # ── Homebrew ──
    if has_cmd("brew"):
        info("Homebrew 已安装")
    else:
        info("安装 Homebrew...")
        if dry_run:
            info('[DRY-RUN] /bin/bash -c "$(curl -fsSL ...install.sh)"')
        else:
            rc = run_visible(
                '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            )
            if rc != 0:
                error("Homebrew 安装失败")
                return
            ensure_brew_path()
            info("Homebrew 安装完成")

    ensure_brew_path()

    # ── 验证 brew 可用 ──
    if not dry_run and not has_cmd("brew"):
        error("brew 不在 PATH 中，请手动执行: eval \"$(/opt/homebrew/bin/brew shellenv)\"")
        return

    # ── git (brew 版本，覆盖系统自带) ──
    _, git_path = run("which git")
    if "/opt/homebrew" not in (git_path or ""):
        info("安装 brew git...")
        if not dry_run:
            run_visible("brew install git")
    else:
        info("git (brew) 已安装")

    # ── GitHub CLI ──
    if has_cmd("gh"):
        info("GitHub CLI 已安装")
    else:
        info("安装 GitHub CLI...")
        if not dry_run:
            run_visible("brew install gh")

    # ── 检查 gh auth ──
    if not dry_run:
        rc, _ = run("gh auth status 2>/dev/null")
        if rc != 0:
            warn("GitHub CLI 未登录，请稍后运行: gh auth login")


# ── 1. Homebrew Bundle ───────────────────────────────────────────────


@step("brew", "1/9 Homebrew Bundle (安装工具和应用)")
def restore_homebrew(dry_run=False, **_):
    section("1/9 Homebrew Bundle")

    ensure_brew_path()

    if not has_cmd("brew"):
        error("Homebrew 未安装，请先运行 prereqs 步骤")
        return

    brewfile = REPO / "Brewfile"
    if not brewfile.exists():
        warn("Brewfile 不存在")
        return

    lines = brewfile.read_text().splitlines()
    taps = sum(1 for l in lines if l.startswith("tap"))
    brews = sum(1 for l in lines if l.startswith("brew"))
    casks = sum(1 for l in lines if l.startswith("cask"))
    info(f"Brewfile: {taps} taps, {brews} formulas, {casks} casks")

    if dry_run:
        info("[DRY-RUN] brew bundle install")
        return

    info("执行 brew bundle install (可能需要较长时间)...")
    rc = run_visible(f'brew bundle install --file="{brewfile}"')
    if rc == 0:
        info("Homebrew 包恢复完成")
    else:
        warn("部分包可能安装失败，请检查输出")


# ── 2. Config Files ──────────────────────────────────────────────────


@step("configs", "2/9 Config Files")
def restore_configs(dry_run=False, **_):
    section("2/9 Config Files")

    single_files = {
        REPO / "configs" / ".zshrc": HOME / ".zshrc",
        REPO / "configs" / ".shell_common": HOME / ".shell_common",
        REPO / "configs" / ".gitconfig": HOME / ".gitconfig",
        REPO / "configs" / ".theme_mode": HOME / ".theme_mode",
        REPO / "configs" / ".aerospace.toml": HOME / ".aerospace.toml",
        REPO / "configs" / "starship.toml": HOME / ".config" / "starship.toml",
        REPO / "configs" / ".bash_profile": HOME / ".bash_profile",
        REPO / "configs" / ".bashrc": HOME / ".bashrc",
        REPO / "configs" / ".zprofile": HOME / ".zprofile",
        REPO / "configs" / ".zshenv": HOME / ".zshenv",
        REPO / "configs" / ".hushlogin": HOME / ".hushlogin",
    }
    for src, dst in single_files.items():
        copy_file(src, dst, dry_run)

    dir_configs = {
        REPO / "configs" / "ghostty": HOME / ".config" / "ghostty",
        REPO / "configs" / "nvim": HOME / ".config" / "nvim",
        REPO / "configs" / "zsh": HOME / ".zsh",
    }
    for src, dst in dir_configs.items():
        copy_dir(src, dst, dry_run)

    # bin/ 脚本
    bin_src = REPO / "bin"
    bin_dst = HOME / ".local" / "bin"
    if bin_src.exists():
        bin_dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(bin_src.iterdir()):
            if f.is_file():
                copy_file(f, bin_dst / f.name, dry_run)
                if not dry_run:
                    (bin_dst / f.name).chmod(0o755)

    # .bashrc_private.example
    example = REPO / "configs" / ".bashrc_private.example"
    target = HOME / ".bashrc_private"
    if example.exists() and not target.exists():
        copy_file(example, target, dry_run)
        if not dry_run:
            target.chmod(0o600)
            info("已创建 ~/.bashrc_private (模板，请填入真实 API keys)")
    elif target.exists():
        info("~/.bashrc_private 已存在，跳过模板")


# ── 4. Oh My Zsh ─────────────────────────────────────────────────────


@step("omz", "3/9 Oh My Zsh + Plugins")
def restore_oh_my_zsh(dry_run=False, **_):
    section("3/9 Oh My Zsh")

    omz_dir = HOME / ".oh-my-zsh"
    if not omz_dir.exists():
        info("安装 Oh My Zsh...")
        if dry_run:
            info("[DRY-RUN] install Oh My Zsh")
        else:
            rc = run_visible(
                'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
            )
            if rc != 0:
                error("Oh My Zsh 安装失败")
                return
            info("Oh My Zsh 安装完成")
    else:
        info("Oh My Zsh 已安装")

    # 恢复自定义插件
    plugins_file = REPO / "configs" / "omz-custom" / "plugins.txt"
    if plugins_file.exists():
        info("安装自定义 zsh 插件...")
        custom_plugins_dir = omz_dir / "custom" / "plugins"
        for line in plugins_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                name, url = parts
                target = custom_plugins_dir / name
                if target.exists():
                    info(f"插件已存在: {name}")
                    continue
                if dry_run:
                    info(f"[DRY-RUN] git clone {url} -> {target}")
                    continue
                rc = run_visible(f'git clone "{url}" "{target}"')
                if rc == 0:
                    info(f"已安装插件: {name}")
                else:
                    error(f"插件安装失败: {name}")

    # 恢复自定义主题
    themes_dir = REPO / "configs" / "omz-custom" / "themes"
    if themes_dir.exists():
        copy_dir(themes_dir, omz_dir / "custom" / "themes", dry_run)


# ── 5. macOS Defaults ────────────────────────────────────────────────


@step("defaults", "4/9 macOS Defaults (系统偏好)")
def restore_defaults(dry_run=False, **_):
    section("4/9 macOS Defaults")

    defaults_dir = REPO / "defaults"
    if not defaults_dir.exists():
        warn("defaults/ 备份不存在")
        return

    domain_map = {
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

    for domain, filename in domain_map.items():
        plist = defaults_dir / f"{filename}.plist"
        defaults_import(domain, plist, dry_run)

    # 截图优化 (plist 可能为空，用 defaults write 确保设置)
    screencapture_settings = [
        'defaults write com.apple.screencapture disable-shadow -bool true',
        'defaults write com.apple.screencapture show-thumbnail -bool false',
        'defaults write com.apple.screencapture type jpg',
        'defaults write com.apple.screencapture name "sc"',
        'defaults write com.apple.screencapture include-date -bool false',
        f'defaults write com.apple.screencapture location -string "{HOME}/Desktop"',
    ]
    # 禁止在网络卷/USB 上生成 .DS_Store
    desktopservices_settings = [
        'defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true',
        'defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true',
    ]
    # 点击桌面显示桌面: 0 = 仅在 Stage Manager 中, 1 = 始终
    windowmanager_settings = [
        'defaults write com.apple.WindowManager EnableStandardClickToShowDesktop -bool false',
    ]
    for cmd in screencapture_settings + desktopservices_settings + windowmanager_settings:
        if dry_run:
            info(f"[DRY-RUN] {cmd}")
        else:
            run(cmd)
    if not dry_run:
        info("截图设置: 无阴影, 无缩略图, jpg 格式, 前缀 sc, 保存到 ~/Desktop")
        info("desktopservices: 禁止网络卷/USB 生成 .DS_Store")
        info("WindowManager: 点击桌面显示桌面仅在 Stage Manager 中生效")

    if not dry_run:
        info("重启 Dock 和 Finder 使设置生效...")
        run("killall Dock")
        run("killall Finder")
        run("killall SystemUIServer")
        info("Dock / Finder / SystemUIServer 已重启")


# ── 6. Services ──────────────────────────────────────────────────────


@step("services", "5/9 Services (Automator Workflows)")
def restore_services(dry_run=False, **_):
    section("5/9 Services")
    src = REPO / "services"
    dst = HOME / "Library" / "Services"
    if not src.exists():
        warn("services/ 备份不存在")
        return
    if dry_run:
        items = [i for i in src.iterdir() if not i.name.startswith(".")]
        info(f"[DRY-RUN] 恢复 {len(items)} 个 Services")
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
    info(f"已恢复 {count} 个 Services -> ~/Library/Services/")


# ── 7. Claude Code ───────────────────────────────────────────────────


@step("claude", "6/9 Claude Code")
def restore_claude_code(dry_run=False, **_):
    section("6/9 Claude Code")

    # ── 检查并安装 Claude Code CLI ──
    if has_cmd("claude"):
        _, ver = run("claude --version 2>/dev/null")
        info(f"Claude Code CLI 已安装: {ver}")
    else:
        info("安装 Claude Code CLI...")
        if dry_run:
            info("[DRY-RUN] curl -fsSL https://claude.ai/install.sh | bash")
        else:
            rc = run_visible("curl -fsSL https://claude.ai/install.sh | bash")
            if rc != 0:
                warn("Claude Code CLI 安装失败，请稍后手动安装:")
                warn("  curl -fsSL https://claude.ai/install.sh | bash")
            else:
                info("Claude Code CLI 安装完成")

    # ── 恢复配置 ──
    claude_src = REPO / "claude"
    claude_dst = HOME / ".claude"

    for f in ["CLAUDE.md", "settings.json"]:
        copy_file(claude_src / f, claude_dst / f, dry_run)

    # 项目 memory
    projects_src = claude_src / "projects"
    if projects_src.exists():
        for project in sorted(projects_src.iterdir()):
            if not project.is_dir():
                continue
            project_dst = claude_dst / "projects" / project.name
            for item in project.iterdir():
                if item.is_dir():
                    copy_dir(item, project_dst / item.name, dry_run)
                else:
                    copy_file(item, project_dst / item.name, dry_run)


# ── 8. Typora Themes ─────────────────────────────────────────────────


@step("typora", "7/9 Typora Themes")
def restore_typora_themes(dry_run=False, **_):
    section("7/9 Typora Themes")
    src = REPO / "typora" / "themes"
    dst = HOME / "Library" / "Application Support" / "abnerworks.Typora" / "themes"
    copy_dir(src, dst, dry_run)


# ── 9. Hide Folders ────────────────────────────────────────────────


@step("hidefolders", "8/9 隐藏 Home 目录文件夹")
def restore_hide_folders(dry_run=False, **_):
    section("8/9 隐藏 Home 目录文件夹")
    folders = [
        HOME / "Applications",
        HOME / "Library",
        HOME / "Movies",
        HOME / "Music",
        HOME / "Pictures",
        HOME / "Public",
        HOME / "miniconda3",
        HOME / "comflowy",
    ]
    count = 0
    for folder in folders:
        if not folder.exists():
            continue
        if dry_run:
            info(f"[DRY-RUN] chflags hidden {folder}")
            count += 1
            continue
        rc, _ = run(f'chflags hidden "{folder}"')
        if rc == 0:
            count += 1
        else:
            error(f"chflags hidden 失败: {folder}")
    info(f"已隐藏 {count} 个文件夹")


# ── 10. Ollama 模型 (可选) ──────────────────────────────────────────


@step("ollama", "9/9 Ollama 模型 (可选，耗时较长)")
def restore_ollama_models(dry_run=False, **_):
    section("9/9 Ollama 模型")

    # 检查 Ollama 是否已安装 (通过 Brewfile cask 或手动)
    if not has_cmd("ollama"):
        warn("Ollama 未安装，请先通过 brew 步骤安装或手动安装 Ollama.app")
        return

    models_file = REPO / "ollama_models.txt"
    if not models_file.exists():
        warn("ollama_models.txt 不存在")
        return

    lines = models_file.read_text().splitlines()
    models = []
    for line in lines[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])

    if not models:
        warn("无模型需要恢复")
        return

    info(f"需要拉取 {len(models)} 个模型:")
    for m in models:
        print(f"    - {m}")

    if dry_run:
        info("[DRY-RUN] ollama pull ...")
        return

    # 检查 ollama 服务是否运行
    rc, _ = run("ollama list 2>/dev/null")
    if rc != 0:
        warn("Ollama 服务未运行，请先启动 Ollama.app 再执行此步骤")
        warn("或稍后手动执行:")
        for m in models:
            print(f"    ollama pull {m}")
        return

    for m in models:
        info(f"拉取 {m} ...")
        rc = run_visible(f"ollama pull {m}")
        if rc == 0:
            info(f"已拉取: {m}")
        else:
            error(f"拉取失败: {m}")


# ── 主流程 ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="macOS 个人设置一键恢复",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
步骤: prereqs, brew, configs, omz, defaults, services, claude, typora, hidefolders, ollama

示例:
  python3 mac_restore.py                    交互式恢复 (每步确认, 不含 ollama)
  python3 mac_restore.py --yes              全部执行 (不含 ollama)
  python3 mac_restore.py --only prereqs brew configs  只执行指定步骤
  python3 mac_restore.py --pull-ollama-models         只拉取 Ollama 模型
  python3 mac_restore.py --dry-run          预览所有操作
""",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="预览恢复内容，不实际操作"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="跳过确认"
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(STEPS.keys()),
        help="只执行指定步骤",
    )
    parser.add_argument(
        "--pull-ollama-models",
        action="store_true",
        help="只拉取 ollama_models.txt 中定义的所有模型",
    )
    args = parser.parse_args()

    # --pull-ollama-models: 直接执行 ollama 步骤后退出
    if args.pull_ollama_models:
        restore_ollama_models(dry_run=args.dry_run)
        return

    print(f"\n{BOLD}{'=' * 60}")
    print(f"  macOS Restore Script")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  备份源: {REPO}")
    if args.dry_run:
        print(f"  {YELLOW}*** DRY-RUN 模式 ***{RESET}")
    print(f"{'=' * 60}{RESET}")

    ts_file = REPO / ".last_backup"
    if ts_file.exists():
        print(f"\n  上次备份时间: {ts_file.read_text().strip()}")

    # 默认流程不含 ollama (耗时长，需单独 --pull-ollama-models 或 --only ollama)
    if args.only:
        steps_to_run = args.only
    else:
        steps_to_run = [s for s in STEPS.keys() if s != "ollama"]

    for step_name in steps_to_run:
        label, func = STEPS[step_name]
        if not args.dry_run and not args.yes:
            if not confirm(f"执行 {label}?"):
                warn(f"跳过: {label}")
                continue
        func(dry_run=args.dry_run)

    print(f"\n{BOLD}{GREEN}{'=' * 60}")
    print(f"  脚本恢复部分完成!")
    print(f"{'=' * 60}{RESET}")

    print(f"\n{BOLD}{YELLOW}请继续完成手动步骤 (详见 human_step_guide.md):{RESET}")
    print(f"  1. 手动复制 ~/.ssh/ 和 ~/.bashrc_private")
    print(f"  2. 手动复制 ~/d/Personal_AI_Brain/")
    print(f"  3. 手动恢复字体 (见 human_step_guide.md 字体部分)")
    print(f"  4. 登录 Apple ID / iCloud")
    print(f"  5. 配置讯飞输入法")
    print(f"  6. 登录 Brave Browser 同步")
    print(f"  7. 登录 Docker Desktop")
    print(f"  8. 在 System Settings > Displays 配置显示器")
    print(f"  9. 配置 Shortcuts (快捷指令)")
    print(f"  10. 启用 Finder 扩展: System Settings > General > Login Items & Extensions > Finder")
    print(f"      确保 Shortcuts 中定义的 Quick Actions 已勾选")

    print(f"\n{BOLD}{YELLOW}以下系统设置受 macOS 保护, defaults import 无法生效, 需手动确认:{RESET}")
    print(f"  {BOLD}Accessibility (System Settings > Accessibility > Display):{RESET}")
    print(f"    - Reduce transparency (减少透明度)")
    print(f"    - Reduce motion (减少动态效果)")
    print(f"    - Increase contrast (增强对比度)")
    print(f"  {BOLD}Accessibility (System Settings > Accessibility):{RESET}")
    print(f"    - Pointer Control > Mouse Keys (鼠标键)")
    print(f"    - Keyboard > Slow Keys (慢速按键)")
    print(f"    - Keyboard > Sticky Keys (粘滞键)")
    print(f"    - Zoom (缩放)")
    print(f"  {BOLD}Privacy & Security:{RESET}")
    print(f"    - Accessibility 权限 (终端、AeroSpace、HyperKey 等)")
    print(f"    - Full Disk Access 权限")
    print(f"    - Input Monitoring 权限")
    print(f"  {BOLD}其他:{RESET}")
    print(f"    - Night Shift / True Tone (System Settings > Displays)")
    print(f"    - 默认浏览器 (System Settings > Desktop & Dock)")
    print(f"    - 锁屏密码 / Touch ID (System Settings > Lock Screen)")


if __name__ == "__main__":
    main()
