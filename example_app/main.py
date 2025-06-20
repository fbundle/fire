import json
import os
import sys
import time

if __name__ == "__main__":
    config_path, i = sys.argv[1], int(sys.argv[2])
    config = json.loads(open(config_path).read())[i]
    print(config, os.environ["NAME"], os.environ["AGE"])
    for i in range(30):
        print(i)
        time.sleep(1)
