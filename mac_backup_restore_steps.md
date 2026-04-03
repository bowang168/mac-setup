# macOS 备份与恢复手动步骤

> 场景: MacBook Pro M3 Pro — 全新 macOS 安装、备份与恢复 + 外置 1TB 盘 (个人)
>
> 自动化脚本: `mac_backup.py` / `mac_restore.py`
>
> 本文档覆盖脚本无法自动化的部分。

---

## 一、备份阶段 (在当前系统上执行)

### 1.1 运行自动备份脚本

```bash
cd ~/dev/mac-setup
python3 mac_backup.py           # 执行备份
python3 mac_backup.py --dry-run # 先预览
```

### 1.2 手动备份敏感文件

将以下内容复制到 **加密 USB** 或其他安全存储:

```bash
# SSH 密钥
cp -r ~/.ssh/ /Volumes/YOUR_USB/manual_backup/ssh/

# API Keys
cp ~/.bashrc_private /Volumes/YOUR_USB/manual_backup/

# Personal AI Brain
cp -r ~/d/Personal_AI_Brain/ /Volumes/YOUR_USB/manual_backup/Personal_AI_Brain/
```

### 1.3 记录当前显示器设置

打开 **System Settings > Displays**, 截图或记录:

| 项目 | 当前值 |
|------|--------|
| 内置显示器分辨率 | ______ |
| 内置显示器缩放 | ______ |
| 外接显示器分辨率 | ______ |
| 外接显示器缩放 | ______ |
| 排列方式 | ______ |
| Night Shift 时间 | ______ |

### 1.4 记录 Shortcuts (快捷指令)

Shortcuts 数据存储在 iCloud/CoreData 中，无法直接文件备份。

**方案 A (推荐): iCloud 同步**
- 确保 Shortcuts 在 iCloud 中已开启同步
- 新系统登录同一 Apple ID 后会自动恢复

**方案 B: 手动记录**
- 脚本已导出名称列表到 `shortcuts_list.txt`
- 复杂的快捷指令需要截图记录其步骤

### 1.5 推送备份到 GitHub

```bash
cd ~/dev/mac-setup
git add -A
git commit -m "backup: $(date +%Y-%m-%d)"
git push
```

---

## 二、目标卷安装 macOS

### 2.1 准备目标卷

1. 连接 1TB 目标硬盘 (建议 USB-C / Thunderbolt SSD)
2. 打开 **Disk Utility**
3. 选择目标卷 → **Erase**:
   - Name: `macOS Personal` (或你喜欢的名字)
   - Format: **APFS**
   - Scheme: **GUID Partition Map**

### 2.2 安装 macOS

**方法 A: macOS Recovery (推荐)**

1. 关机
2. 按住电源键直到看到 "Loading startup options..."
3. 选择 **Options** → Continue
4. 选择 **Reinstall macOS**
5. 安装目标选择 **目标卷**
6. 等待安装完成

**方法 B: 使用 createinstallmedia**

```bash
# 下载 macOS installer (App Store 或 softwareupdate)
# 创建安装盘 (需要另一个 USB)
sudo /Applications/Install\ macOS\ Tahoe.app/Contents/Resources/createinstallmedia \
    --volume /Volumes/YOUR_USB
```

### 2.3 首次启动配置

1. 从目标卷启动: 开机时按住电源键 → 选择目标卷
2. 完成 Setup Assistant:
   - **不要** 使用 Migration Assistant (会带入 旧配置)
   - 创建本地用户 (建议用户名: `yourname`)
   - 登录 Apple ID (可以先跳过, 稍后再登录)
3. 确认 **无 setup verification 提示** 出现

### 2.4 设置默认启动盘

```
System Settings > General > Startup Disk > 选择目标卷
```

> **注意**: 切换回主系统时, 重启按住电源键选择主卷即可。

---

## 三、恢复阶段 (在新系统上执行)

### 3.1 获取备份仓库

新系统自带 git (Xcode CLT 版本)，可以直接 clone：

```bash
mkdir -p ~/dev && cd ~/dev

# 方法 A: HTTPS (无需 SSH key)
git clone https://github.com/YOUR_USERNAME/mac-setup.git

# 方法 B: 如果已手动复制了 SSH key
git clone git@github.com:YOUR_USERNAME/mac-setup.git

cd mac-setup
```

### 3.2 运行自动恢复脚本

脚本会自动检测并安装: Xcode CLT、Homebrew、Git、GitHub CLI、Oh My Zsh、Claude Code。

```bash
# 预览所有操作
python3 mac_restore.py --dry-run

# 交互式恢复 (每步确认，推荐)
python3 mac_restore.py

# 全部恢复 (跳过确认)
python3 mac_restore.py --yes

# 只恢复部分
python3 mac_restore.py --only prereqs brew configs
```

可选步骤: `prereqs`, `brew`, `fonts`, `configs`, `omz`, `defaults`, `services`, `claude`, `typora`, `ollama`, `display`

### 3.3 手动恢复敏感文件

```bash
# 从加密 USB 恢复
cp -r /Volumes/YOUR_USB/manual_backup/ssh/ ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

cp /Volumes/YOUR_USB/manual_backup/.bashrc_private ~/

mkdir -p ~/d
cp -r /Volumes/YOUR_USB/manual_backup/Personal_AI_Brain/ ~/d/Personal_AI_Brain/
```

### 3.4 配置讯飞输入法

1. 从 App Store 或官网下载讯飞输入法
2. System Settings > Keyboard > Input Sources > 添加讯飞输入法
3. 登录账号同步词库 (如果有)

### 3.5 配置浏览器

**Brave Browser:**
1. 打开 Brave (已通过 Brewfile 安装或手动安装)
2. Settings > Sync > 扫码或输入同步链
3. 等待书签、密码、扩展同步完成

**Google Chrome:**
1. 打开 Chrome
2. 登录 Google 账号
3. 同步设置

### 3.6 Docker Desktop

1. 打开 Docker Desktop (已通过 Brewfile 安装)
2. 登录 Docker Hub (如需要)
3. 如有 compose 项目, clone 后 `docker compose up`

### 3.7 配置显示器

1. System Settings > Displays
2. 参照 `display_info.txt` 和 1.3 节记录, 手动设置:
   - 分辨率和缩放
   - 显示器排列
   - Night Shift (如不使用 Flux)

### 3.8 恢复 Shortcuts (快捷指令)

**如果使用 iCloud 同步:**
- 登录 Apple ID 后, 打开 Shortcuts app, 检查是否已同步

**如果手动重建:**
- 参照 `shortcuts_list.txt` 中的名称列表
- 重新创建需要的快捷指令

### 3.9 Ollama 模型

如果恢复脚本中跳过了 Ollama 步骤:

```bash
# 先启动 Ollama.app, 然后:
ollama pull qwen2.5-coder:32b
ollama pull qwen3-embedding:8b
ollama pull minicpm-v:8b
ollama pull qwen3-embedding:0.6b
```

> 总计约 30GB, 建议在稳定网络下执行。

---

## 四、恢复后验证清单

| 项目 | 验证方法 | 状态 |
|------|----------|------|
| Shell (zsh + OMZ + starship) | 打开新终端, 检查 prompt 和 alias | [ ] |
| Neovim | `nvim`, 检查插件和主题 | [ ] |
| Ghostty | 打开 Ghostty, 检查字体和配色 | [ ] |
| AeroSpace | 检查窗口管理快捷键 | [ ] |
| HyperKey | CapsLock 单击 = Esc, 长按 = Hyper | [ ] |
| Git | `git config --list`, 检查用户名和 delta | [ ] |
| SSH | `ssh -T git@github.com` | [ ] |
| Homebrew | `brew doctor` | [ ] |
| Fonts | 打开 Font Book, 检查 MapleMono 等 | [ ] |
| Dock | 自动隐藏, 无动画 | [ ] |
| Finder | 检查偏好设置 | [ ] |
| 键盘快捷键 | System Settings > Keyboard > Shortcuts | [ ] |
| Flux | 检查色温和时间设置 | [ ] |
| TextEdit | 打开, 确认纯文本模式 | [ ] |
| Typora | 打开, 检查主题和设置 | [ ] |
| Claude Code | `claude`, 检查 memory 和设置 | [ ] |
| Automator Services | Finder > Services 菜单检查 | [ ] |
| Shortcuts | 打开 Shortcuts app 检查 | [ ] |
| Ollama | `ollama list` | [ ] |
| Docker | `docker ps` | [ ] |
| 讯飞输入法 | 切换输入法测试 | [ ] |
| Brave | 检查书签和扩展 | [ ] |
| 显示器 | 分辨率和缩放正确 | [ ] |

---

## 五、多卷启动切换

| 操作 | 方法 |
|------|------|
| 切换到新系统 (目标卷) | 重启 → 按住电源键 → 选择目标卷 |
| 切换到主系统 (主卷) | 重启 → 按住电源键 → 选择 Macintosh HD |
| 设置默认启动盘 | System Settings > General > Startup Disk |

> **提示**: 目标卷未连接时, Mac 会自动从主卷启动。

---

## 六、日常维护

### 定期更新备份

```bash
cd ~/dev/mac-setup
python3 mac_backup.py
git add -A
git commit -m "backup: $(date +%Y-%m-%d)"
git push
```

### 新增应用后

```bash
# 更新 Brewfile
brew bundle dump --describe --force --file=~/dev/mac-setup/Brewfile
```

### 修改系统偏好后

```bash
# 重新导出变更的 defaults
python3 mac_backup.py  # 会重新导出所有 defaults
```
