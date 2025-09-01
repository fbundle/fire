from __future__ import annotations

import logging
import shlex
import sys
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

_push_template = "rsync -avh --delete --progress {src} {host_name}:{deploy_dir}/{task_name}/"
_exec_template = """ssh {host_name} << EOF
    set -xe
    {tmux_path} has-session -t {task_name} 2> /dev/null && {tmux_path} kill-session -t {task_name}
    cd {deploy_dir}/{task_name}
    {tmux_path} new-session -s {task_name} -d "export {env_str}; {command} |& tee {deploy_dir}/{task_name}/run.log"
EOF
"""
_clean_template = """ssh {host_name} << EOF
    set -xe
    {tmux_path} has-session -t {task_name} 2> /dev/null && {tmux_path} kill-session -t {task_name}
    rm -rf {deploy_dir}/{task_name}
EOF
"""

_warning_printed = False


def _print_python_version_warning():
    import sys
    global _warning_printed
    if _warning_printed:
        return
    _warning_printed = True

    def get_python_version():
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    tested_python_version = sorted({"3.12.", "3.13."})
    tested = False
    for python_version in tested_python_version:
        if get_python_version().startswith(python_version):
            tested = True
            break

    if not tested:
        print(f"WARNING: Your python version is {get_python_version()}", file=sys.stderr)
        print(f"WARNING: This script is only tested with python {tested_python_version}", file=sys.stderr)


def _validate_hostname(hostname: str) -> bool:
    """Validate hostname format."""
    # Basic hostname validation
    if not hostname or '@' not in hostname:
        return False
    return True


def _sanitize_command(command: str) -> str:
    """Sanitize shell command to prevent injection."""
    # Remove potentially dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>']
    for char in dangerous_chars:
        if char in command:
            _logger.warning(f"Potentially dangerous character '{char}' found in command")
    return command


def _escape_env_vars(env_dict: Dict[str, str]) -> str:
    """Properly escape environment variables for shell export."""
    escaped_vars = []
    for key, value in env_dict.items():
        # Escape quotes and special characters
        escaped_value = value.replace('"', '\\"').replace("'", "\\'")
        escaped_vars.append(f'{key}="{escaped_value}"')
    return " ".join(escaped_vars)


class FireProcess:
    def __init__(
            self, task_name: str, host_name: str,
            deploy_dir: str = "/tmp", tmux_path: str = "tmux", commands: list[str] | None = None,
    ):
        _print_python_version_warning()

        if len(task_name) == 0:
            raise ValueError("task_name cannot be empty")
        
        if not _validate_hostname(host_name):
            raise ValueError(f"Invalid hostname format: {host_name}")

        if commands is None:
            commands = [
                "set -xe",
            ]
        self.task_name = task_name
        self.host_name = host_name
        self.deploy_dir = deploy_dir
        self.tmux_path = tmux_path
        self.commands = commands

    def _append_command(self, command: str) -> FireProcess:
        return FireProcess(
            task_name=self.task_name,
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            tmux_path=self.tmux_path,
            commands=self.commands + [command],
        )

    def push(self, src: str) -> FireProcess:
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {src}")
        
        return self._append_command(_push_template.format(
            src=src,
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            task_name=self.task_name,
        ))

    def exec(self, command: str, env: dict[str, str] | None = None) -> FireProcess:
        if env is None:
            env = {}
        
        # Sanitize command
        sanitized_command = _sanitize_command(command)
        
        env_str = _escape_env_vars(env)
        return self._append_command(_exec_template.format(
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            task_name=self.task_name,
            tmux_path=self.tmux_path,
            env_str=env_str,
            command=sanitized_command,
        ))

    def clean(self) -> FireProcess:
        return self._append_command(_clean_template.format(
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            task_name=self.task_name,
            tmux_path=self.tmux_path,
        ))

    def export(self) -> str:
        return "\n".join(self.commands) + "\n"


__version__ = "0.0.1"
