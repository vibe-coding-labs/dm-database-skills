#!/usr/bin/env python3
"""自动获取达梦 JDBC 驱动 DmJdbcDriver18.jar。

三种获取方式，按优先级尝试：
1. 已安装的达梦目录（/opt/dmdbms/drivers/jdbc/）
2. 运行中的达梦 Docker 容器（docker cp 拷出）
3. 提示从官方下载

成功后将驱动放入 assets/ 目录并输出 JSON。
"""

import argparse
import os
import shutil
import subprocess
import sys

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
DRIVER_NAME = "DmJdbcDriver18.jar"
TARGET_PATH = os.path.join(ASSETS_DIR, DRIVER_NAME)

# 已安装达梦的可能路径
INSTALLED_PATHS = [
    "/opt/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
    "/usr/local/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
    os.path.join(os.environ.get("DM_HOME", ""), "drivers", "jdbc", "DmJdbcDriver18.jar"),
]

# Docker 镜像内可能路径
CONTAINER_DRIVER_PATHS = [
    "/opt/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
    "/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
]


def output_json(success, data=None, message=""):
    import json
    print(json.dumps({"success": success, "data": data, "message": message}, ensure_ascii=False, indent=2))
    sys.exit(0 if success else 1)


def find_from_installed():
    """从已安装达梦目录查找驱动。"""
    for p in INSTALLED_PATHS:
        if p and os.path.isfile(p):
            return p
    return None


def find_running_dm_container():
    """查找运行中的达梦容器，返回容器名列表。"""
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return []
        containers = []
        for line in r.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                name, image = parts
                if any(kw in image.lower() for kw in ["dm", "dameng", "dmdb"]):
                    containers.append(name)
        return containers
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def copy_from_container(container_name):
    """从容器内拷出驱动，返回拷出的临时路径或 None。"""
    for cp_path in CONTAINER_DRIVER_PATHS:
        # 先确认容器内该路径存在
        check = subprocess.run(
            ["docker", "exec", container_name, "test", "-f", cp_path],
            capture_output=True, timeout=15,
        )
        if check.returncode == 0:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            cp = subprocess.run(
                ["docker", "cp", f"{container_name}:{cp_path}", TARGET_PATH],
                capture_output=True, text=True, timeout=60,
            )
            if cp.returncode == 0 and os.path.isfile(TARGET_PATH):
                return TARGET_PATH
    return None


def validate_jar(path):
    """校验 jar 是否含 DmDriver.class。"""
    r = subprocess.run(
        ["unzip", "-l", path], capture_output=True, text=True, timeout=15,
    )
    return r.returncode == 0 and "DmDriver.class" in r.stdout


def main():
    parser = argparse.ArgumentParser(description="自动获取达梦 JDBC 驱动到 assets/ 目录")
    parser.add_argument("--container", default=None, help="指定容器名（不指定则自动探测）")
    args = parser.parse_args()

    # 方式1：已安装目录
    installed = find_from_installed()
    if installed:
        os.makedirs(ASSETS_DIR, exist_ok=True)
        shutil.copy2(installed, TARGET_PATH)
        if validate_jar(TARGET_PATH):
            output_json(True, data={"path": TARGET_PATH, "source": "installed"},
                        message=f"从已安装目录复制驱动成功: {installed}")
        else:
            output_json(False, message=f"复制成功但校验失败（非有效 jar）: {TARGET_PATH}")

    # 方式2：Docker 容器（无 docker 命令则跳过此方式，进入方式3）
    if shutil.which("docker"):
        containers = [args.container] if args.container else find_running_dm_container()
        for name in containers:
            result = copy_from_container(name)
            if result and validate_jar(result):
                output_json(True, data={"path": result, "source": f"container:{name}"},
                            message=f"从容器 {name} 拷出驱动成功")

    # 方式3：提示手动下载
    output_json(
        False,
        message=(
            "未找到 JDBC 驱动。请任选：\n"
            "1. 启动达梦容器后重新运行本脚本（docker run ... chillzhuang/dm）\n"
            "2. 安装达梦客户端到 /opt/dmdbms\n"
            "3. 登录 https://eco.dameng.com/download/ 手动下载 DmJdbcDriver18.jar 放入 assets/"
        ),
    )


if __name__ == "__main__":
    main()
