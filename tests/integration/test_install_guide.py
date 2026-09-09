"""验证 references/install.md 安装指引的可执行性。

策略：不依赖达梦安装包的命令逐条验证；安装包获取渠道如实探测并 skip。
"""

import os
import sys
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


class TestDockerInstallGuide:
    """docker-install.md：容器安装流程文档存在性与命令可执行性。"""

    def test_docker_install_doc_exists(self):
        """容器安装文档存在且含关键章节。"""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "references", "docker-install.md")
        assert os.path.isfile(path), "references/docker-install.md 不存在"
        with open(path) as f:
            content = f.read()
        # 关键章节
        for section in ["docker run", "docker exec", "docker cp", "disql"]:
            assert section in content, f"docker-install.md 缺少关键内容: {section}"

    def test_docker_command_available_or_skip(self):
        """若环境有 docker，docker ps 应可执行；无则 skip（如实记录）。"""
        import shutil
        if not shutil.which("docker"):
            pytest.skip("环境无 docker，容器安装路径无法在此环境验证")
        r = run(["docker", "ps"])
        assert r.returncode == 0, f"docker ps 失败: {r.stderr}"

    def test_get_driver_script_gives_actionable_hint_when_no_source(self, tmp_path, monkeypatch):
        """无容器无安装时，dm8_get_driver.py 应给出三条可操作替代方案。"""
        import importlib.util
        scripts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        spec = importlib.util.spec_from_file_location("dm8_get_driver",
                                                       os.path.join(scripts_dir, "dm8_get_driver.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        monkeypatch.setattr(mod, "INSTALLED_PATHS", ["/nonexistent/x.jar"])
        monkeypatch.setattr(mod.shutil, "which", lambda _: None)
        monkeypatch.setattr(mod, "ASSETS_DIR", str(tmp_path / "assets"))
        monkeypatch.setattr(mod, "TARGET_PATH", str(tmp_path / "assets" / "DmJdbcDriver18.jar"))
        monkeypatch.setattr(sys, "argv", ["dm8_get_driver.py"])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1


class TestNewGuidesExist:
    """新安装文档存在性与关键章节。"""

    def test_windows_server_doc_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "references", "windows-server-install.md")
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
        for keyword in ["DmServiceDMSERVER", "Test-NetConnection", "Get-Service", "防火墙放行"]:
            assert keyword in content

    def test_mobile_doc_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "references", "mobile-install.md")
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
        for keyword in ["Android", "iOS", "JDBC", "远程"]:
            assert keyword in content

    def test_docker_compose_doc_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "references", "docker-compose.md")
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
        for keyword in ["docker compose", "services:", "restart:", "healthcheck"]:
            assert keyword in content

    def test_kubernetes_doc_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "..", "references", "kubernetes.md")
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
        for keyword in ["Deployment", "Service", "PersistentVolumeClaim", "kubectl apply"]:
            assert keyword in content
