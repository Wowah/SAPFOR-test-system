import argparse
import os
import subprocess
import sqlite3
import sys
from pprint import pprint

import exceptions

def exec(cmd):
    proc = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, err) = proc.communicate()
    if err:
        print(f"Error stream not empty: {err.decode('utf-8')}")
    if proc.returncode != 0:
        raise exceptions.ExecError(proc.returncode)
    return output.decode("utf-8")

def read_config(path):
    result = {}
    try:
        with open(path, "r") as f:
            for line in f:
                l = line.strip().split("=",1)
                if len(l) < 2:
                    continue
                result[l[0].strip()] = l[1].strip()
    except Exception as e:
        print(f"Something went wrong while reading config: {e}")
    return result
