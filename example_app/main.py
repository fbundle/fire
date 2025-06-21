import json
import os
import sys
import time

if __name__ == "__main__":
    config_path, i = sys.argv[1], int(sys.argv[2])
    config = json.loads(open(config_path).read())[i]
    print(config, os.environ["NAME"], os.environ["AGE"], file=sys.stdout, flush=True)
    sys.stdout.flush()
    for i in range(30):
        print(i, file=sys.stdout, flush=True)
        sys.stdout.flush()
        time.sleep(1)
