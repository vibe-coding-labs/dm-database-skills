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
