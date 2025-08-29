import json
import os
import sys
import time

if __name__ == "__main__":
    i, config_path = int(sys.argv[1]), sys.argv[2]
    config = json.loads(open(config_path).read())[i]
    print(i, config, os.environ["NAME"], os.environ["AGE"], file=sys.stdout, flush=True)
    for i in range(30):
        print(i, file=sys.stdout, flush=True)
        time.sleep(1)
