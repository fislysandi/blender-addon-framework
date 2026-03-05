import os
import sys
import subprocess
import shutil
import platform
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, List, Optional


class DependencyManager:
    @staticmethod
    def get_proxy_env():
        """Return process env with system proxy values normalized."""
        env = os.environ.copy()
        proxies = urllib.request.getproxies()

        proxy_key_map = {
            "http": "HTTP_PROXY",
            "https": "HTTPS_PROXY",
            "ftp": "FTP_PROXY",
            "no": "NO_PROXY",
        }

        for proxy_key, env_key in proxy_key_map.items():
            value = (
                proxies.get(proxy_key) or env.get(env_key) or env.get(env_key.lower())
            )
            if value:
                env[env_key] = value
                env[env_key.lower()] = value

        return env

    @staticmethod
    def run_install_command(cmd, check=False, capture_output=False, text=False):
        """Run install command with inherited system proxy settings."""
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            env=DependencyManager.get_proxy_env(),
        )

    @staticmethod
    def get_uv_path():
        """
        Find uv executable.
        Checks:
        1. PATH (fastest)
        2. Typical installation locations
        """
        # Check PATH first
        uv_in_path = shutil.which("uv")
        if uv_in_path:
            return uv_in_path

        # Locations to check
        candidates = []

        # Relative to current python executable
        python_dir = Path(sys.executable).parent
        home = Path.home()

        if platform.system() == "Windows":
            # Windows locations
            candidates.append(python_dir / "uv.exe")
            candidates.append(python_dir / "Scripts" / "uv.exe")

            # User AppData
            appdata = os.environ.get("APPDATA")
            if appdata:
                candidates.append(Path(appdata) / "Python" / "Scripts" / "uv.exe")
        else:
            # Linux/Mac locations
            candidates.append(python_dir / "uv")
            candidates.append(python_dir / "bin" / "uv")
            candidates.append(home / ".local" / "bin" / "uv")

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        return None

    @staticmethod
    def ensure_uv():
        """
        Ensure uv is installed.
        Returns path to uv executable or None if failed.
        """
        uv_path = DependencyManager.get_uv_path()
        if uv_path:
            return uv_path

        try:
            # Install uv using standard pip
            DependencyManager.run_install_command(
                [sys.executable, "-m", "pip", "install", "uv"],
                check=True,
                capture_output=False,
            )
            return DependencyManager.get_uv_path()
        except subprocess.CalledProcessError:
            try:
                # Fallback to --user
                DependencyManager.run_install_command(
                    [sys.executable, "-m", "pip", "install", "--user", "uv"],
                    check=True,
                    capture_output=False,
                )
                return DependencyManager.get_uv_path()
            except subprocess.CalledProcessError:
                return None

    @staticmethod
    def get_install_command(packages, constraint=None, extra_args=None, use_uv=True):
        """
        Get command to install packages using uv (preferred) or pip (fallback).
        Returns list of strings [executable, args...]
        """
        result = resolve_install_command(
            packages,
            constraint=constraint,
            extra_args=extra_args,
            use_uv=use_uv,
        )
        return result.command


@dataclass(frozen=True)
class InstallStep:
    """Single dependency installation command step."""

    name: str
    command: List[str]


@dataclass(frozen=True)
class InstallCommandResult:
    """Resolved installer command and metadata."""

    command: List[str]
    installer: str
    message: str


@dataclass(frozen=True)
class InstallPlan:
    """Immutable install plan for dependency execution."""

    steps: List[InstallStep]


def resolve_install_command(
    packages: List[str],
    *,
    constraint: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    use_uv: bool = True,
) -> InstallCommandResult:
    """Resolve installer command with structured metadata."""
    uv_path = DependencyManager.ensure_uv() if use_uv else None

    if uv_path:
        command = [uv_path, "pip", "install", "--python", sys.executable]
        installer = "uv"
        message = f"Using uv installer: {uv_path}"
    else:
        command = [sys.executable, "-m", "pip", "install"]
        installer = "pip"
        message = (
            "UV disabled by settings; using pip"
            if not use_uv
            else "uv unavailable; using pip fallback"
        )

    if constraint:
        command.append(constraint)

    command.extend(packages)

    if extra_args:
        command.extend(extra_args)

    return InstallCommandResult(command=command, installer=installer, message=message)


def build_install_step(
    name: str,
    packages: List[str],
    *,
    use_uv: bool,
    constraint: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
) -> InstallStep:
    """Build an immutable install step from package inputs."""
    command_result = resolve_install_command(
        packages,
        constraint=constraint,
        extra_args=extra_args,
        use_uv=use_uv,
    )
    return InstallStep(name=name, command=command_result.command)


def build_install_plan(steps: List[InstallStep]) -> InstallPlan:
    """Build immutable install plan from ordered steps."""
    return InstallPlan(steps=list(steps))


def execute_install_plan(
    plan: InstallPlan,
    *,
    on_step_start: Optional[Callable[[int, int, InstallStep], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> subprocess.CompletedProcess | None:
    """Execute an install plan sequentially, respecting cancellation callback."""
    total_steps = len(plan.steps)
    for index, step in enumerate(plan.steps, start=1):
        if is_cancelled and is_cancelled():
            return None

        if on_step_start:
            on_step_start(index, total_steps, step)

        result = DependencyManager.run_install_command(
            step.command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return result

    return subprocess.CompletedProcess(args=[], returncode=0)
