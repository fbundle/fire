import argparse
import importlib.util
import json
import os
import shutil
import sys
import types

PYTHON_BIN = "/Users/khanh/miniforge3/envs/test/bin/python"
TMUX_BIN = "/opt/homebrew/bin/tmux"


def load_module(file_path: str) -> types.ModuleType:
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        print(f"Cannot create a module spec for {file_path}", file=sys.stderr)
        sys.exit(1)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "main"):
        module.main()
    return module

def get_make_config_func(file_path: str, make_func_name: str):
    module = load_module(file_path)
    make_func = getattr(module, make_func_name)
    return make_func

def make_fire_script(app_name: str, host_list: list[str], deploy_rootdir: str, env: dict[str, str] | None = None):
    script = ""
    script += "#!/usr/bin/env bash\n"
    script += "set -xe\n"
    # copy
    for host in host_list:
        deploy_dir = f"{deploy_rootdir}/deploy_{app_name}_{host}"
        script += f"rsync -avh --delete --progress tmp/{app_name}.json {host}:{deploy_dir}/ &\n"
        script += f"rsync -avh --delete --progress {app_name} {host}:{deploy_dir}/ &\n"
    script += "wait\n"

    # exec
    env_command = ""
    if env is not None:
        env_command = ";".join(map(lambda kv: f"export {kv[0]}={kv[1]}", env.items()))
    for i, host in enumerate(host_list):
        deploy_dir = f"{deploy_rootdir}/deploy_{app_name}_{host}"
        tmux_session = app_name
        node_script = f"""
            cd {deploy_dir}/{app_name}
            {TMUX_BIN} has-session -t {tmux_session} 2>/dev/null && {TMUX_BIN} kill-session -t {tmux_session}
            {TMUX_BIN} new-session -s {tmux_session} -d "{env_command};{PYTHON_BIN} main.py {deploy_dir}/{app_name}.json {i} |& tee {deploy_dir}/run.log"
        """
        script += f"ssh {host} << EOF\n{node_script}\nEOF\n"

    return script

def make_clean_script(app_name: str, host_list: list[str], deploy_rootdir: str):
    script = ""
    script += "#!/usr/bin/env bash\n"
    script += "set -xe\n"
    # exec
    for i, host in enumerate(host_list):
        deploy_dir = f"{deploy_rootdir}/deploy_{app_name}_{host}"
        tmux_session = app_name
        node_script = f"""
            {TMUX_BIN} has-session -t {tmux_session} 2>/dev/null && {TMUX_BIN} kill-session -t {tmux_session}
            rm -rf {deploy_dir} 
        """
        script += f"ssh {host} << EOF\n{node_script}\nEOF\n"

    return script


def main(app_name: str, host_list_str: str, deploy_rootdir: str, env_str: str, **kwargs):
    host_list = host_list_str.split(",")
    env = {}
    for pair_str in env_str.split(","):
        k, v = pair_str.split("=", maxsplit=1)
        env[k] = v


    if os.path.exists("tmp"):
        shutil.rmtree("tmp")
    os.makedirs("tmp")

    with open(f"tmp/{app_name}.json", "w") as f:
        make = get_make_config_func(
            file_path=f"{app_name}/make_config.py",
            make_func_name="make",
        )
        config = make(*host_list)
        f.write(json.dumps(config))

    with open("tmp/fire", "w") as f:
        script = make_fire_script(
            app_name=app_name,
            host_list=host_list,
            deploy_rootdir=deploy_rootdir,
            env=env,
        )
        f.write(script)
    os.chmod("tmp/fire", 0o700)

    with open("tmp/clean", "w") as f:
        script = make_clean_script(
            app_name=app_name,
            host_list=host_list,
            deploy_rootdir=deploy_rootdir,
        )
        f.write(script)
    os.chmod("tmp/clean", 0o700)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app_name", type=str, default="example_app")
    parser.add_argument("--host_list_str", type=str, default="localhost,127.0.0.1")
    parser.add_argument("--deploy_rootdir", type=str, default="/tmp")
    parser.add_argument("--env_str", type=str, default="NAME=khanh,AGE=28")

    args = parser.parse_args()


    main(**args.__dict__)
