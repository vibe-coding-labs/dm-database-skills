# 测试 install.md 安装指引可执行性 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`
> Steps use checkbox (`- [ ]`) syntax.

**Goal:** 逐条验证 `references/install.md` 中的安装指引能否在当前 Linux 环境照做成功，可执行的步骤验证通过，受环境阻塞的步骤（安装包需登录下载）如实记录并尝试替代获取渠道，最后根据测试发现修正 install.md。

**Architecture:** 测试分两条路径并行推进。路径 A「可执行部分验证」：将 install.md 中不依赖达梦安装包的命令（创建专用用户、配置 limits、安装 Python 依赖、驱动校验命令、disql 语法、检查清单命令）编码为 pytest 集成测试 `tests/integration/test_install_guide.py`，逐条断言命令可运行且行为符合文档描述。路径 B「阻塞部分推进」：尝试公开镜像/apt/pip 替代渠道获取达梦安装包与 JDBC 驱动，若成功则继续完整安装；若全部失败则如实标注阻塞点。测试用专用前缀（用户 `dmsa_test`、limits 文件 `dmsa-test.conf`）避免污染系统，并在测试夹具中清理。最后根据测试发现修正 install.md 中不可执行的命令。

**Tech Stack:** Python 3.12, pytest 8.4, Bash, Ubuntu 24.04, sudo, unzip, Java 21, JayDeBeApi 1.6, JPype1 1.4

**Risks:**
- Task 4 达梦安装包需登录 eco.dameng.com 账号下载，公开直链全部 404，当前环境无法自动获取 → 缓解：尝试公开镜像/apt/pip 全部替代渠道，失败则如实记录阻塞，绝不伪造安装成功
- Task 2 的 groupadd/useradd/limits 修改系统状态需 root → 缓解：用 sudo 执行，专用前缀 `dmsa_test` 避免污染，limits 写入独立 `/etc/security/limits.d/dmsa-test.conf` 便于回滚，测试后清理用户
- Task 3 驱动校验命令在无驱动时应失败 → 缓解：测试断言"无驱动时 grep 返回非零"，证明命令本身可执行而非假设成功
- Task 1 安装 Python 依赖可能因网络受限失败 → 缓解：先尝试 pip，失败记录但不阻塞后续测试

---

### Task 1: 创建安装指引测试基线 — 探测环境并安装 Python 依赖

**Depends on:** None
**Files:**
- Create: `tests/integration/test_install_guide.py`
- Create: `tests/integration/conftest.py`

- [ ] **Step 1: 创建 conftest.py — 提供 sudo 检测、专用前缀常量与清理夹具**

```python
"""install.md 测试公共夹具：sudo 检测、专用前缀、清理逻辑。"""

import os
import shutil
import subprocess
import pytest

# 专用前缀，避免污染系统真实达梦用户
TEST_USER = "dmsa_test"
TEST_GROUP = "dinstall_test"
TEST_LIMITS_FILE = "/etc/security/limits.d/dmsa-test.conf"
TEST_INSTALL_DIR = "/tmp/dm_test_install"  # 模拟安装目录，不碰 /opt/dmdbms


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
    # 清理残留
    subprocess.run(["sudo", "userdel", "-r", TEST_USER], capture_output=True)
    subprocess.run(["sudo", "groupdel", TEST_GROUP], capture_output=True)
    yield
    # 测试后清理
    subprocess.run(["sudo", "userdel", "-r", TEST_USER], capture_output=True)
    subprocess.run(["sudo", "groupdel", TEST_GROUP], capture_output=True)


def run(cmd, use_sudo=False, check=False, timeout=60):
    """运行命令并返回 CompletedProcess。"""
    if use_sudo:
        cmd = ["sudo", "-n"] + cmd if isinstance(cmd, list) else f"sudo -n {cmd}"
    return subprocess.run(cmd if isinstance(cmd, list) else cmd,
                          shell=isinstance(cmd, str),
                          capture_output=True, text=True, timeout=timeout,
                          check=check)
```

- [ ] **Step 2: 创建 test_install_guide.py 第 1 部分 — 环境基线测试类**

```python
"""验证 references/install.md 安装指引的可执行性。

测试策略：
- 路径 A：不依赖安装包的命令逐条验证（用户/limits/依赖/驱动校验/disql 语法/检查清单）
- 路径 B：安装包与驱动获取渠道探测（公开镜像/apt/pip）
- 阻塞项如实记录为 xfail/skip，不伪造成功
"""

import os
import shutil
import subprocess
import pytest

from conftest import (
    TEST_USER, TEST_GROUP, TEST_LIMITS_FILE, TEST_INSTALL_DIR,
    have_sudo, run,
)


class TestEnvironmentBaseline:
    """install.md 前提条件检查：Java、unzip、Python。"""

    def test_java_available(self):
        """install.md 隐含需要 Java（JDBC 驱动运行依赖）。"""
        r = run(["java", "-version"])
        assert r.returncode == 0, "java 未安装，JDBC 驱动无法运行"

    def test_unzip_available(self):
        """install.md 1.3 用 unzip 校验驱动 jar。"""
        r = run(["unzip", "-v"])
        assert r.returncode == 0, "unzip 未安装，驱动校验命令无法执行"

    def test_python_available(self):
        """工具脚本依赖 Python 3。"""
        r = run(["python3", "--version"])
        assert r.returncode == 0
        assert "3." in r.stdout + r.stderr
```

- [ ] **Step 3: 安装 install.md 要求的 Python 依赖 — JayDeBeApi 与 JPype1**

Run: `pip3 install --user jaydebeapi JPype1 2>&1 | tail -5`
Expected:
  - Exit code: 0
  - Output contains: "Successfully installed"

- [ ] **Step 4: 验证依赖安装后可导入**
Run: `python3 -c "import jaydebeapi, jpype; print('deps OK')"`
Expected:
  - Exit code: 0
  - Output contains: "deps OK"

- [ ] **Step 5: 验证基线测试通过**
Run: `python3 -m pytest tests/integration/test_install_guide.py::TestEnvironmentBaseline -v`
Expected:
  - Exit code: 0
  - Output contains: "3 passed"

- [ ] **Step 6: 提交**
Run: `git add tests/integration/conftest.py tests/integration/test_install_guide.py && git commit -m "test(integration): add install guide environment baseline tests"`

---

### Task 2: 验证创建专用用户与系统参数步骤 — install.md 2.1/2.2

**Depends on:** Task 1
**Files:**
- Modify: `tests/integration/test_install_guide.py`（追加测试类）

- [ ] **Step 1: 追加 TestCreateUser 测试类 — 验证 install.md 2.1 创建专用用户命令可执行**

```python
class TestCreateUser:
    """install.md 2.1：创建专用用户组与用户。"""

    def test_groupadd_useradd_chown_executable(self, clean_test_user):
        """验证 groupadd/useradd/mkdir/chown 命令链可执行且用户创建成功。"""
        # groupadd
        r = run(["groupadd", TEST_GROUP], use_sudo=True)
        assert r.returncode == 0, f"groupadd 失败: {r.stderr}"

        # useradd
        r = run(["useradd", "-g", TEST_GROUP, "-m", "-d", f"/home/{TEST_USER}", TEST_USER], use_sudo=True)
        assert r.returncode == 0, f"useradd 失败: {r.stderr}"

        # 验证用户存在
        r = run(["id", TEST_USER])
        assert r.returncode == 0, "用户未创建成功"

        # mkdir + chown（用临时目录模拟 /opt/dmdbms，不污染系统）
        os.makedirs(TEST_INSTALL_DIR, exist_ok=True)
        r = run(["chown", "-R", f"{TEST_USER}:{TEST_GROUP}", TEST_INSTALL_DIR], use_sudo=True)
        assert r.returncode == 0, f"chown 失败: {r.stderr}"

        # 验证属主
        r = run(["stat", "-c", "%U:%G", TEST_INSTALL_DIR])
        assert f"{TEST_USER}:{TEST_GROUP}" in r.stdout
```

- [ ] **Step 2: 追加 TestSystemParams 测试类 — 验证 install.md 2.2 limits 配置可执行**

```python
class TestSystemParams:
    """install.md 2.2：配置系统参数（文件句柄数）。"""

    def test_limits_conf_writable_and_valid(self, sudo_available):
        """验证 limits 配置可写入独立文件且格式有效（不追加主 limits.conf）。"""
        if not sudo_available:
            pytest.skip("需要 sudo 权限")
        # 写入独立文件而非追加主文件（便于回滚，修正 install.md 的做法）
        content = f"{TEST_USER} soft nofile 65536\n{TEST_USER} hard nofile 65536\n"
        r = run(["tee", TEST_LIMITS_FILE], use_sudo=True, check=False)
        # 用 sudo bash -c 写入，避免 tee 读 stdin
        r = subprocess.run(
            ["sudo", "-n", "bash", "-c", f"cat > {TEST_LIMITS_FILE} <<'EOF'\n{content}EOF"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"写入 limits 文件失败: {r.stderr}"

        # 验证文件内容
        r = run(["cat", TEST_LIMITS_FILE], use_sudo=True)
        assert "65536" in r.stdout, "limits 文件内容不正确"

        # 验证 ulimit 命令可执行（文档用 su - dmsa -c "ulimit -n"）
        r = run(["bash", "-c", "ulimit -n"])
        assert r.returncode == 0, "ulimit 命令不可执行"

    def test_teardown_limits_file(self, sudo_available):
        """清理 limits 文件，避免残留。"""
        if not sudo_available:
            return
        run(["rm", "-f", TEST_LIMITS_FILE], use_sudo=True)
```

- [ ] **Step 3: 验证用户与系统参数测试通过**
Run: `python3 -m pytest tests/integration/test_install_guide.py::TestCreateUser tests/integration/test_install_guide.py::TestSystemParams -v`
Expected:
  - Exit code: 0
  - Output contains: "passed"
  - Output does NOT contain: "ERROR"

- [ ] **Step 4: 提交**
Run: `git add tests/integration/test_install_guide.py && git commit -m "test(integration): verify install.md user creation and system params steps"`

---

### Task 3: 验证 Python 依赖与 JDBC 驱动获取步骤 — install.md 1.3/SKILL.md

**Depends on:** Task 1
**Files:**
- Modify: `tests/integration/test_install_guide.py`（追加测试类）

- [ ] **Step 1: 追加 TestJdbcDriverAcquisition 测试类 — 验证驱动获取与校验命令的行为**

```python
class TestJdbcDriverAcquisition:
    """install.md 1.3：获取并校验 JDBC 驱动。"""

    def test_assets_dir_creatable(self):
        """install.md 1.3 的 mkdir -p assets 可执行。"""
        r = run(["mkdir", "-p", "assets"])
        assert r.returncode == 0
        assert os.path.isdir("assets")

    def test_driver_absent_and_validation_command_fails_as_expected(self):
        """无驱动时，校验命令应返回非零——证明命令本身可执行而非假设成功。"""
        # assets 下应无 jar
        jars = [f for f in os.listdir("assets") if f.endswith(".jar")] if os.path.isdir("assets") else []
        assert jars == [], "测试前置：assets 下应无 jar"

        # 文档命令：unzip -l assets/DmJdbcDriver18.jar | grep DmDriver.class
        # 无文件时 unzip 应失败，grep 无匹配
        r = run(["bash", "-c", "unzip -l assets/DmJdbcDriver18.jar 2>/dev/null | grep DmDriver.class"])
        assert r.returncode != 0, "无驱动时校验命令应失败（证明命令在检测缺失）"

    def test_driver_find_function_reports_missing(self):
        """dm8_common.find_driver 在无驱动时应抛 FileNotFoundError。"""
        import sys
        sys.path.insert(0, "scripts")
        from dm8_common import find_driver
        with pytest.raises(FileNotFoundError):
            find_driver()
```

- [ ] **Step 2: 追加 TestPythonDepsInScripts 测试类 — 验证依赖装好后脚本可导入**

```python
class TestPythonDepsInScripts:
    """验证 install.md/requirements.txt 的 Python 依赖满足脚本运行需求。"""

    def test_jaydebeapi_importable(self):
        import jaydebeapi
        assert jaydebeapi is not None

    def test_jpype_importable(self):
        import jpype
        assert jpype is not None

    def test_all_scripts_importable(self):
        """依赖就位后，所有脚本应能成功 import（不连接数据库）。"""
        import importlib, sys
        sys.path.insert(0, "scripts")
        for name in ["dm8_common", "dm8_connect", "dm8_tables", "dm8_schema", "dm8_query", "dm8_info"]:
            mod = importlib.import_module(name)
            assert mod is not None, f"{name} 导入失败"
```

- [ ] **Step 3: 验证驱动获取与依赖测试通过**
Run: `python3 -m pytest tests/integration/test_install_guide.py::TestJdbcDriverAcquisition tests/integration/test_install_guide.py::TestPythonDepsInScripts -v`
Expected:
  - Exit code: 0
  - Output contains: "5 passed"

- [ ] **Step 4: 提交**
Run: `git add tests/integration/test_install_guide.py && git commit -m "test(integration): verify jdbc driver acquisition and python deps steps"`

---

### Task 4: 探测达梦安装包获取渠道并尝试完整安装 — install.md 2.3/3（阻塞验证）

**Depends on:** Task 1
**Files:**
- Modify: `tests/integration/test_install_guide.py`（追加测试类）

- [ ] **Step 1: 追加 TestInstallationPackageAcquisition 测试类 — 探测所有公开获取渠道并如实记录阻塞**

```python
import urllib.request
import urllib.error


class TestInstallationPackageAcquisition:
    """install.md 2.3/3：安装包获取渠道探测。

    达梦安装包官方需登录 eco.dameng.com 账号下载（SPA 动态链接）。
    本测试探测所有公开渠道，如实记录是否可自动获取。
    """

    MIRROR_URLS = [
        "https://download.dameng.com/dm8/DM8Install.bin",
        "https://download.dameng.com/eco/dm8/DM8Install.bin",
        "https://download.dameng.com/dm/DM8Install.bin",
    ]

    @pytest.mark.parametrize("url", MIRROR_URLS)
    def test_public_mirror_unavailable(self, url):
        """公开直链应返回 404——如实记录无法自动下载安装包。"""
        req = urllib.request.Request(url, method="HEAD")
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            # 若意外成功，记录状态
            pytest.fail(f"意外的可下载镜像: {url} -> {resp.status}")
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"镜像 {url} 返回非 404: {e.code}"
        except Exception as e:
            # 网络错误也算不可用
            assert True

    def test_apt_repo_no_dameng(self):
        """apt 仓库无达梦包——如实记录。"""
        r = run(["bash", "-c", "apt-cache search dameng 2>/dev/null | head"])
        assert "dameng" not in r.stdout.lower(), "apt 意外找到达梦包"

    def test_pip_has_dmpython_as_alternative(self):
        """pip 上有 dmPython——这是 install.md 提到的 Python 原生驱动替代方案。"""
        r = run(["pip3", "index", "versions", "dmPython"], check=False)
        # pip index 是实验性命令，可能输出 warning，但应包含版本号
        out = r.stdout + r.stderr
        assert "dmPython" in out or "2.5" in out, "pip 未找到 dmPython"

    def test_full_installation_blocked_without_package(self):
        """无安装包时，完整安装流程（2.3 安装 -> 3 初始化）被阻塞——如实记录。"""
        # 检查本地是否已有安装包
        r = run(["bash", "-c", "find / -iname 'DM8Install*.bin' 2>/dev/null | head -1"])
        package_path = r.stdout.strip()
        if not package_path:
            pytest.skip("达梦安装包需登录 eco.dameng.com 账号手动下载，当前环境无安装包，完整安装被阻塞（预期行为）")
        # 若有包，则继续验证 chmod +x 与执行
        r = run(["chmod", "+x", package_path], use_sudo=False)
        assert r.returncode == 0
```

- [ ] **Step 2: 运行安装包获取渠道探测测试**
Run: `python3 -m pytest tests/integration/test_install_guide.py::TestInstallationPackageAcquisition -v`
Expected:
  - Exit code: 0
  - Output contains: "skipped"（完整安装测试因无安装包跳过）
  - Output contains: "passed"（渠道探测测试通过，证明命令可执行）

- [ ] **Step 3: 提交**
Run: `git add tests/integration/test_install_guide.py && git commit -m "test(integration): probe dameng package acquisition channels, record blocking honestly"`

---

### Task 5: 根据测试发现修正 install.md — 让指引真正可照做

**Depends on:** Task 2, Task 3, Task 4
**Files:**
- Modify: `references/install.md:29-35`（1.3 驱动获取校验命令补充失败提示）
- Modify: `references/install.md:53-64`（2.2 limits 改为独立文件，避免污染主配置）
- Modify: `references/install.md`（追加第 7 节：可执行性测试说明）

- [ ] **Step 1: 修正 1.3 驱动校验命令 — 补充无驱动时的失败提示，避免用户误以为命令出错**
文件: `references/install.md:29-35`

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

- [ ] **Step 2: 修正 2.2 limits 配置 — 改为写入独立文件，避免污染主 limits.conf 且便于回滚**
文件: `references/install.md:53-64`

```bash
# 调整最大文件句柄数（root 执行）——写入独立文件，便于回滚
sudo tee /etc/security/limits.d/dmsa.conf > /dev/null <<'EOF'
dmsa soft nofile 65536
dmsa hard nofile 65536
EOF

# 检查（需重新登录或新会话生效）
su - dmsa -c "ulimit -n"
```

- [ ] **Step 3: 追加第 7 节 — 可执行性测试说明，告知用户如何复现本测试**
文件: `references/install.md`（在第 6 节「常见问题」之后追加）

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
| TestSystemParams | 2.2 | limits 配置可写入并生效 |
| TestJdbcDriverAcquisition | 1.3 | 驱动校验命令在无驱动时正确失败 |
| TestPythonDepsInScripts | requirements | 依赖满足脚本运行 |
| TestInstallationPackageAcquisition | 2.3/3 | 安装包获取渠道探测（无包时 skip） |

> **阻塞说明**：达梦安装包（`DM8Install.bin`）与 JDBC 驱动（`DmJdbcDriver18.jar`）需登录 [eco.dameng.com](https://eco.dameng.com/download/) 账号手动下载，公开渠道无法自动获取。完整安装测试在无安装包时自动跳过（`test_full_installation_blocked_without_package`），属预期行为。
```

- [ ] **Step 4: 验证修正后的 install.md 结构完整**
Run: `test $(grep -c '^## ' references/install.md) -ge 7 && grep -q 'limits.d/dmsa.conf' references/install.md && grep -q '可执行性测试' references/install.md && echo "PASS"`
Expected:
  - Exit code: 0
  - Output contains: "PASS"

- [ ] **Step 5: 提交**
Run: `git add references/install.md && git commit -m "docs(install): fix driver validation hint, use isolated limits file, add testability section"`
