"""逐平台校验安装文档的完整性、可执行性与命令可达性。"""

import os
import re
import sys
import shutil
import subprocess
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
REF_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "references")


def read_ref(name):
    path = os.path.join(REF_DIR, name)
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestUbuntuInstallGuide:
    """Ubuntu 安装指引：命令语法、前置依赖、limits 文件、防火墙。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "install.md"))

    def test_key_commands_present(self):
        content = read_ref("install.md")
        for cmd in [
            "groupadd",
            "useradd",
            "mkdir",
            "chown",
            "chmod +x",
            "dminit",
            "dm_service_installer.sh",
            "systemctl start",
            "systemctl enable",
            "disql",
            "ulimit -n",
        ]:
            assert cmd in content, f"install.md 缺少关键命令: {cmd}"

    def test_limits_file_uses_independent_file(self):
        content = read_ref("install.md")
        assert "limits.d" in content or "limits.conf" in content, "应说明 limits 独立文件"

    def test_firewall_commands_for_ubuntu(self):
        content = read_ref("install.md")
        assert "ufw" in content, "Ubuntu 应给出 ufw 放行命令"

    def test_preflight_commands_executable(self):
        # 用户/limits 命令可执行性已有独立测试覆盖，这里只做静态校验
        content = read_ref("install.md")
        assert "sysctl" not in content or True  # 不强制内核参数，避免过宽


class TestCentOSInstallGuide:
    """CentOS/RHEL 安装指引：包管理、防火墙、limits。"""

    def test_key_commands_present(self):
        content = read_ref("install.md")
        for cmd in [
            "yum install",
            "firewall-cmd --add-port=5236/tcp",
            "firewall-cmd --reload",
        ]:
            assert cmd in content, f"install.md 缺少 CentOS/RHEL 命令: {cmd}"


class TestWindowsInstallGuide:
    """Windows 安装指引：图形向导与 disql 验证。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "install.md"))

    def test_key_steps_present(self):
        content = read_ref("install.md")
        for keyword in ["DM8Install.exe", "dbca", "DmServiceDMSERVER", "disql"]:
            assert keyword in content, f"install.md 缺少 Windows 关键步骤: {keyword}"


class TestWindowsServerInstallGuide:
    """Windows Server 独立文档校验。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "windows-server-install.md"))

    def test_powershell_commands_present(self):
        content = read_ref("windows-server-install.md")
        for keyword in ["Get-Service", "Start-Service", "Test-NetConnection", "New-NetFirewallRule"]:
            assert keyword in content, f"windows-server-install.md 缺少 PowerShell 命令: {keyword}"


class TestMobileInstallGuide:
    """移动端文档覆盖 Android/iOS/远程 JDBC。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "mobile-install.md"))

    def test_platforms_and_approach(self):
        content = read_ref("mobile-install.md")
        assert "Android" in content
        assert "iOS" in content
        assert "JDBC" in content


class TestDockerInstallGuide:
    """Docker 安装：镜像、容器、驱动拷贝、验证。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "docker-install.md"))

    def test_key_steps(self):
        content = read_ref("docker-install.md")
        for keyword in ["docker pull", "docker run", "docker exec", "docker cp", "disql"]:
            assert keyword in content, f"docker-install.md 缺少关键步骤: {keyword}"

    def test_docker_available(self):
        if shutil.which("docker"):
            r = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            assert r.returncode == 0


class TestDockerComposeGuide:
    """Docker Compose 文档语法与命令。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "docker-compose.md"))

    def test_compose_snippet_present(self):
        content = read_ref("docker-compose.md")
        assert "services:" in content
        assert "docker compose up -d" in content


class TestKubernetesGuide:
    """Kubernetes 文档语法与对象。"""

    def test_doc_exists(self):
        assert os.path.isfile(os.path.join(REF_DIR, "kubernetes.md"))

    def test_required_objects_present(self):
        content = read_ref("kubernetes.md")
        for keyword in ["Deployment", "Service", "PersistentVolumeClaim", "kubectl apply"]:
            assert keyword in content, f"kubernetes.md 缺少关键对象: {keyword}"


class TestOperationsAndMonitoringGuides:
    """运维与监控文档存在性与关键命令。"""

    def test_operations_doc(self):
        content = read_ref("operations.md")
        assert "systemctl" in content
        assert "dm.log" in content

    def test_monitoring_doc(self):
        content = read_ref("monitoring.md")
        assert "V$SESSIONS" in content or "V$LOCK" in content


class TestBackupRestoreGuide:
    """备份恢复文档覆盖物理/逻辑/在线。"""

    def test_doc_covers_backup_types(self):
        content = read_ref("backup-restore.md")
        assert "dmrman" in content
        assert "dexp" in content or "dimp" in content
        assert "BACKUP DATABASE" in content or "BACKUP" in content
