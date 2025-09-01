import json
import os
import sys

import fire

TMP_DIR = "tmp"

if __name__ == '__main__':
    os.makedirs(TMP_DIR, exist_ok=True)

    # config
    config = [{
        "name": "config_a"
    }, {
        "name": "config_b"
    }]
    config_path = f"{TMP_DIR}/config.json"
    open(config_path, "w").write(json.dumps(config, indent=2))

    # app
    app1 = fire.FireProcess(
        task_name="example_app",
        host_name="khanh@100.69.15.9",
        deploy_dir="/tmp",
        tmux_path="/opt/homebrew/bin/tmux",
    )
    app2 = fire.FireProcess(
        task_name="example_app",
        host_name="khanh@100.93.62.117",
        deploy_dir="/tmp",
        tmux_path="/usr/bin/tmux",
    )

    ## clean
    clean_script = ""
    clean_script += app1.clean().export()
    clean_script += app2.clean().export()
    open(f"{TMP_DIR}/clean", "w").write(clean_script)

    ## run
    app_path = "example_app/app.py"

    run_script = ""
    run_script += app1.push(src=app_path).push(src=config_path).exec(
        command=f"/Users/khanh/miniforge3/envs/test/bin/python app.py 0 config.json",
        env={"NAME": "khanh", "AGE": "20"},
    ).export()
    run_script += app2.push(src=app_path).push(src=config_path).exec(
        command=f"/home/khanh/miniforge3/envs/test/bin/python app.py 1 config.json",
        env={"NAME": "khanh", "AGE": "21"},
    ).export()
    open(f"{TMP_DIR}/run", "w").write(run_script)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        os.system(f"bash {TMP_DIR}/{command}")