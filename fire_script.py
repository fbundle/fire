import os
import sys
import json
import uuid

import fire

TMP_DIR = "tmp_deploy"

header = """#!/usr/bin/env bash
set -xe
"""

if __name__ == '__main__':
    os.makedirs(TMP_DIR, exist_ok=True)

    # config
    config = [{
        "name": "config_a"
    }, {
        "name": "config_b"
    }]
    config_name = "config.json"
    config_path = f"{TMP_DIR}/{config_name}"
    open(config_path, "w").write(json.dumps(config, indent=2))

    # app
    app1 = fire.Process(
        task_name="example_app" + "_" + uuid.uuid4().hex,
        host_name="khanh@100.69.15.9",
        deploy_dir="/tmp",
        tmux_path="/opt/homebrew/bin/tmux",
    )
    app2 = fire.Process(
        task_name="example_app" + "_" + uuid.uuid4().hex,
        host_name="khanh@100.93.62.117",
        deploy_dir="/tmp",
        tmux_path="/usr/bin/tmux",
    )

    ## clean
    clean_script = ""
    clean_script += app1.clean().export()
    clean_script += app2.clean().export()
    open(f"{TMP_DIR}/clean", "w").write(header + clean_script)

    ## run
    app_name = "app.py"
    app_path = f"example_app/{app_name}"

    run_script = ""
    run_script += app1.push(src=app_path).push(src=config_path).exec(
        command=f"/Users/khanh/miniforge3/envs/test/bin/python {app_name} 0 {config_name}",
        env={"NAME": "khanh", "AGE": "20"},
    ).export()
    run_script += app2.push(src=app_path).push(src=config_path).exec(
        command=f"/home/khanh/miniforge3/envs/test/bin/python {app_name} 1 {config_name}",
        env={"NAME": "khanh", "AGE": "21"},
    ).export()
    open(f"{TMP_DIR}/run", "w").write(header + run_script)
