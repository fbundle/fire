from typing import Any


def make(*host_list: str) -> Any:
    config_list = []
    for host in host_list:
        config_list.append({
            "host": host,
        })
    return config_list




