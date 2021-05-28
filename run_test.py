import argparse
import os
import subprocess
import sqlite3
import sys
from pprint import pprint
import glob
import shutil

import utils
import exceptions
import run_subtest as sub


def write_test_status(conn, queue_id, status_code):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE testing_queue SET status=?, end=CURRENT_TIMESTAMP WHERE ID=?", (status_code, queue_id))
        conn.commit()
    except Exception as e:
        print(f"Something went wrong while updating test status. Error: {e}")
        raise e

def run_parser(name, test_path):
    print(f"Try parse source file for test {name}")
    # TODO: Fix issue with multiple files in src
    try:
        utils.exec(f"Parser {os.listdir(test_path)[0]}/src")
    except Exception as e:
        print(f"Can't parse {os.listdir(test_path)[0]}. Error: {e}")
        raise exceptions.ParserError
    src = os.listdir(test_path)[0]
    if src.endswith(".f"):
        return src[:-2]
    return src[:-4] # .for

def get_pragma_count(file):
    f = open(file, "r")
    result = 0
    for line in f:
        if line.startswith("!DVM$"):
            result += 1
    return result

def get_all_parallel_progs(src_name, test_path):

    files = os.listdir(test_path)
    result = []
    for file in files:
        if file.startswith(src_name) and file.endswith(".for"):
            name = file[:-4]
            num = file[len(src_name)+3:-4]
            var_num = int(num)
            pragma_count = get_pragma_count(file)
            result.append((var_num, name, pragma_count))
    return result

def generate_parallel_programs(src_name, name, test_path):
    print(f"Try generate parallel programs for test {name}")
    cur_dir = os.curdir
    try:
        os.chdir(test_path+"/src")
        utils.exec("Sapfor_F -t 13 -allVars")
        return get_all_parallel_progs(src_name, test_path)
    except Exception as e:
        print(f"Can't parse {os.listdir(test_path)[0]}. Error: {e}")
        raise exceptions.GenerationError
    finally:
        os.chdir(cur_dir)

def int_run_test(conn, queue_id, name, test_path, src_path):
    shutil.copytree(src_path, test_path)
    src_name = run_parser(name, test_path)
    subtests = generate_parallel_programs(src_name, name, test_path)

    print(f"Start inserting subtests info")

    cursor = conn.cursor()

    for subtest in subtests:
        cursor.execute("INSERT INTO subtests_info(queue_id, var_num, name, pragma_count) VALUES (?, ?, ?, ?)", (queue_id, ) + subtest)
    
    print("\nInserting subtests successfully finished. Start testing generated parallel programs\n")
    for subtest in subtests:
        sub.run_subtest()

def run_test(conn, queue_id, name, test_path, src_path):
    print(f"\n\n--------- Test {name} begin ---------\n\n")

    try:
        int_run_test(conn, queue_id, name, test_path, src_path)
    except exceptions.ErrorStatus as st:
        print("\n\n\n-------------------------------------------------\n\n")
        print(f"Test {name} failed. {st}")
        write_test_status(conn, queue_id, st.status)
        
    except Exception as e:
        print("\n\n\n-------------------------------------------------\n\n")
        print(f"Something went wrong in test {name}. Error: {e}")
        print(f"Set status -1 for test {name}")
        write_test_status(conn, queue_id, -1)
        
    else:
        print("\n\n\n-------------------------------------------------\n\n")
        print(f"Test {name} successfully finished")
        write_test_status(conn, queue_id, 1)
        

    print(f"\n\n--------- Test {name} end ---------\n\n")
