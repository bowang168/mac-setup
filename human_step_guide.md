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

### 1.2 手动备份字体

字体文件较大且不适合存储在 git 仓库中，需手动备份。

```bash
# 备份所有自定义字体到加密 USB
mkdir -p /Volumes/YOUR_USB/manual_backup/fonts
cp -r ~/Library/Fonts/ /Volumes/YOUR_USB/manual_backup/fonts/
```

需要备份的关键字体（参见 `docs/Font-README.md`）:

| 字体 | 用途 |
|------|------|
| MapleMono NF | 代码/终端（首选） |
| InputMono / InputSans / InputSerif | 代码/UI/标题 |
| 霞鹜文楷 (LXGWWenKai) | 中文长文阅读 |
| 霞鹜文楷 Mono | 含中文注释的代码 |
| 汉仪楷体S | 正式中文文档 |

### 1.3 手动备份敏感文件

将以下内容复制到 **加密 USB** 或其他安全存储:

```bash
# SSH 密钥
cp -r ~/.ssh/ /Volumes/YOUR_USB/manual_backup/ssh/

# API Keys
cp ~/.bashrc_private /Volumes/YOUR_USB/manual_backup/

# Personal AI Brain
cp -r ~/d/Personal_AI_Brain/ /Volumes/YOUR_USB/manual_backup/Personal_AI_Brain/
```

### 1.4 记录当前显示器设置

打开 **System Settings > Displays**, 截图或记录:

| 项目 | 当前值 |
|------|--------|
| 内置显示器分辨率 | ______ |
| 内置显示器缩放 | ______ |
| 外接显示器分辨率 | ______ |
| 外接显示器缩放 | ______ |
| 排列方式 | ______ |
| Night Shift 时间 | ______ |

### 1.5 记录 Shortcuts (快捷指令)

Shortcuts 数据存储在 iCloud/CoreData 中，无法直接文件备份。

**方案 A (推荐): iCloud 同步**
- 确保 Shortcuts 在 iCloud 中已开启同步
- 新系统登录同一 Apple ID 后会自动恢复

**方案 B: 手动记录**
- 脚本已导出名称列表到 `shortcuts_list.txt`
- 复杂的快捷指令需要截图记录其步骤

### 1.6 推送备份到 GitHub

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
   - 创建本地用户
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

可选步骤: `prereqs`, `brew`, `configs`, `omz`, `defaults`, `services`, `claude`, `typora`, `ollama`, `hidefolders`

### 3.3 手动恢复字体

从加密 USB 恢复字体到 `~/Library/Fonts/`:

```bash
# 从加密 USB 恢复
cp -r /Volumes/YOUR_USB/manual_backup/fonts/* ~/Library/Fonts/
```

**验证**: 打开 **Font Book** app，确认以下字体已安装:
- MapleMono NF（终端和编辑器字体）
- 霞鹜文楷 / 霞鹜文楷 Mono
- InputMono / InputSans / InputSerif
- 汉仪楷体S

> 字体使用指南详见 `docs/Font-README.md`

### 3.4 手动恢复敏感文件

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

### 3.5 配置讯飞输入法

1. 从 App Store 或官网下载讯飞输入法
2. System Settings > Keyboard > Input Sources > 添加讯飞输入法
3. 登录账号同步词库 (如果有)

### 3.6 配置浏览器

**Brave Browser:**
1. 打开 Brave (已通过 Brewfile 安装或手动安装)
2. Settings > Sync > 扫码或输入同步链
3. 等待书签、密码、扩展同步完成
4. 安装 **Vimium** 扩展 (按 `f` 显示链接 hint，`j/k` 滚动)

**Google Chrome:**
1. 打开 Chrome
2. 登录 Google 账号
3. 同步设置
4. 安装 **Vimium** 扩展

### 3.7 Docker Desktop

1. 打开 Docker Desktop (已通过 Brewfile 安装)
2. 登录 Docker Hub (如需要)
3. 如有 compose 项目, clone 后 `docker compose up`

### 3.8 配置显示器

1. System Settings > Displays
2. 参照 `docs/flux-eye-health-guide.md` 和 1.3 节记录, 手动设置:
   - 分辨率和缩放
   - 显示器排列
   - Night Shift (如不使用 Flux)

### 3.9 恢复 Shortcuts (快捷指令)

**如果使用 iCloud 同步:**
- 登录 Apple ID 后, 打开 Shortcuts app, 检查是否已同步

**如果手动重建:**
- 参照 `shortcuts_list.txt` 中的名称列表
- 重新创建需要的快捷指令

### 3.10 Ollama 模型

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
| HyperKey | 确认以下设置 (defaults import 可能不生效): | [ ] |
|        | - Remap physical key to hyper key: **caps lock** | |
|        | - Quick press caps lock to execute: **esc** | |
|        | - Include shift in hyper key: **ON** | |
|        | - Open on login: **ON** | |
|        | - Hide menu bar icon: **ON** | |
| Git | `git config --list`, 检查用户名和 delta | [ ] |
| SSH | `ssh -T git@github.com` | [ ] |
| Homebrew | `brew doctor` | [ ] |
| Fonts (手动) | 打开 Font Book, 检查 MapleMono 等 (见 3.3 节) | [ ] |
| Dock | 自动隐藏, 无动画 | [ ] |
| Finder | 检查偏好设置 | [ ] |
| 键盘快捷键 | System Settings > Keyboard > Shortcuts | [ ] |
| Flux | 检查色温: 白天 3400K / 日落 2700K / 睡前 2300K | [ ] |
| TextEdit | 打开, 确认纯文本模式 | [ ] |
| Typora | 打开, 检查主题和设置 | [ ] |
| Claude Code | `claude`, 检查 memory 和设置 | [ ] |
| Automator Services | Finder > Services 菜单检查 | [ ] |
| Shortcuts | 打开 Shortcuts app 检查 | [ ] |
| Ollama | `ollama list` | [ ] |
| Docker | `docker ps` | [ ] |
| 讯飞输入法 | 切换输入法测试 | [ ] |
| Brave | 检查书签和扩展 | [ ] |
| 触控板三指拖移 | System Settings > Accessibility > Pointer Control > Trackpad Options > 三指拖移 | [ ] |
| Accessibility 显示 | System Settings > Accessibility > Display: Reduce motion ✅ Reduce transparency ✅ | [ ] |
| 截图设置 | 截一张图确认: jpg 格式, 前缀 sc, 无阴影, 保存到 ~/Desktop | [ ] |
| 电池百分比 | System Settings > Control Center > Battery > Show Percentage: ON | [ ] |
| Text Replacement | System Settings > Keyboard > Text Replacements (iCloud 同步, 确认已恢复) | [ ] |
| 显示器 | 分辨率和缩放正确 | [ ] |
| Time Out | 检查休息提醒配置 (见下方推荐) | [ ] |

---

## 五、视觉健康与护眼设置

### 5.1 20-20-20 护眼法则

**每 20 分钟，看 20 英尺 (6 米) 远处，持续 20 秒。**

### 5.2 Time Out 推荐配置

- **微休息**: 每 25 分钟提醒 20 秒 (看远处)
- **长休息**: 每 90 分钟提醒 5 分钟 (离开屏幕走动)
- 编译/等待 CI 时主动看远处

### 5.3 f.lux 推荐设置

| 时段 | 色温 |
|------|------|
| 白天 | Halogen 3400K |
| 日落 | Tungsten 2700K |
| 睡前 | Candle 2300K |

### 5.4 Night Shift (蓝光过滤)

```
System Settings → Displays → Night Shift
- Schedule: Sunset to Sunrise
- Color Temperature: 中间偏暖
```

> 如果使用 f.lux 则可关闭 Night Shift，两者功能重叠。

### 5.5 外接显示器亮度控制 — Lunar (参考)

- `brew install --cask lunar`
- Location Mode: 根据日出日落自动调节亮度
- 使用 DDC 协议直接控制硬件亮度
- 支持快捷键调节

> 仅供参考，不强制安装。

---

## 六、指针和触控板推荐配置

- **启用三指拖移**: 系统设置 → 辅助功能 → 指针控制 → 点击"触控板选项"，勾选"使用触控板拖移"，拖移方式选择"三指拖移"。无需按下即可用三指拖动窗口。
- **调整指针大小与颜色**: 系统设置 → 辅助功能 → 显示 → 指针，拖动滑块设置大小，点击颜色井自定义轮廓和填充色。
- **调整滚动方向**: 系统设置 → 触控板 → 点按与滚动，或系统设置 → 鼠标，开启/关闭"自然滚动"。
- **调节跟踪速度和加速度**: 系统设置 → 鼠标或触控板，在"指针与点击"中拖动"跟踪速度"滑块；高级设置中可关闭指针加速度。

---

## 七、多卷启动切换

| 操作 | 方法 |
|------|------|
| 切换到新系统 (目标卷) | 重启 → 按住电源键 → 选择目标卷 |
| 切换到主系统 (主卷) | 重启 → 按住电源键 → 选择 Macintosh HD |
| 设置默认启动盘 | System Settings > General > Startup Disk |

> **提示**: 目标卷未连接时, Mac 会自动从主卷启动。

---

## 八、日常维护

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

---

## 九、常用但不直觉的快捷键

| 快捷键 | 功能 |
|--------|------|
| `⌘ + ⇧ + .` | Finder 显示/隐藏隐藏文件 |
| `⌘ + \`` | 在同一 app 的多个窗口间切换 |
| `⌃ + ⌘ + Space` | 表情符号面板 |
| `⌘ + ⌥ + Esc` | 强制退出 app |
| `⌘ + ⇧ + 5` | 截图/录屏工具栏 |
| `Space` (Finder 中) | Quick Look 预览文件 |
| `⌥ + ⇧ + 音量/亮度` | 以 1/4 格精细调节 |
| `⌘ + ⌥ + D` | 显示/隐藏 Dock |
