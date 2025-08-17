
from __future__ import annotations

import os

copy_template = "rsync -avh --delete --progress {src} {host_name}:{deploy_dir}/{task_name}/"
exec_template = """ssh {host_name} << EOF
    set -xe
    {tmux_path} has-session -t {task_name} 2> /dev/null && {tmux_path} kill-session -t {task_name}
    cd {deploy_dir}/{task_name}
    {tmux_path} new-session -s {task_name} -d "export {env_str}; {command} |& tee {deploy_dir}/{task_name}/run.log"
EOF
"""
clean_template = """ssh {host_name} << EOF
    set -xe
    {tmux_path} has-session -t {task_name} 2> /dev/null && {tmux_path} kill-session -t {task_name}
    rm -rf {deploy_dir}/{task_name}
EOF
"""

class Process:
    def __init__(self, task_name: str, host_name: str, deploy_dir: str = "/tmp", tmux_path: str = "tmux", commands: list[str] | None = None):
        if commands is None:
            commands = []
        self.task_name = task_name
        self.host_name = host_name
        self.deploy_dir = deploy_dir
        self.tmux_path = tmux_path
        self.commands = commands

    def append_command(self, command: str) -> Process:
        return Process(
            task_name=self.task_name,
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            tmux_path=self.tmux_path,
            commands=self.commands + [command],
        )

    def copy(self, src: str) -> Process:
        return self.append_command(copy_template.format(
            src=src,
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            task_name=self.task_name,
        ))

    def exec(self, command: str, env: dict[str, str] = None) -> Process:
        if env is None:
            env = {}
        env_str = " ".join([f"{k}={v}" for k, v in env.items()])
        return self.append_command(exec_template.format(
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            task_name=self.task_name,
            tmux_path=self.tmux_path,
            env_str=env_str,
            command=command,
        ))

    def clean(self) -> Process:
        return self.append_command(clean_template.format(
            host_name=self.host_name,
            deploy_dir=self.deploy_dir,
            task_name=self.task_name,
            tmux_path=self.tmux_path,
        ))

    def export(self) -> str:
        return "\n".join(self.commands) + "\n"


class Writer:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.f = open(path, "w")
    def __del__(self):
        self.f.close()

    def write(self, data: str) -> Writer:
        self.f.write(data)
        return self

    def write_process(self, process: Process) -> Writer:
        self.f.write(process.export())
        return self

script_template = """#!/usr/bin/env bash
set -xe
"""

SCRIPT_DIR = "tmp"

if __name__ == "__main__":
    app1 = Process(
        task_name="app_100_69_15_9",
        host_name="khanh@100.69.15.9",
        deploy_dir="/tmp",
        tmux_path="/opt/homebrew/bin/tmux",
    )
    app2 = Process(
        task_name="app_100_93_62_117",
        host_name="khanh@100.93.62.117",
        deploy_dir="/tmp",
        tmux_path="/usr/bin/tmux",
    )
    config =  [
    {
      "name": "config_a"
    },
    {
      "name": "config_b"
    }
  ]

    # config
    import json
    Writer(f"{SCRIPT_DIR}/config.json").write(json.dumps(config))

    # clean
    Writer(f"{SCRIPT_DIR}/clean").write(script_template).write_process(
        app1.clean(),
    ).write_process(
        app2.clean(),
    )

    # run
    Writer(f"{SCRIPT_DIR}/run").write(script_template).write_process(app1.copy(
        src="app/app.py",
    ).copy(
        src=f"{SCRIPT_DIR}/config.json",
    ).exec(
        command="/Users/khanh/miniforge3/envs/test/bin/python app.py 0 config.json",
        env={"NAME": "khanh", "AGE": "20"},
    )).write_process(app2.copy(
        src="app/app.py",
    ).copy(
        src=f"{SCRIPT_DIR}/config.json",
    ).exec(
        command="/home/khanh/miniforge3/envs/test/bin/python app.py 0 config.json",
        env={"NAME": "khanh", "AGE": "20"},
    ))

