import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import types

PYTHON_BIN = "/Users/khanh/miniforge3/envs/test/bin/python"
TMUX_BIN = "/opt/homebrew/bin/tmux"



def get_make_config_func(file_path: str, make_func_name: str):
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

    module = load_module(file_path)
    make_func = getattr(module, make_func_name)
    return make_func

fire_script_template = """
rsync -avh --delete --progress tmp/{app_name}.json {host}:{deploy_dir}/
rsync -avh --delete --progress {app_name} {host}:{deploy_dir}/
ssh {host} << EOF
   cd {deploy_dir}/{app_name}
   {tmux_bin} has-session -t {tmux_session} 2> /dev/null && {tmux_bin} kill-session -t {tmux_session}
   {tmux_bin} new-session -s {tmux_session} -d "{env_command} {python_bin} main.py {deploy_dir}/{app_name}.json {i} |& tee {deploy_dir}/run.log"
EOF
"""

def make_fire_script(app_name: str, host_list: list[str], deploy_rootdir: str, env: dict[str, str] | None = None):
    script = "#!/usr/bin/env bash\nset -xe\n"
    for i, host in enumerate(host_list):
        deploy_dir = f"{deploy_rootdir}/deploy_{app_name}_{host}"
        tmux_session = f"deploy_{app_name}_{host}"
        env_command = " ".join(map(lambda kv: f"{kv[0]}={kv[1]}", env.items())) if env is not None else ""
        script += fire_script_template.format(
            app_name=app_name,
            host=host,
            deploy_dir=deploy_dir,
            tmux_bin=TMUX_BIN,
            tmux_session=tmux_session,
            python_bin=PYTHON_BIN,
            env_command=env_command,
            i=i,
        )
    return script

clean_script_template = """
ssh {host} << EOF
   {tmux_bin} has-session -t {tmux_session} 2> /dev/null && {tmux_bin} kill-session -t {tmux_session}
   rm -rf {deploy_dir}
EOF
"""

def make_clean_script(app_name: str, host_list: list[str], deploy_rootdir: str):
    script = "#!/usr/bin/env bash\nset -xe\n"
    for i, host in enumerate(host_list):
        deploy_dir = f"{deploy_rootdir}/deploy_{app_name}_{host}"
        tmux_session = f"deploy_{app_name}_{host}"
        script += clean_script_template.format(
            host=host,
            deploy_dir=deploy_dir,
            tmux_bin=TMUX_BIN,
            tmux_session=tmux_session,
        )

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
    parser.add_argument("--run", action="store_true", default=False)

    args = parser.parse_args()

    main(**args.__dict__)
    if args.run:
        subprocess.run(["./tmp/fire"], check=True)


