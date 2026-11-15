#!/usr/bin/env python3
"""true"
# ===================================================================================
#  uYaST - universal YaST-style system administration TUI
#  This first block is POSIX shell. It only runs when the file is started with
#  "sh uyast.py" (Linux, macOS, BSD, illumos): it installs Python 3.8+ if needed
#  and then re-runs this same file with Python. Python itself treats this block as
#  a string and skips it.
# ===================================================================================
UYAST_FILE="$0"
find_python() {
    for p in python3 python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python \
             /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/pkg/bin/python3.12 /usr/pkg/bin/python3.11 \
             /usr/pkg/bin/python3.10 /opt/local/bin/python3 /usr/bin/python3; do
        if command -v "$p" >/dev/null 2>&1; then
            if [ "$(uname -s)" = "Darwin" ] && [ "$(command -v "$p")" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then
                continue
            fi
            if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
                command -v "$p"
                return 0
            fi
        fi
    done
    return 1
}
if PY=$(find_python); then exec "$PY" "$UYAST_FILE" "$@"; fi

echo "uYaST: Python 3.8 or newer was not found - installing it first ..."
if [ "$(id -u)" = "0" ]; then AS=""; elif command -v sudo >/dev/null 2>&1; then AS="sudo";
elif command -v doas >/dev/null 2>&1; then AS="doas"; else AS="su"; fi
asroot() {
    echo "  # $*"
    if [ "$AS" = "su" ]; then su root -c "$*"; else $AS "$@"; fi
}
case "$(uname -s)" in
  Linux)
    if command -v apt-get >/dev/null 2>&1; then asroot apt-get update; asroot env DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf >/dev/null 2>&1; then asroot dnf install -y python3 python3-pip
    elif command -v yum >/dev/null 2>&1; then asroot yum install -y python3 python3-pip
    elif command -v zypper >/dev/null 2>&1; then asroot zypper --non-interactive install python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then asroot pacman -Syu --needed --noconfirm python python-pip
    elif command -v apk >/dev/null 2>&1; then asroot apk add python3 py3-pip
    elif command -v xbps-install >/dev/null 2>&1; then asroot xbps-install -Sy python3 python3-pip
    elif command -v emerge >/dev/null 2>&1; then asroot emerge --ask=n dev-lang/python
    elif command -v eopkg >/dev/null 2>&1; then asroot eopkg it -y python3
    elif command -v urpmi >/dev/null 2>&1; then asroot urpmi --auto python3
    elif command -v slackpkg >/dev/null 2>&1; then asroot slackpkg -batch=on -default_answer=y install python3
    elif command -v swupd >/dev/null 2>&1; then asroot swupd bundle-add python3-basic
    elif command -v opkg >/dev/null 2>&1; then asroot opkg update; asroot opkg install python3 python3-pip
    else echo "No known package manager found. Install Python 3.8+ and run: python3 $UYAST_FILE"; exit 1; fi ;;
  Darwin)
    if command -v brew >/dev/null 2>&1; then brew install python
    else
      echo "Installing Apple's Command Line Tools (they include Python 3) ..."
      asroot touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
      LABEL=$(softwareupdate -l 2>/dev/null | grep -o 'Command Line Tools for Xcode-[0-9.]*' | tail -n 1)
      if [ -n "$LABEL" ]; then asroot softwareupdate -i "$LABEL"
      else xcode-select --install; echo "Finish the installer window, then run again: sh $UYAST_FILE"; exit 1; fi
      asroot rm -f /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
    fi ;;
  FreeBSD|DragonFly)
    pkg -N >/dev/null 2>&1 || asroot env ASSUME_ALWAYS_YES=yes pkg bootstrap -y
    asroot env ASSUME_ALWAYS_YES=yes pkg install -y python3 ;;
  OpenBSD)
    asroot pkg_add -I python%3.12 || asroot pkg_add -I python%3.11 || asroot pkg_add -I python%3.10 || asroot pkg_add -I python%3 ;;
  NetBSD)
    if ! command -v pkgin >/dev/null 2>&1; then
      REL=$(uname -r | cut -d_ -f1 | cut -d. -f1-2)
      asroot env PKG_PATH="https://cdn.netbsd.org/pub/pkgsrc/packages/NetBSD/$(uname -p)/$REL/All" pkg_add pkgin
      asroot pkgin -y update
    fi
    asroot pkgin -y install python312 || asroot pkgin -y install python311 || asroot pkgin -y install python310 ;;
  SunOS)
    if command -v pkgin >/dev/null 2>&1; then asroot pkgin -y install python312 || asroot pkgin -y install python311
    else asroot pkg install -q runtime/python-312 || asroot pkg install -q runtime/python-311 || asroot pkg install -q runtime/python-39; fi ;;
  *) echo "uYaST: unsupported system $(uname -s)."; exit 1 ;;
esac
if PY=$(find_python); then exec "$PY" "$UYAST_FILE" "$@"; fi
echo "uYaST: Python could not be installed automatically. Install Python 3.8+ and run: python3 $UYAST_FILE"
exit 1
"""
# ===================================================================================
#  uYaST - universal YaST-style system administration TUI, in one file.
#
#  Platforms : macOS (Apple Silicon and Intel), Windows 7 / 8 / 8.1 / 10 / 11 / Server,
#              Linux (any distribution, any kernel), Unix (FreeBSD, OpenBSD, NetBSD,
#              DragonFly, illumos/Solaris and other POSIX systems).
#  Start     : python3 uyast.py        (Windows: py uyast.py)
#              sh uyast.py             (Linux/macOS/BSD without Python yet)
#  Options   : --setup  run the start-up wizard again      --check  only check the environment
#              --reset  forget saved settings              --yes    answer "yes" to every question
#              --glyphs auto|safe|fancy                     --no-elevate / --no-relaunch
#
#  Windows without Python: Windows 10/11 -> "winget install -e --id Python.Python.3.12"
#                          Windows 7/8.1 -> install Python 3.8.10 from python.org
#
#  Layout of this file:
#    1. core helpers, platform detection, command engine
#    2. platform back-ends (Linux, macOS, Windows, Unix) - native built-in tools first
#    3. environment check and start-up wizard (standard library only)
#    4. the YaST-style text user interface (Textual)
# ===================================================================================
from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import getpass
import io
import ipaddress
import json
import os
import platform
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

APP_NAME = "uYaST"
VERSION = "2.0.0"
MIN_PY = (3, 8)
TEXTUAL_REQ = "textual>=6.0"
IS_WINDOWS = os.name == "nt"

PLATFORM_CHOICES = [
    ("macos", "macOS", "Apple Silicon (M-series) and Intel Macs"),
    ("windows", "Windows", "Windows 7, 8, 8.1, 10, 11 and Server"),
    ("linux", "Linux", "any distribution, any kernel"),
    ("unix", "Unix", "BSDs (FreeBSD, OpenBSD, NetBSD, DragonFly) and others (illumos, Solaris ...)"),
]
FAMILY_NAME = {k: n for k, n, _ in PLATFORM_CHOICES}

EXTRA_PATHS = ["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/sbin", "/usr/bin", "/bin",
               "/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/pkg/sbin", "/usr/pkg/bin",
               "/opt/local/bin", "/opt/local/sbin", "/opt/ooce/bin", "/usr/gnu/bin", "/usr/xpg4/bin",
               "/run/current-system/sw/bin", "/usr/libexec", "/usr/libexec/ApplicationFirewall"]


# =============================================================================
# 1. Core helpers
# =============================================================================
class NotSupported(Exception):
    """The current platform / back-end cannot do this."""


_WHICH: Dict[str, Optional[str]] = {}


def which_ext(name: str) -> Optional[str]:
    """shutil.which() that also looks in the usual sbin / Homebrew / pkgsrc folders."""
    if name in _WHICH:
        return _WHICH[name]
    p: Optional[str] = None
    if os.path.isabs(name):
        p = name if (os.path.isfile(name) and os.access(name, os.X_OK)) else None
    else:
        p = shutil.which(name)
        if not p and not IS_WINDOWS:
            for d in EXTRA_PATHS:
                c = os.path.join(d, name)
                if os.path.isfile(c) and os.access(c, os.X_OK):
                    p = c
                    break
    _WHICH[name] = p
    return p


def clear_which_cache() -> None:
    _WHICH.clear()


def extend_path() -> None:
    """Make sure sbin and Homebrew/pkgsrc folders are on PATH (sudo often strips them)."""
    if IS_WINDOWS:
        return
    parts = os.environ.get("PATH", "").split(os.pathsep)
    for d in EXTRA_PATHS:
        if d not in parts and os.path.isdir(d):
            parts.append(d)
    os.environ["PATH"] = os.pathsep.join(p for p in parts if p)


def read_text(path, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return default


def run_quiet(argv: Sequence[str], timeout: float = 15, input_text: Optional[str] = None) -> Tuple[int, str]:
    """Run a command, return (exit code, stdout). Never raises."""
    kw: Dict[str, Any] = {}
    if IS_WINDOWS:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        if input_text is None:
            kw["stdin"] = subprocess.DEVNULL
        r = subprocess.run(list(argv), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
                           input=input_text.encode() if input_text is not None else None, **kw)
        return r.returncode, decode_bytes(r.stdout)
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def decode_bytes(b: bytes) -> str:
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        s = None
        if IS_WINDOWS:
            for enc in ("oem", "mbcs"):
                try:
                    s = b.decode(enc)
                    break
                except Exception:
                    s = None
        if s is None:
            s = b.decode("latin-1", errors="replace")
    return s.replace("﻿", "")


def is_admin() -> bool:
    if IS_WINDOWS:
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0


def invoking_user() -> str:
    for k in ("UYAST_USER", "SUDO_USER", "DOAS_USER"):
        v = os.environ.get(k)
        if v and v != "root":
            return v
    try:
        return getpass.getuser()
    except Exception:
        return ""


def os_release() -> Dict[str, str]:
    data: Dict[str, str] = {}
    for p in ("/etc/os-release", "/usr/lib/os-release", "/var/run/os-release"):
        txt = read_text(p)
        if txt:
            for line in txt.splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")
            break
    return data


def sysctl_n(name: str) -> str:
    return run_quiet(["sysctl", "-n", name], timeout=5)[1].strip()


def fmt_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(n) < 1024 or unit == "PiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return str(n)


def fmt_duration(sec: float) -> str:
    sec = int(sec)
    d, sec = divmod(sec, 86400)
    h, sec = divmod(sec, 3600)
    m, _ = divmod(sec, 60)
    return (f"{d}d " if d else "") + f"{h}h {m}m"


async def in_thread(fn, *args):
    """asyncio.to_thread() for Python 3.8."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args))


# =============================================================================
# Platform detection
# =============================================================================
@dataclass
class PlatformInfo:
    family: str            # macos | windows | linux | unix | unknown
    flavor: str            # macos, windows, linux, freebsd, dragonfly, openbsd, netbsd, illumos, solaris, unix
    name: str              # human readable, e.g. "Ubuntu 24.04 LTS"
    version: str = ""
    arch: str = ""
    detail: str = ""
    distro_id: str = ""
    distro_like: str = ""
    win_build: int = 0
    win_ver: Tuple[int, int] = (0, 0)

    @property
    def key(self) -> str:
        return f"{self.family}:{self.flavor}:{self.version}:{self.arch}"


MAC_NAMES = {"10.13": "High Sierra", "10.14": "Mojave", "10.15": "Catalina", "11": "Big Sur", "12": "Monterey",
             "13": "Ventura", "14": "Sonoma", "15": "Sequoia", "26": "Tahoe"}


def detect_platform() -> PlatformInfo:
    sp = sys.platform
    arch = platform.machine() or "?"
    if sp == "darwin":
        ver = platform.mac_ver()[0] or platform.release()
        major = ver.split(".")[0]
        nick = MAC_NAMES.get(major if major != "10" else ".".join(ver.split(".")[:2]), "")
        arm = sysctl_n("hw.optional.arm64") == "1"
        rosetta = sysctl_n("sysctl.proc_translated") == "1"
        chip = sysctl_n("machdep.cpu.brand_string")
        detail = ("Apple Silicon" if arm else "Intel") + (f" - {chip}" if chip else "")
        if rosetta:
            detail += " (this Python runs under Rosetta 2)"
        return PlatformInfo("macos", "macos", f"macOS {ver} {nick}".strip(), ver, "arm64" if arm else arch, detail)
    if sp.startswith("win"):
        wv = sys.getwindowsversion()
        build = getattr(wv, "build", 0)
        if wv.major == 10:
            name = "Windows 11" if build >= 22000 else "Windows 10"
        else:
            name = {(6, 3): "Windows 8.1", (6, 2): "Windows 8", (6, 1): "Windows 7", (6, 0): "Windows Vista"}.get(
                (wv.major, wv.minor), f"Windows NT {wv.major}.{wv.minor}")
        try:
            edition = platform.win32_edition() or ""
        except Exception:
            edition = ""
        if "Server" in edition:
            name = f"Windows Server ({name.replace('Windows ', '')} kernel)"
        arch = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or arch
        return PlatformInfo("windows", "windows", name, f"{wv.major}.{wv.minor}.{build}", arch,
                            edition, win_build=build, win_ver=(wv.major, wv.minor))
    if sp.startswith("linux"):
        rel = os_release()
        name = rel.get("PRETTY_NAME") or rel.get("NAME") or "Linux"
        extra = []
        if "microsoft" in platform.release().lower():
            extra.append("WSL")
        if os.environ.get("ANDROID_ROOT") or "com.termux" in os.environ.get("PREFIX", ""):
            extra.append("Android/Termux")
        detail = f"kernel {platform.release()}" + (f" ({', '.join(extra)})" if extra else "")
        return PlatformInfo("linux", "linux", name, rel.get("VERSION_ID", ""), arch, detail,
                            rel.get("ID", ""), rel.get("ID_LIKE", ""))
    for prefix, flavor in (("freebsd", "freebsd"), ("openbsd", "openbsd"), ("netbsd", "netbsd"),
                           ("dragonfly", "dragonfly"), ("sunos", "sunos")):
        if sp.startswith(prefix):
            rel = os_release()
            if flavor == "sunos":
                first = read_text("/etc/release").strip().splitlines()
                uname_o = run_quiet(["uname", "-o"], 3)[1].strip().lower()
                flavor = "illumos" if "illumos" in uname_o or "illumos" in " ".join(first).lower() else "solaris"
                name = (first[0].strip() if first else f"SunOS {platform.release()}")
            else:
                name = rel.get("PRETTY_NAME") or f"{platform.system()} {platform.release()}"
            return PlatformInfo("unix", flavor, name, platform.release(), arch, f"kernel {platform.version()[:60]}")
    if sp.startswith(("aix", "hp-ux", "irix", "osf", "qnx")) or os.name == "posix" and sp not in ("cygwin", "msys"):
        return PlatformInfo("unix", "unix", f"{platform.system()} {platform.release()}", platform.release(), arch,
                            "generic POSIX support")
    return PlatformInfo("unknown", sp, f"{platform.system()} ({sp})", platform.release(), arch,
                        "use the native Windows Python instead of Cygwin/MSYS" if sp in ("cygwin", "msys") else "")


# =============================================================================
# Input validation (every value typed into the TUI goes through here)
# =============================================================================
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
RE_HOST = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                     r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$")
RE_POSIX_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,31}\$?$")
RE_WIN_NAME = re.compile(r'^[^\\/\[\]:;|=,+*?<>"@]{1,64}$')


def clean_arg(value: Any, what: str = "value", spaces: bool = False) -> str:
    v = str(value if value is not None else "").strip()
    if not v:
        raise ValueError(f"Please enter a {what}.")
    if v.startswith("-"):
        raise ValueError(f"Invalid {what}: it must not start with '-'.")
    if _CTRL.search(v):
        raise ValueError(f"Invalid {what}: control characters are not allowed.")
    if not spaces and re.search(r"\s", v):
        raise ValueError(f"Invalid {what}: spaces are not allowed.")
    return v


def clean_password(pw: Any, required: bool = False) -> str:
    pw = "" if pw is None else str(pw)
    if any(c in pw for c in "\r\n\x00"):
        raise ValueError("Passwords cannot contain line breaks.")
    if required and not pw:
        raise ValueError("Please enter the password.")
    return pw


def clean_host(value: Any) -> str:
    v = clean_arg(value, "host name or IP address")
    try:
        ipaddress.ip_address(v)
        return v
    except ValueError:
        pass
    if not RE_HOST.match(v):
        raise ValueError(f"'{v}' is not a valid host name or IP address.")
    return v


def parse_port(value: Any) -> Tuple[int, int]:
    v = str(value or "").strip()
    m = re.fullmatch(r"(\d{1,5})(?:\s*[-:]\s*(\d{1,5}))?", v)
    if not m:
        raise ValueError("Port must be a number (e.g. 80) or a range (e.g. 8000-8010).")
    lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
    if not (1 <= lo <= hi <= 65535):
        raise ValueError("Ports must be 1-65535 and a range must go from low to high.")
    return lo, hi


def ps_quote(s: Any) -> str:
    """A PowerShell single-quoted literal (smart quotes doubled too)."""
    if isinstance(s, bool):
        return "$true" if s else "$false"
    if isinstance(s, (list, tuple)):
        return ",".join(ps_quote(x) for x in s)
    return "'" + re.sub(r"(['‘’‚‛])", r"\1\1", str(s)) + "'"


# =============================================================================
# Command engine: Cmd (ready to run), Step/Way (templates), op tables
# =============================================================================
@dataclass
class Cmd:
    argv: Optional[List[str]] = None
    func: Optional[Callable[[], str]] = None
    input: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    desc: str = ""
    allow_fail: bool = False
    user: bool = False             # run as the invoking non-root user (Homebrew refuses root)
    root: bool = False             # needs root / Administrator
    tail: int = 0                  # show only the last N lines
    grep: str = ""                 # show only lines matching (case-insensitive, "a|b" = a or b)
    filter: str = ""               # extra filter typed by the user in the TUI
    ok_codes: Tuple[int, ...] = (0,)
    timeout: float = 0             # 0 = no limit

    def display(self) -> str:
        if self.desc:
            return self.desc
        if not self.argv:
            return "(internal step)"
        return subprocess.list2cmdline(self.argv) if IS_WINDOWS else shlex.join(self.argv)


class Step:
    """One command template. kind: cmd | ps | func."""

    def __init__(self, kind: str, argv=None, script=None, func=None, desc: str = "", needs=None,
                 root: Optional[bool] = None, optional: bool = False, each: str = "", **opts):
        self.kind, self.argv, self.script, self.func, self.desc = kind, argv, script, func, desc
        self.needs = list(needs or [])
        self.root, self.optional, self.each = root, optional, each
        self.opts = opts   # allow_fail, user, tail, grep, input, env, ok_codes, timeout

    def template(self) -> str:
        if self.kind == "cmd":
            return " ".join(a if " " not in a else repr(a) for a in self.argv)
        if self.kind == "ps":
            s = re.sub(r"\s+", " ", self.script).strip()
            return "PowerShell: " + (s if len(s) < 110 else s[:107] + "...")
        return self.desc or "(built-in step)"


def C(*argv: str, needs=None, **kw) -> Step:
    if needs is None:
        needs = [argv[0]] if argv and not argv[0].startswith("{") else []
    return Step("cmd", argv=list(argv), needs=needs, **kw)


def PS(script: str, needs=(), **kw) -> Step:
    return Step("ps", script=script, needs=["@ps", *needs], **kw)


def F(func: Callable[[Dict[str, Any]], str], desc: str, needs=(), **kw) -> Step:
    return Step("func", func=func, desc=desc, needs=list(needs), **kw)


class Way:
    """One complete way to do an operation (a sequence of steps)."""

    def __init__(self, *steps: Step, needs=(), root: Optional[bool] = None):
        self.steps = list(steps)
        self.root = root
        self.needs = list(needs)
        for s in self.steps:
            if not s.optional:
                self.needs += [n for n in s.needs if n not in self.needs]


W = Way

# Operations that change the system and therefore need root / Administrator by default.
ROOT_OPS = set("""
pkg.install pkg.remove pkg.refresh pkg.upgrade pkg.clean pkg.cask pkg.distup repo.add os.updates.install
os.patches.apply os.firmware
svc.start svc.stop svc.restart svc.enable svc.disable svc.manual
user.add user.passwd user.delete user.lock user.unlock group.add group.delete group.adduser group.deluser
fw.enable fw.disable fw.allow fw.remove fw.app.allow fw.app.block fw.stealth.on fw.stealth.off fw.reload
net.hostname.set hosts.add hosts.remove net.dhcp.renew net.dns.flush net.nm.up net.nm.down net.if.up net.if.down
time.sync time.tz.set time.ntp.on time.ntp.off locale.set
kernel.set kernel.load kernel.unload boot.grub boot.target.set boot.timeout
power.reboot power.off power.schedule power.cancel power.suspend power.plan.set
sched.run sched.enable sched.disable printer.default printer.cancel sec.scan
""".split())

_PH = re.compile(r"(?<![$%])\{(\w+)\}")          # ${X} and %{X} belong to dpkg/rpm, not to us
_PH_LIST = re.compile(r"^\{\*(\w+)\}$")


def _sval(v: Any) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (list, tuple)):
        return " ".join(str(x) for x in v)
    return str(v)


def expand_text(text: str, params: Dict[str, Any]) -> str:
    def rep(m):
        k = m.group(1)
        if k not in params:
            raise ValueError(f"missing value: {k}")
        return _sval(params[k])
    return _PH.sub(rep, text)


def expand_argv(argv: List[str], params: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for a in argv:
        m = _PH_LIST.match(a)
        if m:
            v = params.get(m.group(1))
            if v is None:
                raise ValueError(f"missing value: {m.group(1)}")
            out.extend(str(x) for x in (v if isinstance(v, (list, tuple)) else [v]))
        else:
            out.append(expand_text(a, params))
    return out


def expand_ps(script: str, params: Dict[str, Any]) -> str:
    def rep(m):
        k = m.group(1)
        if k not in params:
            return m.group(0)        # PowerShell's own {braces} stay untouched
        return ps_quote(params[k])
    return _PH.sub(rep, script)


PS_PRELUDE = ("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; "
              "try { [Console]::OutputEncoding=[System.Text.Encoding]::UTF8 } catch {}; ")


def ps_exe() -> str:
    return which_ext("powershell.exe") or which_ext("powershell") or which_ext("pwsh") or "powershell.exe"


def ps_argv(script: str) -> List[str]:
    enc = base64.b64encode((PS_PRELUDE + script).encode("utf-16-le")).decode("ascii")
    return [ps_exe(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-OutputFormat", "Text", "-EncodedCommand", enc]


def ps_cmd(script: str, **kw) -> Cmd:
    return Cmd(ps_argv(script), desc=kw.pop("desc", "") or "PS> " + re.sub(r"\s+", " ", script).strip(), **kw)


# =============================================================================
# 2. Platform back-ends
# =============================================================================
@dataclass
class EnvItem:
    """One line of the environment check."""
    key: str
    group: str                       # Core, Terminal, Access, Packages, Tools, Services
    title: str
    ok: bool
    detail: str = ""
    level: str = "recommended"       # required | recommended | optional | info
    pkgs: List[str] = field(default_factory=list)       # OS packages that fix it
    fix: List[Cmd] = field(default_factory=list)        # other steps that fix it
    fix_text: str = ""
    terminal_only: bool = False      # fix needs the interactive start-up terminal (e.g. sudo password)
    order: int = 50                  # fixes run in this order (package manager before tools ...)

    @property
    def fixable(self) -> bool:
        return not self.ok and bool(self.pkgs or self.fix)


DERIVED = {"port_dash": "port", "port_colon": "port", "port_lo": "port", "port_hi": "port", "proto_upper": "proto",
           "pkg_wg": "pkg", "hostname_short": "hostname", "host_short": "host", "repo_alias": "repo",
           "seconds_total": "minutes"}
_USED_RX = re.compile(r"(?<![$%])\{\*?([A-Za-z_]\w*)\}")


def step_placeholders(st: Step) -> set:
    texts: List[str] = list(st.argv or []) + [st.script or "", st.desc or "", st.opts.get("input") or ""]
    texts += list((st.opts.get("env") or {}).values())
    found = set(st.opts.get("uses", ()))
    for t in texts:
        found |= set(_USED_RX.findall(t))
    if st.each:
        found.discard(st.each[:-1] if st.each.endswith("s") else st.each)
        found -= {"pkg_wg"}
        found.add(st.each)
    return found


class Backend:
    family = "generic"
    flavor = "generic"
    pkg_label = "none"
    svc_label = "none"
    fw_label = "none"
    fw_enable_note = ""
    USER_COLS: Tuple[str, ...] = ("Name", "UID", "Home", "Shell", "Full name")
    GROUP_COLS: Tuple[str, ...] = ("Name", "GID", "Members")
    LOG_KINDS = [("log.system", "System log"), ("log.kernel", "Kernel messages"), ("log.auth", "Authentication"),
                 ("log.boot", "This boot"), ("log.errors", "Errors only")]
    UID_MIN = 1000
    assume_root = False          # True in the start-up wizard: commands get sudo/doas/su in front

    def __init__(self, info: PlatformInfo):
        self.info = info
        self.label = info.name
        self.caps: set = set()
        self.ops: Dict[str, List[Way]] = {}
        self.redetect()

    # ---- detection ------------------------------------------------------------
    def redetect(self) -> None:
        clear_which_cache()
        self.caps = set(self.detect_caps())
        raw = self.build_ops()
        self.ops = {k: self._norm(v) for k, v in raw.items()}
        self.labels()

    @staticmethod
    def _norm(v) -> List[Way]:
        items = v if isinstance(v, list) else [v]
        return [x if isinstance(x, Way) else Way(x) for x in items]

    def detect_caps(self) -> set:
        return set()

    def build_ops(self) -> Dict[str, Any]:
        return {}

    def labels(self) -> None:
        pass

    def has(self, need: str) -> bool:
        if need.startswith("@"):
            return need[1:] in self.caps
        if need.startswith("file:"):
            return os.path.exists(need[5:])
        return bool(which_ext(need))

    def _missing(self, way: Way) -> List[str]:
        return [n for n in way.needs if not self.has(n)]

    def _way_root(self, op: str, way: Way) -> bool:
        if way.root is not None:
            return way.root
        roots = [s.root for s in way.steps if s.root is not None]
        if roots:
            return any(roots)
        return op in ROOT_OPS

    def resolve(self, op: str) -> Tuple[Optional[Way], str]:
        ways = self.ops.get(op)
        if not ways:
            return None, f"not available on {FAMILY_NAME.get(self.family, self.family)}"
        missing_all: List[str] = []
        for w in ways:
            miss = self._missing(w)
            if not miss:
                if self._way_root(op, w) and not (is_admin() or self.assume_root):
                    return None, "needs administrator / root rights - restart uYaST with them"
                return w, ""
            missing_all.append(" + ".join(m.lstrip("@").replace("file:", "") for m in miss))
        tools = ", ".join(dict.fromkeys(missing_all))
        if all(m.startswith(("file:", "@")) for w in ways for m in self._missing(w)):
            return None, f"not available on this system (no {tools})"
        return None, f"needs {tools} (Environment Check can install missing tools)"

    def available(self, op: str) -> Tuple[bool, str]:
        w, why = self.resolve(op)
        return w is not None, why

    def describe(self, op: str) -> str:
        ways = self.ops.get(op)
        if not ways:
            return "not available here"
        w, why = self.resolve(op)
        w = w or ways[0]
        txt = "  then  ".join(s.template() for s in w.steps if not s.optional or self._step_ok(s))
        return txt + (f"   [{why}]" if why else "")

    def _step_ok(self, s: Step) -> bool:
        return all(self.has(n) for n in s.needs)

    # ---- building commands -------------------------------------------------------
    def cmds(self, op: str, **raw: Any) -> List[Cmd]:
        way, why = self.resolve(op)
        if way is None:
            raise NotSupported(why)
        steps = [st for st in way.steps if not (st.optional and not self._step_ok(st))]
        used = set()
        for st in steps:
            used |= step_placeholders(st)
        base_used = {DERIVED.get(u, u) for u in used}
        missing = [u for u in base_used if u not in raw]
        if missing:
            raise ValueError("Please fill in: " + ", ".join(sorted(missing)))
        params: Dict[str, Any] = {}
        for k, v in raw.items():
            if k in base_used:
                params.update(self.validate(k, v))
        root = self._way_root(op, way)
        out: List[Cmd] = []
        for st in steps:
            if st.each:
                for item in params.get(st.each) or []:
                    p2 = dict(params)
                    p2.update(self.validate(st.each[:-1] if st.each.endswith("s") else st.each, item))
                    out.append(self._build(st, p2, root))
            else:
                out.append(self._build(st, params, root))
        return out

    def _build(self, st: Step, params: Dict[str, Any], root: bool) -> Cmd:
        o = st.opts
        r = st.root if st.root is not None else root
        common = dict(allow_fail=o.get("allow_fail", False), user=o.get("user", False), root=r,
                      tail=o.get("tail", 0), grep=o.get("grep", ""), ok_codes=tuple(o.get("ok_codes", (0,))),
                      timeout=o.get("timeout", 0))
        inp = expand_text(o["input"], params) if o.get("input") else None
        env = {k: expand_text(v, params) for k, v in (o.get("env") or {}).items()} or None
        secret = str(params.get("password") or params.get("newpw") or "")
        if st.kind == "cmd":
            argv = expand_argv(st.argv, params)
            exe = which_ext(argv[0])
            if exe and not shutil.which(argv[0]):
                argv[0] = exe
            desc = expand_text(st.desc, params) if st.desc else ""
            if secret and not desc:
                shown = [a.replace(secret, "****") if secret in a else a for a in argv]
                desc = subprocess.list2cmdline(shown) if IS_WINDOWS else shlex.join(shown)
            return Cmd(argv=argv, input=inp, env=env, desc=desc, **common)
        if st.kind == "ps":
            script = expand_ps(st.script, params)
            shown = re.sub(r"\s+", " ", script).strip()
            if secret:
                shown = shown.replace(ps_quote(secret), "'****'")
            return Cmd(argv=ps_argv(script), input=inp, env=env, desc=st.desc or "PS> " + shown, **common)
        fn, p = st.func, dict(params)
        return Cmd(func=lambda: fn(p), desc=expand_text(st.desc, {k: ("****" if k in ("password", "newpw") else v)
                                                                 for k, v in params.items()}), **common)

    # ---- validation (one place for every typed value) -------------------------------
    def validate(self, name: str, v: Any) -> Dict[str, Any]:
        if name in ("admin", "persist", "force"):
            return {name: bool(v)}
        if name == "q":
            return {"q": clean_arg(v, "search term", spaces=True)}
        if name in ("pkg", "pkgs"):
            items = str(v or "").split()
            if not items:
                raise ValueError("Please enter at least one package name.")
            items = [clean_arg(i, "package name") for i in items]
            if name == "pkg":
                if len(items) != 1:
                    raise ValueError("Please enter exactly one package name.")
                return {"pkg": items[0], "pkg_wg": ["--id", items[0], "--exact"] if "." in items[0] else [items[0]]}
            return {"pkgs": items}
        if name == "svc":
            return {"svc": clean_arg(v, "service name", spaces=IS_WINDOWS)}
        if name == "user":
            return {"user": self.check_user(v)}
        if name == "group":
            return {"group": self.check_group(v)}
        if name == "password":
            return {"password": clean_password(v)}
        if name == "newpw":
            return {"newpw": clean_password(v, required=True)}
        if name == "host":
            h = clean_host(v)
            return {"host": h, "host_short": h.split(".")[0]}
        if name == "hostname":
            return {"hostname": self.check_hostname(v)}
        if name == "entry":
            s = clean_arg(v, "host name")
            if not RE_HOST.match(s):
                raise ValueError("Host names use letters, digits, '-' and dots (e.g. server1.example.com).")
            return {"entry": s}
        if name == "ip":
            try:
                return {"ip": str(ipaddress.ip_address(str(v).strip()))}
            except ValueError:
                raise ValueError(f"'{v}' is not a valid IP address.")
        if name == "port":
            lo, hi = parse_port(v)
            one = lo == hi
            return {"port": str(v).strip(), "port_lo": lo, "port_hi": hi,
                    "port_dash": str(lo) if one else f"{lo}-{hi}", "port_colon": str(lo) if one else f"{lo}:{hi}"}
        if name == "proto":
            p = str(v or "tcp").lower()
            if p not in ("tcp", "udp"):
                raise ValueError("Protocol must be TCP or UDP.")
            return {"proto": p, "proto_upper": p.upper()}
        if name == "tz":
            return {"tz": self.check_tz(v)}
        if name == "locale":
            s = clean_arg(v, "locale (e.g. en_US.UTF-8)")
            if not re.fullmatch(r"[A-Za-z]{1,8}([_-][A-Za-z0-9]{1,8})*(\.[A-Za-z0-9-]+)?(@\w+)?", s):
                raise ValueError("Locale looks like en_US.UTF-8 or de-DE.")
            return {"locale": s}
        if name == "mod":
            s = clean_arg(v, "module / driver name")
            if not re.fullmatch(r"[A-Za-z0-9_.+-]+", s):
                raise ValueError("Module names use letters, digits, '_', '-', '.'.")
            return {"mod": s}
        if name == "key":
            s = clean_arg(v, "parameter name")
            if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", s):
                raise ValueError("Parameter names look like net.ipv4.ip_forward.")
            return {"key": s}
        if name == "value":
            s = str(v if v is not None else "").strip()
            if not s or _CTRL.search(s):
                raise ValueError("Please enter a value.")
            return {"value": s}
        if name == "pid":
            s = str(v or "").strip()
            if not s.isdigit() or int(s) <= 0:
                raise ValueError("Select a process first.")
            return {"pid": s}
        if name in ("minutes", "seconds"):
            s = str(v or "").strip()
            if not s.isdigit() or not (0 <= int(s) <= 100000):
                raise ValueError(f"Please enter the number of {name}.")
            return {name: s, "seconds_total": str(int(s) * (60 if name == "minutes" else 1))}
        if name == "path":
            s = str(v or "").strip()
            if not s or not os.path.exists(s):
                raise ValueError("Please enter the full path of an existing application or file.")
            return {"path": s}
        if name == "repo":
            s = clean_arg(v, "repository (URL, ppa:..., or tap name)")
            alias = "uyast-" + re.sub(r"[^A-Za-z0-9]+", "-", s.rstrip("/").split("/")[-1] or "repo").strip("-")[:30]
            return {"repo": s, "repo_alias": alias}
        if name in ("iface", "conn", "printer", "task"):
            what = {"iface": "interface name", "conn": "connection name", "printer": "printer name",
                    "task": "task name"}[name]
            return {name: clean_arg(v, what, spaces=True)}
        if name == "target":
            s = str(v or "")
            if s not in ("multi-user.target", "graphical.target", "rescue.target"):
                raise ValueError("Choose a boot target.")
            return {"target": s}
        if name == "plan":
            s = str(v or "")
            if s not in ("SCHEME_BALANCED", "SCHEME_MIN", "SCHEME_MAX"):
                raise ValueError("Choose a power plan.")
            return {"plan": s}
        return {name: v}

    def check_user(self, v: Any) -> str:
        s = clean_arg(v, "user name")
        if not RE_POSIX_NAME.match(s):
            raise ValueError("User names: letters, digits, '_', '-', '.'; start with a letter or '_'; max 32.")
        return s

    def check_group(self, v: Any) -> str:
        s = clean_arg(v, "group name")
        if not RE_POSIX_NAME.match(s):
            raise ValueError("Group names: letters, digits, '_', '-', '.'; start with a letter or '_'.")
        return s

    def check_hostname(self, v: Any) -> str:
        s = clean_arg(v, "host name")
        if not RE_HOST.match(s):
            raise ValueError("Host names use letters, digits, '-' and dots (e.g. server1.example.com).")
        return s

    def check_tz(self, v: Any) -> str:
        s = clean_arg(v, "time zone (e.g. Europe/Berlin)")
        if not re.fullmatch(r"[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+)*", s):
            raise ValueError("Time zones look like Europe/Berlin or America/New_York.")
        if os.path.isdir("/usr/share/zoneinfo") and not os.path.isfile(os.path.join("/usr/share/zoneinfo", s)):
            raise ValueError(f"Unknown time zone '{s}'. Use 'List time zones' to see valid names.")
        return s

    # ---- data for tables (overridden) -------------------------------------------------
    def sysinfo(self) -> List[Tuple[str, str]]:
        info = [("Host name", platform.node()), ("Platform", f"{FAMILY_NAME.get(self.family, '?')} - {self.label}"),
                ("Version / build", self.info.version or platform.release()), ("Architecture", self.info.arch)]
        if self.info.detail:
            info.append(("Details", self.info.detail))
        info.append(("CPU cores", str(os.cpu_count() or "?")))
        try:
            root = (os.environ.get("SystemDrive", "C:") + "\\") if IS_WINDOWS else "/"
            du = shutil.disk_usage(root)
            info.append((f"Disk {root}", f"{fmt_bytes(du.used)} used of {fmt_bytes(du.total)} "
                                        f"({du.used * 100 // max(du.total, 1)}%, {fmt_bytes(du.free)} free)"))
        except OSError:
            pass
        return info

    def tail_info(self) -> List[Tuple[str, str]]:
        return [("Software back-end", self.pkg_label), ("Service manager", self.svc_label),
                ("Firewall back-end", self.fw_label),
                ("Privileges", ("Administrator" if IS_WINDOWS else "root") if is_admin()
                 else "NOT elevated - viewing works, changes are disabled"),
                ("Python", f"{platform.python_version()} ({sys.executable})"), (APP_NAME, VERSION)]

    async def services(self, cap) -> List[List[str]]:
        raise NotSupported("Service management is not available here.")

    async def users(self, cap, show_system: bool) -> List[List[str]]:
        return posix_users(show_system, self.UID_MIN)

    async def groups(self, cap, show_system: bool) -> List[List[str]]:
        return posix_groups(show_system, self.UID_MIN)

    async def processes(self, cap) -> List[List[str]]:
        return await posix_processes(cap)

    # ---- environment ---------------------------------------------------------------------
    def env_tools(self) -> List[Tuple[str, Dict[str, str], str, str]]:
        """(binary, {package manager: package}, what it is for, level)."""
        return []

    def pkg_manager_item(self) -> Optional[EnvItem]:
        return None

    def extra_env_items(self) -> List[EnvItem]:
        return []

    def python_venv_pkgs(self) -> List[str]:
        return []

    def pkg_prepare_cmds(self) -> List[Cmd]:
        """Refresh package indexes before installing tools (fresh systems have none)."""
        try:
            cmds = self.cmds("pkg.refresh")
        except (NotSupported, ValueError):
            return []
        for c in cmds:
            c.allow_fail = True
        return cmds

    def pkg_key(self) -> str:
        return ""

    def console_cmd(self, command: str) -> Cmd:
        command = (command or "").strip()
        if not command:
            raise ValueError("Please type a command.")
        sh = "sh"
        return Cmd([sh, "-c", command], desc="$ " + command, allow_fail=True)


# ---- helpers shared by the POSIX back-ends --------------------------------------------
def posix_users(show_system: bool, uid_min: int, hide_underscore: bool = False) -> List[List[str]]:
    import pwd
    rows = []
    for p in sorted(pwd.getpwall(), key=lambda p: (p.pw_uid, p.pw_name)):
        regular = uid_min <= p.pw_uid < 65534 and not (hide_underscore and p.pw_name.startswith("_"))
        if regular or show_system:
            rows.append([p.pw_name, str(p.pw_uid), p.pw_dir, p.pw_shell, (p.pw_gecos or "").split(",")[0]])
    return rows


def posix_groups(show_system: bool, gid_min: int, keep: Sequence[str] = ()) -> List[List[str]]:
    import grp
    rows = []
    seen = set()
    for g in sorted(grp.getgrall(), key=lambda g: (g.gr_gid, g.gr_name)):
        if g.gr_name in seen:
            continue
        seen.add(g.gr_name)
        if show_system or (gid_min <= g.gr_gid < 65534) or g.gr_name in keep:
            rows.append([g.gr_name, str(g.gr_gid), ", ".join(g.gr_mem)])
    return rows


async def posix_processes(cap) -> List[List[str]]:
    rc, out = await cap(Cmd(["ps", "-A", "-o", "pid=", "-o", "user=", "-o", "pcpu=", "-o", "pmem=", "-o", "comm="]))
    rows: List[List[str]] = []
    if rc == 0 and out.strip():
        for line in out.splitlines():
            parts = line.split(None, 4)
            if len(parts) == 5 and parts[0].isdigit():
                rows.append([parts[0], parts[1], parts[2], parts[3], parts[4]])
        return rows
    rc, out = await cap(Cmd(["ps", "-o", "pid,user,vsz,comm"]))        # BusyBox
    for line in out.splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[0].isdigit():
            rows.append([parts[0], parts[1], "-", parts[2], parts[3]])
    return rows


def hosts_path() -> Path:
    if IS_WINDOWS:
        return Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "drivers" / "etc" / "hosts"
    return Path("/etc/hosts")


def f_hosts_show(p) -> str:
    return f"--- {hosts_path()} ---\n" + (read_text(hosts_path()) or "(empty)")


def _backup_once(path: Path) -> str:
    bak = Path(str(path) + ".uyast.bak")
    if path.exists() and not bak.exists():
        shutil.copy2(str(path), str(bak))
        return f" (backup: {bak})"
    return ""


def f_hosts_add(p) -> str:
    path = hosts_path()
    ip, host = p["ip"], p["entry"]
    lines = read_text(path).splitlines()
    for line in lines:
        toks = line.split("#", 1)[0].split()
        if toks and toks[0] == ip and host.lower() in (t.lower() for t in toks[1:]):
            return f"{host} -> {ip} is already in {path}"
    note = _backup_once(path)
    with open(path, "a", encoding="utf-8", newline="\r\n" if IS_WINDOWS else "\n") as f:
        if lines and lines[-1].strip():
            f.write("\n")
        f.write(f"{ip}\t{host}\t# added by uYaST\n")
    return f"added {ip} {host} to {path}{note}"


def f_hosts_remove(p) -> str:
    path = hosts_path()
    host = p["entry"].lower()
    out, changed = [], 0
    for line in read_text(path).splitlines():
        body, _, comment = line.partition("#")
        toks = body.split()
        if len(toks) >= 2 and host in (t.lower() for t in toks[1:]):
            names = [t for t in toks[1:] if t.lower() != host]
            changed += 1
            if names:
                out.append("\t".join([toks[0]] + names) + (f"\t#{comment}" if comment else ""))
            continue
        out.append(line)
    if not changed:
        raise ValueError(f"{p['entry']} is not in {path}")
    note = _backup_once(path)
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")
    return f"removed {p['entry']} from {changed} line(s) in {path}{note}"


def f_resolv(p) -> str:
    return "--- /etc/resolv.conf ---\n" + (read_text("/etc/resolv.conf") or "(empty)")


def f_hostname(p) -> str:
    return f"Host name: {socket.gethostname()}\nFully qualified: {socket.getfqdn()}"


def f_lookup(p) -> str:
    out = []
    try:
        seen = set()
        for fam, _, _, _, addr in socket.getaddrinfo(p["host"], None):
            a = addr[0]
            if a not in seen:
                seen.add(a)
                out.append(f"{p['host']} -> {a} ({'IPv6' if fam == socket.AF_INET6 else 'IPv4'})")
    except socket.gaierror as e:
        raise ValueError(f"lookup failed: {e}")
    return "\n".join(out)


def f_tcp_test(p) -> str:
    host, port = p["host"], int(p["port_lo"])
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=5):
            return f"TCP {host}:{port} is OPEN (connected in {(time.time() - t0) * 1000:.0f} ms)"
    except OSError as e:
        return f"TCP {host}:{port} is CLOSED or filtered ({e})"


def zoneinfo_names() -> List[str]:
    base = "/usr/share/zoneinfo"
    names = []
    for root, dirs, files in os.walk(base):
        rel = os.path.relpath(root, base)
        if rel.split(os.sep)[0] in ("posix", "right"):
            dirs[:] = []
            continue
        for f in files:
            if f[:1].isupper() and "." not in f:
                names.append(f if rel == "." else rel.replace(os.sep, "/") + "/" + f)
    return sorted(names)


def f_tz_list(p) -> str:
    return "\n".join(zoneinfo_names()) or "(no /usr/share/zoneinfo found)"


def f_tz_symlink(p) -> str:
    tz = p["tz"]
    src = os.path.join("/usr/share/zoneinfo", tz)
    if not os.path.isfile(src):
        raise ValueError(f"unknown time zone {tz}")
    try:
        os.remove("/etc/localtime")
    except FileNotFoundError:
        pass
    os.symlink(src, "/etc/localtime")
    if os.path.exists("/etc/timezone"):
        Path("/etc/timezone").write_text(tz + "\n")
    return f"/etc/localtime -> {src}"


def f_cat(*paths: str) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        out = []
        for path in paths:
            if os.path.isdir(path):
                out.append(f"--- {path}/ ---")
                try:
                    out.extend(sorted(os.listdir(path)))
                except OSError as e:
                    out.append(str(e))
            elif os.path.exists(path):
                out.append(f"--- {path} ---")
                out.append(read_text(path).rstrip())
        return "\n".join(out) or "(nothing found: " + ", ".join(paths) + ")"
    return fn


def f_conf_set(path: str, sep: str = "=", quote: bool = False) -> Callable[[Dict[str, Any]], str]:
    """Set key<sep>value in a simple config file (sysctl.conf, rc.conf ...)."""
    def fn(p) -> str:
        if p.get("persist") is False:
            return "not saved permanently (tick 'Save permanently' to keep it after reboot)"
        key, val = p.get("key") or p.get("var"), p.get("value") if "value" in p else p.get("val")
        v = f'"{val}"' if quote else str(val)
        lines = read_text(path).splitlines()
        rx = re.compile(r"^\s*" + re.escape(key) + r"\s*" + re.escape(sep))
        new = [f"{key}{sep}{v}" if rx.match(l) else l for l in lines]
        if not any(rx.match(l) for l in lines):
            new.append(f"{key}{sep}{v}")
        os.makedirs(os.path.dirname(path) or "/", exist_ok=True)
        Path(path).write_text("\n".join(new) + "\n")
        return f"saved {key}{sep}{v} in {path}"
    return fn


def f_rcconf(value: str) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        return f_conf_set("/etc/rc.conf", "=", quote=False)({"key": p["svc"], "value": value})
    return fn


def f_members(*groups: str) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        import grp
        out = []
        for g in groups:
            try:
                gr = grp.getgrnam(g)
                out.append(f"{g} (gid {gr.gr_gid}): {', '.join(gr.gr_mem) or '(no extra members)'}")
            except KeyError:
                continue
        return "\n".join(out) or "none of these groups exist: " + ", ".join(groups)
    return fn


def f_power_sysfs(p) -> str:
    base = "/sys/class/power_supply"
    out = []
    for d in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        kv = {}
        for line in read_text(os.path.join(base, d, "uevent")).splitlines():
            k, _, v = line.partition("=")
            kv[k.replace("POWER_SUPPLY_", "")] = v
        bits = [f"{k}={kv[k]}" for k in ("TYPE", "STATUS", "CAPACITY", "ONLINE", "HEALTH") if k in kv]
        out.append(f"{d}: " + ", ".join(bits))
    return "\n".join(out) or "No batteries or power supplies reported."


def pf_prepare_func(pf_conf: str, anchor_file: str, default_conf: str) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        os.makedirs(os.path.dirname(anchor_file), exist_ok=True)
        if not os.path.exists(anchor_file):
            Path(anchor_file).write_text("# uYaST managed pf rules\n")
        if not os.path.exists(pf_conf):
            Path(pf_conf).write_text(default_conf)
            return f"created {pf_conf} (blocks inbound traffic except SSH, ICMP and uYaST ports)"
        txt = read_text(pf_conf)
        if 'anchor "uyast"' in txt:
            return f"{pf_conf} already contains the uYaST anchor"
        shutil.copy2(pf_conf, pf_conf + ".uyast.bak")
        with open(pf_conf, "a") as f:
            f.write(f'\n# Added by uYaST\nanchor "uyast"\nload anchor "uyast" from "{anchor_file}"\n')
        return f"appended the uYaST anchor to {pf_conf} (backup: {pf_conf}.uyast.bak)"
    return fn


def pf_default_conf(anchor_file: str) -> str:
    return (f"# pf.conf - created by uYaST\n# Inbound traffic is blocked except SSH, ICMP and ports opened in uYaST.\n"
            f"set skip on lo0\nblock in all\npass out all keep state\npass in quick proto tcp to port 22 keep state\n"
            f"pass in quick inet proto icmp all\npass in quick inet6 proto icmp6 all\n"
            f'anchor "uyast"\nload anchor "uyast" from "{anchor_file}"\n')


def pf_rule_func(anchor_file: str, add: bool, prepare: Optional[Callable] = None) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        port = p["port_lo"] if p["port_lo"] == p["port_hi"] else f"{p['port_lo']}:{p['port_hi']}"
        rule = f"pass in quick proto {p['proto']} to port {port} keep state"
        if prepare and add:
            prepare(p)
        lines = read_text(anchor_file).splitlines()
        if add:
            if rule in lines:
                return "rule already present: " + rule
            Path(anchor_file).write_text("\n".join(lines + [rule]) + "\n")
            return "added: " + rule
        if rule not in lines:
            raise ValueError("no such uYaST rule: " + rule)
        Path(anchor_file).write_text("\n".join(l for l in lines if l != rule) + "\n")
        return "removed: " + rule
    return fn


def f_persist_sysctl(path: str) -> Callable[[Dict[str, Any]], str]:
    return f_conf_set(path, "=")


def posix_common_ops(be: Backend) -> Dict[str, Any]:
    """Operations that work the same on (almost) every POSIX system."""
    return {
        "net.lookup": [C("host", "{host}"), C("nslookup", "{host}"), F(f_lookup, "resolve {host} (built-in resolver)")],
        "net.tcptest": F(f_tcp_test, "connect to {host} port {port}"),
        "net.arp": [C("ip", "neigh", needs=["ip", "@iproute2"]), C("arp", "-an")],
        "net.trace": [C("traceroute", "{host}", allow_fail=True), C("tracepath", "{host}", allow_fail=True)],
        "net.hostname.show": F(f_hostname, "show the host name"),
        "hosts.show": F(f_hosts_show, "show /etc/hosts"),
        "hosts.add": F(f_hosts_add, "add {ip} {entry} to /etc/hosts"),
        "hosts.remove": F(f_hosts_remove, "remove {entry} from /etc/hosts"),
        "net.dns": F(f_resolv, "show /etc/resolv.conf"),
        "proc.kill": C("kill", "-TERM", "{pid}"),
        "proc.kill9": C("kill", "-KILL", "{pid}"),
        "sched.list": C("crontab", "-l", allow_fail=True),
        "sched.system": F(f_cat("/etc/crontab", "/etc/cron.d"), "show /etc/crontab and /etc/cron.d"),
        "sec.logins": C("last", "-n", "25", allow_fail=True),
        "hw.fs": C("df", "-h"),
        "hw.mounts": C("mount"),
        "time.show": C("date"),
        "locale.show": C("locale"),
        "locale.list": C("locale", "-a"),
        "kernel.info": C("uname", "-a"),
        "kernel.params": C("sysctl", "-a", allow_fail=True),
        "hw.printers": C("lpstat", "-t", allow_fail=True),
        "printer.default": C("lpadmin", "-d", "{printer}"),
        "printer.jobs": C("lpstat", "-o", allow_fail=True),
        "printer.cancel": C("cancel", "-a"),
        "power.reboot": C("shutdown", "-r", "now"),
        "power.schedule": C("shutdown", "-h", "+{minutes}"),
        "power.cancel": C("killall", "shutdown"),
        "log.dmesg": C("dmesg", tail=300, allow_fail=True),
    }


# ---- Linux ------------------------------------------------------------------------------
def _pm(label, **ops):
    ops["label"] = label
    return ops


LINUX_PM: Dict[str, Dict[str, Any]] = {
    "apt": _pm("APT (Debian, Ubuntu, Mint ...)", bin="apt-get", env={"DEBIAN_FRONTEND": "noninteractive"},
               search=[["apt-cache", "search", "{q}"]], info=[["apt-cache", "show", "{pkg}"]],
               install=[["apt-get", "install", "-y", "{*pkgs}"]], remove=[["apt-get", "remove", "-y", "{*pkgs}"]],
               list=[["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"]], refresh=[["apt-get", "update"]],
               upgrade=[["apt-get", "update"], ["apt-get", "-y", "upgrade"]], outdated=[["apt", "list", "--upgradable"]],
               clean=[["apt-get", "-y", "autoremove"], ["apt-get", "clean"]],
               repos=f_cat("/etc/apt/sources.list", "/etc/apt/sources.list.d"),
               repoadd=[["add-apt-repository", "-y", "{repo}"]], venv=["python3-venv", "python3-pip"]),
    "dnf": _pm("DNF (Fedora, RHEL, Rocky, Alma ...)", bin="dnf",
               search=[["dnf", "search", "{q}"]], info=[["dnf", "info", "{pkg}"]],
               install=[["dnf", "install", "-y", "{*pkgs}"]], remove=[["dnf", "remove", "-y", "{*pkgs}"]],
               list=[["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"]], refresh=[["dnf", "makecache"]],
               upgrade=[["dnf", "upgrade", "-y"]], outdated=[["dnf", "check-update"]],
               clean=[["dnf", "autoremove", "-y"], ["dnf", "clean", "all"]], repos=[["dnf", "repolist", "--all"]],
               venv=["python3-pip"]),
    "yum": _pm("YUM (CentOS 7, RHEL 7)", bin="yum",
               search=[["yum", "search", "{q}"]], info=[["yum", "info", "{pkg}"]],
               install=[["yum", "install", "-y", "{*pkgs}"]], remove=[["yum", "remove", "-y", "{*pkgs}"]],
               list=[["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"]], refresh=[["yum", "makecache"]],
               upgrade=[["yum", "update", "-y"]], outdated=[["yum", "check-update"]],
               clean=[["yum", "clean", "all"]], repos=[["yum", "repolist", "all"]], venv=["python3-pip"]),
    "zypper": _pm("Zypper (openSUSE, SLES)", bin="zypper",
                  search=[["zypper", "--non-interactive", "search", "{q}"]], info=[["zypper", "--non-interactive", "info", "{pkg}"]],
                  install=[["zypper", "--non-interactive", "install", "{*pkgs}"]],
                  remove=[["zypper", "--non-interactive", "remove", "{*pkgs}"]],
                  list=[["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"]],
                  refresh=[["zypper", "--non-interactive", "refresh"]], upgrade=[["zypper", "--non-interactive", "update"]],
                  outdated=[["zypper", "--non-interactive", "list-updates"]], clean=[["zypper", "clean", "--all"]],
                  repos=[["zypper", "repos", "-d"]], repoadd=[["zypper", "--non-interactive", "addrepo", "-f", "{repo}", "{repo_alias}"],
                                                       ["zypper", "--non-interactive", "--gpg-auto-import-keys", "refresh"]],
                  patches=[["zypper", "--non-interactive", "list-patches"]],
                  patch=[["zypper", "--non-interactive", "patch"]],
                  distup=[["zypper", "--non-interactive", "dist-upgrade"]], venv=["python3-pip"]),
    "pacman": _pm("Pacman (Arch, Manjaro, EndeavourOS ...)", bin="pacman",
                  search=[["pacman", "-Ss", "{q}"]], info=[["pacman", "-Si", "{pkg}"]],
                  install=[["pacman", "-S", "--needed", "--noconfirm", "{*pkgs}"]],
                  remove=[["pacman", "-Rns", "--noconfirm", "{*pkgs}"]], list=[["pacman", "-Q"]],
                  refresh=[["pacman", "-Sy"]], upgrade=[["pacman", "-Syu", "--noconfirm"]], outdated=[["pacman", "-Qu"]],
                  clean=[["pacman", "-Sc", "--noconfirm"]], repos=f_cat("/etc/pacman.conf"),
                  prepare=[["pacman", "-Syu", "--noconfirm"]], venv=["python-pip"]),
    "apk": _pm("APK (Alpine)", bin="apk",
               search=[["apk", "search", "-v", "{q}"]], info=[["apk", "info", "-a", "{pkg}"]],
               install=[["apk", "add", "{*pkgs}"]], remove=[["apk", "del", "{*pkgs}"]], list=[["apk", "info", "-v"]],
               refresh=[["apk", "update"]], upgrade=[["apk", "update"], ["apk", "upgrade"]],
               outdated=[["apk", "version", "-l", "<"]], clean=[["apk", "cache", "clean"]],
               repos=f_cat("/etc/apk/repositories"), venv=["py3-pip"]),
    "xbps": _pm("XBPS (Void Linux)", bin="xbps-install",
                search=[["xbps-query", "-Rs", "{q}"]], info=[["xbps-query", "-R", "{pkg}"]],
                install=[["xbps-install", "-y", "{*pkgs}"]], remove=[["xbps-remove", "-y", "{*pkgs}"]],
                list=[["xbps-query", "-l"]], refresh=[["xbps-install", "-S"]], upgrade=[["xbps-install", "-Suy"]],
                outdated=[["xbps-install", "-Mun"]], clean=[["xbps-remove", "-Oy"]], repos=[["xbps-query", "-L"]],
                venv=["python3-pip"]),
    "emerge": _pm("Portage (Gentoo)", bin="emerge",
                  search=[["emerge", "--search", "{q}"]], info=[["emerge", "--pretend", "--verbose", "{pkg}"]],
                  install=[["emerge", "--ask=n", "--quiet-build", "{*pkgs}"]],
                  remove=[["emerge", "--ask=n", "--depclean", "{*pkgs}"]], list=f_cat("/var/db/pkg"),
                  refresh=[["emerge", "--sync"]], upgrade=[["emerge", "--ask=n", "-uDN", "@world"]],
                  outdated=[["emerge", "--pretend", "-uDN", "@world"]], clean=[["emerge", "--ask=n", "--depclean"]],
                  repos=f_cat("/etc/portage/repos.conf", "/var/db/repos"), venv=["dev-python/pip"]),
    "eopkg": _pm("eopkg (Solus)", bin="eopkg",
                 search=[["eopkg", "search", "{q}"]], info=[["eopkg", "info", "{pkg}"]],
                 install=[["eopkg", "install", "-y", "{*pkgs}"]], remove=[["eopkg", "remove", "-y", "{*pkgs}"]],
                 list=[["eopkg", "list-installed"]], refresh=[["eopkg", "update-repo"]], upgrade=[["eopkg", "upgrade", "-y"]],
                 outdated=[["eopkg", "list-upgrades"]], clean=[["eopkg", "delete-cache"]], repos=[["eopkg", "list-repo"]],
                 venv=["pip"]),
    "urpmi": _pm("urpmi (Mageia)", bin="urpmi",
                 search=[["urpmq", "-y", "{q}"]], info=[["urpmq", "-i", "{pkg}"]],
                 install=[["urpmi", "--auto", "{*pkgs}"]], remove=[["urpme", "--auto", "{*pkgs}"]],
                 list=[["rpm", "-qa"]], refresh=[["urpmi.update", "-a"]], upgrade=[["urpmi", "--auto", "--auto-update"]],
                 repos=[["urpmq", "--list-media"]], venv=["python3-pip"]),
    "slackpkg": _pm("slackpkg (Slackware)", bin="slackpkg",
                    search=[["slackpkg", "search", "{q}"]], info=[["slackpkg", "info", "{pkg}"]],
                    install=[["slackpkg", "-batch=on", "-default_answer=y", "install", "{*pkgs}"]],
                    remove=[["slackpkg", "-batch=on", "-default_answer=y", "remove", "{*pkgs}"]],
                    list=f_cat("/var/log/packages"), refresh=[["slackpkg", "-batch=on", "-default_answer=y", "update"]],
                    upgrade=[["slackpkg", "-batch=on", "-default_answer=y", "upgrade-all"]],
                    repos=f_cat("/etc/slackpkg/mirrors")),
    "swupd": _pm("swupd (Clear Linux bundles)", bin="swupd",
                 search=[["swupd", "search", "{q}"]], info=[["swupd", "bundle-info", "{pkg}"]],
                 install=[["swupd", "bundle-add", "{*pkgs}"]], remove=[["swupd", "bundle-remove", "{*pkgs}"]],
                 list=[["swupd", "bundle-list"]], upgrade=[["swupd", "update"]], outdated=[["swupd", "check-update"]]),
    "nix": _pm("Nix (nix-env; NixOS itself is configured declaratively)", bin="nix-env",
               search=[["nix-env", "-qaP", ".*{q}.*"]], install=[["nix-env", "-i", "{*pkgs}"]],
               remove=[["nix-env", "-e", "{*pkgs}"]], list=[["nix-env", "-q"]], refresh=[["nix-channel", "--update"]],
               upgrade=[["nix-env", "-u"]], repos=[["nix-channel", "--list"]]),
    "opkg": _pm("opkg (OpenWrt)", bin="opkg",
                search=[["opkg", "find", "*{q}*"]], info=[["opkg", "info", "{pkg}"]],
                install=[["opkg", "install", "{*pkgs}"]], remove=[["opkg", "remove", "{*pkgs}"]],
                list=[["opkg", "list-installed"]], refresh=[["opkg", "update"]], outdated=[["opkg", "list-upgradable"]],
                repos=f_cat("/etc/opkg/distfeeds.conf", "/etc/opkg/customfeeds.conf"), venv=["python3-pip"]),
}
LINUX_PM_ORDER = ["apt", "dnf", "yum", "zypper", "pacman", "apk", "xbps", "emerge", "eopkg", "urpmi",
                  "slackpkg", "swupd", "opkg", "nix"]


def f_chpasswd_opt(p) -> str:
    if not p.get("password"):
        return "no password given - the account stays locked until you set one"
    rc, out = run_quiet(["chpasswd"], input_text=f"{p['user']}:{p['password']}\n", timeout=30)
    if rc != 0:
        raise ValueError("chpasswd failed: " + out.strip())
    return "password set"


def f_admin_group(groups: Sequence[str], argv_fn: Callable[[str, str], List[str]]) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        if not p.get("admin"):
            return "not added to an administrator group (Administrator not ticked)"
        import grp
        for g in groups:
            try:
                grp.getgrnam(g)
            except KeyError:
                continue
            rc, out = run_quiet(argv_fn(p["user"], g), timeout=30)
            if rc != 0:
                raise ValueError(f"could not add {p['user']} to {g}: {out.strip()}")
            return f"added {p['user']} to the administrator group '{g}'"
        raise ValueError("no administrator group (" + ", ".join(groups) + ") exists")
    return fn


def f_proc_cmdline(p) -> str:
    return "Kernel command line: " + read_text("/proc/cmdline").strip()


def f_runit(enable: bool, svdir: str, rundir: str) -> Callable[[Dict[str, Any]], str]:
    def fn(p) -> str:
        link = os.path.join(rundir, p["svc"])
        if enable:
            src = os.path.join(svdir, p["svc"])
            if not os.path.isdir(src):
                raise ValueError(f"{src} does not exist")
            if not os.path.lexists(link):
                os.symlink(src, link)
            return f"enabled: {link} -> {src}"
        if os.path.islink(link):
            os.remove(link)
            return f"disabled: removed {link}"
        return f"{p['svc']} was not enabled"
    return fn


class LinuxBackend(Backend):
    family = "linux"
    flavor = "linux"

    def detect_caps(self) -> set:
        caps = set()
        if os.path.isdir("/run/systemd/system") and which_ext("systemctl"):
            caps.add("systemd")
        elif which_ext("rc-service") and (os.path.isdir("/run/openrc") or os.path.exists("/sbin/openrc")):
            caps.add("openrc")
        elif which_ext("sv") and (os.path.isdir("/run/runit") or os.path.isdir("/etc/runit")):
            caps.add("runit")
        elif which_ext("dinitctl"):
            caps.add("dinit")
        elif os.path.isdir("/etc/init.d"):
            caps.add("sysv")
        ip = which_ext("ip")
        if ip and os.path.basename(os.path.realpath(ip)) != "busybox":
            caps.add("iproute2")
        if which_ext("nmcli") and run_quiet(["nmcli", "-t", "-f", "RUNNING", "general"], 5)[1].strip() == "running":
            caps.add("nm")
        if os.path.exists("/boot/grub2/grub.cfg"):
            caps.add("grub2cfg")
        if os.path.exists("/boot/grub/grub.cfg"):
            caps.add("grubcfg")
        if self.info.arch.lower() in ("x86_64", "amd64", "i386", "i686"):
            caps.add("x86")
        self.pm = next((p for p in LINUX_PM_ORDER if which_ext(LINUX_PM[p]["bin"])), "")
        if self.pm:
            caps.add("pm")
        self.pmd = LINUX_PM.get(self.pm, {})
        self.init = next((c for c in ("systemd", "openrc", "runit", "dinit", "sysv") if c in caps), "")
        if which_ext("firewall-cmd") and (self.pm in ("dnf", "yum", "zypper") or not which_ext("ufw")):
            self.fw = "firewalld"
        elif which_ext("ufw"):
            self.fw = "ufw"
        elif which_ext("firewall-cmd"):
            self.fw = "firewalld"
        elif which_ext("nft"):
            self.fw = "nft"
        elif which_ext("iptables"):
            self.fw = "iptables"
        else:
            self.fw = ""
        self.runsvdir = next((d for d in ("/var/service", "/run/runit/service", "/etc/runit/runsvdir/default",
                                          "/etc/service") if os.path.isdir(d)), "/var/service")
        return caps

    def labels(self) -> None:
        self.pkg_label = self.pmd.get("label", "no supported package manager found")
        self.svc_label = {"systemd": "systemd (systemctl)", "openrc": "OpenRC (rc-service, rc-update)",
                          "runit": "runit (sv)", "dinit": "dinit (dinitctl)", "sysv": "SysV init (service)"
                          }.get(self.init, "none found")
        self.fw_label = {"firewalld": "firewalld (firewall-cmd)", "ufw": "UFW (Uncomplicated Firewall)",
                         "nft": "nftables (view only - install ufw or firewalld)",
                         "iptables": "iptables (view only - install ufw or firewalld)"
                         }.get(self.fw, "none found - Environment Check can install one")

    def pkg_key(self) -> str:
        return self.pm

    def _pmway(self, op: str):
        v = self.pmd.get(op)
        if v is None:
            return None
        env = self.pmd.get("env")
        if callable(v):
            return W(F(v, f"show {op}"))
        steps = [C(*a, env=env, ok_codes=(0, 100) if op == "outdated" else (0,)) for a in v]
        if op == "outdated":
            for s in steps:
                s.opts["allow_fail"] = True
        return W(*steps)

    def build_ops(self) -> Dict[str, Any]:
        sd = ["@systemd"]
        ops: Dict[str, Any] = posix_common_ops(self)
        # software -------------------------------------------------------------------
        for op, key in (("pkg.search", "search"), ("pkg.info", "info"), ("pkg.install", "install"),
                        ("pkg.remove", "remove"), ("pkg.list", "list"), ("pkg.refresh", "refresh"),
                        ("pkg.upgrade", "upgrade"), ("pkg.outdated", "outdated"), ("pkg.clean", "clean"),
                        ("pkg.repos", "repos"), ("repo.add", "repoadd"), ("os.patches.list", "patches"),
                        ("os.patches.apply", "patch"), ("pkg.distup", "distup")):
            w = self._pmway(key)
            if w:
                ops[op] = w
        # services -------------------------------------------------------------------
        if self.init == "systemd":
            ops.update({
                "svc.start": C("systemctl", "start", "{svc}"), "svc.stop": C("systemctl", "stop", "{svc}"),
                "svc.restart": C("systemctl", "restart", "{svc}"),
                "svc.status": C("systemctl", "status", "{svc}", "--no-pager", "-l", allow_fail=True),
                "svc.enable": C("systemctl", "enable", "{svc}"), "svc.disable": C("systemctl", "disable", "{svc}"),
                "svc.failed": C("systemctl", "--failed", "--no-pager"),
            })
        elif self.init == "openrc":
            ops.update({"svc.start": C("rc-service", "{svc}", "start"), "svc.stop": C("rc-service", "{svc}", "stop"),
                        "svc.restart": C("rc-service", "{svc}", "restart"),
                        "svc.status": C("rc-service", "{svc}", "status", allow_fail=True),
                        "svc.enable": C("rc-update", "add", "{svc}", "default"),
                        "svc.disable": C("rc-update", "del", "{svc}", "default"),
                        "svc.failed": C("rc-status", "--crashed", allow_fail=True)})
        elif self.init == "runit":
            ops.update({"svc.start": C("sv", "up", "{svc}"), "svc.stop": C("sv", "down", "{svc}"),
                        "svc.restart": C("sv", "restart", "{svc}"), "svc.status": C("sv", "status", "{svc}", allow_fail=True),
                        "svc.enable": F(f_runit(True, "/etc/sv", self.runsvdir), "link /etc/sv/{svc} into " + self.runsvdir),
                        "svc.disable": F(f_runit(False, "/etc/sv", self.runsvdir), "unlink {svc} from " + self.runsvdir)})
        elif self.init == "dinit":
            ops.update({k: C("dinitctl", a, "{svc}", allow_fail=(a == "status")) for k, a in (
                ("svc.start", "start"), ("svc.stop", "stop"), ("svc.restart", "restart"), ("svc.status", "status"),
                ("svc.enable", "enable"), ("svc.disable", "disable"))})
        elif self.init == "sysv":
            ops.update({"svc.start": C("service", "{svc}", "start"), "svc.stop": C("service", "{svc}", "stop"),
                        "svc.restart": C("service", "{svc}", "restart"),
                        "svc.status": C("service", "{svc}", "status", allow_fail=True),
                        "svc.enable": [C("chkconfig", "{svc}", "on"), C("update-rc.d", "{svc}", "defaults")],
                        "svc.disable": [C("chkconfig", "{svc}", "off"), C("update-rc.d", "{svc}", "disable")]})
        # users and groups -----------------------------------------------------------------
        shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
        admin = f_admin_group(("sudo", "wheel", "admin"), lambda u, g: (["usermod", "-aG", g, u] if which_ext("usermod")
                                                                          else ["addgroup", u, g]))
        ops.update({
            "user.add": [W(C("useradd", "-m", "-s", shell, "{user}"), F(f_chpasswd_opt, "set the password (chpasswd)", uses=["user", "password"]),
                           F(admin, "administrator group", uses=["user", "admin"]), needs=["chpasswd"]),
                         W(C("adduser", "-D", "-s", "/bin/sh", "{user}"), F(f_chpasswd_opt, "set the password (chpasswd)", uses=["user", "password"]),
                           F(admin, "administrator group", uses=["user", "admin"]), needs=["chpasswd"])],
            "user.passwd": C("chpasswd", input="{user}:{newpw}\n", desc="chpasswd   (new password for {user})"),
            "user.delete": [C("userdel", "-r", "{user}", ok_codes=(0, 12)), C("deluser", "--remove-home", "{user}"),
                            C("deluser", "{user}")],
            "user.lock": [C("usermod", "-L", "{user}"), C("passwd", "-l", "{user}")],
            "user.unlock": [C("usermod", "-U", "{user}"), C("passwd", "-u", "{user}")],
            "user.info": W(C("id", "{user}"), C("chage", "-l", "{user}", optional=True, allow_fail=True)),
            "group.add": [C("groupadd", "{group}"), C("addgroup", "{group}")],
            "group.delete": [C("groupdel", "{group}"), C("delgroup", "{group}")],
            "group.adduser": [C("usermod", "-aG", "{group}", "{user}"), C("gpasswd", "-a", "{user}", "{group}"),
                              C("addgroup", "{user}", "{group}")],
            "group.deluser": [C("gpasswd", "-d", "{user}", "{group}"), C("deluser", "{user}", "{group}"),
                              C("delgroup", "{user}", "{group}")],
            "sec.admins": F(f_members("sudo", "wheel", "admin", "adm"), "members of sudo / wheel / admin"),
        })
        # network ---------------------------------------------------------------------------
        nm = ["nmcli", "@nm"]
        ops.update({
            "net.interfaces": [C("ip", "-br", "addr", needs=["ip", "@iproute2"]), C("ip", "addr"), C("ifconfig", "-a")],
            "net.links": [C("ip", "-br", "link", needs=["ip", "@iproute2"]), C("ip", "link")],
            "net.routes": [W(C("ip", "route"), C("ip", "-6", "route", optional=True, needs=["ip", "@iproute2"])),
                           C("route", "-n"), C("netstat", "-rn")],
            "net.dns": [W(C("resolvectl", "status", "--no-pager", allow_fail=True), F(f_resolv, "show /etc/resolv.conf")),
                        F(f_resolv, "show /etc/resolv.conf")],
            "net.ports": [C("ss", "-tulpn", needs=["ss", "@iproute2"]), C("netstat", "-tulpn"), C("lsof", "-nP", "-i")],
            "net.conns": [C("ss", "-tunp", "state", "established", needs=["ss", "@iproute2"]),
                          C("netstat", "-tunp", grep="ESTABLISHED")],
            "net.ping": C("ping", "-c", "4", "{host}", allow_fail=True),
            "net.dhcp.renew": [C("nmcli", "device", "reapply", "{iface}", needs=nm), C("networkctl", "renew", "{iface}"),
                               C("dhcpcd", "-n", "{iface}"), C("dhclient", "-v", "{iface}")],
            "net.dns.flush": [C("resolvectl", "flush-caches"), C("systemd-resolve", "--flush-caches"), C("nscd", "-i", "hosts")],
            "net.if.up": C("ip", "link", "set", "{iface}", "up"),
            "net.if.down": C("ip", "link", "set", "{iface}", "down"),
            "net.nm.devices": C("nmcli", "device", "status", needs=nm),
            "net.nm.conns": C("nmcli", "connection", "show", needs=nm),
            "net.nm.wifi": C("nmcli", "device", "wifi", "list", needs=nm, allow_fail=True),
            "net.nm.up": C("nmcli", "connection", "up", "{conn}", needs=nm),
            "net.nm.down": C("nmcli", "connection", "down", "{conn}", needs=nm),
            "net.hostname.show": [C("hostnamectl", needs=["hostnamectl", "@systemd"]), F(f_hostname, "show the host name")],
            "net.hostname.set": [C("hostnamectl", "set-hostname", "{hostname}", needs=["hostnamectl", "@systemd"]),
                                 W(F(lambda p: (Path("/etc/hostname").write_text(p["hostname"] + "\n"), "wrote /etc/hostname")[1],
                                     "write {hostname} to /etc/hostname"), C("hostname", "{hostname}"))],
        })
        # firewall ----------------------------------------------------------------------------
        if self.fw == "ufw":
            ops.update({"fw.status": C("ufw", "status", "verbose", root=True),
                        "fw.rules": C("ufw", "status", "numbered", root=True),
                        "fw.enable": W(C("ufw", "allow", "22/tcp"), C("ufw", "--force", "enable")),
                        "fw.disable": C("ufw", "disable"), "fw.reload": C("ufw", "reload"),
                        "fw.allow": C("ufw", "allow", "{port_colon}/{proto}"),
                        "fw.remove": C("ufw", "delete", "allow", "{port_colon}/{proto}")})
            self.fw_enable_note = "Port 22/tcp (SSH) is allowed first, so a remote session is not cut off."
        elif self.fw == "firewalld":
            ops.update({"fw.status": W(C("firewall-cmd", "--state", allow_fail=True), C("firewall-cmd", "--list-all", allow_fail=True)),
                        "fw.rules": C("firewall-cmd", "--list-all-zones", allow_fail=True),
                        "fw.enable": C("systemctl", "enable", "--now", "firewalld"),
                        "fw.disable": C("systemctl", "disable", "--now", "firewalld"),
                        "fw.reload": C("firewall-cmd", "--reload"),
                        "fw.allow": W(C("firewall-cmd", "--permanent", "--add-port={port_dash}/{proto}"), C("firewall-cmd", "--reload")),
                        "fw.remove": W(C("firewall-cmd", "--permanent", "--remove-port={port_dash}/{proto}"), C("firewall-cmd", "--reload"))})
            self.fw_enable_note = "firewalld keeps the 'ssh' service open in the default zone."
        elif self.fw == "nft":
            ops.update({"fw.status": C("nft", "list", "ruleset", root=True), "fw.rules": C("nft", "list", "ruleset", root=True)})
        elif self.fw == "iptables":
            ops.update({"fw.status": C("iptables", "-L", "-n", "-v", root=True), "fw.rules": C("iptables", "-S", root=True)})
        # logs ------------------------------------------------------------------------------------
        j = ["journalctl", "@systemd"]
        ops.update({
            "log.system": [C("journalctl", "-n", "300", "--no-pager", needs=j),
                           C("tail", "-n", "300", "/var/log/syslog", needs=["tail", "file:/var/log/syslog"], root=True),
                           C("tail", "-n", "300", "/var/log/messages", needs=["tail", "file:/var/log/messages"], root=True),
                           C("logread", tail=300)],
            "log.kernel": [C("journalctl", "-k", "-n", "300", "--no-pager", needs=j), C("dmesg", tail=300, root=True)],
            "log.auth": [C("tail", "-n", "300", "/var/log/auth.log", needs=["tail", "file:/var/log/auth.log"], root=True),
                         C("tail", "-n", "300", "/var/log/secure", needs=["tail", "file:/var/log/secure"], root=True),
                         C("journalctl", "SYSLOG_FACILITY=4", "SYSLOG_FACILITY=10", "-n", "300", "--no-pager", needs=j)],
            "log.boot": [C("journalctl", "-b", "-p", "warning", "-n", "300", "--no-pager", needs=j), C("dmesg", tail=300, root=True)],
            "log.errors": [C("journalctl", "-p", "err", "-n", "300", "--no-pager", needs=j),
                           C("tail", "-n", "3000", "/var/log/messages", needs=["tail", "file:/var/log/messages"], root=True,
                             grep="error|fail|crit|panic")],
        })
        # hardware --------------------------------------------------------------------------------
        ops.update({
            "hw.summary": [W(C("hostnamectl", needs=["hostnamectl", "@systemd"], allow_fail=True),
                             C("lscpu", optional=True, grep="model name|^cpu(s)|architecture|vendor"),
                             C("free", "-h", optional=True)),
                           C("lshw", "-short", root=True),
                           W(C("uname", "-snrmo"), C("lscpu", optional=True, grep="model name|^cpu(s)|architecture|vendor"),
                             C("free", "-h", optional=True), F(f_cat("/sys/class/dmi/id/sys_vendor", "/sys/class/dmi/id/product_name",
                                                                   "/proc/device-tree/model"), "machine model"))],
            "hw.cpu": [C("lscpu"), F(f_cat("/proc/cpuinfo"), "show /proc/cpuinfo")],
            "hw.memory": W(C("free", "-h"), C("dmidecode", "-t", "memory", optional=True, root=True, needs=["dmidecode", "@x86"],
                                               grep="size|speed|type:|locator|manufacturer")),
            "hw.gpu": [C("lspci", grep="vga|3d|display"), C("lshw", "-C", "display", root=True)],
            "hw.pci": C("lspci"),
            "hw.usb": C("lsusb"),
            "hw.bios": [C("dmidecode", "-t", "bios", "-t", "system", "-t", "baseboard", root=True, needs=["dmidecode", "@x86"]),
                        F(f_cat("/sys/class/dmi/id/bios_vendor", "/sys/class/dmi/id/bios_version", "/sys/class/dmi/id/product_name",
                                "/sys/class/dmi/id/sys_vendor", "/proc/device-tree/model"), "read firmware IDs from /sys")],
            "hw.sensors": [W(C("sensors", allow_fail=True), F(f_power_sysfs, "battery / power supplies")),
                           F(f_power_sysfs, "battery / power supplies")],
            "hw.disks": [C("lsblk", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"), C("fdisk", "-l", root=True)],
            "hw.fs": [C("df", "-hT", "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs", "-x", "overlay", allow_fail=True), C("df", "-h")],
            "hw.smart": C("smartctl", "--scan", allow_fail=True),
        })
        # time / locale ----------------------------------------------------------------------------
        td = ["timedatectl", "@systemd"]
        ops.update({
            "time.show": [C("timedatectl", needs=td), C("date")],
            "time.sync": [C("chronyc", "makestep"), C("timedatectl", "set-ntp", "true", needs=td),
                          C("ntpdate", "-b", "pool.ntp.org"), C("busybox", "ntpd", "-q", "-n", "-p", "pool.ntp.org")],
            "time.ntp.on": C("timedatectl", "set-ntp", "true", needs=td),
            "time.ntp.off": C("timedatectl", "set-ntp", "false", needs=td),
            "time.tz.list": [C("timedatectl", "list-timezones", "--no-pager", needs=td), F(f_tz_list, "list /usr/share/zoneinfo")],
            "time.tz.set": [C("timedatectl", "set-timezone", "{tz}", needs=td), F(f_tz_symlink, "link /etc/localtime to {tz}")],
            "locale.show": [C("localectl", "status", needs=["localectl", "@systemd"]), C("locale")],
            "locale.list": [C("localectl", "list-locales", "--no-pager", needs=["localectl", "@systemd"]), C("locale", "-a")],
            "locale.set": C("localectl", "set-locale", "LANG={locale}", needs=["localectl", "@systemd"]),
        })
        # kernel / boot ------------------------------------------------------------------------------
        ops.update({
            "kernel.info": W(C("uname", "-a"), F(f_proc_cmdline, "show the kernel command line")),
            "kernel.modules": C("lsmod"),
            "kernel.load": C("modprobe", "{mod}"),
            "kernel.unload": C("modprobe", "-r", "{mod}"),
            "kernel.params": C("sysctl", "-a", allow_fail=True),
            "kernel.set": W(C("sysctl", "-w", "{key}={value}"),
                            F(f_persist_sysctl("/etc/sysctl.d/99-uyast.conf"), "save in /etc/sysctl.d/99-uyast.conf", uses=["key", "value", "persist"])),
            "boot.show": W(F(f_cat("/etc/default/grub"), "show /etc/default/grub"), F(f_proc_cmdline, "kernel command line"),
                           C("bootctl", "status", "--no-pager", optional=True, allow_fail=True, root=True)),
            "boot.entries": [C("efibootmgr", "-v", root=True), C("bootctl", "list", "--no-pager", root=True)],
            "boot.grub": [C("update-grub"), C("grub2-mkconfig", "-o", "/boot/grub2/grub.cfg", needs=["grub2-mkconfig", "@grub2cfg"]),
                          C("grub-mkconfig", "-o", "/boot/grub/grub.cfg", needs=["grub-mkconfig", "@grubcfg"])],
            "boot.target.show": C("systemctl", "get-default", needs=["systemctl", "@systemd"]),
            "boot.target.set": C("systemctl", "set-default", "{target}", needs=["systemctl", "@systemd"]),
            "sched.timers": C("systemctl", "list-timers", "--all", "--no-pager", needs=sd + ["systemctl"]),
        })
        # power -------------------------------------------------------------------------------------------
        ops.update({
            "power.info": [W(C("upower", "-d", allow_fail=True)), F(f_power_sysfs, "battery / power supplies")],
            "power.reboot": [C("systemctl", "reboot", needs=["systemctl", "@systemd"]), C("shutdown", "-r", "now"), C("reboot")],
            "power.off": [C("systemctl", "poweroff", needs=["systemctl", "@systemd"]), C("shutdown", "-h", "now"), C("poweroff")],
            "power.suspend": [C("systemctl", "suspend", needs=["systemctl", "@systemd"]), C("loginctl", "suspend"), C("zzz")],
            "power.schedule": C("shutdown", "-h", "+{minutes}"),
            "power.cancel": C("shutdown", "-c"),
        })
        # security ---------------------------------------------------------------------------------------
        ops.update({
            "sec.overview": W(
                F(lambda p: f"Kernel: {platform.release()}   Distribution: {self.label}", "system"),
                C("getenforce", optional=True, allow_fail=True), C("sestatus", optional=True, allow_fail=True),
                C("aa-status", optional=True, allow_fail=True, root=True, tail=15),
                C("ufw", "status", optional=True, allow_fail=True, root=True),
                C("firewall-cmd", "--state", optional=True, allow_fail=True),
                C("sshd", "-T", optional=True, allow_fail=True, root=True,
                  grep="^permitrootlogin|^passwordauthentication|^port |^pubkeyauthentication"),
                C("systemctl", "--failed", "--no-pager", "--no-legend", optional=True, allow_fail=True, needs=["systemctl", "@systemd"])),
            "sec.failed": [C("lastb", "-n", "25", root=True, allow_fail=True),
                           C("journalctl", "_COMM=sshd", "-n", "400", "--no-pager", needs=j, grep="failed|invalid")],
        })
        return ops

    # ---- data ---------------------------------------------------------------------------------------
    def sysinfo(self):
        info = super().sysinfo()
        mem_total = mem_avail = None
        for line in read_text("/proc/meminfo").splitlines():
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1]) * 1024
            elif line.startswith("MemAvailable:"):
                mem_avail = int(line.split()[1]) * 1024
        cpu = next((l.split(":", 1)[1].strip() for l in read_text("/proc/cpuinfo").splitlines()
                    if l.lower().startswith(("model name", "hardware", "cpu model"))), "")
        if cpu:
            info.append(("CPU model", cpu))
        if mem_total:
            info.append(("Memory", f"{fmt_bytes(mem_total - (mem_avail or 0))} used of {fmt_bytes(mem_total)}"))
        up = read_text("/proc/uptime").split()
        if up:
            info.append(("Uptime", fmt_duration(float(up[0]))))
        try:
            la = os.getloadavg()
            info.append(("Load average", f"{la[0]:.2f}  {la[1]:.2f}  {la[2]:.2f}"))
        except OSError:
            pass
        virt = run_quiet(["systemd-detect-virt"], 3)[1].strip() if which_ext("systemd-detect-virt") else ""
        if virt and virt != "none":
            info.append(("Virtualization", virt))
        return info + self.tail_info()

    async def services(self, cap):
        if self.init == "systemd":
            _, units = await cap(Cmd(["systemctl", "list-units", "--type=service", "--all", "--no-legend", "--no-pager", "--plain"]))
            _, files = await cap(Cmd(["systemctl", "list-unit-files", "--type=service", "--no-legend", "--no-pager"]))
            startup = {}
            for line in files.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    startup[parts[0]] = parts[1]
            rows: Dict[str, List[str]] = {}
            for line in units.splitlines():
                parts = line.replace("●", " ").split(None, 4)
                if len(parts) >= 4 and parts[0].endswith(".service"):
                    rows[parts[0]] = [parts[0], f"{parts[2]} ({parts[3]})", startup.get(parts[0], "-"),
                                      parts[4] if len(parts) > 4 else ""]
            for name, st in startup.items():
                if name not in rows and not name.endswith("@.service"):
                    rows[name] = [name, "inactive", st, ""]
            return sorted(rows.values(), key=lambda r: r[0].lower())
        if self.init == "openrc":
            _, names = await cap(Cmd(["rc-service", "-l"]))
            _, upd = await cap(Cmd(["rc-update", "show", "-v"]))
            _, st = await cap(Cmd(["rc-status", "-a"]))
            levels = {}
            for line in upd.splitlines():
                if "|" in line:
                    n, lv = line.split("|", 1)
                    levels[n.strip()] = lv.strip()
            state = {m.group(1): m.group(2) for m in re.finditer(r"^\s*(\S+)\s+\[\s*([\w ]+?)\s*\]", st, re.M)}
            return [[n, state.get(n, "stopped"), levels.get(n) or "manual", ""]
                    for n in sorted(x.strip() for x in names.splitlines() if x.strip())]
        if self.init == "runit":
            avail = sorted(os.listdir("/etc/sv")) if os.path.isdir("/etc/sv") else []
            enabled = set(os.listdir(self.runsvdir)) if os.path.isdir(self.runsvdir) else set()
            st: Dict[str, str] = {}
            if enabled:
                _, out = await cap(Cmd(["sv", "status"] + [os.path.join(self.runsvdir, e) for e in sorted(enabled)]))
                for line in out.splitlines():
                    m = re.match(r"(\w+): ([^:]+):", line)
                    if m:
                        st[os.path.basename(m.group(2))] = m.group(1)
            return [[n, st.get(n, "down" if n in enabled else "-"), "enabled" if n in enabled else "disabled", ""]
                    for n in sorted(set(avail) | enabled)]
        if self.init == "dinit":
            _, out = await cap(Cmd(["dinitctl", "list"]))
            rows = []
            for line in out.splitlines():
                m = re.match(r"\[(.)(.)\s*(.*?)\]\s+(\S+)", line.strip())
                if m:
                    rows.append([m.group(4), "started" if "+" in m.group(1) + m.group(2) else "stopped", "-", ""])
            return rows
        try:
            names = sorted(n for n in os.listdir("/etc/init.d") if not n.startswith((".", "README", "skeleton", "rc", "functions")))
        except OSError:
            names = []
        return [[n, "?", "?", "press Status"] for n in names]

    # ---- environment -----------------------------------------------------------------------------
    def python_venv_pkgs(self) -> List[str]:
        return list(self.pmd.get("venv", []))

    def pkg_prepare_cmds(self) -> List[Cmd]:
        if self.pm in ("emerge", "nix", "swupd", "slackpkg", "") :
            return []
        steps = self.pmd.get("prepare") or self.pmd.get("refresh") or []
        return [Cmd(argv=list(a), env=self.pmd.get("env"), root=True, allow_fail=True) for a in steps]

    def env_tools(self):
        x86 = "x86" in self.caps
        termux = "Termux" in self.info.detail
        tools = [
            ("sudo", {"*": "sudo"}, "run admin tasks as a normal user", "recommended" if not termux else "info"),
            ("ip", {"dnf": "iproute", "yum": "iproute", "emerge": "sys-apps/iproute2", "*": "iproute2"}, "Network Settings", "recommended"),
            ("ping", {"apt": "iputils-ping", "emerge": "net-misc/iputils", "*": "iputils"}, "Network Diagnostics", "recommended"),
            ("ps", {"apt": "procps", "zypper": "procps", "apk": "procps", "emerge": "sys-process/procps", "*": "procps-ng"},
             "Processes", "recommended"),
            ("lspci", {"emerge": "sys-apps/pciutils", "*": "pciutils"}, "Hardware Information", "recommended"),
            ("lsusb", {"emerge": "sys-apps/usbutils", "*": "usbutils"}, "Hardware Information", "recommended"),
            ("lsblk", {"emerge": "sys-apps/util-linux", "*": "util-linux"}, "Storage", "recommended"),
            ("traceroute", {"emerge": "net-analyzer/traceroute", "*": "traceroute"}, "Network Diagnostics", "optional"),
            ("host", {"apt": "bind9-host", "pacman": "bind", "apk": "bind-tools", "emerge": "net-dns/bind-tools", "*": "bind-utils"},
             "DNS lookups", "optional"),
            ("lsof", {"emerge": "sys-process/lsof", "*": "lsof"}, "open files and ports", "optional"),
            ("sensors", {"apt": "lm-sensors", "apk": "lm-sensors", "emerge": "sys-apps/lm-sensors", "*": "lm_sensors"},
             "temperature sensors", "optional"),
            ("lpstat", {"pacman": "cups", "xbps": "cups", "emerge": "net-print/cups", "*": "cups-client"}, "Printers", "optional"),
            ("crontab", {"apt": "cron", "emerge": "sys-process/cronie", "*": "cronie"}, "Scheduled Tasks", "optional"),
        ]
        if x86:
            tools.append(("dmidecode", {"emerge": "sys-apps/dmidecode", "*": "dmidecode"}, "BIOS / memory details", "optional"))
        if self.pm in ("apt", "pacman", "apk", "xbps", "eopkg"):
            tools.append(("ufw", {"*": "ufw"}, "Firewall (UFW)", "recommended"))
        elif self.pm in ("dnf", "yum", "zypper", "urpmi"):
            tools.append(("firewall-cmd", {"*": "firewalld"}, "Firewall (firewalld)", "recommended"))
        return tools

    def pkg_manager_item(self) -> Optional[EnvItem]:
        if self.pm:
            return EnvItem("pm", "Packages", "Package manager", True, self.pkg_label, "required")
        return EnvItem("pm", "Packages", "Package manager", False,
                       "none of apt, dnf, yum, zypper, pacman, apk, xbps, emerge, eopkg, urpmi, slackpkg, swupd, opkg, nix",
                       "recommended", fix_text="install your distribution's package manager")

    def extra_env_items(self) -> List[EnvItem]:
        items = []
        if self.init == "systemd":
            rc, out = run_quiet(["systemctl", "is-system-running"], 5)
            state = out.strip() or "unknown"
            items.append(EnvItem("systemd", "Services", "systemd state", state in ("running", "degraded"),
                                 state + (" (some units failed - see Services > Failed)" if state == "degraded" else ""), "info"))
        else:
            items.append(EnvItem("init", "Services", "Service manager", bool(self.init), self.svc_label, "info"))
        return items


# ---- macOS (Apple Silicon and Intel) --------------------------------------------------------
SFW = "/usr/libexec/ApplicationFirewall/socketfilterfw"


def brew_path() -> str:
    for p in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew", "/home/linuxbrew/.linuxbrew/bin/brew"):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return which_ext("brew") or ""


def f_mac_admin(p) -> str:
    if not p.get("admin"):
        return "not added to the admin group (Administrator not ticked)"
    rc, out = run_quiet(["dseditgroup", "-o", "edit", "-a", p["user"], "-t", "user", "admin"], 30)
    if rc != 0:
        raise ValueError("dseditgroup failed: " + out.strip())
    return f"added {p['user']} to the admin group"


class MacBackend(Backend):
    family = "macos"
    flavor = "macos"
    UID_MIN = 501
    LOG_KINDS = [("log.system", "Last 15 minutes"), ("log.kernel", "Kernel"), ("log.auth", "Logins / sudo"),
                 ("log.boot", "Since boot (errors)"), ("log.errors", "Errors (1 hour)")]

    def detect_caps(self) -> set:
        self.brew = brew_path()
        caps = set()
        if self.brew:
            caps.add("brew")
        if self.info.arch == "arm64":
            caps.add("applesilicon")
        try:
            caps.add("macos11") if int(self.info.version.split(".")[0]) >= 11 else None
        except ValueError:
            pass
        return caps

    def labels(self) -> None:
        self.pkg_label = f"Homebrew ({self.brew})" if self.brew else "Homebrew is not installed - Environment Check installs it"
        self.svc_label = "launchd (launchctl)"
        self.fw_label = "Application Firewall (socketfilterfw)"
        self.fw_enable_note = ("Turns on the macOS Application Firewall. It filters per application, so use "
                               "'Allow app' / 'Block app' for programs; port rules are not used on macOS.")

    def pkg_key(self) -> str:
        return "brew"

    def build_ops(self) -> Dict[str, Any]:
        ops: Dict[str, Any] = posix_common_ops(self)
        b = self.brew or "brew"
        benv = {"HOMEBREW_NO_ENV_HINTS": "1", "NONINTERACTIVE": "1", "HOMEBREW_NO_AUTO_UPDATE": "1"}
        bu = dict(user=True, root=False, env=benv, needs=[b])

        def brew(*a, **kw):
            o = dict(bu)
            o.update(kw)
            return C(b, *a, **o)
        ops.update({
            "pkg.search": brew("search", "{q}"), "pkg.info": brew("info", "{pkg}"),
            "pkg.install": brew("install", "{*pkgs}"), "pkg.cask": brew("install", "--cask", "{*pkgs}"),
            "pkg.remove": brew("uninstall", "{*pkgs}"), "pkg.list": brew("list", "--versions"),
            "pkg.refresh": brew("update", env={"HOMEBREW_NO_ENV_HINTS": "1", "NONINTERACTIVE": "1"}),
            "pkg.upgrade": brew("upgrade", env={"HOMEBREW_NO_ENV_HINTS": "1", "NONINTERACTIVE": "1"}),
            "pkg.outdated": brew("outdated", "--verbose", allow_fail=True), "pkg.clean": brew("cleanup"),
            "pkg.repos": brew("tap"), "repo.add": brew("tap", "{repo}"),
            "os.updates.list": C("softwareupdate", "--list", allow_fail=True, root=False),
            "os.updates.install": C("softwareupdate", "--install", "--all", "--verbose"),
        })
        # services (launchd system domain) -------------------------------------------------------
        ops.update({
            "svc.start": C("launchctl", "kickstart", "system/{svc}"),
            "svc.stop": C("launchctl", "kill", "SIGTERM", "system/{svc}"),
            "svc.restart": C("launchctl", "kickstart", "-k", "system/{svc}"),
            "svc.status": C("launchctl", "print", "system/{svc}", allow_fail=True, tail=80, root=True),
            "svc.enable": C("launchctl", "enable", "system/{svc}"),
            "svc.disable": C("launchctl", "disable", "system/{svc}"),
        })
        # users and groups --------------------------------------------------------------------------
        ops.update({
            "user.add": W(C("sysadminctl", "-addUser", "{user}", "-fullName", "{user}", "-password", "{newpw}"),
                          F(f_mac_admin, "admin group", uses=["user", "admin"])),
            "user.passwd": C("sysadminctl", "-resetPasswordFor", "{user}", "-newPassword", "{newpw}"),
            "user.delete": C("sysadminctl", "-deleteUser", "{user}"),
            "user.lock": C("pwpolicy", "-u", "{user}", "-disableuser"),
            "user.unlock": C("pwpolicy", "-u", "{user}", "-enableuser"),
            "user.info": W(C("id", "{user}"), C("dscl", ".", "-read", "/Users/{user}", "RealName", "UniqueID",
                                                "NFSHomeDirectory", "UserShell", allow_fail=True)),
            "group.add": C("dseditgroup", "-o", "create", "{group}"),
            "group.delete": C("dseditgroup", "-o", "delete", "{group}"),
            "group.adduser": C("dseditgroup", "-o", "edit", "-a", "{user}", "-t", "user", "{group}"),
            "group.deluser": C("dseditgroup", "-o", "edit", "-d", "{user}", "-t", "user", "{group}"),
            "sec.admins": C("dscl", ".", "-read", "/Groups/admin", "GroupMembership"),
        })
        # network ----------------------------------------------------------------------------------------
        ops.update({
            "net.interfaces": W(C("networksetup", "-listallhardwareports"), C("ifconfig", grep="flags=|inet |inet6 |ether |status:")),
            "net.links": C("networksetup", "-listallnetworkservices"),
            "net.routes": C("netstat", "-rn"),
            "net.dns": C("scutil", "--dns", grep="resolver #|nameserver|search domain|domain   "),
            "net.ports": W(C("lsof", "-nP", "-iTCP", "-sTCP:LISTEN", root=True), C("lsof", "-nP", "-iUDP", root=True)),
            "net.conns": C("netstat", "-anp", "tcp", grep="ESTABLISHED"),
            "net.ping": C("ping", "-c", "4", "{host}", allow_fail=True),
            "net.trace": C("traceroute", "-w", "2", "-m", "20", "{host}", allow_fail=True),
            "net.arp": C("arp", "-an"),
            "net.dhcp.renew": C("ipconfig", "set", "{iface}", "DHCP"),
            "net.dns.flush": W(C("dscacheutil", "-flushcache"), C("killall", "-HUP", "mDNSResponder", allow_fail=True)),
            "net.if.up": C("ifconfig", "{iface}", "up"),
            "net.if.down": C("ifconfig", "{iface}", "down"),
            "net.wifi": C("networksetup", "-getairportnetwork", "en0", allow_fail=True),
            "net.hostname.show": W(C("scutil", "--get", "ComputerName", allow_fail=True),
                                   C("scutil", "--get", "LocalHostName", allow_fail=True), C("hostname")),
            "net.hostname.set": W(C("scutil", "--set", "ComputerName", "{hostname}"),
                                  C("scutil", "--set", "LocalHostName", "{hostname_short}"),
                                  C("scutil", "--set", "HostName", "{hostname}")),
        })
        # firewall (Application Firewall) --------------------------------------------------------------------
        ops.update({
            "fw.status": W(C(SFW, "--getglobalstate"), C(SFW, "--getstealthmode"), C(SFW, "--getblockall", allow_fail=True)),
            "fw.rules": C(SFW, "--listapps"),
            "fw.enable": C(SFW, "--setglobalstate", "on"),
            "fw.disable": C(SFW, "--setglobalstate", "off"),
            "fw.app.allow": W(C(SFW, "--add", "{path}"), C(SFW, "--unblockapp", "{path}")),
            "fw.app.block": W(C(SFW, "--add", "{path}"), C(SFW, "--blockapp", "{path}")),
            "fw.stealth.on": C(SFW, "--setstealthmode", "on"),
            "fw.stealth.off": C(SFW, "--setstealthmode", "off"),
        })
        # logs (unified logging) ---------------------------------------------------------------------------------
        lg = ["log", "show", "--style", "syslog"]
        ops.update({
            "log.system": C(*lg, "--last", "15m", tail=300),
            "log.kernel": C(*lg, "--last", "1h", "--predicate", "processID == 0", tail=300),
            "log.auth": C(*lg, "--last", "2h", "--predicate",
                          'process == "sudo" OR process == "sshd" OR process == "loginwindow" OR process == "authd"', tail=300),
            "log.boot": C(*lg, "--last", "boot", "--predicate", "messageType == error", tail=300),
            "log.errors": C(*lg, "--last", "1h", "--predicate", "messageType == error OR messageType == fault", tail=300),
        })
        # hardware ----------------------------------------------------------------------------------------------
        sp = "system_profiler"
        ops.update({
            "hw.summary": C(sp, "SPHardwareDataType"),
            "hw.cpu": W(C("sysctl", "-n", "machdep.cpu.brand_string"),
                        C("sysctl", "hw.ncpu", "hw.physicalcpu", "hw.logicalcpu", "hw.memsize", "hw.optional.arm64", allow_fail=True)),
            "hw.memory": W(C(sp, "SPMemoryDataType"), C("vm_stat")),
            "hw.gpu": C(sp, "SPDisplaysDataType"),
            "hw.pci": C(sp, "SPPCIDataType"),
            "hw.usb": W(C(sp, "SPUSBHostDataType", allow_fail=True), C(sp, "SPUSBDataType", allow_fail=True)),
            "hw.bios": C(sp, "SPHardwareDataType", grep="model|chip|processor|boot rom|firmware|serial|uuid|os loader|activation"),
            "hw.sensors": W(C("pmset", "-g", "batt"), C("pmset", "-g", "therm", allow_fail=True)),
            "hw.disks": C("diskutil", "list"),
            "hw.smart": C("diskutil", "info", "-all", grep="device identifier|smart status|media name|disk size"),
        })
        # time / locale ------------------------------------------------------------------------------------------
        ss = "systemsetup"
        ops.update({
            "time.show": W(C("date"), C(ss, "-gettimezone", allow_fail=True, root=True),
                           C(ss, "-getusingnetworktime", allow_fail=True, root=True)),
            "time.sync": C("sntp", "-sS", "time.apple.com"),
            "time.ntp.on": C(ss, "-setusingnetworktime", "on"),
            "time.ntp.off": C(ss, "-setusingnetworktime", "off"),
            "time.tz.list": C(ss, "-listtimezones", root=True),
            "time.tz.set": C(ss, "-settimezone", "{tz}"),
            "locale.show": W(C("defaults", "read", "-g", "AppleLocale", user=True, root=False, allow_fail=True),
                             C("defaults", "read", "-g", "AppleLanguages", user=True, root=False, allow_fail=True), C("locale")),
        })
        # kernel / boot / power ----------------------------------------------------------------------------------
        ops.update({
            "kernel.info": W(C("uname", "-a"), C("sw_vers")),
            "kernel.modules": [C("kmutil", "showloaded", "--list-only", allow_fail=True), C("kextstat")],
            "kernel.set": C("sysctl", "-w", "{key}={value}"),
            "boot.show": W(C("nvram", "-p", allow_fail=True, root=True), C(ss, "-getstartupdisk", allow_fail=True, root=True)),
            "power.info": W(C("pmset", "-g"), C("pmset", "-g", "batt")),
            "power.off": C("shutdown", "-h", "now"),
            "power.suspend": C("pmset", "sleepnow"),
            "power.cancel": C("killall", "shutdown", allow_fail=True),
        })
        # security -----------------------------------------------------------------------------------------------
        ops.update({
            "sec.overview": W(C("sw_vers", optional=True), C("csrutil", "status", optional=True, allow_fail=True),
                              C("spctl", "--status", optional=True, allow_fail=True),
                              C("fdesetup", "status", optional=True, allow_fail=True),
                              C(SFW, "--getglobalstate", optional=True, allow_fail=True),
                              C("profiles", "status", "-type", "enrollment", optional=True, allow_fail=True, root=True)),
            "sec.failed": C(*lg, "--last", "24h", "--predicate", 'process == "sudo" OR process == "sshd"', grep="fail|incorrect|invalid", tail=200),
        })
        return ops

    def check_hostname(self, v: Any) -> str:
        return super().check_hostname(v)

    def validate(self, name: str, v: Any) -> Dict[str, Any]:
        out = super().validate(name, v)
        if name == "hostname":
            out["hostname_short"] = out["hostname"].split(".")[0]
        return out

    def check_tz(self, v: Any) -> str:
        s = clean_arg(v, "time zone (e.g. Europe/Berlin)")
        if not re.fullmatch(r"[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+)*", s):
            raise ValueError("Time zones look like Europe/Berlin or America/New_York.")
        return s

    def sysinfo(self):
        info = super().sysinfo()
        mem = sysctl_n("hw.memsize")
        if mem.isdigit():
            info.append(("Memory", fmt_bytes(int(mem))))
        boot = re.search(r"sec\s*=\s*(\d+)", sysctl_n("kern.boottime"))
        if boot:
            info.append(("Uptime", fmt_duration(time.time() - int(boot.group(1)))))
        try:
            la = os.getloadavg()
            info.append(("Load average", f"{la[0]:.2f}  {la[1]:.2f}  {la[2]:.2f}"))
        except OSError:
            pass
        info.append(("Homebrew", self.brew or "not installed"))
        return info + self.tail_info()

    async def services(self, cap):
        _, out = await cap(Cmd(["launchctl", "list"]))
        _, dis = await cap(Cmd(["launchctl", "print-disabled", "system"]))
        disabled = {m.group(1) for m in re.finditer(r'"([^"]+)"\s*=>\s*(?:disabled|true)', dis)}
        rows = []
        for line in out.splitlines()[1:]:
            parts = line.split("\t") if "\t" in line else line.split(None, 2)
            if len(parts) >= 3:
                pid, status, label = parts[0].strip(), parts[1].strip(), parts[2].strip()
                state = f"running (pid {pid})" if pid != "-" else ("stopped" if status in ("0", "-") else f"exited ({status})")
                rows.append([label, state, "disabled" if label in disabled else "enabled", ""])
        return sorted(rows, key=lambda r: r[0].lower())

    async def users(self, cap, show_system):
        return posix_users(show_system, 501, hide_underscore=True)

    async def groups(self, cap, show_system):
        return posix_groups(show_system, 501, keep=("admin", "staff", "wheel"))

    def env_tools(self):
        return []

    def pkg_manager_item(self) -> Optional[EnvItem]:
        clt = run_quiet(["xcode-select", "-p"], 5)[0] == 0
        if self.brew:
            return EnvItem("pm", "Packages", "Homebrew", True, self.brew, "recommended", order=20)
        fix: List[Cmd] = []
        if not clt:
            fix.append(Cmd(["sh", "-c", 'touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress; '
                                        'L=$(softwareupdate -l 2>/dev/null | grep -o "Command Line Tools for Xcode-[0-9.]*" | tail -n 1); '
                                        'if [ -n "$L" ]; then softwareupdate -i "$L"; else xcode-select --install; fi; '
                                        'rm -f /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress'],
                           desc="install Apple Command Line Tools", root=True))
        fix += [Cmd(["sudo", "-v"], desc="sudo -v   (Homebrew's installer needs your password once)", root=False),
                Cmd(["/bin/bash", "-c", 'NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL '
                                        'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'],
                    desc="install Homebrew (official installer from brew.sh)", root=False)]
        return EnvItem("pm", "Packages", "Homebrew", False,
                       "not installed" + ("" if clt else "; Apple Command Line Tools missing too"), "recommended",
                       fix=fix, fix_text="install Homebrew (and the Command Line Tools)", terminal_only=True, order=20)

    def extra_env_items(self) -> List[EnvItem]:
        clt = run_quiet(["xcode-select", "-p"], 5)[0] == 0
        return [EnvItem("clt", "Packages", "Apple Command Line Tools", clt,
                        "installed" if clt else "not installed (installed together with Homebrew)", "info")]


# ---- Windows 7 / 8 / 8.1 / 10 / 11 / Server -------------------------------------------------
WIN_GNAME = (r"function GName($sid) { (New-Object System.Security.Principal.SecurityIdentifier($sid))"
             r".Translate([System.Security.Principal.NTAccount]).Value.Split('\')[-1] }; ")
WMI_FN = (r"function Get-UWmi([string]$Class, [string]$Filter) { "
          r"if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { "
          r"if ($Filter) { Get-CimInstance -ClassName $Class -Filter $Filter } else { Get-CimInstance -ClassName $Class } } "
          r"else { if ($Filter) { Get-WmiObject -Class $Class -Filter $Filter } else { Get-WmiObject -Class $Class } } }; ")
OUT = " | Out-String -Width 220"


def WPS(script: str, **kw) -> Step:
    """PowerShell step with the WMI/CIM helper available (works on PowerShell 2.0 - 5.1)."""
    return PS(WMI_FN + script, **kw)


def win_console_name() -> str:
    if os.environ.get("WT_SESSION"):
        return "Windows Terminal"
    if os.environ.get("ConEmuPID"):
        return "ConEmu"
    if os.environ.get("TERM_PROGRAM"):
        return os.environ["TERM_PROGRAM"]
    return "Windows Console Host (conhost)"


def wt_path() -> str:
    p = which_ext("wt.exe") or which_ext("wt")
    if not p:
        c = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "wt.exe")
        p = c if os.path.exists(c) else ""
    return p


def conemu_path() -> str:
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", "")):
        for exe in ("ConEmu64.exe", "ConEmu.exe"):
            p = os.path.join(base, "ConEmu", exe)
            if base and os.path.exists(p):
                return p
    return ""


class WindowsBackend(Backend):
    family = "windows"
    flavor = "windows"
    USER_COLS = ("Name", "RID", "Enabled", "Description", "SID")
    GROUP_COLS = ("Name", "SID", "Description")
    LOG_KINDS = [("log.system", "System"), ("log.app", "Application"), ("log.security", "Security"),
                 ("log.errors", "Errors & critical"), ("log.setup", "Setup / updates")]

    def detect_caps(self) -> set:
        caps = set()
        self.psver = 0
        if which_ext("powershell.exe") or which_ext("powershell") or which_ext("pwsh"):
            caps.add("ps")
            if IS_WINDOWS:
                rc, out = run_quiet([ps_exe(), "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.Major"], 30)
                m = re.search(r"\d+", out)
                self.psver = int(m.group(0)) if (rc == 0 and m) else 2
            else:
                self.psver = 5
            if self.psver >= 3:
                caps.add("ps3")
            if self.psver >= 5:
                caps.add("ps5")
        build = self.info.win_build
        if build >= 9200 or not IS_WINDOWS:
            caps.add("win8")
        if self.info.win_ver[0] >= 10 or not IS_WINDOWS:
            caps.add("win10")
        self.pm = "winget" if which_ext("winget") else ("choco" if which_ext("choco") else "")
        if self.pm:
            caps.add(self.pm)
        return caps

    def labels(self) -> None:
        self.pkg_label = {"winget": "winget (Windows Package Manager)", "choco": "Chocolatey"}.get(
            self.pm, "none - Environment Check installs winget or Chocolatey")
        self.svc_label = "Windows services (sc.exe / PowerShell)"
        self.fw_label = "Windows Defender Firewall (netsh advfirewall)"
        self.fw_enable_note = "Turns Windows Defender Firewall on for the Domain, Private and Public profiles."

    def pkg_key(self) -> str:
        return self.pm

    def build_ops(self) -> Dict[str, Any]:
        agree = ["--accept-source-agreements"]
        ops: Dict[str, Any] = {}
        if self.pm == "winget":
            ops.update({
                "pkg.search": C("winget", "search", "{q}", *agree), "pkg.info": C("winget", "show", "{*pkg_wg}", *agree),
                "pkg.install": C("winget", "install", "{*pkg_wg}", "--silent", "--accept-package-agreements", *agree, each="pkgs"),
                "pkg.remove": C("winget", "uninstall", "{*pkg_wg}", "--silent", *agree, each="pkgs"),
                "pkg.list": C("winget", "list", *agree), "pkg.refresh": C("winget", "source", "update"),
                "pkg.upgrade": C("winget", "upgrade", "--all", "--silent", "--accept-package-agreements", *agree),
                "pkg.outdated": C("winget", "upgrade", *agree, allow_fail=True), "pkg.repos": C("winget", "source", "list"),
            })
        elif self.pm == "choco":
            ops.update({
                "pkg.search": C("choco", "search", "{q}"), "pkg.info": C("choco", "info", "{pkg}"),
                "pkg.install": C("choco", "install", "-y", "{*pkgs}"), "pkg.remove": C("choco", "uninstall", "-y", "{*pkgs}"),
                "pkg.list": C("choco", "list", "--local-only", allow_fail=True), "pkg.upgrade": C("choco", "upgrade", "all", "-y"),
                "pkg.outdated": C("choco", "outdated", allow_fail=True), "pkg.repos": C("choco", "source", "list"),
            })
        ops.update({
            "os.updates.list": PS('$s = New-Object -ComObject Microsoft.Update.Session; '
                                  '$r = $s.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0"); '
                                  "if ($r.Updates.Count -eq 0) { 'No Windows updates are waiting.' } else { "
                                  "foreach ($u in $r.Updates) { '{0}   ({1} MB)' -f $u.Title, [math]::Round($u.MaxDownloadSize / 1MB, 1) } }",
                                  root=False),
            "os.updates.install": PS('$s = New-Object -ComObject Microsoft.Update.Session; '
                                     '$r = $s.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0 and Type=\'Software\'"); '
                                     "if ($r.Updates.Count -eq 0) { 'No Windows updates to install.' } else { "
                                     "$c = New-Object -ComObject Microsoft.Update.UpdateColl; "
                                     "foreach ($u in $r.Updates) { if (-not $u.EulaAccepted) { $u.AcceptEula() }; [void]$c.Add($u); 'Queued: ' + $u.Title }; "
                                     "'Downloading ...'; $d = $s.CreateUpdateDownloader(); $d.Updates = $c; [void]$d.Download(); "
                                     "'Installing ...'; $i = $s.CreateUpdateInstaller(); $i.Updates = $c; $res = $i.Install(); "
                                     "'Result code: ' + $res.ResultCode + ' (2 = succeeded)   Restart needed: ' + $res.RebootRequired }"),
        })
        # services ---------------------------------------------------------------------------------------
        ops.update({
            "svc.start": PS("Start-Service -Name {svc}; Get-Service -Name {svc}" + OUT),
            "svc.stop": PS("Stop-Service -Name {svc} -Force; Get-Service -Name {svc}" + OUT),
            "svc.restart": PS("Restart-Service -Name {svc} -Force; Get-Service -Name {svc}" + OUT),
            "svc.status": W(C("sc", "query", "{svc}", allow_fail=True), C("sc", "qc", "{svc}", allow_fail=True)),
            "svc.enable": C("sc", "config", "{svc}", "start=", "auto"),
            "svc.manual": C("sc", "config", "{svc}", "start=", "demand"),
            "svc.disable": C("sc", "config", "{svc}", "start=", "disabled"),
        })
        # users and groups (ADSI + net.exe: Windows 7 - 11, any language) ---------------------------------------
        pc = r"$pc = $env:COMPUTERNAME; "
        ops.update({
            "user.add": PS(pc + WIN_GNAME + r'$c = [ADSI]("WinNT://$pc,computer"); $u = $c.Create("User", {user}); '
                           r"if ($env:UYAST_PW) { $u.SetPassword($env:UYAST_PW) }; $u.SetInfo(); "
                           r"$u.Put('Description', 'Created by uYaST'); $u.SetInfo(); "
                           r'([ADSI]("WinNT://$pc/" + (GName "S-1-5-32-545") + ",group")).Add("WinNT://$pc/" + {user} + ",user"); '
                           r"if ($env:UYAST_ADMIN -eq '1') { "
                           r'([ADSI]("WinNT://$pc/" + (GName "S-1-5-32-544") + ",group")).Add("WinNT://$pc/" + {user} + ",user"); '
                           r"'Added to the Administrators group.' }; 'User ' + {user} + ' created.'",
                           env={"UYAST_PW": "{password}", "UYAST_ADMIN": "{admin}"}, desc="PS> create local user {user}"),
            "user.passwd": PS(r'$u = [ADSI]("WinNT://" + $env:COMPUTERNAME + "/" + {user} + ",user"); '
                              r"$u.SetPassword($env:UYAST_PW); $u.SetInfo(); 'Password changed.'",
                              env={"UYAST_PW": "{newpw}"}, desc="PS> set a new password for {user}"),
            "user.delete": PS(r'([ADSI]("WinNT://" + $env:COMPUTERNAME + ",computer")).Delete("User", {user}); ' + "'User removed.'"),
            "user.lock": C("net", "user", "{user}", "/active:no"),
            "user.unlock": C("net", "user", "{user}", "/active:yes"),
            "user.info": C("net", "user", "{user}", allow_fail=True),
            "group.add": C("net", "localgroup", "{group}", "/add"),
            "group.delete": C("net", "localgroup", "{group}", "/delete"),
            "group.adduser": C("net", "localgroup", "{group}", "{user}", "/add"),
            "group.deluser": C("net", "localgroup", "{group}", "{user}", "/delete"),
            "group.members": C("net", "localgroup", "{group}", allow_fail=True),
            "sec.admins": PS(WIN_GNAME + "$n = GName 'S-1-5-32-544'; 'Local group: ' + $n; net localgroup $n"),
        })
        # network ----------------------------------------------------------------------------------------------
        ops.update({
            "net.interfaces": C("ipconfig", "/all"),
            "net.links": C("netsh", "interface", "show", "interface"),
            "net.routes": C("route", "print"),
            "net.dns": WPS("Get-UWmi Win32_NetworkAdapterConfiguration 'IPEnabled=True' | Select-Object Description,"
                           "DNSServerSearchOrder,DNSDomain,DefaultIPGateway | Format-List" + OUT),
            "net.ports": [WPS("Get-NetTCPConnection -State Listen | Sort-Object LocalPort | Format-Table LocalAddress,LocalPort,"
                              "OwningProcess,@{n='Process';e={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}}"
                              " -AutoSize" + OUT, needs=["@win8"]),
                          C("netstat", "-ano")],
            "net.conns": [WPS("Get-NetTCPConnection -State Established | Sort-Object RemoteAddress | Format-Table LocalAddress,"
                              "LocalPort,RemoteAddress,RemotePort,OwningProcess -AutoSize" + OUT, needs=["@win8"]),
                          C("netstat", "-ano")],
            "net.ping": C("ping", "-n", "4", "{host}", allow_fail=True),
            "net.trace": C("tracert", "-d", "-h", "20", "{host}", allow_fail=True),
            "net.lookup": [C("nslookup", "{host}", allow_fail=True), F(f_lookup, "resolve {host}")],
            "net.tcptest": F(f_tcp_test, "connect to {host} port {port}"),
            "net.arp": C("arp", "-a"),
            "net.dhcp.renew": C("ipconfig", "/renew", allow_fail=True),
            "net.dns.flush": C("ipconfig", "/flushdns"),
            "net.if.up": C("netsh", "interface", "set", "interface", "name={iface}", "admin=enabled"),
            "net.if.down": C("netsh", "interface", "set", "interface", "name={iface}", "admin=disabled"),
            "net.wifi": C("netsh", "wlan", "show", "networks", "mode=bssid", allow_fail=True),
            "net.hostname.show": W(C("hostname"), F(f_hostname, "show the host name")),
            "net.hostname.set": PS("$r = (Get-WmiObject Win32_ComputerSystem).Rename({hostname}); "
                                   "if ($r.ReturnValue -eq 0) { 'Renamed - restart Windows to apply it.' } "
                                   "else { throw ('Rename failed, error code ' + $r.ReturnValue) }"),
            "hosts.show": F(f_hosts_show, "show the hosts file"),
            "hosts.add": W(F(f_hosts_add, "add {ip} {entry} to the hosts file"), C("ipconfig", "/flushdns", allow_fail=True)),
            "hosts.remove": W(F(f_hosts_remove, "remove {entry} from the hosts file"), C("ipconfig", "/flushdns", allow_fail=True)),
        })
        # firewall -----------------------------------------------------------------------------------------------
        nf = ["netsh", "advfirewall"]
        ops.update({
            "fw.status": C(*nf, "show", "allprofiles", "state"),
            "fw.rules": C(*nf, "firewall", "show", "rule", "name=all", grep="uyast", allow_fail=True),
            "fw.enable": C(*nf, "set", "allprofiles", "state", "on"),
            "fw.disable": C(*nf, "set", "allprofiles", "state", "off"),
            "fw.allow": C(*nf, "firewall", "add", "rule", "name=uYaST-allow-{port_dash}-{proto}", "dir=in", "action=allow",
                          "protocol={proto_upper}", "localport={port_dash}"),
            "fw.remove": C(*nf, "firewall", "delete", "rule", "name=uYaST-allow-{port_dash}-{proto}"),
        })
        # logs (wevtutil: Vista and newer) ------------------------------------------------------------------------
        def wev(log, count="150", query=None, **kw):
            a = ["wevtutil", "qe", log, f"/c:{count}", "/rd:true", "/f:text"]
            if query:
                a.insert(3, f"/q:{query}")
            return C(*a, allow_fail=True, **kw)
        ops.update({
            "log.system": wev("System"), "log.app": wev("Application"), "log.security": wev("Security", root=True),
            "log.errors": wev("System", query="*[System[(Level=1 or Level=2)]]"),
            "log.setup": wev("Setup", count="80"),
        })
        # hardware ----------------------------------------------------------------------------------------------
        ops.update({
            "hw.summary": WPS("Get-UWmi Win32_ComputerSystem | Format-List Manufacturer,Model,SystemType,NumberOfProcessors,"
                              "@{n='MemoryGB';e={[math]::Round($_.TotalPhysicalMemory/1GB,1)}}" + OUT +
                              "; Get-UWmi Win32_OperatingSystem | Format-List Caption,Version,BuildNumber,OSArchitecture,InstallDate,LastBootUpTime" + OUT),
            "hw.full": C("systeminfo"),
            "hw.cpu": WPS("Get-UWmi Win32_Processor | Format-List Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,"
                          "MaxClockSpeed,L2CacheSize,L3CacheSize,VirtualizationFirmwareEnabled" + OUT),
            "hw.memory": WPS("Get-UWmi Win32_PhysicalMemory | Format-Table BankLabel,DeviceLocator,"
                             "@{n='GB';e={[math]::Round($_.Capacity/1GB,1)}},Speed,Manufacturer,PartNumber -AutoSize" + OUT +
                             "; $os = Get-UWmi Win32_OperatingSystem; 'Free memory: ' + [math]::Round($os.FreePhysicalMemory/1MB,2) + "
                             "' GB of ' + [math]::Round($os.TotalVisibleMemorySize/1MB,2) + ' GB'"),
            "hw.gpu": WPS("Get-UWmi Win32_VideoController | Format-List Name,DriverVersion,VideoModeDescription,"
                          "@{n='MemoryMB';e={[math]::Round($_.AdapterRAM/1MB)}}" + OUT),
            "hw.pci": WPS("Get-UWmi Win32_PnPEntity | Where-Object { $_.DeviceID -like 'PCI*' } | Sort-Object Name | "
                          "Format-Table Name,Status -AutoSize" + OUT),
            "hw.usb": WPS("Get-UWmi Win32_PnPEntity | Where-Object { $_.DeviceID -like 'USB*' } | Sort-Object Name | "
                          "Format-Table Name,Status -AutoSize" + OUT),
            "hw.bios": WPS("Get-UWmi Win32_BIOS | Format-List Manufacturer,SMBIOSBIOSVersion,ReleaseDate,SerialNumber" + OUT +
                           "; Get-UWmi Win32_BaseBoard | Format-List Manufacturer,Product,Version" + OUT),
            "hw.sensors": WPS("$b = Get-UWmi Win32_Battery; if ($b) { $b | Format-List Name,EstimatedChargeRemaining,"
                              "BatteryStatus,EstimatedRunTime" + OUT + " } else { 'No battery found.' }; "
                              "try { Get-WmiObject -Namespace root/wmi MSAcpi_ThermalZoneTemperature | ForEach-Object { "
                              "'Thermal zone ' + $_.InstanceName + ': ' + [math]::Round($_.CurrentTemperature / 10 - 273.15, 1) + ' C' } } "
                              "catch { 'Temperature sensors are not exposed by this computer.' }"),
            "hw.disks": WPS("Get-UWmi Win32_DiskDrive | Format-Table Model,InterfaceType,MediaType,"
                            "@{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}},Status -AutoSize" + OUT),
            "hw.fs": WPS("Get-UWmi Win32_LogicalDisk | Format-Table DeviceID,VolumeName,FileSystem,"
                         "@{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}},@{n='FreeGB';e={[math]::Round($_.FreeSpace/1GB,1)}} -AutoSize" + OUT),
            "hw.smart": WPS("Get-UWmi Win32_DiskDrive | Format-Table Model,Status -AutoSize" + OUT),
            "hw.printers": WPS("Get-UWmi Win32_Printer | Format-Table Name,Default,PortName,DriverName -AutoSize" + OUT),
            "printer.default": C("rundll32", "printui.dll,PrintUIEntry", "/y", "/n", "{printer}"),
            "printer.jobs": WPS("$j = Get-UWmi Win32_PrintJob; if ($j) { $j | Format-Table Document,JobStatus,Owner,TotalPages -AutoSize" + OUT +
                                " } else { 'No print jobs.' }"),
            "printer.cancel": PS("$j = Get-WmiObject Win32_PrintJob; if ($j) { $j | ForEach-Object { [void]$_.Delete() }; "
                                 "'Cancelled ' + @($j).Count + ' job(s).' } else { 'No print jobs.' }"),
        })
        # time / locale -----------------------------------------------------------------------------------------
        ops.update({
            "time.show": W(PS("Get-Date | Out-String"), C("tzutil", "/g"), C("w32tm", "/query", "/status", allow_fail=True)),
            "time.sync": W(C("net", "start", "w32time", allow_fail=True), C("w32tm", "/resync", allow_fail=True)),
            "time.tz.list": C("tzutil", "/l"),
            "time.tz.set": C("tzutil", "/s", "{tz}"),
            "locale.show": W(PS("[System.Globalization.CultureInfo]::CurrentCulture | Format-List Name,DisplayName" + OUT +
                                "; [System.Globalization.CultureInfo]::CurrentUICulture | Format-List Name,DisplayName" + OUT),
                             PS("Get-WinSystemLocale" + OUT, needs=["@win8"], optional=True, allow_fail=True)),
            "locale.set": PS("Set-WinSystemLocale -SystemLocale {locale}; 'System locale set - restart Windows to apply it.'",
                             needs=["@win8"]),
        })
        # kernel / boot / scheduled tasks / power -------------------------------------------------------------------
        ops.update({
            "kernel.info": W(C("cmd", "/c", "ver"), PS("[Environment]::OSVersion | Format-List" + OUT)),
            "kernel.modules": C("driverquery", "/fo", "table"),
            "boot.show": C("bcdedit", "/enum", root=True),
            "boot.entries": C("bcdedit", "/enum", "firmware", root=True, allow_fail=True),
            "boot.timeout": C("bcdedit", "/timeout", "{seconds}"),
            "sched.list": C("schtasks", "/query", "/fo", "table"),
            "sched.run": C("schtasks", "/run", "/tn", "{task}"),
            "sched.enable": C("schtasks", "/change", "/tn", "{task}", "/enable"),
            "sched.disable": C("schtasks", "/change", "/tn", "{task}", "/disable"),
            "power.info": W(C("powercfg", "/list"), C("powercfg", "/getactivescheme")),
            "power.plan.set": C("powercfg", "/setactive", "{plan}"),
            "power.reboot": C("shutdown", "/r", "/t", "0"),
            "power.off": C("shutdown", "/s", "/t", "0"),
            "power.schedule": C("shutdown", "/s", "/t", "{seconds_total}"),
            "power.cancel": C("shutdown", "/a"),
            "proc.kill": C("taskkill", "/PID", "{pid}"),
            "proc.kill9": C("taskkill", "/F", "/PID", "{pid}"),
        })
        # security ----------------------------------------------------------------------------------------------
        ops.update({
            "sec.overview": W(
                PS("Get-MpComputerStatus | Format-List AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,"
                   "AntivirusSignatureLastUpdated,QuickScanEndTime" + OUT, needs=["@win8"], optional=True, allow_fail=True),
                C(*nf, "show", "allprofiles", "state", optional=True, allow_fail=True),
                C("reg", "query", r"HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System", "/v", "EnableLUA",
                  optional=True, allow_fail=True),
                PS("try { 'Secure Boot enabled: ' + (Confirm-SecureBootUEFI) } catch { 'Secure Boot: not supported (legacy BIOS) or not readable' }",
                   needs=["@win8"], optional=True, allow_fail=True),
                C("manage-bde", "-status", optional=True, allow_fail=True, root=True)),
            "sec.logins": C("wevtutil", "qe", "Security", "/q:*[System[(EventID=4624)]]", "/c:10", "/rd:true", "/f:text",
                            root=True, allow_fail=True),
            "sec.failed": C("wevtutil", "qe", "Security", "/q:*[System[(EventID=4625)]]", "/c:20", "/rd:true", "/f:text",
                            root=True, allow_fail=True),
            "sec.scan": [PS("Start-MpScan -ScanType QuickScan; 'Quick scan finished.'", needs=["@win8"]),
                         PS(r"& (Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe') -Scan -ScanType 1")],
        })
        return ops

    # ---- validation specific to Windows ---------------------------------------------------------------
    def check_user(self, v: Any) -> str:
        s = clean_arg(v, "user name", spaces=True)
        if not RE_WIN_NAME.match(s) or len(s) > 20:
            raise ValueError('Windows user names: max 20 characters, none of \\ / [ ] : ; | = , + * ? < > " @')
        return s

    def check_group(self, v: Any) -> str:
        s = clean_arg(v, "group name", spaces=True)
        if not RE_WIN_NAME.match(s):
            raise ValueError('Group names cannot contain \\ / [ ] : ; | = , + * ? < > " @')
        return s

    def check_hostname(self, v: Any) -> str:
        s = clean_arg(v, "computer name")
        if not re.fullmatch(r"[A-Za-z0-9-]{1,15}", s) or s.isdigit():
            raise ValueError("Windows computer names: letters, digits and '-', max 15 characters, not only digits.")
        return s

    def check_tz(self, v: Any) -> str:
        s = clean_arg(v, "time zone (e.g. W. Europe Standard Time)", spaces=True)
        if not re.fullmatch(r"[A-Za-z0-9 ._()+&'-]+", s):
            raise ValueError("Use a Windows time zone ID from 'List time zones', e.g. W. Europe Standard Time.")
        return s

    def validate(self, name: str, v: Any) -> Dict[str, Any]:
        if name == "task":
            s = str(v or "").strip()
            if not s or _CTRL.search(s) or s.startswith("-"):
                raise ValueError("Please enter a task name (e.g. \\Microsoft\\Windows\\Defrag\\ScheduledDefrag).")
            return {"task": s}
        return super().validate(name, v)

    def console_cmd(self, command: str) -> Cmd:
        command = (command or "").strip()
        if not command:
            raise ValueError("Please type a command.")
        return ps_cmd(command, allow_fail=True)

    # ---- data ---------------------------------------------------------------------------------------------
    @staticmethod
    def _csv(out: str) -> List[Dict[str, str]]:
        text = out.lstrip("\ufeff").strip()
        if not text:
            return []
        start = text.find('"')
        return list(csv.DictReader(io.StringIO(text[start:] if start >= 0 else text)))

    async def services(self, cap):
        rc, out = await cap(ps_cmd(WMI_FN + "Get-UWmi Win32_Service | Select-Object Name,DisplayName,State,StartMode | "
                                   "ConvertTo-Csv -NoTypeInformation"), 90)
        rows = [[d.get("Name") or "", d.get("State") or "", d.get("StartMode") or "", d.get("DisplayName") or ""]
                for d in self._csv(out)]
        return sorted(rows, key=lambda r: r[0].lower())

    async def users(self, cap, show_system):
        rc, out = await cap(ps_cmd(WMI_FN + "Get-UWmi Win32_UserAccount 'LocalAccount=True' | Select-Object Name,SID,"
                                   "Disabled,Description | ConvertTo-Csv -NoTypeInformation"), 60)
        rows = []
        for d in self._csv(out):
            sid = d.get("SID") or ""
            rid = sid.rsplit("-", 1)[-1]
            regular = rid.isdigit() and int(rid) >= 1000
            if regular or show_system:
                rows.append([d.get("Name") or "", rid, "no" if (d.get("Disabled") or "").lower() == "true" else "yes",
                             d.get("Description") or "", sid])
        return rows

    async def groups(self, cap, show_system):
        rc, out = await cap(ps_cmd(WMI_FN + "Get-UWmi Win32_Group 'LocalAccount=True' | Select-Object Name,SID,Description | "
                                   "ConvertTo-Csv -NoTypeInformation"), 60)
        return [[d.get("Name") or "", d.get("SID") or "", d.get("Description") or ""] for d in self._csv(out)]

    async def processes(self, cap):
        rc, out = await cap(Cmd(["tasklist", "/v", "/fo", "csv", "/nh"]), 60)
        rows = []
        for r in csv.reader(io.StringIO(out)):
            if len(r) >= 8 and r[1].strip().isdigit():
                rows.append([r[1], r[6], r[7], r[4], r[0]])
            elif len(r) >= 5 and r[1].strip().isdigit():
                rows.append([r[1], "", "", r[4], r[0]])
        return rows

    def sysinfo(self):
        info = super().sysinfo()
        try:
            import ctypes

            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMSTAT()
            m.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            info.append(("Memory", f"{fmt_bytes(m.ullTotalPhys - m.ullAvailPhys)} used of {fmt_bytes(m.ullTotalPhys)}"))
            ctypes.windll.kernel32.GetTickCount64.restype = ctypes.c_ulonglong
            info.append(("Uptime", fmt_duration(ctypes.windll.kernel32.GetTickCount64() / 1000)))
        except Exception:
            pass
        cpu = os.environ.get("PROCESSOR_IDENTIFIER", "")
        if cpu:
            info.append(("CPU model", cpu))
        info.append(("PowerShell", f"{self.psver}.x" if self.psver else "not found"))
        info.append(("Console", win_console_name()))
        return info + self.tail_info()

    # ---- environment ---------------------------------------------------------------------------------------
    def pkg_manager_item(self) -> Optional[EnvItem]:
        if self.pm:
            return EnvItem("pm", "Packages", "Package manager", True, self.pkg_label, "recommended", order=20)
        fix: List[Cmd] = []
        if self.info.win_build >= 17763:
            fix.append(ps_cmd("Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe",
                              allow_fail=True, desc="register winget (App Installer)"))
        fix.append(ps_cmd("if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { "
                          "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                          "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                          "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')) }",
                          root=True, desc="install Chocolatey if winget is still missing (community.chocolatey.org)"))
        return EnvItem("pm", "Packages", "Package manager", False, "neither winget nor Chocolatey found", "recommended",
                       fix=fix, fix_text="register winget, or install Chocolatey", order=20)

    def extra_env_items(self) -> List[EnvItem]:
        items: List[EnvItem] = []
        items.append(EnvItem("ps", "Core", "Windows PowerShell", "ps" in self.caps,
                             f"version {self.psver}" if self.psver else "not found - most modules need it", "required"))
        rc, out = run_quiet(["sc", "query", "winmgmt"], 10)
        running = "RUNNING" in out.upper() or rc != 0 and not IS_WINDOWS
        items.append(EnvItem("wmi", "Services", "WMI service (winmgmt)", running, "running" if running else "not running",
                             "recommended", fix=[Cmd(["sc", "config", "winmgmt", "start=", "auto"], root=True),
                                                 Cmd(["net", "start", "winmgmt"], root=True, allow_fail=True)],
                             fix_text="start the WMI service", order=30))
        build = self.info.win_build
        console = win_console_name()
        modern = console != "Windows Console Host (conhost)"
        vt_ok = build >= 10586 or modern or not IS_WINDOWS
        wt, ce = wt_path(), conemu_path()
        if not vt_ok:
            fix = [] if ce else [Cmd(["choco", "install", "conemu", "-y"], root=True, desc="choco install conemu")]
            items.append(EnvItem("term", "Terminal", "Terminal with colour/escape support", bool(ce),
                                 f"{console} on Windows {self.info.win_ver[0]}.{self.info.win_ver[1]} cannot draw the TUI"
                                 + ("; ConEmu is installed - uYaST opens itself in it" if ce else "; ConEmu is needed"),
                                 "required", fix=fix, fix_text="install ConEmu (via Chocolatey)", order=40))
        else:
            fix = []
            if not wt and build >= 19041:
                fix = [Cmd(["winget", "install", "-e", "--id", "Microsoft.WindowsTerminal", "--accept-package-agreements",
                            "--accept-source-agreements"], root=False, allow_fail=True, desc="winget install Windows Terminal")] \
                    if which_ext("winget") else [Cmd(["choco", "install", "microsoft-windows-terminal", "-y"], root=True)]
            ok = modern or bool(wt) or build < 19041
            items.append(EnvItem("term", "Terminal", "Modern terminal + fonts (Windows Terminal, Cascadia)", ok,
                                 console + ("" if modern else ("; Windows Terminal is installed - uYaST opens itself in it" if wt
                                                               else "; Windows Terminal brings full colours, mouse and the Cascadia fonts")),
                                 "recommended", fix=fix, fix_text="install Windows Terminal", order=40))
        return items


# ---- Unix: FreeBSD, DragonFly, OpenBSD, NetBSD, illumos / Solaris, other POSIX ----------------
def f_hash_passwd(hasher: List[str], usermod: List[str]) -> Callable[[Dict[str, Any]], str]:
    """OpenBSD 'encrypt' / NetBSD 'pwhash': hash from stdin, then usermod -p (password never on a command line)."""
    def fn(p) -> str:
        pw = p.get("newpw") or p.get("password")
        if not pw:
            return "no password given - the account stays locked until you set one"
        rc, out = run_quiet(hasher, 15, input_text=pw + "\n")
        hashed = out.strip().splitlines()[-1].strip() if out.strip() else ""
        if rc != 0 or not hashed or " " in hashed:
            raise ValueError("could not hash the password: " + out.strip())
        rc, out = run_quiet(usermod + [hashed, p["user"]], 30)
        if rc != 0:
            raise ValueError("usermod failed: " + out.strip())
        return "password set"
    return fn


def f_pw_passwd_opt(p) -> str:
    if not p.get("password"):
        return "no password given - the account stays locked until you set one"
    rc, out = run_quiet(["pw", "usermod", "-n", p["user"], "-h", "0"], 30, input_text=p["password"] + "\n")
    if rc != 0:
        raise ValueError("pw usermod failed: " + out.strip())
    return "password set"


def f_solaris_addgroup(p) -> str:
    """Solaris/illumos usermod -G replaces the list, so merge with the current groups first."""
    import grp
    cur = [g.gr_name for g in grp.getgrall() if p["user"] in g.gr_mem]
    if p["group"] not in cur:
        cur.append(p["group"])
    rc, out = run_quiet(["usermod", "-G", ",".join(cur), p["user"]], 30)
    if rc != 0:
        raise ValueError(out.strip())
    return f"{p['user']} is now in: {', '.join(cur)}"


def f_write_myname(p) -> str:
    path = "/etc/nodename" if os.path.exists("/etc/nodename") else "/etc/myname"
    Path(path).write_text(p["hostname"] + "\n")
    return f"wrote {path}"


class UnixBackend(Backend):
    family = "unix"
    LOG_KINDS = [("log.system", "System log"), ("log.kernel", "Kernel messages"), ("log.auth", "Authentication"),
                 ("log.boot", "Boot messages"), ("log.errors", "Errors only")]

    def __init__(self, info: PlatformInfo):
        self.flavor = info.flavor
        super().__init__(info)

    def detect_caps(self) -> set:
        caps = {self.flavor}
        fl = self.flavor
        if fl in ("freebsd", "dragonfly"):
            self.pm = "pkg" if (which_ext("pkg") and run_quiet(["pkg", "-N"], 5)[0] == 0) else ""
        elif fl == "openbsd":
            self.pm = "pkg_add" if which_ext("pkg_add") else ""
        elif fl == "netbsd":
            self.pm = "pkgin" if which_ext("pkgin") else ""
        elif fl in ("illumos", "solaris"):
            self.pm = "ips" if which_ext("pkg") else ("pkgin" if which_ext("pkgin") else "")
        else:
            self.pm = ""
        if self.pm:
            caps.add("pm")
        return caps

    def labels(self) -> None:
        fl = self.flavor
        self.pkg_label = {"pkg": "pkg", "pkg_add": "pkg_add / pkg_info", "pkgin": "pkgin (pkgsrc)", "ips": "pkg (IPS)"
                          }.get(self.pm, "none found" + (" - Environment Check can set it up" if fl in ("freebsd", "dragonfly", "netbsd") else ""))
        self.svc_label = {"freebsd": "rc.d (service, sysrc)", "dragonfly": "rc.d (service, rc.conf)",
                          "openbsd": "rc.d (rcctl)", "netbsd": "rc.d (service, rc.conf)",
                          "illumos": "SMF (svcs, svcadm)", "solaris": "SMF (svcs, svcadm)"}.get(fl, "not available")
        self.fw_label = {"freebsd": "pf (rules in anchor 'uyast')", "dragonfly": "pf (rules in anchor 'uyast')",
                         "openbsd": "pf (rules in anchor 'uyast')", "netbsd": "NPF (npfctl)",
                         "illumos": "IP Filter (ipf)", "solaris": "IP Filter (ipf)"}.get(fl, "not available")
        if fl in ("freebsd", "dragonfly", "openbsd"):
            self.fw_enable_note = ("If /etc/pf.conf does not exist, a default one is created that blocks inbound traffic "
                                   "except SSH (22/tcp), ICMP and ports you open here. An existing pf.conf is backed up and "
                                   "only gets the 'uyast' anchor appended.")
        else:
            self.fw_enable_note = "Starts the system firewall with its current rule file."

    def pkg_key(self) -> str:
        return self.pm

    def build_ops(self) -> Dict[str, Any]:
        fl = self.flavor
        ops: Dict[str, Any] = posix_common_ops(self)
        ops["net.ping"] = C("ping", "-c", "4", "{host}", allow_fail=True)
        ops["net.interfaces"] = C("ifconfig", "-a")
        ops["net.routes"] = C("netstat", "-rn")
        ops["net.hostname.set"] = W(F(f_write_myname, "write {hostname} to /etc/myname"), C("hostname", "{hostname}"))
        ops["kernel.set"] = W(C("sysctl", "{key}={value}"), F(f_persist_sysctl("/etc/sysctl.conf"), "save in /etc/sysctl.conf",
                                                              uses=["key", "value", "persist"]))
        ops["power.off"] = C("shutdown", "-p", "now")
        ops["power.schedule"] = C("shutdown", "-p", "+{minutes}")
        ops["sec.admins"] = F(f_members("wheel", "operator", "sudo"), "members of wheel / operator")
        ops["time.tz.list"] = F(f_tz_list, "list /usr/share/zoneinfo")
        ops["time.tz.set"] = F(f_tz_symlink, "link /etc/localtime to {tz}")
        ops["time.sync"] = [C("ntpdate", "-b", "pool.ntp.org"), C("rdate", "-n", "pool.ntp.org"), C("ntpd", "-q", "-g")]
        ops["log.system"] = C("tail", "-n", "300", "/var/log/messages", root=True)
        ops["log.kernel"] = C("dmesg", tail=300)
        ops["log.boot"] = [F(f_cat("/var/run/dmesg.boot"), "show /var/run/dmesg.boot", needs=["file:/var/run/dmesg.boot"]),
                           C("dmesg", tail=300)]
        ops["log.errors"] = C("tail", "-n", "3000", "/var/log/messages", root=True, grep="error|fail|panic|crit")
        ops["hw.disks"] = C("sysctl", "hw.disknames")
        ops["sec.overview"] = W(C("uname", "-a", optional=True), C("sysctl", "kern.securelevel", optional=True, allow_fail=True))

        if fl in ("freebsd", "dragonfly"):
            env = {"ASSUME_ALWAYS_YES": "yes"}
            ops.update({
                "pkg.search": C("pkg", "search", "{q}"), "pkg.info": C("pkg", "search", "-f", "{pkg}"),
                "pkg.install": C("pkg", "install", "-y", "{*pkgs}", env=env), "pkg.remove": C("pkg", "delete", "-y", "{*pkgs}", env=env),
                "pkg.list": C("pkg", "info"), "pkg.refresh": C("pkg", "update", env=env),
                "pkg.upgrade": W(C("pkg", "update", env=env), C("pkg", "upgrade", "-y", env=env)),
                "pkg.outdated": C("pkg", "version", "-vRL=", allow_fail=True), "pkg.repos": C("pkg", "-vv", tail=40),
                "pkg.clean": W(C("pkg", "autoremove", "-y", env=env), C("pkg", "clean", "-ay", env=env)),
                "svc.start": C("service", "{svc}", "onestart"), "svc.stop": C("service", "{svc}", "onestop"),
                "svc.restart": C("service", "{svc}", "onerestart"), "svc.status": C("service", "{svc}", "onestatus", allow_fail=True),
                "user.add": W(C("pw", "useradd", "-n", "{user}", "-m", "-s", "/bin/sh", "-c", "{user}"),
                              F(f_pw_passwd_opt, "set the password (pw usermod -h 0, via stdin)", uses=["user", "password"]),
                              F(f_admin_group(("wheel",), lambda u, g: ["pw", "groupmod", g, "-m", u]), "wheel group", uses=["user", "admin"])),
                "user.passwd": C("pw", "usermod", "-n", "{user}", "-h", "0", input="{newpw}\n", desc="pw usermod -n {user} -h 0  (password via stdin)"),
                "user.delete": C("pw", "userdel", "-n", "{user}", "-r"),
                "user.lock": C("pw", "lock", "{user}"), "user.unlock": C("pw", "unlock", "{user}"),
                "user.info": W(C("id", "{user}"), C("pw", "usershow", "{user}")),
                "group.add": C("pw", "groupadd", "{group}"), "group.delete": C("pw", "groupdel", "{group}"),
                "group.adduser": C("pw", "groupmod", "{group}", "-m", "{user}"),
                "group.deluser": C("pw", "groupmod", "{group}", "-d", "{user}"),
                "net.dns": F(f_resolv, "show /etc/resolv.conf"),
                "net.ports": C("sockstat", "-4", "-6", "-l"), "net.conns": C("sockstat", "-4", "-6", "-c"),
                "net.dhcp.renew": C("dhclient", "{iface}"),
                "net.if.up": C("ifconfig", "{iface}", "up"), "net.if.down": C("ifconfig", "{iface}", "down"),
                "log.auth": C("tail", "-n", "300", "/var/log/auth.log", root=True),
                "hw.summary": C("sysctl", "hw.model", "hw.machine", "hw.ncpu", "hw.physmem", "kern.ostype", "kern.osrelease"),
                "hw.cpu": C("sysctl", "hw.model", "hw.ncpu", "hw.clockrate", allow_fail=True),
                "hw.memory": C("sysctl", "hw.physmem", "hw.usermem", "hw.realmem", allow_fail=True),
                "hw.pci": C("pciconf", "-lv", root=True), "hw.gpu": C("pciconf", "-lv", grep="vga|display|3d", root=True),
                "hw.usb": [C("usbconfig", "list", root=True), C("usbdevs", "-v")],
                "hw.bios": C("kenv", grep="smbios", allow_fail=True),
                "hw.sensors": W(C("sysctl", "-a", grep="temperature", allow_fail=True), C("acpiconf", "-i", "0", optional=True, allow_fail=True)),
                "kernel.modules": C("kldstat"), "kernel.load": C("kldload", "{mod}"), "kernel.unload": C("kldunload", "{mod}"),
                "boot.show": F(f_cat("/boot/loader.conf", "/boot/loader.conf.local"), "show /boot/loader.conf"),
                "boot.entries": C("efibootmgr", "-v", root=True),
                "power.info": C("acpiconf", "-i", "0", allow_fail=True), "power.suspend": C("acpiconf", "-s", "3"),
            })
            if fl == "freebsd":
                ops.update({
                    "svc.enable": C("service", "{svc}", "enable"), "svc.disable": C("service", "{svc}", "disable"),
                    "net.hostname.set": W(C("sysrc", "hostname={hostname}"), C("hostname", "{hostname}")),
                    "hw.disks": W(C("geom", "disk", "list", grep="name:|mediasize|descr|ident"), C("gpart", "show", optional=True)),
                    "time.tz.set": C("tzsetup", "{tz}"),
                    "os.updates.list": C("freebsd-update", "--not-running-from-cron", "fetch", env={"PAGER": "cat"},
                                         allow_fail=True, root=True),
                    "os.updates.install": C("freebsd-update", "--not-running-from-cron", "install", env={"PAGER": "cat"},
                                            ok_codes=(0, 2)),
                    "sec.scan": C("pkg", "audit", "-F", allow_fail=True),
                })
                ops["sec.overview"] = W(C("freebsd-version", "-kru", optional=True), C("sysctl", "kern.securelevel", optional=True),
                                        C("pfctl", "-s", "info", optional=True, allow_fail=True, root=True),
                                        C("pkg", "audit", optional=True, allow_fail=True))
            else:
                ops.update({"svc.enable": F(f_rcconf("YES"), "set {svc}_enable=YES in /etc/rc.conf"),
                            "svc.disable": F(f_rcconf("NO"), "set {svc}_enable=NO in /etc/rc.conf")})
            anchor = "/usr/local/etc/uyast/pf-anchor.conf"
            self._pf_ops(ops, anchor, start=[C("kldload", "-n", "pf"), C("sysrc", "pf_enable=YES", needs=["sysrc"], optional=True)])
        elif fl == "openbsd":
            ops.update({
                "pkg.search": C("pkg_info", "-Q", "{q}"), "pkg.info": C("pkg_info", "{pkg}", allow_fail=True),
                "pkg.install": C("pkg_add", "-I", "{*pkgs}"), "pkg.remove": C("pkg_delete", "-I", "{*pkgs}"),
                "pkg.list": C("pkg_info", "-mz"), "pkg.upgrade": C("pkg_add", "-Iu"),
                "pkg.outdated": C("pkg_add", "-Iun", allow_fail=True), "pkg.clean": C("pkg_delete", "-Ia"),
                "pkg.repos": F(f_cat("/etc/installurl"), "show /etc/installurl"),
                "os.updates.list": C("syspatch", "-c", allow_fail=True, root=True), "os.updates.install": C("syspatch"),
                "os.firmware": C("fw_update"),
                "svc.start": C("rcctl", "start", "{svc}"), "svc.stop": C("rcctl", "stop", "{svc}"),
                "svc.restart": C("rcctl", "restart", "{svc}"), "svc.status": C("rcctl", "check", "{svc}", allow_fail=True),
                "svc.enable": C("rcctl", "enable", "{svc}"), "svc.disable": C("rcctl", "disable", "{svc}"),
                "user.add": W(C("useradd", "-m", "-s", "/bin/ksh", "{user}"),
                              F(f_hash_passwd(["encrypt"], ["usermod", "-p"]), "set the password (encrypt + usermod)", uses=["user", "password"]),
                              F(f_admin_group(("wheel",), lambda u, g: ["usermod", "-G", g, u]), "wheel group", uses=["user", "admin"])),
                "user.passwd": F(f_hash_passwd(["encrypt"], ["usermod", "-p"]), "set a new password for {user}", uses=["user", "newpw"]),
                "user.delete": C("userdel", "-r", "{user}"), "user.info": W(C("id", "{user}"), C("userinfo", "{user}", optional=True)),
                "group.add": C("groupadd", "{group}"), "group.delete": C("groupdel", "{group}"),
                "group.adduser": C("usermod", "-G", "{group}", "{user}"),
                "net.ports": W(C("netstat", "-an", "-f", "inet", grep="listen"), C("netstat", "-an", "-f", "inet6", grep="listen")),
                "net.conns": C("netstat", "-an", "-f", "inet", grep="established"),
                "net.routes": C("route", "-n", "show"),
                "net.dhcp.renew": [C("dhcpleasectl", "{iface}"), C("dhclient", "{iface}")],
                "net.if.up": C("ifconfig", "{iface}", "up"), "net.if.down": C("ifconfig", "{iface}", "down"),
                "log.auth": C("tail", "-n", "300", "/var/log/authlog", root=True),
                "hw.summary": C("sysctl", "hw.vendor", "hw.product", "hw.model", "hw.ncpu", "hw.physmem", "kern.version", allow_fail=True),
                "hw.cpu": C("sysctl", "hw.model", "hw.ncpu", "hw.ncpuonline", "hw.cpuspeed", allow_fail=True),
                "hw.memory": C("sysctl", "hw.physmem", "hw.usermem"),
                "hw.pci": C("pcidump", "-v", root=True), "hw.gpu": C("pcidump", "-v", grep="vga|display", root=True),
                "hw.usb": C("usbdevs", "-v", allow_fail=True),
                "hw.bios": C("sysctl", "hw.vendor", "hw.product", "hw.version", "hw.serialno", "hw.uuid", allow_fail=True),
                "hw.sensors": W(C("sysctl", "hw.sensors", allow_fail=True), C("apm", optional=True, allow_fail=True)),
                "boot.show": F(f_cat("/etc/boot.conf", "/etc/rc.conf.local"), "show /etc/boot.conf"),
                "power.info": C("apm", allow_fail=True), "power.suspend": C("zzz"),
                "power.off": C("shutdown", "-hp", "now"), "power.schedule": C("shutdown", "-hp", "+{minutes}"),
            })
            ops["sec.overview"] = W(C("uname", "-a", optional=True), C("sysctl", "kern.securelevel", optional=True),
                                    C("pfctl", "-s", "info", optional=True, allow_fail=True, root=True),
                                    C("syspatch", "-c", optional=True, allow_fail=True, root=True))
            self._pf_ops(ops, "/etc/uyast/pf-anchor.conf", start=[])
        elif fl == "netbsd":
            ops.update({
                "pkg.search": C("pkgin", "search", "{q}"), "pkg.info": C("pkgin", "pkg-descr", "{pkg}", allow_fail=True),
                "pkg.install": C("pkgin", "-y", "install", "{*pkgs}"), "pkg.remove": C("pkgin", "-y", "remove", "{*pkgs}"),
                "pkg.list": C("pkgin", "list"), "pkg.refresh": C("pkgin", "update"),
                "pkg.upgrade": C("pkgin", "-y", "full-upgrade"), "pkg.outdated": C("pkgin", "-n", "full-upgrade", allow_fail=True),
                "pkg.clean": C("pkgin", "clean"),
                "pkg.repos": F(f_cat("/usr/pkg/etc/pkgin/repositories.conf"), "show pkgin repositories"),
                "svc.start": C("service", "{svc}", "onestart"), "svc.stop": C("service", "{svc}", "onestop"),
                "svc.restart": C("service", "{svc}", "onerestart"), "svc.status": C("service", "{svc}", "onestatus", allow_fail=True),
                "svc.enable": F(f_rcconf("YES"), "set {svc}=YES in /etc/rc.conf"),
                "svc.disable": F(f_rcconf("NO"), "set {svc}=NO in /etc/rc.conf"),
                "user.add": W(C("useradd", "-m", "-s", "/bin/sh", "{user}"),
                              F(f_hash_passwd(["pwhash"], ["usermod", "-p"]), "set the password (pwhash + usermod)", uses=["user", "password"]),
                              F(f_admin_group(("wheel",), lambda u, g: ["usermod", "-G", g, u]), "wheel group", uses=["user", "admin"])),
                "user.passwd": F(f_hash_passwd(["pwhash"], ["usermod", "-p"]), "set a new password for {user}", uses=["user", "newpw"]),
                "user.delete": C("userdel", "-r", "{user}"), "user.info": C("id", "{user}"),
                "group.add": C("groupadd", "{group}"), "group.delete": C("groupdel", "{group}"),
                "group.adduser": C("usermod", "-G", "{group}", "{user}"),
                "net.ports": [C("sockstat", "-l"), C("netstat", "-an", grep="listen")],
                "net.conns": C("netstat", "-an", grep="established"),
                "net.dhcp.renew": C("dhcpcd", "-n", "{iface}"),
                "net.if.up": C("ifconfig", "{iface}", "up"), "net.if.down": C("ifconfig", "{iface}", "down"),
                "log.auth": C("tail", "-n", "300", "/var/log/authlog", root=True),
                "fw.status": C("npfctl", "show", root=True), "fw.rules": C("npfctl", "show", root=True),
                "fw.enable": W(F(lambda p: f_conf_set("/etc/rc.conf")({"key": "npf", "value": "YES"}), "set npf=YES in /etc/rc.conf"),
                               C("npfctl", "reload"),
                               C("npfctl", "start")),
                "fw.disable": C("npfctl", "stop"),
                "hw.summary": C("sysctl", "hw.model", "hw.machine", "hw.ncpu", "hw.physmem64", "kern.version", allow_fail=True),
                "hw.cpu": C("sysctl", "hw.model", "hw.ncpu", allow_fail=True), "hw.memory": C("sysctl", "hw.physmem64", "hw.usermem64"),
                "hw.pci": C("pcictl", "pci0", "list", root=True), "hw.usb": C("usbdevs", "-v", allow_fail=True),
                "hw.sensors": C("envstat", allow_fail=True),
                "kernel.modules": C("modstat"), "kernel.load": C("modload", "{mod}"), "kernel.unload": C("modunload", "{mod}"),
                "boot.show": F(f_cat("/boot.cfg"), "show /boot.cfg"),
                "power.suspend": C("sysctl", "-w", "hw.acpi.sleep.state=3"),
            })
            ops["kernel.set"] = W(C("sysctl", "-w", "{key}={value}"), F(f_persist_sysctl("/etc/sysctl.conf"), "save in /etc/sysctl.conf",
                                                                        uses=["key", "value", "persist"]))
        elif fl in ("illumos", "solaris"):
            if self.pm == "ips":
                ops.update({
                    "pkg.search": C("pkg", "search", "-r", "{q}"), "pkg.info": C("pkg", "info", "-r", "{pkg}"),
                    "pkg.install": C("pkg", "install", "{*pkgs}", ok_codes=(0, 4)), "pkg.remove": C("pkg", "uninstall", "{*pkgs}"),
                    "pkg.list": C("pkg", "list"), "pkg.refresh": C("pkg", "refresh"),
                    "pkg.upgrade": C("pkg", "update", ok_codes=(0, 4)), "pkg.outdated": C("pkg", "update", "-nv", ok_codes=(0, 4)),
                    "pkg.repos": C("pkg", "publisher"),
                })
            elif self.pm == "pkgin":
                ops.update({"pkg.search": C("pkgin", "search", "{q}"), "pkg.install": C("pkgin", "-y", "install", "{*pkgs}"),
                            "pkg.remove": C("pkgin", "-y", "remove", "{*pkgs}"), "pkg.list": C("pkgin", "list"),
                            "pkg.refresh": C("pkgin", "update"), "pkg.upgrade": C("pkgin", "-y", "full-upgrade")})
            ops.update({
                "svc.start": C("svcadm", "enable", "-t", "{svc}"), "svc.stop": C("svcadm", "disable", "-t", "{svc}"),
                "svc.restart": C("svcadm", "restart", "{svc}"), "svc.status": C("svcs", "-xv", "{svc}", allow_fail=True),
                "svc.enable": C("svcadm", "enable", "{svc}"), "svc.disable": C("svcadm", "disable", "{svc}"),
                "svc.failed": C("svcs", "-xv", allow_fail=True),
                "user.add": W(C("useradd", "-m", "-s", "/bin/sh", "{user}"),
                              F(f_admin_group(("staff",), lambda u, g: ["usermod", "-G", g, u]), "staff group", uses=["user", "admin"])),
                "user.delete": C("userdel", "-r", "{user}"), "user.info": C("id", "-a", "{user}"),
                "user.lock": C("passwd", "-l", "{user}"), "user.unlock": C("passwd", "-u", "{user}"),
                "group.add": C("groupadd", "{group}"), "group.delete": C("groupdel", "{group}"),
                "group.adduser": F(f_solaris_addgroup, "add {user} to {group} (keeps the other groups)"),
                "net.interfaces": [W(C("ipadm", "show-addr"), C("dladm", "show-link", optional=True)), C("ifconfig", "-a")],
                "net.ports": C("netstat", "-an", "-P", "tcp", grep="listen"),
                "net.conns": C("netstat", "-an", "-P", "tcp", grep="established"),
                "net.ping": C("ping", "-s", "{host}", "56", "4", allow_fail=True),
                "log.system": C("tail", "-n", "300", "/var/adm/messages", root=True),
                "log.auth": C("tail", "-n", "300", "/var/log/authlog", root=True, allow_fail=True),
                "log.errors": C("tail", "-n", "3000", "/var/adm/messages", root=True, grep="error|fail|panic|warning"),
                "fw.status": C("ipfstat", "-io", root=True, allow_fail=True), "fw.rules": C("ipfstat", "-io", root=True, allow_fail=True),
                "fw.enable": C("svcadm", "enable", "network/ipfilter"), "fw.disable": C("svcadm", "disable", "network/ipfilter"),
                "hw.summary": [C("prtdiag", "-v", allow_fail=True), C("prtconf", tail=40)],
                "hw.cpu": C("psrinfo", "-pv"), "hw.memory": C("prtconf", grep="memory"),
                "hw.pci": C("prtconf", "-D", allow_fail=True), "hw.disks": C("iostat", "-En", allow_fail=True),
                "hw.usb": C("cfgadm", "-al", allow_fail=True),
                "kernel.modules": C("modinfo"),
                "boot.show": C("bootadm", "list-menu", allow_fail=True, root=True),
                "power.reboot": C("reboot"), "power.off": C("poweroff"),
                "time.tz.set": F(f_tz_symlink, "link /etc/localtime to {tz}"),
                "sec.overview": W(C("uname", "-a", optional=True), C("svcs", "-xv", optional=True, allow_fail=True)),
            })
            for k in ("power.schedule", "kernel.set", "kernel.params", "time.tz.set"):
                ops.pop(k, None)
        else:
            ops.update({"net.ports": C("netstat", "-an", grep="listen"), "net.conns": C("netstat", "-an", grep="established"),
                        "log.system": [C("tail", "-n", "300", "/var/adm/messages", needs=["tail", "file:/var/adm/messages"], root=True),
                                       C("tail", "-n", "300", "/var/log/messages", needs=["tail", "file:/var/log/messages"], root=True),
                                       C("tail", "-n", "300", "/var/log/syslog", needs=["tail", "file:/var/log/syslog"], root=True)],
                        "user.add": C("useradd", "-m", "{user}"), "user.delete": C("userdel", "-r", "{user}"),
                        "user.info": C("id", "{user}"), "group.add": C("groupadd", "{group}"), "group.delete": C("groupdel", "{group}"),
                        "power.reboot": C("shutdown", "-r", "now")})
            for k in ("log.errors", "log.boot", "kernel.set", "hw.disks", "time.tz.set", "power.off", "power.schedule"):
                ops.pop(k, None)
        return ops

    def _pf_ops(self, ops: Dict[str, Any], anchor: str, start: List[Step]) -> None:
        conf = "/etc/pf.conf"
        prep = pf_prepare_func(conf, anchor, pf_default_conf(anchor))
        reload_anchor = C("pfctl", "-a", "uyast", "-f", anchor)
        ops.update({
            "fw.status": C("pfctl", "-s", "info", allow_fail=True, root=True),
            "fw.rules": W(C("pfctl", "-s", "rules", allow_fail=True, root=True), C("pfctl", "-a", "uyast", "-s", "rules", allow_fail=True, root=True)),
            "fw.enable": W(F(prep, "prepare /etc/pf.conf and the uYaST anchor", uses=[]), *start, C("pfctl", "-f", conf),
                           C("sh", "-c", "pfctl -e 2>&1 || true", desc="pfctl -e"), reload_anchor),
            "fw.disable": W(C("pfctl", "-d", allow_fail=True), C("sysrc", "pf_enable=NO", optional=True)),
            "fw.reload": W(C("pfctl", "-f", conf), reload_anchor),
            "fw.allow": W(F(pf_rule_func(anchor, True, prep), f"add a pass rule for {{port}}/{{proto}} to {anchor}"), reload_anchor),
            "fw.remove": W(F(pf_rule_func(anchor, False), f"remove the rule for {{port}}/{{proto}} from {anchor}"), reload_anchor),
        })

    # ---- data -------------------------------------------------------------------------------------
    def sysinfo(self):
        info = super().sysinfo()
        mem = sysctl_n("hw.physmem64") or sysctl_n("hw.physmem")
        if mem.isdigit():
            info.append(("Memory", fmt_bytes(int(mem))))
        boot = re.search(r"sec\s*=\s*(\d+)", sysctl_n("kern.boottime"))
        if boot:
            info.append(("Uptime", fmt_duration(time.time() - int(boot.group(1)))))
        elif sysctl_n("kern.boottime").isdigit():
            info.append(("Uptime", fmt_duration(time.time() - int(sysctl_n("kern.boottime")))))
        model = sysctl_n("hw.model")
        if model:
            info.append(("CPU model", model))
        try:
            la = os.getloadavg()
            info.append(("Load average", f"{la[0]:.2f}  {la[1]:.2f}  {la[2]:.2f}"))
        except OSError:
            pass
        return info + self.tail_info()

    async def services(self, cap):
        fl = self.flavor
        if fl in ("freebsd", "dragonfly"):
            _, alln = await cap(Cmd(["service", "-l"]))
            _, enabled = await cap(Cmd(["service", "-e"]))
            en = {os.path.basename(l.strip()) for l in enabled.splitlines() if l.strip()}
            names = sorted({l.strip() for l in alln.splitlines() if l.strip() and not l.strip().isupper()} | en)

            async def status(n):
                rc, _ = await cap(Cmd(["service", n, "onestatus"]), 10)
                return n, "running" if rc == 0 else "stopped"
            st = dict(await asyncio.gather(*(status(n) for n in en)))
            return [[n, st.get(n, "-"), "enabled" if n in en else "disabled", ""] for n in names]
        if fl == "openbsd":
            _, alln = await cap(Cmd(["rcctl", "ls", "all"]))
            _, on = await cap(Cmd(["rcctl", "ls", "on"]))
            _, started = await cap(Cmd(["rcctl", "ls", "started"]))
            on_s, st_s = set(on.split()), set(started.split())
            return [[n, "running" if n in st_s else "stopped", "enabled" if n in on_s else "disabled", ""]
                    for n in sorted(set(alln.split()))]
        if fl == "netbsd":
            rc_conf = read_text("/etc/rc.conf")
            yes = {m.group(1) for m in re.finditer(r"^\s*(\w+)\s*=\s*\"?(?:YES|yes|Yes)", rc_conf, re.M)}
            names = sorted(os.listdir("/etc/rc.d")) if os.path.isdir("/etc/rc.d") else []
            return [[n, "-", "enabled" if n in yes else "disabled", "press Status"] for n in names if not n.isupper()]
        if fl in ("illumos", "solaris"):
            _, out = await cap(Cmd(["svcs", "-aH", "-o", "state,stime,fmri"]))
            rows = []
            for line in out.splitlines():
                parts = line.split(None, 2)
                if len(parts) == 3:
                    rows.append([parts[2], parts[0], "disabled" if parts[0] == "disabled" else "enabled", f"since {parts[1]}"])
            return sorted(rows, key=lambda r: r[0])
        raise NotSupported("Service management is not available on this Unix.")

    async def groups(self, cap, show_system):
        return posix_groups(show_system, 1000, keep=("wheel", "staff", "operator"))

    # ---- environment ----------------------------------------------------------------------------------
    def env_tools(self):
        if self.flavor in ("freebsd", "dragonfly", "netbsd") and not is_admin():
            return [("sudo", {"*": "sudo"}, "run admin tasks as a normal user", "recommended")]
        return []

    def python_venv_pkgs(self) -> List[str]:
        v = sys.version_info
        if self.flavor in ("freebsd", "dragonfly"):
            return [f"py{v.major}{v.minor}-pip"]
        if self.flavor == "netbsd":
            return [f"py{v.major}{v.minor}-pip"]
        if self.flavor == "openbsd":
            return ["py3-pip"]
        return []

    def pkg_manager_item(self) -> Optional[EnvItem]:
        fl = self.flavor
        if self.pm:
            return EnvItem("pm", "Packages", "Package manager", True, self.pkg_label, "recommended", order=20)
        if fl in ("freebsd", "dragonfly"):
            return EnvItem("pm", "Packages", "Package manager (pkg)", False, "pkg is not bootstrapped yet", "recommended",
                           fix=[Cmd(["env", "ASSUME_ALWAYS_YES=yes", "pkg", "bootstrap", "-y"], root=True),
                                Cmd(["env", "ASSUME_ALWAYS_YES=yes", "pkg", "update"], root=True, allow_fail=True)],
                           fix_text="bootstrap pkg", order=20)
        if fl == "netbsd":
            rel = ".".join(platform.release().split("_")[0].split(".")[:2])
            url = f"https://cdn.netbsd.org/pub/pkgsrc/packages/NetBSD/{platform.machine()}/{rel}/All"
            return EnvItem("pm", "Packages", "Package manager (pkgin)", False, "pkgin is not installed", "recommended",
                           fix=[Cmd(["env", f"PKG_PATH={url}", "pkg_add", "pkgin"], root=True),
                                Cmd(["pkgin", "-y", "update"], root=True, allow_fail=True)],
                           fix_text="install pkgin", order=20)
        if fl == "openbsd" and not os.path.exists("/etc/installurl"):
            return EnvItem("pm", "Packages", "Package mirror (/etc/installurl)", False, "no mirror configured", "recommended",
                           fix=[Cmd(func=lambda: (Path("/etc/installurl").write_text("https://cdn.openbsd.org/pub/OpenBSD\n"),
                                                  "wrote /etc/installurl")[1], desc="set the OpenBSD CDN mirror", root=True)],
                           order=20)
        return EnvItem("pm", "Packages", "Package manager", False, "not found", "info")


def make_backend(info: PlatformInfo) -> Backend:
    if info.family == "linux":
        return LinuxBackend(info)
    if info.family == "macos":
        return MacBackend(info)
    if info.family == "windows":
        return WindowsBackend(info)
    if info.family == "unix":
        return UnixBackend(info)
    raise NotSupported(f"{info.name} is not supported.")


# =============================================================================
# 3. Environment check and start-up wizard (standard library only)
# =============================================================================
def default_home() -> Path:
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "uyast"
    return Path.home() / ".uyast"


def venv_python(home: Path) -> Path:
    return home / "venv" / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def load_config(home: Path) -> dict:
    try:
        return json.loads((home / "config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(home: Path, cfg: dict) -> None:
    try:
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except OSError:
        pass


def textual_version(vpy: Optional[Path] = None) -> str:
    if vpy is None:
        try:
            import textual
            return getattr(textual, "__version__", "?")
        except Exception:
            return ""
    if not vpy.exists():
        return ""
    rc, out = run_quiet([str(vpy), "-c", "import textual, sys; sys.stdout.write(textual.__version__)"], 30)
    return out.strip() if rc == 0 else ""


def utf8_ok() -> bool:
    enc = (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "")
    if IS_WINDOWS:
        return True                      # the Windows console API is Unicode
    lang = (os.environ.get("LC_ALL") or os.environ.get("LC_CTYPE") or os.environ.get("LANG") or "").lower()
    return "utf8" in enc or "utf-8" in lang or "utf8" in lang


def pick_utf8_locale() -> str:
    rc, out = run_quiet(["locale", "-a"], 5)
    have = {l.strip().lower().replace("-", ""): l.strip() for l in out.splitlines()}
    for want in ("c.utf8", "en_us.utf8", "c.utf8"):
        if want in have:
            return have[want]
    return "en_US.UTF-8" if sys.platform == "darwin" or "bsd" in sys.platform else "C.UTF-8"


def decide_safe_glyphs(cfg: dict) -> Tuple[bool, str]:
    """Safe symbols = only characters every console font has. Returns (safe, reason)."""
    mode = cfg.get("glyphs", "auto")
    if mode == "safe":
        return True, "set to 'safe' in uYaST Settings"
    if mode == "fancy":
        return False, "set to 'fancy' in uYaST Settings"
    if IS_WINDOWS:
        if os.environ.get("WT_SESSION") or os.environ.get("ConEmuPID") or os.environ.get("TERM_PROGRAM") \
                or os.environ.get("WEZTERM_PANE") or os.environ.get("ALACRITTY_WINDOW_ID"):
            return False, "modern terminal with full Unicode fonts"
        return True, "classic Windows console fonts lack some symbols"
    term = os.environ.get("TERM", "")
    if term == "linux" or term.startswith(("vt1", "vt2", "cons", "pcvt", "wsvt", "sun")):
        return True, f"text console (TERM={term}) has a limited font"
    if not utf8_ok():
        return True, "the terminal is not in UTF-8 mode"
    return False, "UTF-8 terminal"


def terminal_items() -> List[EnvItem]:
    items: List[EnvItem] = []
    tty = sys.stdin.isatty() and sys.stdout.isatty()
    items.append(EnvItem("tty", "Terminal", "Interactive terminal", tty,
                         "yes" if tty else "not a terminal - start uYaST from a terminal window", "required"))
    cols, rows = shutil.get_terminal_size((80, 24))
    items.append(EnvItem("size", "Terminal", "Window size", cols >= 80 and rows >= 24, f"{cols} x {rows}"
                         + ("" if cols >= 80 and rows >= 24 else " - make the window at least 80 x 24 (100 x 30 is comfortable)"),
                         "recommended"))
    ct = os.environ.get("COLORTERM", "").lower()
    term = os.environ.get("TERM", "")
    colors = "true colour" if ct in ("truecolor", "24bit") or os.environ.get("WT_SESSION") else (
        "256 colours" if "256" in term or IS_WINDOWS else ("16 colours" if term else "unknown"))
    items.append(EnvItem("colors", "Terminal", "Colours", True, colors + (f" (TERM={term})" if term else ""), "info"))
    u8 = utf8_ok()
    items.append(EnvItem("utf8", "Terminal", "Unicode / UTF-8", True,
                         "yes" if u8 else f"no - uYaST starts itself with the {pick_utf8_locale()} locale", "info"))
    safe, why = decide_safe_glyphs({})
    items.append(EnvItem("glyphs", "Terminal", "Symbols and fonts", True,
                         ("plain console symbols" if safe else "full Unicode symbols") + f" ({why})", "info"))
    if os.environ.get("SSH_CONNECTION"):
        items.append(EnvItem("ssh", "Terminal", "Remote session", True, "over SSH - keyboard works fully, mouse if your terminal sends it", "info"))
    if os.environ.get("TMUX") or os.environ.get("STY"):
        items.append(EnvItem("mux", "Terminal", "Multiplexer", True, "tmux/screen - set 'mouse on' there for mouse support", "info"))
    return items


def environment_check(be: Backend, home: Path, in_tui: bool = False) -> List[EnvItem]:
    items: List[EnvItem] = []
    items.append(EnvItem("python", "Core", "Python", sys.version_info >= MIN_PY,
                         f"{platform.python_version()} ({sys.executable})", "required"))
    vpy = venv_python(home)
    tv = textual_version() if in_tui else textual_version(vpy)
    if tv:
        items.append(EnvItem("venv", "Core", "Private Python environment", True, str(home / "venv"), "required"))
    else:
        venv_ok = run_quiet([sys.executable, "-c", "import venv, ensurepip"], 20)[0] == 0 or \
            run_quiet([sys.executable, "-c", "import venv, pip"], 20)[0] == 0
        pk = be.python_venv_pkgs()
        items.append(EnvItem("venv", "Core", "Python venv + pip", venv_ok,
                             "available" if venv_ok else ("missing - package " + " ".join(pk) if pk else "missing"),
                             "required", pkgs=[] if venv_ok else pk, fix_text="install Python venv/pip support", order=10))
    items.append(EnvItem("tui", "Core", f"TUI library ({TEXTUAL_REQ})", bool(tv), f"Textual {tv}" if tv else "not installed yet",
                         "required", fix=[] if tv else [Cmd(func=lambda: ensure_venv(home), desc="create the environment and install Textual")],
                         fix_text="create the private environment and install Textual", order=90))
    if not in_tui:
        items += terminal_items()
    adm = is_admin()
    if adm:
        detail, ok = ("Administrator" if IS_WINDOWS else "root"), True
    elif IS_WINDOWS:
        detail, ok = "not elevated - uYaST asks to restart as Administrator", False
    else:
        pre = posix_priv_prefix()
        detail, ok = (f"via {pre[0]}" if pre else ("via su (root password)" if which_ext("su") else "no sudo/doas/su")), bool(pre or which_ext("su"))
    items.append(EnvItem("admin", "Access", "Administrator rights", ok, detail, "recommended"))
    pmi = be.pkg_manager_item()
    if pmi:
        items.append(pmi)
    key = be.pkg_key()
    for binary, pkgmap, purpose, level in be.env_tools():
        if level == "info":
            continue
        found = which_ext(binary)
        pkg = pkgmap.get(key) or pkgmap.get("*") if key else ""
        items.append(EnvItem(f"tool:{binary}", "Tools", f"{binary} ({purpose})", bool(found),
                             found or (f"missing - package {pkg}" if pkg else "missing"), level,
                             pkgs=[pkg] if (pkg and not found) else [], order=60))
    items += be.extra_env_items()
    return items


def fix_plan(items: List[EnvItem]) -> List[Tuple[str, str, Any]]:
    todo = sorted([i for i in items if i.fixable], key=lambda i: i.order)
    plan: List[Tuple[str, str, Any]] = []
    for i in todo:
        if i.fix and i.order < 50:
            plan.append(("cmds", i.fix_text or i.title, i.fix))
    pkgs: List[str] = []
    for i in todo:
        for p in i.pkgs:
            if p not in pkgs:
                pkgs.append(p)
    if pkgs:
        plan.append(("pkgs", "install packages: " + " ".join(pkgs), pkgs))
    for i in todo:
        if i.fix and i.order >= 50:
            plan.append(("cmds", i.fix_text or i.title, i.fix))
    return plan


# ---- terminal helpers ------------------------------------------------------------------------
def banner() -> None:
    print("=" * 72)
    print(f"  {APP_NAME} {VERSION} - YaST-style system administration for every platform")
    print("  macOS (Apple Silicon & Intel)  |  Windows 7-11  |  Linux  |  Unix (BSD & others)")
    print("=" * 72)


AUTO_YES = False


def ask_yes(prompt: str, default: bool = True) -> bool:
    if AUTO_YES:
        print(prompt + " [yes]")
        return True
    suffix = " [Y/n] " if default else " [y/N] "
    try:
        ans = input(prompt + suffix).strip().lower()
    except EOFError:
        print()
        return default
    if not ans:
        return default
    return ans in ("y", "yes", "j", "ja", "o", "oui", "si", "da", "ha")


def timed_input(prompt: str, timeout: float) -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if AUTO_YES or timeout <= 0:
        print()
        return ""
    if not sys.stdin.isatty():
        try:
            return input().strip()
        except EOFError:
            print()
            return ""
    if IS_WINDOWS:
        import msvcrt
        end, buf = time.time() + timeout, ""
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                end = float("inf")
                if ch in "\r\n":
                    print()
                    return buf.strip()
                if ch == "\x03":
                    raise KeyboardInterrupt
                if ch == "\b":
                    if buf:
                        buf = buf[:-1]
                        sys.stdout.write("\b \b")
                elif ch.isprintable():
                    buf += ch
                    sys.stdout.write(ch)
                sys.stdout.flush()
            elif time.time() > end:
                print("  (no answer - detecting automatically)")
                return ""
            else:
                time.sleep(0.05)
    import select
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
    except (OSError, ValueError):
        ready = [sys.stdin]
    if ready:
        return sys.stdin.readline().strip()
    print("  (no answer - detecting automatically)")
    return ""


def ask_platform(info: PlatformInfo, preset: Optional[str], timeout: float) -> str:
    keys = [k for k, _, _ in PLATFORM_CHOICES]
    detected = info.family if info.family in keys else ""
    if preset:
        choice = preset
    else:
        print("\nWhat platform is it?\n")
        for i, (k, name, desc) in enumerate(PLATFORM_CHOICES, 1):
            print(f"   {i}) {name:<8} - {desc}")
        print("\n   Enter = detect automatically" + (f"   (auto-detect in {int(timeout)} s)" if timeout > 0 else ""))
        ans = timed_input("\nChoice: ", timeout).lower()
        names = {n.lower(): k for k, n, _ in PLATFORM_CHOICES}
        choice = keys[int(ans) - 1] if ans in ("1", "2", "3", "4") else names.get(ans, keys[0] if ans == "mac" else "")
    print(f"\nDetected: {FAMILY_NAME.get(detected, 'unknown')} - {info.name}"
          + (f"  ({info.detail}, {info.arch})" if info.detail else f"  ({info.arch})"))
    if not choice:
        print(f"[ok] Platform detected automatically: {FAMILY_NAME.get(detected, info.family)}")
    elif choice == detected:
        print(f"[ok] Confirmed: {FAMILY_NAME[choice]}")
    else:
        print(f"[!]  You chose {FAMILY_NAME.get(choice, choice)}, but this machine is {FAMILY_NAME.get(detected, 'unknown')} "
              f"({info.name}).\n     {FAMILY_NAME.get(choice, choice)} tools cannot run here, so uYaST continues with "
              f"{FAMILY_NAME.get(detected, 'the detected system')}.")
    return detected


def print_report(items: List[EnvItem]) -> None:
    mark = {True: "[ok]", False: "[!!]"}
    group = ""
    for it in items:
        if it.group != group:
            group = it.group
            print(f"\n  {group}")
        if it.ok:
            m = "[ok]" if it.level != "info" else "[--]"
        else:
            m = {"required": "[!!]", "recommended": "[! ]", "optional": "[  ]", "info": "[--]"}[it.level]
        lvl = "" if it.ok or it.level == "info" else f"  <{it.level}" + (", can be fixed>" if it.fixable else ">")
        print(f"   {m} {it.title:<46} {it.detail}{lvl}")
    print()
    _ = mark


def posix_priv_prefix() -> Optional[List[str]]:
    if IS_WINDOWS or os.geteuid() == 0:
        return []
    if which_ext("sudo"):
        return ["sudo"]
    if which_ext("doas"):
        return ["doas"]
    return None


def run_sync(cmd: Cmd, priv: Optional[List[str]] = None, quiet: bool = False) -> int:
    if cmd.func:
        if not quiet:
            print(f"  > {cmd.desc}")
        try:
            out = cmd.func()
            if out and not quiet:
                print("    " + str(out).replace("\n", "\n    "))
            return 0
        except Exception as e:
            print(f"  ! {e}")
            return 1
    argv = list(cmd.argv or [])
    env = None
    use_priv = priv if (cmd.root and priv) else None
    if cmd.env:
        if use_priv:
            argv = ["env"] + [f"{k}={v}" for k, v in cmd.env.items()] + argv
        else:
            env = dict(os.environ, **cmd.env)
    if use_priv:
        argv = (["su", "root", "-c", shlex.join(argv)] if use_priv == ["su"] else use_priv + argv)
    if not quiet:
        shown = cmd.desc or (subprocess.list2cmdline(argv) if IS_WINDOWS else shlex.join(argv))
        print(f"  $ {shown}")
    try:
        r = subprocess.run(argv, env=env, input=cmd.input, text=True if cmd.input is not None else None,
                           stdout=subprocess.DEVNULL if quiet else None, stderr=subprocess.DEVNULL if quiet else None)
    except FileNotFoundError:
        if not quiet:
            print(f"  ! command not found: {argv[0]}")
        return 127
    return 0 if r.returncode in cmd.ok_codes else r.returncode


def install_pkgs_sync(be: Backend, pkgs: List[str], priv: List[str]) -> List[str]:
    try:
        bulk = be.cmds("pkg.install", pkgs=" ".join(pkgs))
    except (NotSupported, ValueError) as e:
        print(f"  ! cannot install packages here: {e}")
        return pkgs
    for c in be.pkg_prepare_cmds():
        run_sync(c, priv)
    if all(run_sync(c, priv) == 0 for c in bulk):
        return []
    print("  bulk install failed - trying the packages one at a time ...")
    failed = []
    for p in pkgs:
        if any(run_sync(c, priv) != 0 for c in be.cmds("pkg.install", pkgs=p)):
            failed.append(p)
    return failed


def run_fixes_terminal(be: Backend, items: List[EnvItem], home: Path) -> None:
    priv = posix_priv_prefix()
    needs_root = any(i.pkgs for i in items) or any(c.root for i in items for c in i.fix)
    if priv is None and needs_root:
        print("  Some fixes need root, and neither sudo nor doas is installed.")
        if which_ext("su") and ask_yes("  Run them as root with 'su' (asks for the root password each time)?", True):
            priv = ["su"]
        else:
            print("  Skipping fixes that need root.")
            priv = []
    for kind, title, payload in fix_plan(items):
        print(f"\n>> {title}")
        if kind == "pkgs":
            failed = install_pkgs_sync(be, payload, priv or [])
            if failed:
                print("  [!] could not install: " + ", ".join(failed))
            be.redetect()
            continue
        for c in payload:
            if c.user and not IS_WINDOWS and is_admin():
                print("  ! skipped (must run as a normal user, not root): " + c.display())
                break
            rc = run_sync(c, priv)
            if rc != 0 and not c.allow_fail:
                print(f"  [!] step failed (exit code {rc})")
                break
        be.redetect()


def pip_ok(vpy: Path) -> bool:
    return vpy.exists() and run_sync(Cmd([str(vpy), "-m", "pip", "--version"]), quiet=True) == 0


def ensure_venv(home: Path) -> str:
    vdir, vpy = home / "venv", venv_python(home)
    home.mkdir(parents=True, exist_ok=True)
    if not pip_ok(vpy):
        shutil.rmtree(str(vdir), ignore_errors=True)
        print(f"    creating {vdir}")
        if run_sync(Cmd([sys.executable, "-m", "venv", str(vdir)])) != 0 or not pip_ok(vpy):
            shutil.rmtree(str(vdir), ignore_errors=True)
            print("    retrying with the system pip ...")
            run_sync(Cmd([sys.executable, "-m", "venv", "--system-site-packages", "--without-pip", str(vdir)]))
            if not pip_ok(vpy):
                run_sync(Cmd([str(vpy), "-m", "ensurepip", "--upgrade"]), quiet=True)
    if not pip_ok(vpy):
        raise RuntimeError("could not create a Python environment with pip")
    print(f"    installing {TEXTUAL_REQ} (the TUI library) ...")
    if run_sync(Cmd([str(vpy), "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", "--quiet", TEXTUAL_REQ])) != 0:
        raise RuntimeError("pip could not install Textual - check the internet connection")
    return f"Textual {textual_version(vpy)} installed in {vdir}"


# ---- launching the TUI --------------------------------------------------------------------------
def tui_args(home: Path) -> List[str]:
    return [str(venv_python(home)), "-B", os.path.abspath(__file__), "--tui", "--home", str(home),
            "--user-name", invoking_user()]


def launch_tui(home: Path, cfg: dict, args) -> int:
    targs = tui_args(home)
    if IS_WINDOWS:
        console = win_console_name()
        if console == "Windows Console Host (conhost)" and not args.no_relaunch:
            wt, ce = wt_path(), conemu_path()
            build = sys.getwindowsversion().build
            try:
                if wt and cfg.get("use_wt", True) and build >= 18362:
                    subprocess.Popen([wt, "new-tab", "--title", "uYaST"] + targs)
                    print("uYaST opened in Windows Terminal.")
                    return 0
                if ce and build < 10586:
                    subprocess.Popen([ce, "-Title", "uYaST", "-run"] + targs)
                    print("uYaST opened in ConEmu.")
                    return 0
            except OSError as e:
                print(f"Could not open a new terminal ({e}); using this window.")
            cols, rows = shutil.get_terminal_size((80, 24))
            if cols < 100 or rows < 30:
                os.system("mode con: cols=120 lines=40 >nul 2>&1")
        return subprocess.call(targs)
    env_pass = {k: os.environ[k] for k in ("TERM", "COLORTERM", "TERM_PROGRAM", "LANG", "LC_ALL", "LC_CTYPE",
                                           "SSH_CONNECTION", "TMUX", "STY", "WT_SESSION") if os.environ.get(k)}
    if not utf8_ok():
        env_pass["LC_ALL"] = pick_utf8_locale()
    env_pass["UYAST_USER"] = invoking_user()
    if not is_admin() and not args.no_elevate:
        pre = posix_priv_prefix()
        envargs = ["env"] + [f"{k}={v}" for k, v in env_pass.items()]
        if pre and ask_yes(f"Most modules change the system and need root. Start uYaST through {pre[0]}?", True):
            os.execvp(pre[0], pre + envargs + targs)
        if pre is None and which_ext("su") and ask_yes("Most modules need root. Start uYaST as root with 'su'?", True):
            os.execvp("su", ["su", "root", "-c", shlex.join(envargs + targs)])
        print("Continuing without root - viewing works, changes are disabled.")
        time.sleep(1.2)
    os.execve(targs[0], targs, dict(os.environ, **env_pass))
    return 0


def relaunch_elevated_windows(argv: List[str]) -> bool:
    import ctypes
    params = subprocess.list2cmdline([os.path.abspath(__file__)] + argv + ["--elevated"])
    r = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, os.getcwd(), 1)
    return r > 32


def wizard(args, home: Path) -> int:
    global AUTO_YES
    AUTO_YES = bool(args.yes)
    cfg = load_config(home)
    info = detect_platform()
    first = bool(args.setup or not cfg.get("setup_done") or cfg.get("platform_key") != info.key
                 or not venv_python(home).exists())
    if first or args.check:
        banner()
    if first and not args.check:
        ask_platform(info, args.platform, args.timeout)
    if info.family == "unknown":
        print(f"\n[!!] {info.name} is not supported. {info.detail}")
        return 1
    be = make_backend(info)
    be.assume_root = True
    if first or args.check:
        print("\nChecking the environment ...")
    items = environment_check(be, home)
    problems = [i for i in items if not i.ok and i.level in ("required", "recommended")]
    if first or args.check or problems:
        print_report(items)
    if args.check:
        return 1 if any(not i.ok and i.level == "required" for i in items) else 0
    fixable = [i for i in items if i.fixable and i.level in ("required", "recommended")]
    if fixable:
        names = ", ".join(i.title.split(" (")[0] for i in fixable)
        if ask_yes(f"Install / fix {len(fixable)} item(s) now ({names})?", True):
            run_fixes_terminal(be, fixable, home)
    optional = [i for i in items if i.fixable and i.level == "optional"]
    if optional and first and not cfg.get("optional_asked"):
        names = ", ".join(i.title.split(" (")[0] for i in optional)
        cfg["optional_asked"] = True
        if ask_yes(f"Also install {len(optional)} optional tool(s) ({names})?", False):
            run_fixes_terminal(be, optional, home)
    if fixable or optional:
        be.redetect()
        items = environment_check(be, home)
        still = [i for i in items if not i.ok and i.level in ("required", "recommended")]
        if still:
            print("\nStill open after the fixes:")
            print_report(still)
    missing = [i for i in items if not i.ok and i.level == "required"]
    if missing:
        print("[!!] uYaST cannot start until these are fixed: " + ", ".join(i.title for i in missing))
        if IS_WINDOWS and args.elevated:
            input("Press Enter to close ...")
        return 1
    cfg.update({"setup_done": True, "platform_key": info.key, "platform": info.name, "family": info.family,
                "version": VERSION, "setup_at": time.strftime("%Y-%m-%d %H:%M:%S")})
    save_config(home, cfg)
    print("[ok] Environment ready - starting uYaST ...")
    return launch_tui(home, cfg, args)


def tui_main(args, home: Path) -> int:
    extend_path()
    if args.user_name:
        os.environ["UYAST_USER"] = args.user_name
    if not HAVE_TEXTUAL:
        print(f"Textual is not installed for {sys.executable}. Run:  python3 {os.path.basename(__file__)} --setup")
        return 1
    cfg = load_config(home)
    info = detect_platform()
    try:
        be = make_backend(info)
    except NotSupported as e:
        print(e)
        return 1
    safe, _ = decide_safe_glyphs(cfg)
    if safe:
        apply_safe_glyphs()
    try:
        result = (SafeUYastApp if safe else UYastApp)(be, cfg, home, safe).run()
    except Exception:
        traceback.print_exc()
        if IS_WINDOWS:
            input("Press Enter to close ...")
        return 1
    if result == "reset":
        print(f"Settings were reset. Run {os.path.basename(__file__)} again to start the wizard.")
    elif result == "setup":
        print(f"Run:  python3 {os.path.basename(__file__)} --setup")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="uyast", description=f"{APP_NAME} - YaST-style system administration TUI "
                                 "for macOS, Windows 7-11, Linux and Unix")
    ap.add_argument("--setup", action="store_true", help="run the start-up wizard again (platform question + checks)")
    ap.add_argument("--check", action="store_true", help="only check the environment and print the report")
    ap.add_argument("--reset", action="store_true", help="forget saved settings")
    ap.add_argument("--yes", "-y", action="store_true", help="answer yes to every question (unattended setup)")
    ap.add_argument("--platform", choices=[k for k, _, _ in PLATFORM_CHOICES], help="answer the platform question")
    ap.add_argument("--timeout", type=float, default=15, help="seconds before the platform is detected automatically")
    ap.add_argument("--glyphs", choices=["auto", "safe", "fancy"], help="symbol style (saved)")
    ap.add_argument("--no-elevate", action="store_true", help="do not ask for root / Administrator")
    ap.add_argument("--no-relaunch", action="store_true", help="Windows: stay in this console window")
    ap.add_argument("--home", help="data folder (default ~/.uyast or %%LOCALAPPDATA%%\\uyast)")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")
    ap.add_argument("--tui", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--user-name", help=argparse.SUPPRESS)
    ap.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if sys.version_info < MIN_PY:
        print(f"{APP_NAME} needs Python {MIN_PY[0]}.{MIN_PY[1]} or newer (this is {platform.python_version()}).")
        return 1
    home = Path(args.home).expanduser() if args.home else default_home()
    if args.tui:
        return tui_main(args, home)
    if args.reset:
        try:
            (home / "config.json").unlink()
        except OSError:
            pass
        print("Saved settings removed - the wizard runs next time.")
        return 0
    if args.glyphs:
        cfg = load_config(home)
        cfg["glyphs"] = args.glyphs
        save_config(home, cfg)
        print(f"Symbol style set to '{args.glyphs}'.")
    if IS_WINDOWS and not is_admin() and not args.no_elevate and not args.check and not args.elevated:
        if ask_yes("uYaST needs Administrator rights for most modules. Restart as Administrator?", True):
            if relaunch_elevated_windows(sys.argv[1:] if argv is None else argv):
                print("uYaST continues in the new Administrator window.")
                return 0
            print("Elevation was cancelled - continuing without Administrator rights.")
    try:
        return wizard(args, home)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


# =============================================================================
# 4. The YaST-style text user interface (Textual)
# =============================================================================
try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.screen import ModalScreen, Screen
    from textual.scrollbar import ScrollBar, ScrollBarRender
    from textual.widgets import (Button, Checkbox, DataTable, Footer, Header, Input, Label, ListItem, ListView,
                                 RichLog, Select, Static)
    from rich.table import Table
    from rich.text import Text
    HAVE_TEXTUAL = True
except Exception:          # first run: Textual is installed by the wizard
    HAVE_TEXTUAL = False


if HAVE_TEXTUAL:
    try:
        from textual.theme import Theme
        YAST_THEMES = [
            Theme(name="yast", primary="#73BA25", secondary="#21A4DF", accent="#35B9AB", warning="#F2C14E",
                  error="#E5534B", success="#73BA25", foreground="#E7EEE3", background="#0B2630",
                  surface="#10333F", panel="#173F4F", dark=True),
            Theme(name="yast-light", primary="#4E8A12", secondary="#1279B0", accent="#1F8C82", warning="#B7791F",
                  error="#C0392B", success="#4E8A12", foreground="#1B2A30", background="#F3F6F1",
                  surface="#FFFFFF", panel="#DDE7D6", dark=False),
            Theme(name="yast-classic", primary="#00AAAA", secondary="#AAAA00", accent="#55FFFF", warning="#FFFF55",
                  error="#FF5555", success="#55FF55", foreground="#FFFFFF", background="#0000AA",
                  surface="#0000AA", panel="#000080", dark=True),
        ]
    except Exception:
        YAST_THEMES = []

    SPINNER_RE = re.compile(r"^[\s\-\\|/.]*$")

    def parse_mnemonic(label: str) -> Tuple[str, str]:
        """'&Start' -> ('[u]S[/u]tart', 's').  '&&' is a literal '&'."""
        out, mn, i = [], "", 0
        while i < len(label):
            ch = label[i]
            if ch == "&" and i + 1 < len(label):
                nxt = label[i + 1]
                if nxt == "&":
                    out.append("&")
                elif not mn:
                    mn = nxt.lower()
                    out.append(f"[u]{nxt}[/u]")
                else:
                    out.append(nxt)
                i += 2
                continue
            out.append("\\[" if ch == "[" else ch)
            i += 1
        return "".join(out), mn

    def plain_label(label: str) -> str:
        return label.replace("&&", "\0").replace("&", "").replace("\0", "&")

    class YButton(Button):
        """Button with an Alt+letter mnemonic (underlined letter), like YaST's ncurses buttons."""

        def __init__(self, label: str, id: Optional[str] = None, variant: str = "default", action=None, **kw):
            text, mn = parse_mnemonic(label)
            super().__init__(text, id=id, variant=variant, **kw)
            self.mnemonic = mn
            self.plain = plain_label(label)
            self.action_fn = action

    # ---- dialogs ------------------------------------------------------------------------------------
    class ConfirmScreen(ModalScreen):
        BINDINGS = [Binding("escape", "answer(False)", "No"), Binding("n", "answer(False)", "No", show=False),
                    Binding("y", "answer(True)", "Yes", show=False), Binding("left", "app.focus_previous", show=False),
                    Binding("right", "app.focus_next", show=False)]

        def __init__(self, message: str, danger: bool = True, yes: str = "&Yes", no: str = "&No"):
            super().__init__()
            self.message, self.danger, self.yes, self.no = message, danger, yes, no

        def compose(self) -> ComposeResult:
            with Vertical(id="dlg", classes="dialog"):
                yield Static(self.message, id="dlg-text")
                with Horizontal(classes="dlg-buttons"):
                    yield YButton(self.yes, id="dlg-yes", variant="error" if self.danger else "success")
                    yield YButton(self.no, id="dlg-no", variant="primary")

        def on_mount(self):
            self.query_one("#dlg-no" if self.danger else "#dlg-yes", Button).focus()

        def on_button_pressed(self, event: Button.Pressed):
            event.stop()
            self.dismiss(event.button.id == "dlg-yes")

        def action_answer(self, value: bool):
            self.dismiss(value)

    class TextScreen(ModalScreen):
        """Scrollable help / information window."""
        BINDINGS = [Binding("escape", "close", "Close"), Binding("f1", "close", "Close", show=False),
                    Binding("f9", "close", "Close", show=False), Binding("f10", "close", "Close", show=False),
                    Binding("q", "close", "Close", show=False)]

        def __init__(self, title: str, body: Any):
            super().__init__()
            self.title_text, self.body = title, body

        def compose(self) -> ComposeResult:
            with Vertical(id="txt", classes="dialog wide"):
                yield Static(self.title_text, classes="dlg-title")
                with VerticalScroll(id="txt-scroll"):
                    yield Static(self.body)
                with Horizontal(classes="dlg-buttons"):
                    yield YButton("&Close", id="txt-close", variant="primary")

        def on_mount(self):
            self.query_one("#txt-scroll").focus()

        def on_button_pressed(self, event: Button.Pressed):
            event.stop()
            self.dismiss(None)

        def action_close(self):
            self.dismiss(None)

    # ---- keyboard helpers shared by all screens ------------------------------------------------------
    class KeyNav:
        """Alt+letter mnemonics and arrow-key movement between buttons, fields and rows."""
        PLAIN_MNEMONICS = True

        def _focusables(self, container) -> List[Any]:
            out = []
            for w in container.query("*"):
                if isinstance(w, (Button, Input, Checkbox, Select)) and w.display and not w.disabled \
                        and getattr(w, "can_focus", True) and w.styles.display != "none":
                    out.append(w)
            return out

        def _row_of(self, w):
            node = w.parent
            while node is not None and node is not self:
                if node.has_class("row"):
                    return node
                node = node.parent
            return None

        def _rows(self) -> List[Any]:
            return [r for r in self.query(".row") if r.display and self._focusables(r)]

        def handle_nav_key(self, event) -> bool:
            key, f = event.key, self.focused
            letter = ""
            if key.startswith("alt+") and len(key) == 5:
                letter = key[4]
            elif len(key) == 1 and key.isalpha() and self.PLAIN_MNEMONICS and not isinstance(f, (Input, Select)):
                letter = key.lower()
            if letter:
                for b in self.query(YButton):
                    if b.mnemonic == letter and not b.disabled and b.display and b.screen is self:
                        b.focus()
                        b.press()
                        return True
            if f is None or not isinstance(f, (Button, Checkbox, Input, Select)):
                return False
            row = self._row_of(f)
            if row is None:
                return False
            if key in ("left", "right") and isinstance(f, (Button, Checkbox)):
                items = self._focusables(row)
                if f in items:
                    i = items.index(f) + (1 if key == "right" else -1)
                    if 0 <= i < len(items):
                        items[i].focus()
                    elif key == "right":
                        self.app.action_focus_next()
                    else:
                        self.app.action_focus_previous()
                    return True
            if key in ("up", "down") and not isinstance(f, Select):
                if isinstance(f, Input) and getattr(f, "history_nav", False):
                    return False
                rows = self._rows()
                if row not in rows:
                    return False
                i = rows.index(row) + (1 if key == "down" else -1)
                if 0 <= i < len(rows):
                    target = self._focusables(rows[i])
                    x = f.region.x
                    best = min(target, key=lambda w: abs(w.region.x - x))
                    best.focus()
                else:
                    (self.app.action_focus_next if key == "down" else self.app.action_focus_previous)()
                return True
            return False

    # ---- Control Center ------------------------------------------------------------------------------
    GROUPS = [("software", "Software"), ("hardware", "Hardware"), ("system", "System"),
              ("network", "Network Services"), ("security", "Security and Users"), ("support", "Support"),
              ("misc", "Miscellaneous")]
    MODULES: List[Any] = []        # filled by @yast_module

    def yast_module(key: str, group: str, title: str, desc: str):
        def deco(cls):
            cls.KEY, cls.GROUP, cls.TITLE, cls.DESC = key, group, title, desc
            MODULES.append(cls)
            return cls
        return deco

    CC_HELP = f"""[b]{APP_NAME} Control Center[/b] - like YaST, for every platform.

[b]Keyboard (everything works without a mouse)[/b]
  Up / Down          move in a list               Right or Enter   go from groups to modules
  Enter              open the selected module     Left / Esc       back to the groups
  1 - 7              jump to a group              / or Ctrl+F      search all modules
  typing a letter    starts a search              Tab / Shift+Tab  next / previous field
  Alt+H  Help        Alt+R  Run module            Alt+Q / F9       Quit (also Ctrl+Q)

[b]Inside a module[/b]
  Arrow keys move between buttons and rows of fields; Enter presses a button; Space ticks a box.
  Alt+<underlined letter> presses a button (the letter alone works when no text field is focused).
  F1 Help   F2 Refresh   F3 Add   F4 Edit   F5 Delete   F7 bigger output   F8 clear output
  F9 / Esc  back to the Control Center   Ctrl+K stop a running command   PgUp/PgDn scroll the output

[b]Mouse[/b]
  Click groups, modules, buttons and table rows; scroll with the wheel.

Every action runs the platform's own built-in command and shows it in the output before it runs.
Buttons that need a missing tool are disabled; Miscellaneous > Environment Check installs what is missing.
"""

    class ControlCenter(KeyNav, Screen):
        PLAIN_MNEMONICS = False
        BINDINGS = [Binding("f1", "help", "Help"), Binding("f10", "run", "Run"), Binding("f9", "quit_app", "Quit"),
                    Binding("slash", "search", "Search", key_display="/"), Binding("ctrl+f", "search", "Search", show=False),
                    Binding("ctrl+q", "quit_app", "Quit", show=False, priority=True)]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True, icon=self.app.HEADER_ICON)
            yield Static(f" YaST Control Center  -  {platform.node()}  -  {self.app.backend.label}", classes="title")
            with Horizontal(id="cc-main"):
                with Vertical(id="cc-left"):
                    yield ListView(*[ListItem(Label(f" {i}  {name}"), id=f"g-{key}") for i, (key, name) in enumerate(GROUPS, 1)],
                                   id="cc-groups")
                with Vertical(id="cc-right"):
                    yield Input(placeholder="Search modules  ( / )", id="cc-search")
                    yield ListView(id="cc-modules")
            yield Static(id="cc-desc")
            with Horizontal(classes="row buttonbar"):
                yield YButton("&Help", id="cc-help")
                yield Static(classes="spacer")
                yield YButton("&Run", id="cc-run", variant="primary")
                yield YButton("&Quit", id="cc-quit", variant="error")
            yield Footer()

        def on_mount(self):
            self.query_one("#cc-groups").border_title = "Groups"
            self.query_one("#cc-modules").border_title = "Modules"
            self.current: List[Any] = []
            self.query_one("#cc-groups", ListView).focus()
            self.run_worker(self.show_group(GROUPS[0][0]))

        def module_ok(self, cls) -> Tuple[bool, str]:
            return cls.check_available(self.app.backend)

        async def fill(self, mods: List[Any]):
            lv = self.query_one("#cc-modules", ListView)
            await lv.clear()
            self.current = mods
            items = []
            for cls in mods:
                ok, _ = self.module_ok(cls)
                lab = Label(f" {cls.TITLE}" + ("" if ok else "   (not available here)"))
                if not ok:
                    lab.add_class("dim")
                items.append(ListItem(lab))
            if items:
                await lv.extend(items)
                lv.index = 0
            self.describe(mods[0] if mods else None)

        async def show_group(self, gkey: str):
            await self.fill([m for m in MODULES if m.GROUP == gkey])

        def describe(self, cls):
            d = self.query_one("#cc-desc", Static)
            if cls is None:
                d.update(" No module matches.")
                return
            ok, why = self.module_ok(cls)
            d.update(Text.assemble((f" {cls.TITLE}: ", "bold"), cls.DESC, ("" if ok else f"\n Not available here: {why}", "italic")))

        @on(ListView.Highlighted, "#cc-groups")
        async def group_moved(self, event):
            if event.item is not None and event.item.id and not self.query_one("#cc-search", Input).value:
                await self.show_group(event.item.id[2:])

        @on(ListView.Selected, "#cc-groups")
        def group_selected(self, event):
            self.query_one("#cc-modules", ListView).focus()

        @on(ListView.Highlighted, "#cc-modules")
        def module_moved(self, event):
            lv = self.query_one("#cc-modules", ListView)
            if lv.index is not None and 0 <= lv.index < len(self.current):
                self.describe(self.current[lv.index])

        @on(ListView.Selected, "#cc-modules")
        def module_selected(self, event):
            self.action_run()

        @on(Input.Changed, "#cc-search")
        async def searched(self, event):
            q = event.value.strip().lower()
            if not q:
                g = self.query_one("#cc-groups", ListView)
                idx = g.index or 0
                await self.show_group(GROUPS[idx][0])
                return
            await self.fill([m for m in MODULES if q in (m.TITLE + " " + m.DESC + " " + m.KEY).lower()])

        @on(Input.Submitted, "#cc-search")
        def search_enter(self):
            if self.current:
                self.query_one("#cc-modules", ListView).focus()

        def on_key(self, event):
            f = self.focused
            groups = self.query_one("#cc-groups", ListView)
            mods = self.query_one("#cc-modules", ListView)
            search = self.query_one("#cc-search", Input)
            key = event.key
            if f is groups and key == "right":
                mods.focus()
                event.stop()
                return
            if f is mods and key in ("left", "escape"):
                groups.focus()
                event.stop()
                return
            if f is search:
                if key == "down":
                    mods.focus()
                    event.stop()
                elif key == "escape":
                    search.value = ""
                    groups.focus()
                    event.stop()
                return
            if f in (groups, mods) and len(key) == 1 and key.isdigit() and 1 <= int(key) <= len(GROUPS):
                search.value = ""
                groups.index = int(key) - 1
                groups.focus()
                self.run_worker(self.show_group(GROUPS[int(key) - 1][0]))
                event.stop()
                return
            if f in (groups, mods) and key in ("home", "end", "pageup", "pagedown"):
                n = len(f.children)
                if n:
                    cur = f.index or 0
                    f.index = {"home": 0, "end": n - 1, "pageup": max(0, cur - 10), "pagedown": min(n - 1, cur + 10)}[key]
                event.stop()
                return
            if f in (groups, mods) and event.character and event.character.isprintable() and len(event.character) == 1 \
                    and not key.startswith(("alt+", "ctrl+")) and event.character not in "/ ":
                search.focus()
                search.value = event.character
                search.cursor_position = 1
                event.stop()
                return
            if self.handle_nav_key(event):
                event.stop()

        def on_button_pressed(self, event: Button.Pressed):
            event.stop()
            {"cc-help": self.action_help, "cc-run": self.action_run, "cc-quit": self.action_quit_app}.get(
                event.button.id, lambda: None)()

        def action_help(self):
            self.app.push_screen(TextScreen("Help - Control Center", CC_HELP))

        def action_search(self):
            self.query_one("#cc-search", Input).focus()

        def action_quit_app(self):
            self.app.exit()

        def action_run(self):
            lv = self.query_one("#cc-modules", ListView)
            if lv.index is None or not (0 <= lv.index < len(self.current)):
                self.notify("Pick a module first.", severity="warning")
                return
            cls = self.current[lv.index]
            ok, why = self.module_ok(cls)
            if not ok:
                self.notify(f"{cls.TITLE} is not available here: {why}", severity="warning", timeout=6)
                return
            self.app.push_screen(cls())

    # ---- module screens ------------------------------------------------------------------------------
    class ModuleScreen(KeyNav, Screen):
        KEY = GROUP = TITLE = DESC = ""
        HELP = ""
        OPS: List[str] = []
        DATA = False          # module shows a table (body fills the screen, output stays small)
        REFRESH = False
        BINDINGS = [Binding("f1", "help", "Help"), Binding("f2", "refresh", "Refresh"),
                    Binding("f7", "toggle_log", "Output"), Binding("f8", "clear_log", "Clear", show=False),
                    Binding("f9", "back", "Back"), Binding("f10", "back", "OK", show=False),
                    Binding("escape", "esc", "Back", show=False), Binding("ctrl+k", "stop", "Stop"),
                    Binding("ctrl+q", "app.quit", "Quit", show=False, priority=True)]

        @classmethod
        def check_available(cls, be: Backend) -> Tuple[bool, str]:
            if not cls.OPS:
                return True, ""
            if any(op in be.ops for op in cls.OPS):
                return True, ""
            return False, f"no {cls.TITLE.lower()} tools on {FAMILY_NAME.get(be.family, be.family)}"

        @property
        def be(self) -> Backend:
            return self.app.backend

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True, icon=self.app.HEADER_ICON)
            yield Static(f" {self.TITLE}  -  {platform.node()}", classes="title")
            body = Vertical(id="body") if self.DATA else VerticalScroll(id="body")
            with body:
                yield from self.compose_body()
                yield Static(id="unavail", classes="unavail")
            yield RichLog(id="log", highlight=False, markup=False, wrap=True, max_lines=20000)
            with Horizontal(classes="row buttonbar"):
                yield YButton("Help  F1", id="bar-help")
                yield YButton("Clear output  F8", id="bar-clear")
                yield Static(classes="spacer")
                yield YButton("Back  F9", id="bar-back", variant="primary")
            yield Footer()

        def compose_body(self):
            yield Static("")

        def on_mount(self):
            if self.DATA:
                self.add_class("data")
            self.query_one("#log").border_title = "Output"
            self.after_mount()
            self.show_unavailable()
            first = next((w for w in self.query("*") if isinstance(w, (DataTable, Input, Button)) and w.focusable
                          and not (w.id or "").startswith("bar-")), None)
            if first is not None:
                first.focus()
            if self.REFRESH:
                self.run_worker(self.safe(self.refresh_data))

        def after_mount(self):
            pass

        def show_unavailable(self):
            lines = getattr(self, "_unavail", [])
            w = self.query_one("#unavail", Static)
            if lines:
                w.update(Text("Not available here:\n" + "\n".join(f"  - {a}: {b}" for a, b in lines), style="italic"))
                w.display = True
            else:
                w.display = False

        # ---- running things ----------------------------------------------------------------------------
        @property
        def log_w(self) -> RichLog:
            return self.query_one("#log", RichLog)

        def say(self, text: str, style: str = ""):
            self.log_w.write(Text(text, style=style))

        async def safe(self, fn):
            try:
                await fn()
            except (ValueError, NotSupported) as e:
                self.say("!! " + str(e), "bold red")
                self.notify(str(e), title=APP_NAME, severity="error", timeout=6)
            except Exception as e:
                self.say(traceback.format_exc(), "red")
                self.notify(f"{type(e).__name__}: {e}", title=APP_NAME, severity="error")

        def go(self, fn):
            self.run_worker(self.safe(fn), group="actions")

        async def run_op(self, op: str, confirm: str = "", danger: bool = True, grep: str = "", **params) -> int:
            cmds = self.be.cmds(op, **params)
            if grep:
                for c in cmds:
                    c.filter = grep
            if confirm and not await self.confirm(confirm, danger):
                self.say("cancelled", "yellow")
                return -1
            rc, _ = await self.app.run_cmds(cmds, self.log_w)
            return rc

        async def confirm(self, message: str, danger: bool = True) -> bool:
            return bool(await self.app.push_screen_wait(ConfirmScreen(message, danger)))

        def val(self, wid: str) -> Any:
            w = self.query_one("#" + wid)
            if isinstance(w, Select):
                v = w.value
                return None if v is getattr(Select, "BLANK", object()) else v
            return w.value

        # ---- keys and buttons ----------------------------------------------------------------------------
        def on_key(self, event):
            if self.handle_nav_key(event):
                event.stop()
                event.prevent_default()

        def on_button_pressed(self, event: Button.Pressed):
            bid = event.button.id or ""
            if bid == "bar-help":
                event.stop()
                self.action_help()
            elif bid == "bar-clear":
                event.stop()
                self.action_clear_log()
            elif bid == "bar-back":
                event.stop()
                self.action_back()
            elif isinstance(event.button, YButton) and event.button.action_fn is not None:
                event.stop()
                self.go(event.button.action_fn)

        def action_press_button(self, bid: str):
            try:
                b = self.query_one("#" + bid, Button)
            except Exception:
                return
            if not b.disabled:
                b.focus()
                b.press()

        def check_action(self, action: str, parameters) -> Optional[bool]:
            if action == "refresh":
                return bool(self.REFRESH)          # False = hidden from the footer
            if action == "stop":
                return bool(self.app.busy)
            return True

        async def refresh_data(self):
            pass

        def action_refresh(self):
            if self.REFRESH:
                self.go(self.refresh_data)

        def action_help(self):
            self.app.push_screen(TextScreen(f"Help - {self.TITLE}", self.help_text()))

        def help_text(self) -> Any:
            t = Text()
            t.append(f"{self.TITLE}\n", style="bold")
            t.append(self.DESC + "\n\n")
            if self.HELP:
                t.append(self.HELP.strip() + "\n\n")
            ops = self.help_ops()
            if ops:
                t.append("What the buttons run on this system\n", style="bold")
                for label, op in ops:
                    ok, why = self.be.available(op)
                    t.append(f"  {label}: ", style="bold" if ok else "dim")
                    t.append(self.be.describe(op) + "\n", style="" if ok else "dim")
            t.append("\nKeys: Alt+underlined letter presses a button; arrows move between buttons and rows; "
                     "F7 bigger output; F8 clear; F9 or Esc back; Ctrl+K stops a running command.\n")
            return t

        def help_ops(self) -> List[Tuple[str, str]]:
            return []

        def action_toggle_log(self):
            self.log_w.toggle_class("big")

        def action_clear_log(self):
            self.log_w.clear()

        def action_back(self):
            if self.app.busy:
                self.notify("A command is still running - press Ctrl+K to stop it first.", severity="warning")
                return
            self.app.pop_screen()

        def action_esc(self):
            f = self.focused
            if isinstance(f, Input) and f.value:
                f.value = ""
                return
            self.action_back()

        def action_stop(self):
            self.app.stop_command()

    # ---- declarative "button" modules ----------------------------------------------------------------
    class B:
        def __init__(self, label: str, op: str, variant: str = "default", args: Optional[Dict[str, Any]] = None,
                     confirm: str = "", danger: bool = True, grep: str = "", key: str = "", after: str = ""):
            self.label, self.op, self.variant, self.args = label, op, variant, args or {}
            self.confirm, self.danger, self.grep, self.key, self.after = confirm, danger, grep, key, after

    class I:
        def __init__(self, id: str, placeholder: str, width: str = "", password: bool = False, value: str = ""):
            self.id, self.placeholder, self.width, self.password, self.value = id, placeholder, width, password, value

    class Sel:
        def __init__(self, id: str, options: List[Tuple[str, str]], value: str = "", width: str = ""):
            self.id, self.options, self.value, self.width = id, options, value or options[0][1], width

    class K:
        def __init__(self, id: str, label: str, value: bool = False):
            self.id, self.label, self.value = id, label, value

    class T:
        def __init__(self, text: str):
            self.text = text

    class ActionModule(ModuleScreen):
        """A module described by SPEC: a list of rows (strings are section headings)."""
        SPEC: List[Any] = []
        BIG_OUTPUT = True

        def __init_subclass__(cls, **kw):
            super().__init_subclass__(**kw)
            binds = []
            for r, row in enumerate(cls.SPEC):
                if isinstance(row, list):
                    for c, item in enumerate(row):
                        if isinstance(item, B) and item.key:
                            binds.append(Binding(item.key, f"press_button('b{r}_{c}')", plain_label(item.label)))
            if binds:
                cls.BINDINGS = list(ModuleScreen.BINDINGS) + binds

        @classmethod
        def all_ops(cls) -> List[str]:
            return [it.op for row in cls.SPEC if isinstance(row, list) for it in row if isinstance(it, B)]

        @classmethod
        def check_available(cls, be: Backend) -> Tuple[bool, str]:
            ops = cls.all_ops() or cls.OPS
            if not ops or any(op in be.ops for op in ops):
                return True, ""
            return False, f"no {cls.TITLE.lower()} tools on {FAMILY_NAME.get(be.family, be.family)}"

        def spec(self) -> List[Any]:
            return self.SPEC

        def fmt(self, text: str) -> str:
            be = self.be
            try:
                return text.format(pkg_label=be.pkg_label, svc_label=be.svc_label, fw_label=be.fw_label,
                                   note=be.fw_enable_note, platform=be.label)
            except (KeyError, IndexError):
                return text

        def compose_body(self):
            self._unavail = []
            self._specs: Dict[str, B] = {}
            pending_heading = None
            for r, row in enumerate(self.spec()):
                if isinstance(row, str):
                    pending_heading = row
                    continue
                buttons = [it for it in row if isinstance(it, B)]
                states = {id(b): self.be.available(b.op) for b in buttons}
                for b in buttons:
                    ok, why = states[id(b)]
                    if not ok and b.op in self.be.ops:
                        self._unavail.append((plain_label(b.label), why))
                if buttons and not any(b.op in self.be.ops for b in buttons):
                    continue          # this platform has none of these -> hide the row
                widgets = []
                for c, item in enumerate(row):
                    if isinstance(item, B):
                        if item.op not in self.be.ops:
                            continue
                        ok, why = states[id(item)]
                        bid = f"b{r}_{c}"
                        btn = YButton(item.label, id=bid, variant=item.variant if ok else "default",
                                      action=self._make_action(item))
                        btn.disabled = not ok
                        try:
                            btn.tooltip = why or self.be.describe(item.op)
                        except Exception:
                            pass
                        self._specs[bid] = item
                        widgets.append(btn)
                    elif isinstance(item, I):
                        inp = Input(placeholder=item.placeholder, id=item.id, password=item.password, value=item.value)
                        if item.width:
                            inp.styles.width = item.width
                        widgets.append(inp)
                    elif isinstance(item, Sel):
                        s = Select(item.options, value=item.value, allow_blank=False, id=item.id)
                        if item.width:
                            s.styles.width = item.width
                        widgets.append(s)
                    elif isinstance(item, K):
                        widgets.append(Checkbox(item.label, item.value, id=item.id))
                    elif isinstance(item, T):
                        widgets.append(Static(self.fmt(item.text), classes="hint"))
                if not widgets:
                    continue
                if pending_heading:
                    yield Static(pending_heading, classes="section")
                    pending_heading = None
                yield Horizontal(*widgets, classes="row")

        def _make_action(self, item: B):
            async def run():
                params = {}
                for k, v in item.args.items():
                    params[k] = self.val(v[1:]) if isinstance(v, str) and v.startswith("#") else v
                grep = ""
                if item.grep:
                    grep = str(self.val(item.grep[1:]) or "").strip() if item.grep.startswith("#") else item.grep
                shown = {k: ("****" if k in ("password", "newpw") else v) for k, v in params.items()}
                confirm = ""
                if item.confirm:
                    try:
                        confirm = self.fmt(item.confirm).format(**shown) if "{" in item.confirm else item.confirm
                    except (KeyError, IndexError):
                        confirm = item.confirm
                rc = await self.run_op(item.op, confirm=confirm, danger=item.danger, grep=grep, **params)
                if rc == 0 and item.after and self.be.available(item.after)[0]:
                    await self.run_op(item.after)
            return run

        def help_ops(self):
            return [(plain_label(b.label), b.op) for row in self.spec() if isinstance(row, list)
                    for b in row if isinstance(b, B) and b.op in self.be.ops]

        @on(Input.Submitted)
        def input_enter(self, event):
            row = self._row_of(event.input)
            rows = list(self.query(".row"))
            if row is None:
                return
            i = rows.index(row) if row in rows else -1
            for r in [row] + (rows[i + 1:i + 2] if i >= 0 else []):
                for b in r.query(YButton):
                    if not b.disabled:
                        event.stop()
                        b.press()
                        return

    # ---- the application ------------------------------------------------------------------------------
    BASE_CSS = """
    Screen { background: $background; }
    .title { height: 1; background: $primary; color: $background; text-style: bold; }
    .dim { color: $text-muted; }
    .hint { color: $text-muted; text-style: italic; padding: 0 1 0 0; height: auto; width: 1fr; }
    .section { color: $accent; text-style: bold; padding: 1 0 0 0; height: auto; }
    .unavail { color: $text-muted; padding: 1 0 0 0; height: auto; }
    .row { height: auto; margin: 0 0 1 0; }
    .row Button { margin: 0 1 0 0; min-width: 8; }
    .row Input { width: 1fr; margin: 0 1 0 0; }
    .row Select { width: 22; margin: 0 1 0 0; }
    .row Checkbox { margin: 0 1 0 0; }
    .row .spacer { width: 1fr; height: 1; }
    .buttonbar { height: auto; margin: 0; padding: 0 1; background: $panel; }
    .buttonbar Button { margin: 0 1 0 0; }
    #cc-main { height: 1fr; }
    #cc-left { width: 30; }
    #cc-groups { height: 1fr; border: round $primary; }
    #cc-modules { height: 1fr; border: round $secondary; }
    #cc-search { margin: 0 0 0 0; }
    #cc-desc { height: 4; padding: 0 1; border-top: solid $primary; }
    ListView > ListItem.--highlight { text-style: bold; }
    ModuleScreen #body { height: auto; max-height: 65%; padding: 0 1; }
    ModuleScreen.data #body { height: 1fr; max-height: 100%; }
    ModuleScreen #log { height: 1fr; min-height: 5; border: round $secondary; }
    ModuleScreen.data #log { height: 10; }
    ModuleScreen #log.big { height: 80%; }
    ModuleScreen DataTable { height: 1fr; min-height: 5; margin: 0 0 1 0; }
    ModuleScreen .tables { height: 1fr; }
    ModuleScreen .tables DataTable { width: 1fr; margin: 0 1 1 0; }
    .dialog { width: 76; height: auto; max-height: 90%; background: $surface; border: thick $warning; padding: 1 2; }
    .dialog.wide { width: 100; height: 90%; border: thick $accent; }
    .dlg-title { text-style: bold; color: $accent; height: auto; padding: 0 0 1 0; }
    #txt-scroll { height: 1fr; }
    .dlg-buttons { height: auto; align-horizontal: right; margin: 1 0 0 0; }
    .dlg-buttons Button { margin: 0 0 0 2; }
    ConfirmScreen, TextScreen { align: center middle; }
    #ov-info { height: auto; }
    """

    SAFE_CSS = """
    #cc-groups { border: solid $primary; }
    #cc-modules { border: solid $secondary; }
    ModuleScreen #log { border: solid $secondary; }
    .dialog { border: double $warning; }
    .dialog.wide { border: double $accent; }
    Button, Button:hover, Button:focus, Button.-active, Button:disabled { border: blank !important; }
    Button:focus { text-style: bold reverse; }
    Input { border: solid $border-blurred !important; }
    Input:focus { border: solid $border !important; }
    SelectCurrent { border: solid $border-blurred !important; }
    Select:focus > SelectCurrent { border: solid $border !important; }
    SelectOverlay { border: solid $border !important; }
    ToggleButton { border: solid $border-blurred !important; }
    ToggleButton:focus { border: solid $border !important; }
    Toast { border-left: solid $primary !important; }
    Toast.-warning { border-left: solid $warning !important; }
    Toast.-error { border-left: solid $error !important; }
    """

    class SafeScrollBarRender(ScrollBarRender):
        VERTICAL_BARS = [" "] * 8
        HORIZONTAL_BARS = [" "] * 8

    def apply_safe_glyphs():
        from textual.widgets._toggle_button import ToggleButton
        ScrollBar.renderer = SafeScrollBarRender
        ToggleButton.BUTTON_LEFT, ToggleButton.BUTTON_INNER, ToggleButton.BUTTON_RIGHT = "[", "X", "]"

    def grep_match(line: str, pattern: str) -> bool:
        low = line.lower()
        for alt in pattern.lower().split("|"):
            alt = alt.strip() if alt.strip() else alt
            if not alt:
                continue
            if alt.startswith("^"):
                if low.lstrip().startswith(alt[1:]):
                    return True
            elif alt in low:
                return True
        return False

    class UYastApp(App):
        TITLE = APP_NAME
        CSS = BASE_CSS
        HEADER_ICON = "≡"
        ENABLE_COMMAND_PALETTE = False

        def __init__(self, backend: Backend, cfg: dict, home: Path, safe: bool = False):
            super().__init__()
            self.backend, self.cfg, self.home, self.safe = backend, cfg, home, safe
            self._lock = asyncio.Lock()
            self.busy = False
            self._proc = None
            self._stopped = False
            self.base_subtitle = ""

        def on_mount(self):
            for th in YAST_THEMES:
                try:
                    self.register_theme(th)
                except Exception:
                    pass
            try:
                self.theme = self.cfg.get("theme", "yast")
            except Exception:
                pass
            self.base_subtitle = f"{FAMILY_NAME.get(self.backend.family, '?')}  |  " + (
                ("Administrator" if IS_WINDOWS else "root") if is_admin() else "NOT elevated - changes disabled")
            self.sub_title = self.base_subtitle
            self.push_screen(ControlCenter())

        def set_busy(self, busy: bool, what: str = ""):
            self.busy = busy
            self.sub_title = ("running: " + what[:70]) if busy else self.base_subtitle
            try:
                self.screen.refresh_bindings()
            except Exception:
                pass

        def stop_command(self):
            if self._proc is not None and self._proc.returncode is None:
                self._stopped = True
                try:
                    self._proc.kill()
                except Exception:
                    pass
                self.notify("Command stopped.", severity="warning")

        def _wrap_user(self, cmd: Cmd) -> List[str]:
            argv = list(cmd.argv or [])
            user = invoking_user()
            if not cmd.user or IS_WINDOWS or not is_admin() or not user or user == "root":
                return argv
            envs = [f"{k}={v}" for k, v in (cmd.env or {}).items()] + [f"PATH={os.environ.get('PATH', '')}"]
            if which_ext("sudo"):
                return ["sudo", "-u", user, "-H", "env"] + envs + argv
            return ["su", user, "-c", shlex.join(["env"] + envs + argv)]

        @staticmethod
        def _spawn_kwargs() -> Dict[str, Any]:
            if IS_WINDOWS:
                return {"creationflags": 0x08000000}
            return {"start_new_session": True}

        async def capture(self, cmd: Cmd, timeout: float = 60) -> Tuple[int, str]:
            env = dict(os.environ, **(cmd.env or {}))
            try:
                proc = await asyncio.create_subprocess_exec(
                    *self._wrap_user(cmd), stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, env=env, **self._spawn_kwargs())
            except (OSError, ValueError):
                return 127, ""
            try:
                out, _ = await asyncio.wait_for(proc.communicate(), timeout)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return 124, ""
            return proc.returncode or 0, decode_bytes(out)

        async def run_cmds(self, cmds: List[Cmd], log: RichLog) -> Tuple[int, str]:
            if self._lock.locked():
                self.notify("Another command is running - this one starts after it.", timeout=3)
            async with self._lock:
                out: List[str] = []
                self.set_busy(True, cmds[0].display() if cmds else "")
                try:
                    for c in cmds:
                        rc = await self._run_one(c, log, out)
                        if self._stopped:
                            self._stopped = False
                            log.write(Text("-- stopped --", style="bold yellow"))
                            return 130, "\n".join(out)
                        if rc not in c.ok_codes:
                            if c.allow_fail:
                                log.write(Text(f"(exit code {rc})", style="yellow"))
                            else:
                                log.write(Text(f"!! failed (exit code {rc})", style="bold red"))
                                self.notify(f"Command failed (exit code {rc}) - see the output.", severity="error")
                                return rc, "\n".join(out)
                    log.write(Text("-> done", style="green"))
                    return 0, "\n".join(out)
                finally:
                    self._proc = None
                    self.set_busy(False)

        async def _run_one(self, c: Cmd, log: RichLog, out: List[str]) -> int:
            grep = c.grep
            extra = c.filter
            if c.func:
                log.write(Text("> " + c.desc, style="bold cyan"))
                try:
                    res = await in_thread(c.func)
                except Exception as e:
                    log.write(Text(str(e), style="red"))
                    return 1
                lines = str(res or "").splitlines()
                shown = [l for l in lines if (not grep or grep_match(l, grep)) and (not extra or grep_match(l, extra))]
                for line in (shown[-c.tail:] if c.tail else shown):
                    log.write(Text(line))
                out.extend(lines)
                return 0
            disp = c.display()
            log.write(Text(disp if disp.startswith(("PS>", "$ ")) else "$ " + disp, style="bold cyan"))
            argv = self._wrap_user(c)
            env = dict(os.environ, **(c.env or {}))
            try:
                proc = await asyncio.create_subprocess_exec(
                    *argv, stdin=asyncio.subprocess.PIPE if c.input is not None else asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env=env, **self._spawn_kwargs())
            except (OSError, ValueError) as e:
                log.write(Text(f"cannot run {argv[0]}: {getattr(e, 'strerror', None) or e}", style="red"))
                return 127
            self._proc = proc
            if c.input is not None:
                try:
                    proc.stdin.write(c.input.encode())
                    await proc.stdin.drain()
                    proc.stdin.close()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            kept: List[str] = []
            buf = b""
            t0 = time.time()

            def emit(raw: bytes):
                line = ANSI_RE.sub("", decode_bytes(raw)).rstrip()
                if not line or SPINNER_RE.match(line) or re.search("[█▒░]", line):
                    return
                out.append(line)
                if len(out) > 50000:
                    del out[:25000]
                if (grep and not grep_match(line, grep)) or (extra and not grep_match(line, extra)):
                    return
                if c.tail:
                    kept.append(line)
                    if len(kept) > c.tail:
                        del kept[0]
                else:
                    log.write(Text(line))
            while True:
                try:
                    chunk = await (asyncio.wait_for(proc.stdout.read(4096), c.timeout) if c.timeout else proc.stdout.read(4096))
                except asyncio.TimeoutError:
                    proc.kill()
                    log.write(Text(f"-- timed out after {c.timeout:.0f}s --", style="yellow"))
                    break
                if not chunk:
                    break
                parts = re.split(rb"\r\n|\n|\r", buf + chunk)
                buf = parts.pop()
                for p in parts:
                    emit(p)
            if buf:
                emit(buf)
            for line in kept:
                log.write(Text(line))
            rc = await proc.wait()
            if time.time() - t0 > 3:
                log.write(Text(f"({time.time() - t0:.0f} s)", style="dim"))
            return rc

    class SafeUYastApp(UYastApp):
        CSS = BASE_CSS + SAFE_CSS

        def format_title(self, title, sub_title):
            from textual.content import Content
            if not sub_title:
                return Content(title)
            return Content.assemble(Content(title), ("  |  ", "dim"), Content(sub_title).stylize("dim"))

    ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][0-9A-Za-z]")


if HAVE_TEXTUAL:
    # ---- helpers for table modules ---------------------------------------------------------------------
    class TableModule(ModuleScreen):
        DATA = True
        REFRESH = True

        def opbtn(self, label: str, op: str, fn, variant: str = "default", id: Optional[str] = None) -> YButton:
            ok, why = self.be.available(op)
            b = YButton(label, id=id, variant=variant if ok else "default", action=fn)
            b.disabled = not ok
            if not ok:
                if not hasattr(self, "_unavail"):
                    self._unavail = []
                if op in self.be.ops:
                    self._unavail.append((plain_label(label), why))
            try:
                b.tooltip = why or self.be.describe(op)
            except Exception:
                pass
            if op not in self.be.ops:
                b.display = False
            return b

        def fill_table(self, table: DataTable, rows: List[List[str]], flt: str = "", width: int = 70):
            f = flt.strip().lower()
            cur = table.cursor_row if table.row_count else 0
            table.clear()
            for r in rows:
                if not f or f in " ".join(r).lower():
                    table.add_row(*[str(c)[:width] for c in r])
            if table.row_count:
                table.move_cursor(row=min(cur, table.row_count - 1))

        def selected(self, table_id: str, col: int = 0, what: str = "row") -> str:
            t = self.query_one("#" + table_id, DataTable)
            if t.row_count == 0:
                raise ValueError(f"No {what} selected.")
            return str(t.get_row_at(t.cursor_row)[col])

    # ======================= System =======================================================================
    @yast_module("overview", "system", "System Overview",
                 "Host, operating system, CPU, memory, disks, uptime and which tools uYaST uses on this machine.")
    class OverviewModule(ModuleScreen):
        REFRESH = True

        def compose_body(self):
            yield Static(id="ov-info")
            yield Horizontal(YButton("&Refresh", variant="primary", action=self.refresh_data),
                             YButton("Failed &services", action=self.failed), classes="row")

        async def refresh_data(self):
            info = await in_thread(self.be.sysinfo)
            t = Table(show_header=False, box=None, padding=(0, 2))
            t.add_column(style="bold")
            t.add_column()
            for k, v in info:
                t.add_row(k, Text(str(v), style="bold red" if "NOT elevated" in str(v) else ""))
            self.query_one("#ov-info", Static).update(t)

        async def failed(self):
            if not self.be.available("svc.failed")[0]:
                raise NotSupported("Listing failed services is not available here.")
            await self.run_op("svc.failed")

    @yast_module("services", "system", "Services Manager",
                 "Start, stop and restart services and choose which ones start at boot (systemd, OpenRC, runit, launchd, Windows services, rc.d, SMF).")
    class ServicesModule(TableModule):
        OPS = ["svc.status", "svc.start"]
        HELP = "Pick a service in the table (type in the filter to narrow it), then use a button. Enter on a row shows its status."

        def compose_body(self):
            yield Static(f"Back-end: {self.be.svc_label}", classes="hint")
            yield Horizontal(Input(placeholder="filter services ...", id="svc-filter"),
                             YButton("Re&fresh", action=self.refresh_data), classes="row")
            yield DataTable(id="svc-table", cursor_type="row", zebra_stripes=True)
            yield Horizontal(self.opbtn("&Start", "svc.start", lambda: self.act("start"), "success"),
                             self.opbtn("S&top", "svc.stop", lambda: self.act("stop"), "error"),
                             self.opbtn("&Restart", "svc.restart", lambda: self.act("restart"), "warning"),
                             self.opbtn("Stat&us", "svc.status", lambda: self.act("status"), "primary"),
                             self.opbtn("&Enable at boot", "svc.enable", lambda: self.act("enable")),
                             self.opbtn("&Disable at boot", "svc.disable", lambda: self.act("disable")),
                             self.opbtn("&Manual start", "svc.manual", lambda: self.act("manual")), classes="row")

        def after_mount(self):
            self.rows: List[List[str]] = []
            self.query_one("#svc-table", DataTable).add_columns("Service", "State", "Start at boot", "Description")

        async def refresh_data(self):
            self.say("loading services ...", "dim")
            self.rows = await self.be.services(self.app.capture)
            self.fill_table(self.query_one("#svc-table", DataTable), self.rows, self.val("svc-filter"))
            self.say(f"{len(self.rows)} services", "dim")

        @on(Input.Changed, "#svc-filter")
        def filtered(self):
            self.fill_table(self.query_one("#svc-table", DataTable), getattr(self, "rows", []), self.val("svc-filter"))

        @on(DataTable.RowSelected, "#svc-table")
        def row_enter(self):
            self.go(lambda: self.act("status"))

        async def act(self, action: str):
            name = self.selected("svc-table", what="service")
            ask = {"stop": f"Stop service '{name}'?\n\nStopping sshd / remote-access services can cut off your session.",
                   "disable": f"Stop '{name}' from starting at boot?"}.get(action, "")
            rc = await self.run_op(f"svc.{action}", confirm=ask, svc=name)
            if action != "status" and rc == 0:
                await self.refresh_data()

        def help_ops(self):
            return [(a.title(), f"svc.{a}") for a in ("start", "stop", "restart", "status", "enable", "disable", "manual")
                    if f"svc.{a}" in self.be.ops]

    @yast_module("processes", "system", "Processes",
                 "Running processes with CPU and memory use; end or kill a process (like a task manager).")
    class ProcessesModule(TableModule):
        BINDINGS = ModuleScreen.BINDINGS + [Binding("f5", "press_button('pr-end')", "End process"),
                                            Binding("delete", "press_button('pr-end')", "End", show=False)]

        def compose_body(self):
            yield Horizontal(Input(placeholder="filter processes ...", id="pr-filter"),
                             Select([("Sort: CPU", "cpu"), ("Sort: memory", "mem"), ("Sort: PID", "pid"), ("Sort: name", "name")],
                                    value="cpu", allow_blank=False, id="pr-sort"),
                             Checkbox("Auto-refresh (5 s)", False, id="pr-auto"),
                             YButton("Re&fresh", action=self.refresh_data), classes="row")
            yield DataTable(id="pr-table", cursor_type="row", zebra_stripes=True)
            yield Horizontal(self.opbtn("&End process", "proc.kill", lambda: self.kill(False), "warning", id="pr-end"),
                             self.opbtn("&Kill (force)", "proc.kill9", lambda: self.kill(True), "error"), classes="row")

        def after_mount(self):
            self.rows = []
            cpu = "CPU time" if IS_WINDOWS else "CPU %"
            mem = "Memory" if IS_WINDOWS else "Mem %"
            self.query_one("#pr-table", DataTable).add_columns("PID", "User", cpu, mem, "Command")
            self._timer = self.set_interval(5, self._auto, pause=True)

        def _auto(self):
            if self.query_one("#pr-auto", Checkbox).value and not self.app.busy:
                self.go(self.refresh_data)

        @on(Checkbox.Changed, "#pr-auto")
        def auto_changed(self, event):
            (self._timer.resume if event.value else self._timer.pause)()

        @staticmethod
        def _num(s: str) -> float:
            m = re.search(r"[\d.,:]+", s or "")
            if not m:
                return 0.0
            v = m.group(0)
            if ":" in v:
                parts = [float(x or 0) for x in v.split(":")]
                total = 0.0
                for p in parts:
                    total = total * 60 + p
                return total
            v = v.replace(",", "") if v.count(",") and "." not in v and len(v.split(",")[-1]) == 3 else v.replace(",", ".")
            try:
                return float(v.replace(".", "", v.count(".") - 1) if v.count(".") > 1 else v)
            except ValueError:
                return 0.0

        def sorted_rows(self):
            key = self.val("pr-sort")
            if key == "pid":
                return sorted(self.rows, key=lambda r: int(r[0]))
            if key == "name":
                return sorted(self.rows, key=lambda r: r[4].lower())
            idx = 2 if key == "cpu" else 3
            return sorted(self.rows, key=lambda r: self._num(r[idx]), reverse=True)

        async def refresh_data(self):
            self.rows = await self.be.processes(self.app.capture)
            self.fill_table(self.query_one("#pr-table", DataTable), self.sorted_rows(), self.val("pr-filter"), 90)

        @on(Input.Changed, "#pr-filter")
        @on(Select.Changed, "#pr-sort")
        def resort(self):
            self.fill_table(self.query_one("#pr-table", DataTable), self.sorted_rows(), self.val("pr-filter"), 90)

        async def kill(self, force: bool):
            pid = self.selected("pr-table", what="process")
            name = self.selected("pr-table", 4)
            op = "proc.kill9" if force else "proc.kill"
            rc = await self.run_op(op, confirm=f"{'KILL' if force else 'End'} process {pid} ({name})?", pid=pid)
            if rc == 0:
                await asyncio.sleep(0.5)
                await self.refresh_data()

    @yast_module("datetime", "system", "Date, Time and Language",
                 "Clock, time zone, network time synchronisation and system language / locale.")
    class DateTimeModule(ActionModule):
        SPEC = [
            [B("&Show date and time", "time.show", "primary"), B("Synchronize &now", "time.sync"),
             B("Network time &on", "time.ntp.on"), B("Network time o&ff", "time.ntp.off")],
            "Time zone",
            [I("tz", "time zone, e.g. Europe/Berlin  (Windows: W. Europe Standard Time)"),
             B("&List time zones", "time.tz.list", grep="#tz"),
             B("Set &time zone", "time.tz.set", "warning", args={"tz": "#tz"}, confirm="Set the time zone to {tz}?", danger=False)],
            "Language / locale",
            [I("locale", "locale, e.g. en_US.UTF-8 or de-DE"), B("Show l&anguage", "locale.show"),
             B("List lo&cales", "locale.list", grep="#locale"),
             B("Set locale", "locale.set", "warning", args={"locale": "#locale"}, confirm="Set the system locale to {locale}?", danger=False)],
        ]
        HELP = "Typing in a field filters the lists: e.g. type 'Berlin' and press 'List time zones'."

    @yast_module("kernel", "system", "Kernel Settings",
                 "Kernel version, loaded modules / drivers, kernel parameters (sysctl) and loading or unloading modules.")
    class KernelModule(ActionModule):
        SPEC = [
            [B("Kernel &info", "kernel.info", "primary"), B("Loaded &modules / drivers", "kernel.modules"),
             B("&Parameters", "kernel.params", grep="#key")],
            "Change a kernel parameter (sysctl)",
            [I("key", "parameter, e.g. net.ipv4.ip_forward"), I("value", "value", width="18"),
             K("persist", "Save permanently", True),
             B("&Set", "kernel.set", "warning", args={"key": "#key", "value": "#value", "persist": "#persist"},
               confirm="Set kernel parameter {key} = {value}?")],
            "Kernel modules",
            [I("mod", "module name, e.g. loop"), B("&Load", "kernel.load", args={"mod": "#mod"}),
             B("&Unload", "kernel.unload", "warning", args={"mod": "#mod"}, confirm="Unload kernel module {mod}?")],
        ]
        HELP = "Type part of a parameter name into the first field before pressing 'Parameters' to show only matching lines."

    @yast_module("boot", "system", "Boot Configuration",
                 "Boot loader settings, firmware boot entries, default boot target and boot menu timeout.")
    class BootModule(ActionModule):
        SPEC = [
            [B("Boot &configuration", "boot.show", "primary"), B("Firmware boot &entries", "boot.entries"),
             B("Default &target", "boot.target.show")],
            "Change",
            [Sel("target", [("Text mode (multi-user)", "multi-user.target"), ("Graphical desktop", "graphical.target"),
                            ("Rescue mode", "rescue.target")], width="34"),
             B("Set boot ta&rget", "boot.target.set", "warning", args={"target": "#target"}, confirm="Boot into {target} from now on?")],
            [B("Re&generate GRUB menu", "boot.grub", "warning", confirm="Regenerate the GRUB boot menu from /etc/default/grub?")],
            [I("seconds", "boot menu timeout in seconds", width="34"),
             B("Set ti&meout", "boot.timeout", "warning", args={"seconds": "#seconds"}, confirm="Set the boot menu timeout to {seconds} s?")],
        ]

    @yast_module("schedule", "system", "Scheduled Tasks",
                 "cron jobs, systemd timers and the Windows Task Scheduler.")
    class ScheduleModule(ActionModule):
        SPEC = [
            [I("filter", "filter the output (optional)")],
            [B("&Scheduled tasks", "sched.list", "primary", grep="#filter"), B("S&ystem crontab", "sched.system"),
             B("systemd &timers", "sched.timers", grep="#filter")],
            "Windows Task Scheduler",
            [I("task", "task name, e.g. \\Microsoft\\Windows\\Defrag\\ScheduledDefrag"),
             B("&Run task", "sched.run", args={"task": "#task"}),
             B("&Enable", "sched.enable", args={"task": "#task"}),
             B("&Disable", "sched.disable", "warning", args={"task": "#task"}, confirm="Disable scheduled task {task}?")],
        ]

    @yast_module("power", "system", "Power Management",
                 "Battery and power settings, power plans, suspend, restart and power off (now or later).")
    class PowerModule(ActionModule):
        SPEC = [
            [B("Power &information", "power.info", "primary")],
            "Power plan",
            [Sel("plan", [("Balanced", "SCHEME_BALANCED"), ("High performance", "SCHEME_MIN"), ("Power saver", "SCHEME_MAX")],
                 width="26"), B("Set &plan", "power.plan.set", args={"plan": "#plan"})],
            "Shut down / restart",
            [B("&Suspend", "power.suspend", confirm="Suspend (sleep) the computer now?"),
             B("&Restart", "power.reboot", "warning", confirm="RESTART the computer now?\n\nEveryone working on it will be disconnected."),
             B("Power &off", "power.off", "error", confirm="POWER OFF the computer now?\n\nEveryone working on it will be disconnected.")],
            [I("minutes", "minutes", width="14"),
             B("Power off &later", "power.schedule", "warning", args={"minutes": "#minutes"}, confirm="Power off in {minutes} minute(s)?"),
             B("&Cancel scheduled shutdown", "power.cancel")],
        ]

    # ======================= Software ===================================================================
    @yast_module("software", "software", "Software Management",
                 "Search, install, remove and inspect packages with the platform's package manager.")
    class SoftwareModule(ActionModule):
        SPEC = [
            [T("Back-end: {pkg_label}.  Several package names can be separated by spaces.")],
            [I("q", "package name(s) or search term")],
            [B("&Search", "pkg.search", "primary", args={"q": "#q"}),
             B("&Details", "pkg.info", args={"pkg": "#q"}, key="f4"),
             B("&Install", "pkg.install", "success", args={"pkgs": "#q"}, key="f3"),
             B("Install &app (cask)", "pkg.cask", "success", args={"pkgs": "#q"}),
             B("&Remove", "pkg.remove", "error", args={"pkgs": "#q"}, key="f5", confirm="Remove these packages?\n\n  {pkgs}")],
            [B("&List installed", "pkg.list", grep="#q"),
             B("Clean &cache", "pkg.clean", confirm="Remove unneeded packages and clean the package cache?", danger=False)],
        ]
        HELP = ("Enter in the field runs Search. F3 installs, F4 shows details, F5 removes. "
                "'List installed' shows only lines containing what you typed (leave empty for all).")

    @yast_module("update", "software", "Online Update",
                 "Check for and install package updates, patches and operating-system updates.")
    class UpdateModule(ActionModule):
        SPEC = [
            [T("Packages: {pkg_label}.  Operating-system updates use the platform's own updater.")],
            "Packages",
            [B("&Check for updates", "pkg.outdated", "primary"), B("Refresh &repositories", "pkg.refresh"),
             B("&Update all packages", "pkg.upgrade", "warning", confirm="Upgrade all installed packages now?\nThis can take a while.", danger=False),
             B("&Distribution upgrade", "pkg.distup", "warning", confirm="Run a full distribution upgrade (zypper dup)?")],
            "Patches",
            [B("List &patches", "os.patches.list"), B("&Apply patches", "os.patches.apply", "warning",
                                                       confirm="Install all needed patches now?", danger=False)],
            "Operating system",
            [B("List &OS updates", "os.updates.list", "primary"),
             B("&Install OS updates", "os.updates.install", "warning",
               confirm="Download and install all operating-system updates now?\nA restart may be needed afterwards.", danger=False),
             B("&Firmware updates", "os.firmware")],
        ]

    @yast_module("repos", "software", "Software Repositories",
                 "Show, refresh and add package sources (APT, Zypper, DNF, Homebrew taps, winget sources ...).")
    class ReposModule(ActionModule):
        SPEC = [
            [B("&Show repositories", "pkg.repos", "primary"), B("&Refresh", "pkg.refresh")],
            "Add a repository",
            [I("repo", "URL (zypper), ppa:user/name (Ubuntu) or tap (Homebrew)"),
             B("&Add", "repo.add", "success", args={"repo": "#repo"}, confirm="Add repository {repo}?", danger=False)],
        ]

    # ======================= Hardware ===================================================================
    @yast_module("hardware", "hardware", "Hardware Information",
                 "CPU, memory, graphics, PCI and USB devices, firmware / BIOS, sensors and battery.")
    class HardwareModule(ActionModule):
        SPEC = [
            [B("&Summary", "hw.summary", "primary"), B("&CPU", "hw.cpu"), B("&Memory", "hw.memory"), B("&Graphics", "hw.gpu")],
            [B("&PCI devices", "hw.pci"), B("&USB devices", "hw.usb"), B("&BIOS / firmware", "hw.bios"),
             B("Sensors / batter&y", "hw.sensors"), B("&Full report", "hw.full")],
        ]

    @yast_module("storage", "hardware", "Storage and Disks",
                 "Disks and partitions, file-system usage, mount points and disk health (read-only, safe).")
    class StorageModule(ActionModule):
        SPEC = [[B("&Disks", "hw.disks", "primary"), B("&File systems / usage", "hw.fs"), B("&Mounts", "hw.mounts"),
                 B("Disk &health", "hw.smart")]]

    @yast_module("printers", "hardware", "Printers",
                 "Installed printers, print queue, cancelling jobs and choosing the default printer.")
    class PrinterModule(ActionModule):
        SPEC = [
            [B("&Printers", "hw.printers", "primary"), B("Print &jobs", "printer.jobs"),
             B("&Cancel all jobs", "printer.cancel", "warning", confirm="Cancel all print jobs?")],
            [I("printer", "printer name"), B("Set as &default", "printer.default", args={"printer": "#printer"})],
        ]

    # ======================= Network ====================================================================
    @yast_module("network", "network", "Network Settings",
                 "Interfaces, addresses, routes, DNS, open ports, connections, DHCP, Wi-Fi and NetworkManager.")
    class NetworkModule(ActionModule):
        SPEC = [
            [B("&Interfaces", "net.interfaces", "primary"), B("&Links / adapters", "net.links"), B("&Routes", "net.routes"),
             B("&DNS servers", "net.dns")],
            [B("Listening &ports", "net.ports"), B("Active &connections", "net.conns"), B("&ARP / neighbours", "net.arp"),
             B("&Wi-Fi networks", "net.wifi")],
            "Interface",
            [I("iface", "interface, e.g. eth0, en0, Wi-Fi"), B("Interface &up", "net.if.up", args={"iface": "#iface"}),
             B("Interface d&own", "net.if.down", "warning", args={"iface": "#iface"},
               confirm="Take interface {iface} down?\nIf you are connected through it, you will lose the connection."),
             B("Renew D&HCP", "net.dhcp.renew", args={"iface": "#iface"}), B("&Flush DNS cache", "net.dns.flush")],
            "NetworkManager",
            [B("NM d&evices", "net.nm.devices"), B("NM &saved connections", "net.nm.conns"), B("Wi-Fi sca&n", "net.nm.wifi")],
            [I("conn", "connection name"), B("Connec&t", "net.nm.up", args={"conn": "#conn"}),
             B("Deacti&vate", "net.nm.down", "warning", args={"conn": "#conn"}, confirm="Disconnect {conn}?")],
        ]

    @yast_module("diag", "network", "Network Diagnostics",
                 "Ping, traceroute, DNS lookup and TCP port test.")
    class DiagModule(ActionModule):
        SPEC = [
            [I("host", "host name or IP address"), I("port", "port for the TCP test", width="26")],
            [B("&Ping", "net.ping", "primary", args={"host": "#host"}), B("&Traceroute", "net.trace", args={"host": "#host"}),
             B("&DNS lookup", "net.lookup", args={"host": "#host"}),
             B("Test TCP p&ort", "net.tcptest", args={"host": "#host", "port": "#port"})],
        ]
        HELP = "Ctrl+K stops a long traceroute."

    @yast_module("hosts", "network", "Hostname and Hosts",
                 "Show or change the host name and edit the hosts file (local name resolution).")
    class HostsModule(ActionModule):
        SPEC = [
            [B("Show &host name", "net.hostname.show", "primary"), B("Show hosts &file", "hosts.show")],
            "Change the host name",
            [I("hostname", "new host name"), B("&Set host name", "net.hostname.set", "warning", args={"hostname": "#hostname"},
                                              confirm="Change the host name to {hostname}?", danger=False)],
            "Hosts file entries",
            [I("ip", "IP address", width="26"), I("hname", "host name"),
             B("&Add entry", "hosts.add", "success", args={"ip": "#ip", "entry": "#hname"}),
             B("&Remove host", "hosts.remove", "warning", args={"entry": "#hname"}, confirm="Remove {entry} from the hosts file?")],
        ]

    # ======================= Security and Users =========================================================
    @yast_module("users", "security", "User and Group Management",
                 "Local users and groups: add, delete, passwords, lock / unlock, group membership.")
    class UsersModule(TableModule):
        OPS = ["user.add", "user.info"]
        BINDINGS = ModuleScreen.BINDINGS + [Binding("f3", "press_button('u-add')", "Add"),
                                            Binding("f4", "press_button('u-pw')", "Password"),
                                            Binding("f5", "press_button('u-del')", "Delete")]
        HELP = ("Selecting a user or group in a table copies its name into the fields below. "
                "Tick 'Administrator' before 'Add user' to add the new user to the admin group "
                "(sudo/wheel on Linux & BSD, admin on macOS, Administrators on Windows).")

        def compose_body(self):
            yield Horizontal(Checkbox("Show system accounts", False, id="u-system"),
                             YButton("Re&fresh", action=self.refresh_data), classes="row")
            with Horizontal(classes="tables"):
                yield DataTable(id="u-users", cursor_type="row", zebra_stripes=True)
                yield DataTable(id="u-groups", cursor_type="row", zebra_stripes=True)
            yield Horizontal(Input(placeholder="user name", id="u-name"), Input(placeholder="password", password=True, id="u-pass"),
                             Input(placeholder="group", id="u-group"), Checkbox("Administrator", False, id="u-admin"), classes="row")
            yield Horizontal(self.opbtn("&Add user", "user.add", self.add, "success", id="u-add"),
                             self.opbtn("Set &password", "user.passwd", self.passwd, id="u-pw"),
                             self.opbtn("&Delete user", "user.delete", self.delete, "error", id="u-del"),
                             self.opbtn("&Lock", "user.lock", lambda: self.simple("user.lock")),
                             self.opbtn("&Unlock", "user.unlock", lambda: self.simple("user.unlock")),
                             self.opbtn("&Info", "user.info", lambda: self.simple("user.info")), classes="row")
            yield Horizontal(self.opbtn("&New group", "group.add", lambda: self.grp("group.add")),
                             self.opbtn("D&elete group", "group.delete", lambda: self.grp("group.delete", True)),
                             self.opbtn("Add to &group", "group.adduser", lambda: self.grp("group.adduser")),
                             self.opbtn("Re&move from group", "group.deluser", lambda: self.grp("group.deluser", True)),
                             self.opbtn("Mem&bers", "group.members", lambda: self.grp("group.members")), classes="row")

        def after_mount(self):
            u = self.query_one("#u-users", DataTable)
            u.add_columns(*self.be.USER_COLS)
            u.border_title = "Users"
            g = self.query_one("#u-groups", DataTable)
            g.add_columns(*self.be.GROUP_COLS)
            g.border_title = "Groups"

        async def refresh_data(self):
            show = self.query_one("#u-system", Checkbox).value
            self.fill_table(self.query_one("#u-users", DataTable), await self.be.users(self.app.capture, show), width=40)
            self.fill_table(self.query_one("#u-groups", DataTable), await self.be.groups(self.app.capture, show), width=40)

        @on(Checkbox.Changed, "#u-system")
        def toggled(self):
            self.go(self.refresh_data)

        @on(DataTable.RowHighlighted, "#u-users")
        def pick_user(self, event):
            try:
                self.query_one("#u-name", Input).value = str(event.data_table.get_row_at(event.cursor_row)[0])
            except Exception:
                pass

        @on(DataTable.RowHighlighted, "#u-groups")
        def pick_group(self, event):
            try:
                self.query_one("#u-group", Input).value = str(event.data_table.get_row_at(event.cursor_row)[0])
            except Exception:
                pass

        def _clear_pw(self):
            self.query_one("#u-pass", Input).value = ""

        async def add(self):
            name, pw = self.val("u-name"), self.val("u-pass")
            admin = self.query_one("#u-admin", Checkbox).value
            cmds_kw = dict(user=name, password=pw, newpw=pw, admin=admin)
            self._clear_pw()
            if await self.run_op("user.add", **cmds_kw) == 0:
                await self.refresh_data()

        async def passwd(self):
            name, pw = self.val("u-name"), self.val("u-pass")
            self._clear_pw()
            await self.run_op("user.passwd", user=name, newpw=pw)

        async def delete(self):
            name = str(self.val("u-name")).strip()
            if name.lower() in ("root", "administrator", "toor"):
                raise ValueError(f"Refusing to delete {name}.")
            if await self.run_op("user.delete", user=name,
                                 confirm=f"Delete user '{name}'?\n\nOn Linux, macOS and BSD the home folder is deleted too.") == 0:
                await self.refresh_data()

        async def simple(self, op: str):
            confirm = f"Lock the account '{self.val('u-name')}'?" if op == "user.lock" else ""
            await self.run_op(op, user=self.val("u-name"), confirm=confirm, danger=False)
            if op != "user.info":
                await self.refresh_data()

        async def grp(self, op: str, ask: bool = False):
            g, u = self.val("u-group"), self.val("u-name")
            confirm = ""
            if op == "group.delete":
                confirm = f"Delete group '{g}'?"
            elif op == "group.deluser":
                confirm = f"Remove '{u}' from group '{g}'?"
            if await self.run_op(op, group=g, user=u, confirm=confirm) == 0 and op != "group.members":
                await self.refresh_data()

        def help_ops(self):
            return [(n, o) for n, o in (("Add user", "user.add"), ("Set password", "user.passwd"), ("Delete user", "user.delete"),
                                        ("Lock", "user.lock"), ("Unlock", "user.unlock"), ("Info", "user.info"),
                                        ("New group", "group.add"), ("Delete group", "group.delete"),
                                        ("Add to group", "group.adduser"), ("Remove from group", "group.deluser"),
                                        ("Members", "group.members")) if o in self.be.ops]

    @yast_module("firewall", "security", "Firewall",
                 "Firewall status, on / off, open or close ports (ufw, firewalld, pf, Windows Defender Firewall, macOS application firewall).")
    class FirewallModule(ActionModule):
        SPEC = [
            [T("Back-end: {fw_label}")],
            [B("&Status", "fw.status", "primary"), B("&Rules", "fw.rules"),
             B("&Enable", "fw.enable", "success", confirm="Enable the firewall?\n\n{note}", danger=False, after="fw.status"),
             B("&Disable", "fw.disable", "error", confirm="Disable the firewall?\nThe computer will accept all incoming traffic."),
             B("Re&load", "fw.reload")],
            "Ports (incoming)",
            [I("port", "port or range, e.g. 80 or 8000-8010", width="40"), Sel("proto", [("TCP", "tcp"), ("UDP", "udp")], width="14"),
             B("&Allow port", "fw.allow", "success", args={"port": "#port", "proto": "#proto"}),
             B("Remove r&ule", "fw.remove", "warning", args={"port": "#port", "proto": "#proto"},
               confirm="Remove the rule for {port}/{proto}?", danger=False)],
            "Applications (macOS)",
            [I("path", "full path, e.g. /Applications/Foo.app"), B("Allow a&pp", "fw.app.allow", args={"path": "#path"}),
             B("&Block app", "fw.app.block", "warning", args={"path": "#path"}),
             B("Stealth &on", "fw.stealth.on"), B("Stealth o&ff", "fw.stealth.off")],
        ]

    @yast_module("security", "security", "Security Overview",
                 "Security status at a glance: SELinux/AppArmor, SIP/Gatekeeper/FileVault, Defender/BitLocker, logins, admins, scans.")
    class SecurityModule(ActionModule):
        SPEC = [
            [B("Security &overview", "sec.overview", "primary"), B("Recent &logins", "sec.logins"),
             B("&Failed logins", "sec.failed"), B("&Administrators", "sec.admins")],
            [B("&Malware / vulnerability scan", "sec.scan", "warning"), B("Failed &services", "svc.failed")],
        ]

    # ======================= Support =====================================================================
    @yast_module("logs", "support", "System Logs",
                 "System, kernel, authentication, boot and error logs (journal, syslog, unified log, Event Log).")
    class LogsModule(ActionModule):
        HELP = "Type text into the filter to show only matching lines ('|' means OR, e.g. error|fail)."

        def spec(self):
            return [[I("filter", "show only lines containing ...  (use | for OR, e.g. error|fail)")],
                    [B(f"&{label}" if i == 0 else label, op, "primary" if i == 0 else "default", grep="#filter")
                     for i, (op, label) in enumerate(self.be.LOG_KINDS)],
                    [B("Kernel ring &buffer (dmesg)", "log.dmesg", grep="#filter")]]

        @classmethod
        def check_available(cls, be):
            return True, ""

    @yast_module("report", "support", "Support Report",
                 "Collect system information, network, disks, failed services and recent errors into one text file.")
    class ReportModule(ModuleScreen):
        PARTS = [("System", None), ("Network interfaces", "net.interfaces"), ("Routes", "net.routes"), ("DNS", "net.dns"),
                 ("File systems", "hw.fs"), ("Disks", "hw.disks"), ("Failed services", "svc.failed"),
                 ("Security", "sec.overview"), ("Recent errors", "log.errors")]

        def compose_body(self):
            yield Static("The report is saved as a text file you can attach to a support request. "
                         "It contains host names, addresses and log lines - review it before sharing.", classes="hint")
            yield Horizontal(YButton("&Create report", variant="primary", action=self.create),
                             YButton("&Show last report", action=self.show_last), classes="row")

        def report_dir(self) -> Path:
            return self.app.home / "reports"

        async def create(self):
            parts: List[str] = [f"{APP_NAME} {VERSION} support report - {time.strftime('%Y-%m-%d %H:%M:%S')}", "=" * 72]
            for title, op in self.PARTS:
                self.say(f"collecting: {title}", "dim")
                parts.append(f"\n## {title}\n")
                if op is None:
                    parts += [f"{k}: {v}" for k, v in await in_thread(self.be.sysinfo)]
                    continue
                if not self.be.available(op)[0]:
                    parts.append("(not available here)")
                    continue
                for c in self.be.cmds(op):
                    if c.func:
                        try:
                            parts.append(str(await in_thread(c.func)))
                        except Exception as e:
                            parts.append(f"(failed: {e})")
                        continue
                    rc, out = await self.app.capture(c, 120)
                    lines = [l for l in out.splitlines() if not c.grep or grep_match(l, c.grep)]
                    parts.append(f"$ {c.display()}")
                    parts += lines[-(c.tail or 400):]
            d = self.report_dir()
            d.mkdir(parents=True, exist_ok=True)
            path = d / f"uyast-report-{time.strftime('%Y%m%d-%H%M%S')}.txt"
            path.write_text("\n".join(parts) + "\n", encoding="utf-8")
            try:
                os.chmod(str(path), 0o600)
            except OSError:
                pass
            self.say(f"Report saved: {path}", "bold green")
            self.notify(f"Report saved: {path}", timeout=8)

        async def show_last(self):
            d = self.report_dir()
            files = sorted(d.glob("uyast-report-*.txt")) if d.exists() else []
            if not files:
                raise ValueError("No report yet - press 'Create report' first.")
            self.app.push_screen(TextScreen(str(files[-1]), read_text(files[-1])))

    # ======================= Miscellaneous ===============================================================
    @yast_module("console", "misc", "Command Console",
                 "Run a single command with uYaST's rights (sh on Linux/macOS/Unix, PowerShell on Windows).")
    class ConsoleModule(ModuleScreen):
        HELP = "Up / Down in the field walk through the command history. Interactive programs (editors, pagers, password prompts) cannot run here."

        def compose_body(self):
            shell = "PowerShell" if IS_WINDOWS else "sh"
            yield Static(f"Runs one {shell} command. The output appears below.", classes="hint")
            inp = Input(placeholder="command", id="con-cmd")
            inp.history_nav = True
            yield Horizontal(inp, YButton("&Run", variant="primary", action=self.run_cmd), classes="row")

        def after_mount(self):
            self.history: List[str] = list(self.app.cfg.get("console_history", []))[-50:]
            self.hpos = len(self.history)

        async def run_cmd(self):
            command = self.val("con-cmd").strip()
            cmd = self.be.console_cmd(command)
            if command and (not self.history or self.history[-1] != command):
                self.history.append(command)
                self.app.cfg["console_history"] = self.history[-50:]
                save_config(self.app.home, self.app.cfg)
            self.hpos = len(self.history)
            await self.app.run_cmds([cmd], self.log_w)

        @on(Input.Submitted, "#con-cmd")
        def enter(self):
            self.go(self.run_cmd)

        def on_key(self, event):
            f = self.focused
            if isinstance(f, Input) and f.id == "con-cmd" and event.key in ("up", "down") and self.history:
                self.hpos = max(0, self.hpos - 1) if event.key == "up" else min(len(self.history), self.hpos + 1)
                f.value = self.history[self.hpos] if self.hpos < len(self.history) else ""
                f.cursor_position = len(f.value)
                event.stop()
                return
            super().on_key(event)

    @yast_module("envcheck", "misc", "Environment Check",
                 "Check that everything uYaST needs is present (tools, package manager, terminal, services) and install what is missing.")
    class EnvModule(TableModule):
        HELP = ("Required items must be OK for uYaST to work; recommended ones make more modules usable; optional ones "
                "add extra features. 'Fix' installs packages with the platform's package manager.")

        def compose_body(self):
            yield DataTable(id="env-table", cursor_type="row", zebra_stripes=True)
            yield Horizontal(YButton("Re-&check", variant="primary", action=self.refresh_data),
                             YButton("&Fix selected", action=self.fix_selected),
                             YButton("Fix all &recommended", variant="success", action=lambda: self.fix_level(("required", "recommended"))),
                             YButton("Install &optional tools", action=lambda: self.fix_level(("optional",))), classes="row")

        def after_mount(self):
            self.items: List[EnvItem] = []
            self.query_one("#env-table", DataTable).add_columns("Status", "Group", "Item", "Details", "Level")

        async def refresh_data(self):
            self.say("checking ...", "dim")
            self.be.redetect()
            self.items = await in_thread(lambda: environment_check(self.be, self.app.home, in_tui=True))
            t = self.query_one("#env-table", DataTable)
            t.clear()
            for it in self.items:
                status = "OK" if it.ok else ("info" if it.level == "info" else ("MISSING" if it.fixable else "PROBLEM"))
                t.add_row(status, it.group, it.title[:48], it.detail[:80], it.level)
            bad = [i for i in self.items if not i.ok and i.level in ("required", "recommended")]
            self.say(f"{len(self.items)} items checked, {len(bad)} need attention", "bold" if bad else "green")

        async def _fix(self, items: List[EnvItem]):
            items = [i for i in items if i.fixable]
            if not items:
                self.say("Nothing to fix here.", "green")
                return
            tonly = [i for i in items if i.terminal_only]
            if tonly:
                self.say("Needs the start-up wizard (run uyast.py --setup in a terminal): " + ", ".join(i.title for i in tonly), "yellow")
            items = [i for i in items if not i.terminal_only]
            if not items:
                return
            plan = fix_plan(items)
            text = "\n".join(f"  - {title}" for _, title, _ in plan)
            if not await self.confirm(f"Run these fixes?\n\n{text}", danger=False):
                return
            for kind, title, payload in plan:
                self.say(f">> {title}", "bold")
                if kind == "pkgs":
                    cmds = self.be.pkg_prepare_cmds()
                    if cmds:
                        await self.app.run_cmds(cmds, self.log_w)
                    rc, _ = await self.app.run_cmds(self.be.cmds("pkg.install", pkgs=" ".join(payload)), self.log_w)
                    if rc != 0:
                        for p in payload:
                            await self.app.run_cmds(self.be.cmds("pkg.install", pkgs=p), self.log_w)
                else:
                    await self.app.run_cmds(list(payload), self.log_w)
            await self.refresh_data()

        async def fix_selected(self):
            t = self.query_one("#env-table", DataTable)
            if not t.row_count:
                raise ValueError("Nothing selected.")
            await self._fix([self.items[t.cursor_row]])

        async def fix_level(self, levels):
            await self._fix([i for i in self.items if i.level in levels])

    @yast_module("settings", "misc", "uYaST Settings",
                 "Colour theme, symbol style (for fonts without special characters), Windows Terminal, upgrades and reset.")
    class SettingsModule(ModuleScreen):
        def compose_body(self):
            themes = [("YaST (openSUSE green)", "yast"), ("YaST light", "yast-light"), ("YaST classic blue", "yast-classic")]
            try:
                themes += [(n, n) for n in sorted(self.app.available_themes) if not n.startswith("yast")]
            except Exception:
                pass
            cur = self.app.cfg.get("theme", "yast")
            if cur not in [v for _, v in themes]:
                cur = "yast"
            yield Static("Theme", classes="section")
            yield Horizontal(Select(themes, value=cur, allow_blank=False, id="set-theme"),
                             YButton("&Apply theme", variant="primary", action=self.apply_theme), classes="row")
            yield Static("Symbols", classes="section")
            safe_now, why = decide_safe_glyphs(self.app.cfg)
            yield Static(f"Now: {'safe console symbols' if self.app.safe else 'full Unicode symbols'}  ({why})", classes="hint")
            yield Horizontal(Select([("Automatic", "auto"), ("Safe - plain console characters", "safe"),
                                     ("Fancy - full Unicode", "fancy")], value=self.app.cfg.get("glyphs", "auto"),
                                    allow_blank=False, id="set-glyphs"),
                             YButton("&Save symbol style", action=self.save_glyphs), classes="row")
            if IS_WINDOWS:
                yield Horizontal(Checkbox("Open uYaST in Windows Terminal when it is installed", self.app.cfg.get("use_wt", True),
                                          id="set-wt"), classes="row")
            yield Static("Maintenance", classes="section")
            yield Horizontal(YButton("&Upgrade TUI library", action=self.upgrade),
                             YButton("Run setup &wizard", action=self.wizard_again),
                             YButton("&Reset and quit", variant="error", action=self.reset), classes="row")
            yield Static(id="set-info", classes="hint")

        def after_mount(self):
            self.query_one("#set-info", Static).update(
                f"Settings: {self.app.home / 'config.json'}\nPython environment: {self.app.home / 'venv'}\n"
                f"Script: {os.path.abspath(__file__)}\nTextual {textual_version()}  -  Python {platform.python_version()}")

        def save(self):
            save_config(self.app.home, self.app.cfg)

        async def apply_theme(self):
            name = self.val("set-theme")
            self.app.theme = name
            self.app.cfg["theme"] = name
            self.save()
            self.say(f"Theme '{name}' applied and saved.", "green")

        async def save_glyphs(self):
            self.app.cfg["glyphs"] = self.val("set-glyphs")
            self.save()
            self.say("Symbol style saved - it takes effect the next time uYaST starts.", "green")

        @on(Checkbox.Changed, "#set-wt")
        def wt_changed(self, event):
            self.app.cfg["use_wt"] = event.value
            self.save()

        async def upgrade(self):
            vpy = venv_python(self.app.home)
            cmd = Cmd([str(vpy), "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", TEXTUAL_REQ],
                      user=not IS_WINDOWS)
            if await self.confirm("Upgrade the TUI library (Textual) now?\nRestart uYaST afterwards.", danger=False):
                await self.app.run_cmds([cmd], self.log_w)

        async def wizard_again(self):
            if await self.confirm("Quit uYaST so you can run the setup wizard (uyast.py --setup)?", danger=False):
                self.app.exit("setup")

        async def reset(self):
            if await self.confirm("Forget all uYaST settings and quit?\nThe start-up wizard runs next time."):
                try:
                    (self.app.home / "config.json").unlink()
                except OSError:
                    pass
                self.app.exit("reset")


if __name__ == "__main__":
    sys.exit(main())
