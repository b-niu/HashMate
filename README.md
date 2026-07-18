# HashMate

> 中文 | [English](#english)

基于 `uv` + Python + PySide6 的哈希值校验工具。

- 输入**文件路径**（支持拖拽 / 浏览）
- 粘贴**自由格式文本**，智能解析其中的 MD5 / SHA1 / SHA-256 / SHA-512 等哈希值
- 解析结果以**可编辑表格**呈现，支持人工纠错（改类型、改值、增删行）
- 一键**校验**文件实际哈希与文本目标值是否一致

代码注释使用中文；本仓库使用 [ruff](https://docs.astral.sh/ruff/) 进行格式化与 import 排序。

---

## 使用教程

### 1. 安装依赖

```bash
uv sync
```

### 2. 启动图形界面

**方式一 — 双击快捷方式（推荐 Windows 用户）**
```powershell
.\scripts\run.ps1 -CreateShortcut
```
执行后桌面生成 `HashMate.lnk`，双击即可启动（带图标）。

**方式二 — 直接运行启动脚本**
```powershell
.\scripts\run.ps1         # Windows
./scripts/run.sh           # Linux / macOS
```

**方式三 — 手动**
```bash
uv run hashmate            # 或：uv run python -m hashmate
```

### 3. 启动后如何使用

1. **选文件**：拖拽文件到虚线框，或点击「浏览…」
2. **输入哈希信息**：将包含 MD5、SHA1、SHA-256 等信息的文本粘贴到输入框
3. **解析文本**：点击「解析文本」，结果自动填入表格
4. **纠错**：可修改类型下拉框、编辑哈希值、添加/删除行
5. **校验**：点击「校验文件哈希」，查看每条是否匹配

---

## ⚠ Windows 常见问题

### 执行策略（禁止运行脚本）

首次运行 `.ps1` 时可能遇到：
```
无法加载文件 ...\run.ps1，因为在此系统上禁止运行脚本。
```

**解决方法**（以管理员身份运行 PowerShell 后执行一次）：
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
之后 `.\scripts\run.ps1` 即可正常运行。

### 控制台中文乱码

启动脚本 `scripts/run.ps1` 和 `scripts/run.sh` 均已使用英文输出，不会出现乱码。

---

## 文本解析示例

以下格式均可被正确解析（兼容全角 / 半角冒号、大小写、空格）：

```
MD5： 6c8000da9731a35fa6ad37132c4005ee
SHA1： 24d8a2e91672db579ca73cee4084918e97343431
SHA-256： 591ae6d22871a6e7918fbe8ccc0c9d0279c771a0b0a3d8e7dbec4abfe78335b7
```

---

## 扩展解析规则

解析器采用「规则注册表」设计，便于持续追加新格式。在 `src/hashmate/parser.py` 中：

1. 继承 `BaseExtractor` 实现 `extract(text) -> List[HashMatch]`
2. 用 `register_extractor(YourExtractor())` 注册

新增标签同义词（如新的算法别名）只需在 `LABEL_SYNONYMS` 中追加，无需改动其它代码。

---

## 开发命令

```bash
uv run pytest -q            # 测试
uv run ruff format .        # 格式化
uv run ruff check --fix .   # 检查 + import 排序
uv run python -m hashmate   # 运行 GUI
```

## 项目结构

```
HashMate/
├─ assets/
│  ├─ logo.png           # 应用图标（源文件，可自行修改）
│  └─ icon.ico           # Windows 多尺寸图标
├─ scripts/
│  ├─ run.ps1            # Windows 启动脚本
│  └─ run.sh             # Linux / macOS 启动脚本
├─ src/hashmate/
│  ├─ app.py             # PySide6 图形界面
│  ├─ parser.py          # 可扩展文本解析器（核心）
│  ├─ hasher.py          # 文件哈希计算
├─ tests/
│  └─ test_parser.py
└─ pyproject.toml
```

---

<a id="english"></a>

## English

A file hash validator built with `uv`, Python and PySide6.

- Provide a **file path** (drag-and-drop or browse)
- Paste **free-form text**; hashes such as MD5 / SHA1 / SHA-256 / SHA-512 are extracted intelligently
- Results appear in an **editable table** for manual correction (change type, edit value, add/remove rows)
- One-click **verification** compares the file's actual hashes against the target values from the text

Code comments are written in Chinese. This repository uses [ruff](https://docs.astral.sh/ruff/) for formatting and import sorting.

### Quick start

```bash
uv sync
uv run hashmate          # launch the GUI
```

### Windows: execution policy

If you see this error when running the `.ps1` script:
```
cannot be loaded because running scripts is disabled on this system
```
Run this once as **Administrator**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Creating a desktop shortcut (Windows)

```powershell
.\scripts\run.ps1 -CreateShortcut
```

A shortcut with the application icon will appear on your desktop.

### Installing a desktop entry (Linux)

```bash
chmod +x scripts/run.sh
./scripts/run.sh --install-desktop
```

The app will appear in your application launcher with the icon.

### Text parsing example

The following formats are all parsed correctly (full/half-width colons, upper/lower case and spaces are tolerated):

```
MD5： 6c8000da9731a35fa6ad37132c4005ee
SHA1： 24d8a2e91672db579ca73cee4084918e97343431
SHA-256： 591ae6d22871a6e7918fbe8ccc0c9d0279c771a0b0a3d8e7dbec4abfe78335b7
```

### Extending the parser

The parser uses a rule registry so new formats can be added continuously. In `src/hashmate/parser.py`:

1. Subclass `BaseExtractor` and implement `extract(text) -> List[HashMatch]`
2. Register it with `register_extractor(YourExtractor())`

New label synonyms (e.g. new algorithm aliases) only need to be appended to `LABEL_SYNONYMS`, with no changes elsewhere.
