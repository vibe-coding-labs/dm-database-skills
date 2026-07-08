# 修复达梦 SKILLS 测试中发现的问题 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`
> Steps use checkbox (`- [ ]`) syntax.

**Goal:** 修复测试与实测中暴露的 8 个问题：get_connection 的 database 参数无效 bug、缺依赖时报错不可操作、install.md 三处文档缺陷、集成测试从未落地、遗留 Plan 文档未提交，使达梦 SKILLS 流程真正可用。

**Architecture:** 修复分三层。代码层：先修 `dm8_common.py` 的 `get_connection`（database 未拼入 URL 的 bug）并新增 `preflight` 预检函数（连接前检查 jaydebeapi 依赖与驱动存在性，给出可操作提示），每处修复配回归测试。文档层：修正 `install.md` 的 1.3 驱动校验提示、2.2 limits 改独立文件、追加第 7 节可执行性测试说明。测试层：落地上一轮计划中的 `tests/integration/test_install_guide.py`（验证 install.md 各章节命令可执行）。数据流：用户运行脚本 → preflight 先查依赖与驱动 → 缺失则输出可操作 JSON 并退出 → 齐备则 get_connection 用正确 URL 连接。设计理由：preflight 前置检查避免用户面对 ModuleNotFoundError 这类技术栈错误，回归测试防止 bug 复发。

**Tech Stack:** Python 3.12, pytest 8.4, JayDeBeApi 1.6, JPype1 1.4, Ubuntu 24.04, sudo, Markdown

**Risks:**
- Task 1 修改共享的 get_connection 影响所有脚本 → 缓解：先补回归测试（mock 验证 URL 拼接），改完跑全量测试
- Task 2 preflight 在依赖已装时不能误拦 → 缓解：测试覆盖有依赖/无依赖两种场景，无依赖时返回结构化错误
- Task 3 集成测试用 sudo 创建用户/写 limits 改系统状态 → 缓解：专用前缀 `dmsa_test` + `dinstall_test` + 独立 limits 文件，夹具自动清理
- Task 4 改 install.md 时行号会随编辑偏移 → 缓解：用章节名 + 代码上下文定位，不依赖固定行号
- Task 3 preflight 依赖缺失会让集成测试里的"脚本可导入"测试失败 → 缓解：Task 3 在 Task 1/2 之后执行，且测试用 try/except 容错

---

### Task 1: 修复 get_connection 的 database 参数无效 bug — 让 --database 真正生效

**Depends on:** None
**Files:**
- Create: `tests/test_dm8_common_preflight.py`
- Modify: `scripts/dm8_common.py:60-71`

- [ ] **Step 1: 创建回归测试 — 验证 get_connection 拼接的 JDBC URL 包含 database/schema**

```python
"""dm8_common 连接逻辑回归测试：验证 JDBC URL 拼接与 preflight 预检。"""

import os
import sys
import argparse
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import dm8_common


def make_args(**over):
    base = dict(host="127.0.0.1", port=5236, user="SYSDBA", password="p",
                database=None, schema=None)
    base.update(over)
    return argparse.Namespace(**base)


class TestJdbcUrlConstruction:
    """验证 get_connection 拼接的 JDBC URL 正确包含 host/port/database/schema。"""

    def _capture_url(self, args):
        """mock jaydebeapi.connect，捕获实际传入的 url 参数。"""
        captured = {}
        def fake_connect(driver_class, url, creds, driver_path):
            captured["url"] = url
            captured["creds"] = creds
            return mock.MagicMock()
        with mock.patch("dm8_common.find_driver", return_value="/fake/driver.jar"), \
             mock.patch.dict(sys.modules, {"jaydebeapi": mock.MagicMock(connect=fake_connect)}):
            dm8_common.get_connection(args)
        return captured

    def test_url_without_database(self):
        cap = self._capture_url(make_args())
        assert cap["url"] == "jdbc:dm://127.0.0.1:5236"

    def test_url_with_database(self):
        """P1 回归：--database 必须拼入 URL。"""
        cap = self._capture_url(make_args(database="DAMENG"))
        assert "DAMENG" in cap["url"], f"database 未拼入 URL: {cap['url']}"

    def test_url_with_database_and_schema(self):
        cap = self._capture_url(make_args(database="DAMENG", schema="SCH"))
        assert "DAMENG" in cap["url"] and "SCH" in cap["url"]
```

- [ ] **Step 2: 修复 get_connection — database 拼入 URL，schema 作为查询参数**

文件: `scripts/dm8_common.py:60-71`（替换 get_connection 函数）

```python
def get_connection(args: argparse.Namespace):
    """建立 JDBC 连接，返回 connection 对象。"""
    import jaydebeapi

    driver_path = find_driver()
    jdbc_url = JDBC_URL_TEMPLATE.format(host=args.host, port=args.port)
    # 拼接 database 与 schema 作为 URL 查询参数
    params = []
    if args.database:
        params.append(f"db={args.database}")
    if args.schema:
        params.append(f"schema={args.schema}")
    if params:
        jdbc_url = jdbc_url + "?" + "&".join(params)

    conn = jaydebeapi.connect(
        DRIVER_CLASS,
        jdbc_url,
        [args.user, args.password],
        driver_path,
    )
    return conn
```

- [ ] **Step 3: 验证 URL 拼接回归测试通过**
Run: `python3 -m pytest tests/test_dm8_common_preflight.py::TestJdbcUrlConstruction -v`
Expected:
  - Exit code: 0
  - Output contains: "3 passed"

- [ ] **Step 4: 验证全量单元测试未回归**
Run: `python3 -m pytest tests/ -q 2>&1 | tail -3`
Expected:
  - Exit code: 0
  - Output contains: "passed"
  - Output does NOT contain: "FAILED" or "ERROR"

- [ ] **Step 5: 提交**
Run: `git add scripts/dm8_common.py tests/test_dm8_common_preflight.py && git commit -m "fix(scripts): include database/schema in JDBC URL, add regression tests"`

---

### Task 2: 新增 preflight 预检函数 — 连接前检查依赖与驱动并给出可操作提示

**Depends on:** Task 1
**Files:**
- Modify: `scripts/dm8_common.py`（新增 preflight 函数 + run_with_connection 调用）
- Modify: `tests/test_dm8_common_preflight.py`（追加 preflight 测试）

- [ ] **Step 1: 在 dm8_common.py 新增 preflight 函数 — 检查 jaydebeapi 依赖与驱动存在性**

文件: `scripts/dm8_common.py`（在 find_driver 函数之后、build_arg_parser 之前插入）

```python
def preflight() -> None:
    """连接前预检：确认 jaydebeapi 依赖与 JDBC 驱动均可用。

    缺失时抛 PreflightError，附带可操作的安装指引。
    """
    # 1. 检查 jaydebeapi 依赖
    try:
        import jaydebeapi  # noqa: F401
    except ImportError:
        raise PreflightError(
            "缺少 Python 依赖 jaydebeapi。请运行: pip install jaydebeapi JPype1"
        )
    # 2. 检查 JDBC 驱动
    try:
        find_driver()
    except FileNotFoundError as e:
        raise PreflightError(str(e))


class PreflightError(Exception):
    """预检失败异常，携带可操作的用户提示。"""
    pass
```

- [ ] **Step 2: 修改 run_with_connection — 在连接前调用 preflight，捕获 PreflightError 输出可操作 JSON**

文件: `scripts/dm8_common.py`（替换 run_with_connection 函数）

```python
def run_with_connection(handler, args: argparse.Namespace, action_desc: str) -> None:
    """通用执行模板：preflight 预检 -> 连接 -> 执行 handler -> 输出结果 -> 关闭连接。"""
    try:
        preflight()
        conn = get_connection(args)
        try:
            result = handler(conn, args)
            output_json(True, data=result, message=f"{action_desc}成功")
        finally:
            conn.close()
    except PreflightError as e:
        output_json(False, message=f"预检失败: {e}")
    except FileNotFoundError as e:
        output_json(False, message=str(e))
    except Exception as e:
        output_json(False, message=f"{action_desc}失败: {type(e).__name__}: {e}")
```

- [ ] **Step 3: 追加 preflight 测试 — 覆盖有依赖/无依赖、有驱动/无驱动场景**

文件: `tests/test_dm8_common_preflight.py`（追加测试类）

```python
class TestPreflight:
    """P2 回归：preflight 在缺依赖/缺驱动时给出可操作提示。"""

    def test_preflight_passes_when_deps_and_driver_present(self, tmp_path):
        jar = tmp_path / "DmJdbcDriver18.jar"
        jar.write_text("fake")
        fake_jaydebeapi = mock.MagicMock()
        with mock.patch("dm8_common.DRIVER_SEARCH_PATHS", [str(jar)]), \
             mock.patch.dict(sys.modules, {"jaydebeapi": fake_jaydebeapi}):
            # 不抛异常即通过
            dm8_common.preflight()

    def test_preflight_reports_missing_dependency(self):
        """缺 jaydebeapi 时提示 pip install 命令。"""
        with mock.patch.dict(sys.modules, {"jaydebeapi": None}):
            with pytest.raises(dm8_common.PreflightError) as exc:
                dm8_common.preflight()
        assert "pip install jaydebeapi" in str(exc.value)

    def test_preflight_reports_missing_driver(self):
        """缺驱动时提示放置位置。"""
        fake_jaydebeapi = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"jaydebeapi": fake_jaydebeapi}), \
             mock.patch("dm8_common.DRIVER_SEARCH_PATHS", ["/nonexistent/x.jar"]):
            with pytest.raises(dm8_common.PreflightError) as exc:
                dm8_common.preflight()
        assert "DmJdbcDriver18.jar" in str(exc.value)
```

- [ ] **Step 4: 验证 preflight 测试通过**
Run: `python3 -m pytest tests/test_dm8_common_preflight.py -v`
Expected:
  - Exit code: 0
  - Output contains: "6 passed"

- [ ] **Step 5: 验证脚本真实运行时给出可操作提示**
Run: `python3 scripts/dm8_connect.py --host 127.0.0.1 --password test123; echo "EXIT=$?"`
Expected:
  - Exit code: 1
  - Output contains: "预检失败"
  - Output contains: "pip install jaydebeapi" 或 "DmJdbcDriver18.jar"

- [ ] **Step 6: 提交**
Run: `git add scripts/dm8_common.py tests/test_dm8_common_preflight.py && git commit -m "feat(scripts): add preflight check for deps and driver with actionable hints"`

---

### Task 3: 落地 install.md 可执行性集成测试 — 验证安装指引各步骤命令

**Depends on:** Task 1, Task 2
**Files:**
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_install_guide.py`

- [ ] **Step 1: 创建 conftest.py — 提供 sudo 检测、专用前缀常量与清理夹具**

```python
"""install.md 测试公共夹具：sudo 检测、专用前缀、清理逻辑。"""

import os
import subprocess
import pytest

# 专用前缀，避免污染系统真实达梦用户
TEST_USER = "dmsa_test"
TEST_GROUP = "dinstall_test"
TEST_LIMITS_FILE = "/etc/security/limits.d/dmsa-test.conf"
TEST_INSTALL_DIR = "/tmp/dm_test_install"


def have_sudo() -> bool:
    """检测当前是否可免密 sudo。"""
    try:
        subprocess.run(["sudo", "-n", "true"], check=True, capture_output=True, timeout=10)
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def sudo_available():
    return have_sudo()


@pytest.fixture
def clean_test_user(sudo_available):
    """每个测试前后清理测试用户，避免残留。"""
    if not sudo_available:
        pytest.skip("需要 sudo 权限")
    subprocess.run(["sudo", "userdel", "-r", TEST_USER], capture_output=True)
    subprocess.run(["sudo", "groupdel", TEST_GROUP], capture_output=True)
    yield
    subprocess.run(["sudo", "userdel", "-r", TEST_USER], capture_output=True)
    subprocess.run(["sudo", "groupdel", TEST_GROUP], capture_output=True)


def run(cmd, use_sudo=False, check=False, timeout=60):
    """运行命令并返回 CompletedProcess。"""
    if use_sudo and isinstance(cmd, list):
        cmd = ["sudo", "-n"] + cmd
    return subprocess.run(cmd,
                          shell=isinstance(cmd, str),
                          capture_output=True, text=True, timeout=timeout,
                          check=check)
```

- [ ] **Step 2: 创建 test_install_guide.py — 验证 install.md 各章节命令可执行**

```python
"""验证 references/install.md 安装指引的可执行性。

策略：不依赖达梦安装包的命令逐条验证；安装包获取渠道如实探测并 skip。
"""

import os
import subprocess
import urllib.request
import urllib.error
import pytest

from conftest import (
    TEST_USER, TEST_GROUP, TEST_LIMITS_FILE, TEST_INSTALL_DIR,
    have_sudo, run,
)


class TestEnvironmentBaseline:
    """install.md 前提条件：Java/unzip/Python。"""

    def test_java_available(self):
        r = run(["java", "-version"])
        assert r.returncode == 0, "java 未安装"

    def test_unzip_available(self):
        r = run(["unzip", "-v"])
        assert r.returncode == 0, "unzip 未安装"

    def test_python_available(self):
        r = run(["python3", "--version"])
        assert r.returncode == 0
        assert "3." in r.stdout + r.stderr


class TestCreateUser:
    """install.md 2.1：创建专用用户。"""

    def test_groupadd_useradd_chown_executable(self, clean_test_user):
        r = run(["groupadd", TEST_GROUP], use_sudo=True)
        assert r.returncode == 0, f"groupadd 失败: {r.stderr}"

        r = run(["useradd", "-g", TEST_GROUP, "-m", "-d", f"/home/{TEST_USER}", TEST_USER], use_sudo=True)
        assert r.returncode == 0, f"useradd 失败: {r.stderr}"

        r = run(["id", TEST_USER])
        assert r.returncode == 0, "用户未创建成功"

        os.makedirs(TEST_INSTALL_DIR, exist_ok=True)
        r = run(["chown", "-R", f"{TEST_USER}:{TEST_GROUP}", TEST_INSTALL_DIR], use_sudo=True)
        assert r.returncode == 0, f"chown 失败: {r.stderr}"

        r = run(["stat", "-c", "%U:%G", TEST_INSTALL_DIR])
        assert f"{TEST_USER}:{TEST_GROUP}" in r.stdout


class TestSystemParams:
    """install.md 2.2：limits 配置（独立文件）。"""

    def test_limits_file_writable_and_ulimit_runs(self, sudo_available):
        if not sudo_available:
            pytest.skip("需要 sudo 权限")
        content = f"{TEST_USER} soft nofile 65536\n{TEST_USER} hard nofile 65536\n"
        r = subprocess.run(
            ["sudo", "-n", "bash", "-c", f"cat > {TEST_LIMITS_FILE} <<'EOF'\n{content}EOF"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"写入 limits 失败: {r.stderr}"

        r = run(["cat", TEST_LIMITS_FILE], use_sudo=True)
        assert "65536" in r.stdout

        r = run(["bash", "-c", "ulimit -n"])
        assert r.returncode == 0

    def teardown_method(self):
        subprocess.run(["sudo", "-n", "rm", "-f", TEST_LIMITS_FILE], capture_output=True)


class TestJdbcDriverAcquisition:
    """install.md 1.3：驱动获取与校验。"""

    def test_assets_dir_creatable(self):
        r = run(["mkdir", "-p", "assets"])
        assert r.returncode == 0
        assert os.path.isdir("assets")

    def test_driver_absent_validation_fails_as_expected(self):
        """无驱动时校验命令应返回非零——证明命令在检测缺失。"""
        jars = [f for f in os.listdir("assets") if f.endswith(".jar")] if os.path.isdir("assets") else []
        assert jars == [], "测试前置：assets 下应无 jar"
        r = run(["bash", "-c", "unzip -l assets/DmJdbcDriver18.jar 2>/dev/null | grep DmDriver.class"])
        assert r.returncode != 0


class TestInstallationPackageAcquisition:
    """install.md 2.3/3：安装包获取渠道探测，如实记录阻塞。"""

    MIRROR_URLS = [
        "https://download.dameng.com/dm8/DM8Install.bin",
        "https://download.dameng.com/eco/dm8/DM8Install.bin",
    ]

    @pytest.mark.parametrize("url", MIRROR_URLS)
    def test_public_mirror_unavailable(self, url):
        req = urllib.request.Request(url, method="HEAD")
        try:
            urllib.request.urlopen(req, timeout=15)
            pytest.fail(f"意外的可下载镜像: {url}")
        except urllib.error.HTTPError as e:
            assert e.code == 404
        except Exception:
            assert True

    def test_full_installation_blocked_without_package(self):
        """无安装包时完整安装被阻塞——预期 skip。"""
        r = run(["bash", "-c", "find / -iname 'DM8Install*.bin' 2>/dev/null | head -1"])
        if not r.stdout.strip():
            pytest.skip("达梦安装包需登录 eco.dameng.com 手动下载，完整安装被阻塞（预期）")
```

- [ ] **Step 3: 运行集成测试**
Run: `python3 -m pytest tests/integration/ -v 2>&1 | tail -20`
Expected:
  - Exit code: 0
  - Output contains: "passed"
  - Output contains: "skipped"（完整安装测试因无安装包跳过）
  - Output does NOT contain: "ERROR"

- [ ] **Step 4: 提交**
Run: `git add tests/integration/ && git commit -m "test(integration): land install guide executability tests with sudo cleanup"`

---

### Task 4: 修正 install.md 三处文档缺陷 — 让指引真正可照做

**Depends on:** None
**Files:**
- Modify: `references/install.md`（1.3 节、2.2 节、追加第 7 节）

- [ ] **Step 1: 修正 1.3 驱动校验命令 — 补充无驱动时的失败提示与 unzip 安装说明**

文件: `references/install.md`（替换「### 1.3 获取 JDBC 驱动」整节，从标题到代码块结束）

```markdown
### 1.3 获取 JDBC 驱动（工具脚本必需）

```bash
# 下载页登录后下载 DmJdbcDriver18.jar，放入项目 assets 目录
mkdir -p assets
cp /path/to/downloaded/DmJdbcDriver18.jar assets/
# 校验文件存在且为有效 jar（成功输出 DmDriver.class 行；无驱动时该命令返回非零，属正常提示缺失）
unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class
```

> 若 `unzip` 未安装：`sudo apt install unzip`（Debian/Ubuntu）或 `sudo yum install unzip`（RHEL/CentOS）。

> 驱动就位后，脚本会在连接前自动 preflight 检查（见 scripts/dm8_common.py 的 preflight 函数），缺失时输出可操作的安装提示而非技术性报错。
```

- [ ] **Step 2: 修正 2.2 limits 配置 — 改为写入独立文件，避免污染主 limits.conf**

文件: `references/install.md`（替换「### 2.2 配置系统参数」整节的代码块）

```bash
# 调整最大文件句柄数（root 执行）——写入独立文件，便于回滚
sudo tee /etc/security/limits.d/dmsa.conf > /dev/null <<'EOF'
dmsa soft nofile 65536
dmsa hard nofile 65536
EOF

# 检查（需重新登录或新会话生效）
su - dmsa -c "ulimit -n"
```

- [ ] **Step 3: 追加第 7 节 — 可执行性测试说明，告知用户如何复现**

文件: `references/install.md`（在「## 6. 常见问题」表格之后追加）

```markdown
## 7. 可执行性测试

本安装指引附自动化测试，验证各步骤命令可执行。运行：

```bash
# 安装测试依赖
pip3 install --user jaydebeapi JPype1 pytest

# 运行安装指引可执行性测试（需 sudo 用于用户/limits 步骤）
python3 -m pytest tests/integration/test_install_guide.py -v
```

测试覆盖范围：

| 测试类 | 覆盖 install.md 章节 | 说明 |
|--------|---------------------|------|
| TestEnvironmentBaseline | 前提条件 | Java/unzip/Python 可用 |
| TestCreateUser | 2.1 | groupadd/useradd/chown 链可执行 |
| TestSystemParams | 2.2 | limits 独立文件可写入 |
| TestJdbcDriverAcquisition | 1.3 | 驱动校验命令在无驱动时正确失败 |
| TestInstallationPackageAcquisition | 2.3/3 | 安装包获取渠道探测（无包时 skip） |

> **阻塞说明**：达梦安装包（`DM8Install.bin`）与 JDBC 驱动（`DmJdbcDriver18.jar`）需登录 [eco.dameng.com](https://eco.dameng.com/download/) 账号手动下载，公开渠道无法自动获取。完整安装测试在无安装包时自动跳过，属预期行为。
```

- [ ] **Step 4: 验证修正后的 install.md 结构完整**
Run: `test $(grep -c '^## ' references/install.md) -ge 7 && grep -q 'limits.d/dmsa.conf' references/install.md && grep -q '可执行性测试' references/install.md && grep -q 'preflight' references/install.md && echo "PASS"`
Expected:
  - Exit code: 0
  - Output contains: "PASS"

- [ ] **Step 5: 提交**
Run: `git add references/install.md && git commit -m "docs(install): fix driver validation hint, isolated limits file, add testability section"`

---

### Task 5: 提交遗留的 Plan 文档 — 补全 git 历史

**Depends on:** None
**Files:**
- Modify: git index（提交两个 untracked 的 Plan 文档）

- [ ] **Step 1: 提交两个遗留的 Plan 文档**
Run: `git add docs/superpowers/plans/2026-07-08-dm-database-skills.md docs/superpowers/plans/2026-07-08-test-install-guide.md docs/superpowers/plans/2026-07-09-fix-install-issues.md && git commit -m "docs(plans): add dm-database-skills, test-install-guide, fix-install-issues plans"`

- [ ] **Step 2: 验证工作区干净**
Run: `git status --short`
Expected:
  - Exit code: 0
  - Output 为空（无 untracked / modified 文件）

---

### Task 6: 全量验证 — 确保所有修复与测试齐备

**Depends on:** Task 1, Task 2, Task 3, Task 4
**Files:**
- 无（仅验证）

- [ ] **Step 1: 运行全量测试（单元 + 集成）**
Run: `python3 -m pytest tests/ -v 2>&1 | tail -25`
Expected:
  - Exit code: 0
  - Output contains: "passed"
  - Output contains: "skipped"（安装包阻塞测试）
  - Output does NOT contain: "FAILED" or "ERROR"

- [ ] **Step 2: 验证脚本真实运行给出可操作提示（端到端）**
Run: `python3 scripts/dm8_connect.py --host 127.0.0.1 --password test123; echo "EXIT=$?"`
Expected:
  - Exit code: 1
  - Output contains: "预检失败"
  - Output contains: "pip install jaydebeapi" 或 "DmJdbcDriver18.jar"

- [ ] **Step 3: 验证脚本 --help 仍正常（无回归）**
Run: `for s in connect tables schema query info; do python3 scripts/dm8_${s}.py --help >/dev/null 2>&1 && echo "OK" || echo "FAIL"; done`
Expected:
  - Exit code: 0
  - Output contains: "OK"（5 次）
  - Output does NOT contain: "FAIL"

- [ ] **Step 4: 提交最终状态（如有残留改动）**
Run: `git add -A && git commit -m "chore: final verification of dm skills fixes" || echo "nothing to commit"`
Expected:
  - Exit code: 0
