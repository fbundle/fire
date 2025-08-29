import os
import sys

import fire

TMP_DIR = "tmp"

script_header = """#!/usr/bin/env bash
set -xe
"""

if __name__ == '__main__':
    os.makedirs(TMP_DIR, exist_ok=True)
    app1 = fire.Process(
        task_name="app_100_69_15_9",
        host_name="khanh@100.69.15.9",
        deploy_dir="/tmp",
        tmux_path="/opt/homebrew/bin/tmux",
    )
    app2 = fire.Process(
        task_name="app_100_93_62_117",
        host_name="khanh@100.93.62.117",
        deploy_dir="/tmp",
        tmux_path="/usr/bin/tmux",
    )

    # config
    import json

    open(f"{TMP_DIR}/config.json", "w").write(json.dumps([
        {
            "name": "config_a"
        },
        {
            "name": "config_b"
        },
    ]))

    # clean
    clean = script_header
    clean += app1.clean().export()
    clean += app2.clean().export()
    open(f"{TMP_DIR}/clean", "w").write(clean)

    # run
    run = script_header
    run += app1.push(src="app/app.py").push(src=f"{TMP_DIR}/config.json").exec(
        command="/Users/khanh/miniforge3/envs/test/bin/python app.py 0 config.json",
        env={"NAME": "khanh", "AGE": "20"},
    ).export()
    run += app2.push(src="app/app.py").push(src=f"{TMP_DIR}/config.json").exec(
        command="/home/khanh/miniforge3/envs/test/bin/python app.py 1 config.json",
        env={"NAME": "khanh", "AGE": "21"},
    ).export()
    open(f"{TMP_DIR}/run", "w").write(run)

    if len(sys.argv) > 1:
        name = sys.argv[1]
        os.system(f"{TMP_DIR}/{name}")

