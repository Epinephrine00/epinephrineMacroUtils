"""MuMu Player VM 목록과 ADB serial 조회.

MuMuManager.exe 의 ``info -v all`` 출력(JSON)을 읽어서 켜져 있는 VM 의
``adb_host_ip:adb_port`` 를 serial 로 만든다. 표준 라이브러리만 쓴다.

    from mumuManager import get_running_serials
    serials = get_running_serials()            # ['127.0.0.1:16448', ...], adb connect 까지 해 둠

    import uiautomator2 as ua
    devices = [ua.connect(s) for s in serials]

명령줄에서는 ``python mumuManager.py`` 로 표를 보고, ``--json`` 으로 원본을 본다.
``--launch 2`` 로 VM 을 켜고 부팅을 기다릴 수 있고, ``--shutdown 2`` 로 끈다.

MuMuManager.exe 위치는 인자 > 환경변수 ``MUMU_MANAGER`` > 모든 드라이브의 기본 설치 경로 순으로 찾는다.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import string
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

# 설치 경로 후보 (드라이브 문자는 뒤에서 붙인다)
_MANAGER_RELATIVE_PATHS = (
    r"Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe",            # MuMu Player (nx)
    r"Program Files\Netease\MuMu Player 12\shell\MuMuManager.exe",           # MuMu Player 12
    r"Program Files\Netease\MuMuPlayerGlobal-12.0\shell\MuMuManager.exe",    # Global 12
    r"Program Files (x86)\Netease\MuMuPlayer\nx_main\MuMuManager.exe",
    r"Program Files (x86)\Netease\MuMu Player 12\shell\MuMuManager.exe",
)
_ENV_NAME = "MUMU_MANAGER"
_RUN_TIMEOUT = 30


class MuMuManagerNotFound(FileNotFoundError):
    pass


class MuMuManagerError(RuntimeError):
    pass


@dataclass(frozen=True)
class MuMuVM:
    index: str
    name: str
    running: bool                  # 안드로이드까지 부팅이 끝난 상태
    adb_host: Optional[str]
    adb_port: Optional[int]
    state: str                     # player_state (예: start_finished). 꺼져 있으면 ''
    raw: dict

    @property
    def serial(self) -> Optional[str]:
        if self.adb_host and self.adb_port:
            return f"{self.adb_host}:{self.adb_port}"
        return None


# ---------- MuMuManager.exe 찾기 / 실행


def find_manager(path: Optional[str] = None) -> str:
    """MuMuManager.exe 경로를 돌려준다. 못 찾으면 MuMuManagerNotFound."""
    candidates = []
    if path:
        candidates.append(path)
    env = os.environ.get(_ENV_NAME)
    if env:
        candidates.append(env)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
        if os.path.isdir(candidate):
            exe = os.path.join(candidate, "MuMuManager.exe")
            if os.path.isfile(exe):
                return exe
    for drive in string.ascii_uppercase:
        root = f"{drive}:\\"
        if not os.path.exists(root):
            continue
        for relative in _MANAGER_RELATIVE_PATHS:
            exe = os.path.join(root, relative)
            if os.path.isfile(exe):
                return exe
    raise MuMuManagerNotFound(
        "MuMuManager.exe 를 찾지 못했습니다. 경로를 인자로 주거나 환경변수 "
        f"{_ENV_NAME} 에 넣어 주세요."
    )


def _run(args: list[str], timeout: float = _RUN_TIMEOUT) -> str:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired as exc:
        raise MuMuManagerError(f"응답이 없습니다 ({timeout:.0f}초): {' '.join(args)}") from exc
    out = proc.stdout.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip() or out.strip()
        raise MuMuManagerError(f"종료 코드 {proc.returncode}: {err[:300]}")
    return out


def get_mumu_info(manager_path: Optional[str] = None, vmindex: str = "all") -> dict:
    """``MuMuManager.exe info -v <vmindex>`` 를 실행해 ``{index: {...}}`` 로 돌려준다.

    VM 하나만 물으면 MuMuManager 가 바깥 키 없이 평평한 dict 를 주는데, 그 경우에도
    ``{index: {...}}`` 모양으로 맞춘다. VM 이 하나도 없으면 빈 dict.
    """
    exe = find_manager(manager_path)
    out = _run([exe, "info", "-v", str(vmindex)])
    start = out.find("{")
    if start < 0:
        if not out.strip():
            return {}
        raise MuMuManagerError(f"JSON 이 아닙니다: {out.strip()[:200]}")
    try:
        data = json.loads(out[start:])
    except json.JSONDecodeError as exc:
        raise MuMuManagerError(f"JSON 해석 실패: {exc}: {out.strip()[:200]}") from exc
    if not isinstance(data, dict):
        return {}
    if "index" in data and not any(isinstance(v, dict) for v in data.values()):
        return {str(data["index"]): data}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


# ---------- VM 목록 / serial


def list_vms(manager_path: Optional[str] = None) -> list[MuMuVM]:
    """모든 VM. index 순."""
    vms = []
    for index, row in get_mumu_info(manager_path).items():
        port = row.get("adb_port")
        try:
            port = int(port) if port is not None else None
        except (TypeError, ValueError):
            port = None
        running = bool(row.get("is_android_started")) and port is not None
        vms.append(
            MuMuVM(
                index=str(row.get("index", index)),
                name=str(row.get("name", "")),
                running=running,
                adb_host=row.get("adb_host_ip") if running else None,
                adb_port=port if running else None,
                state=str(row.get("player_state") or ""),
                raw=row,
            )
        )
    vms.sort(key=lambda vm: _index_key(vm.index))
    return vms


def get_running_serials(manager_path: Optional[str] = None, connect: bool = True) -> list[str]:
    """켜져 있는 VM 의 serial 목록. ``connect=True`` 면 각 serial 에 ``adb connect`` 도 해 둔다."""
    serials = [vm.serial for vm in list_vms(manager_path) if vm.running and vm.serial]
    if connect:
        adb = find_adb(manager_path)
        if adb:
            for serial in serials:
                adb_connect(serial, adb)
    return serials


def find_adb(manager_path: Optional[str] = None) -> Optional[str]:
    """PATH 의 adb, 없으면 MuMu 가 들고 있는 adb.exe."""
    found = shutil.which("adb")
    if found:
        return found
    try:
        folder = os.path.dirname(find_manager(manager_path))
    except MuMuManagerNotFound:
        return None
    for name in ("adb.exe", "adb"):
        exe = os.path.join(folder, name)
        if os.path.isfile(exe):
            return exe
    return None


def adb_connect(serial: str, adb: Optional[str] = None, timeout: float = 10) -> bool:
    """``adb connect <serial>``. 이미 붙어 있어도 True."""
    adb = adb or find_adb()
    if not adb:
        return False
    try:
        out = _run([adb, "connect", serial], timeout=timeout)
    except MuMuManagerError:
        return False
    return "connected" in out.lower()


def control(action: str, vmindex: str, manager_path: Optional[str] = None, timeout: float = 60) -> str:
    """``MuMuManager.exe control -v <vmindex> <action>`` (launch / shutdown / restart / show_window / hide_window ...)."""
    exe = find_manager(manager_path)
    return _run([exe, "control", "-v", str(vmindex), action], timeout=timeout)


def launch_vm(vmindex: str, manager_path: Optional[str] = None, wait: float = 180, connect: bool = True) -> Optional[str]:
    """VM 을 켜고, ``wait`` 초 안에 안드로이드가 부팅되면 serial 을 돌려준다. 시간 안에 못 켜지면 None."""
    import time

    control("launch", vmindex, manager_path)
    deadline = time.time() + wait
    while time.time() < deadline:
        for vm in list_vms(manager_path):
            if vm.index == str(vmindex) and vm.running and vm.serial:
                if connect:
                    adb = find_adb(manager_path)
                    if adb:
                        adb_connect(vm.serial, adb)
                return vm.serial
        time.sleep(2)
    return None


def shutdown_vm(vmindex: str, manager_path: Optional[str] = None) -> None:
    control("shutdown", vmindex, manager_path)


def _index_key(index: str):
    try:
        return (0, int(index))
    except ValueError:
        return (1, index)


# ---------- 명령줄


def _main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="켜져 있는 MuMu VM 의 adb serial 을 보여 준다.")
    parser.add_argument("--manager", "-m", default=None, help="MuMuManager.exe 경로 (기본: 자동 탐색)")
    parser.add_argument("--all", "-a", action="store_true", help="꺼진 VM 도 표에 넣는다")
    parser.add_argument("--json", action="store_true", help="MuMuManager info 원본 JSON 출력")
    parser.add_argument("--serials", action="store_true", help="serial 만 한 줄에 하나씩 출력 (스크립트용)")
    parser.add_argument("--no-connect", action="store_true", help="adb connect 를 하지 않는다")
    parser.add_argument("--launch", metavar="IDX", default=None, help="이 VM(들)을 켜고 부팅될 때까지 기다린다 (예: 2 또는 1,2)")
    parser.add_argument("--shutdown", metavar="IDX", default=None, help="이 VM(들)을 끈다 (예: 2 또는 all)")
    args = parser.parse_args(argv)

    try:
        if args.shutdown:
            shutdown_vm(args.shutdown, args.manager)
        if args.launch:
            for index in str(args.launch).split(","):
                serial = launch_vm(index.strip(), args.manager, connect=not args.no_connect)
                print(f"VM {index.strip()}: {serial or '시간 안에 켜지지 않음'}")
        if args.json:
            print(json.dumps(get_mumu_info(args.manager), ensure_ascii=False, indent=2))
            return 0
        vms = list_vms(args.manager)
    except (MuMuManagerNotFound, MuMuManagerError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2

    running = [vm for vm in vms if vm.running and vm.serial]
    if not args.no_connect and running:
        adb = find_adb(args.manager)
        if adb:
            for vm in running:
                adb_connect(vm.serial, adb)

    if args.serials:
        for vm in running:
            print(vm.serial)
        return 0 if running else 1

    rows = vms if args.all else running
    if not rows:
        print("켜져 있는 VM 이 없습니다." if not args.all else "VM 이 없습니다.")
        return 1
    width = max(len(vm.name) for vm in rows)
    print(f"{'idx':>3}  {'name':<{width}}  {'serial':<22}  state")
    for vm in rows:
        print(f"{vm.index:>3}  {vm.name:<{width}}  {vm.serial or '-':<22}  {vm.state or 'stopped'}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
