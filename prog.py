import argparse
import os
import sqlite3
import subprocess
import sys
from pprint import pprint

import run_test as r
import utils

prog_name = sys.argv[0]

def initdb(conn):
    with open("init.sql") as file:
        content = file.read()

    cursor = conn.cursor()

    try:
        cursor.executescript(content)
    except Exception as e:
        print("Error while executing init SQL script. Error: {}".format(e))


def get_current_active_test_runs(conn):
    cursor = conn.cursor()

    return list(map(lambda x: x[0], cursor.execute("SELECT ID FROM testing_info WHERE end is NULL").fetchall()))

def add_new_test(cursor, path):
    path = os.path.abspath(path)
    config = utils.read_config(path + "/config.txt")
    test_name = config.get("TESTNAME", get_file_name(path))
    test_suite_name = config.get("SUITENAME", "")
    
    args = (test_name, path)
    cursor.execute("INSERT OR REPLACE INTO tests_info(name, path) VALUES (?, ?)", args)

    print("Test {} was successfully inserted in 'tests_info' table".format(test_name))

    test_id = cursor.lastrowid
    
    if test_suite_name != "":
        print("Need add test {} in test suite {}".format(test_name, test_suite_name))

        x = cursor.execute("SELECT ID FROM test_suites_info WHERE name=?", (test_suite_name,)).fetchone()

        if x is None:
            print("Need add test suite {} in database".format(test_suite_name))
            cursor.execute("INSERT OR REPLACE INTO test_suites_info(name, type) VALUES (?, 1)", (test_suite_name,))
            print("New test suite was successfully inserted in 'test_suites_info' table")
            test_suite_id = cursor.lastrowid
        else:
            test_suite_id = x[0]

        cursor.execute("INSERT OR REPLACE INTO test_suites_rel(test_id, test_suite_id) VALUES (?, ?)", (test_id, test_suite_id))
        print("Test {} was successfully added in test suite {}".format(test_name, test_suite_name))



def get_file_name(path):
    return path.split("/")[-1]

def add_tests(conn, dir_path):
    print("Starting adding new tests from directory")
    dirs = [dir_path + "/" + f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f))]
    print("Target directory:", dir_path)
    try:
        cursor = conn.cursor()
        for d in dirs:
            print("\n------test {} inserting start------\n".format(d))
            try:
                add_new_test(cursor, d)
            except Exception as e:
                print("Error while inserting test {}. Error: {}".format(d, e))
            print("\n------test {} inserting finish------\n".format(d))
            

        conn.commit()

    except Exception as e:
        print("Something went wrong. Error: {}".format(e))
    else:
        print("All tests was successfully added in testing system")

def get_all_tests(conn):
    cursor = conn.cursor()

    result = []
    try:
        result = list(cursor.execute("SELECT ID, name, path FROM tests_info").fetchall())
    except Exception as e:
        print(f"Something went wrong. Error: {e}")
    return result

def get_suite_tests(conn, suite):
    cursor = conn.cursor()

    result = []
    try:
        result = list(cursor.execute("SELECT t.ID, t.name, t.path FROM tests_info as t JOIN test_suites_rel as r ON r.test_id JOIN test_suites_info as s ON r.test_suite_id=s.id WHERE s.name=?", (suite,)).fetchall())
    except Exception as e:
        print(f"Something went wrong. Error: {e}")
    return result

def run(conn, dirp, suite, config_path):
    print("Start new testing\n\n")

    config = utils.read_config(config_path)
    testing_name=config.get("TESTINGNAME", None)
    sys_info = config.get("SYSINFO", "")
    sap_version = config.get("SAPVERSION", "")

    dirp = os.path.abspath(dirp)

    if sys_info == "":
        sys_info = utils.exec("uname -a").strip()
    
    if sap_version == "":
        sap_version = utils.exec("Sapfor_F -ver").strip()
    
    print(f"Testing name: {testing_name}")
    print(f"System info: {sys_info}")
    print(f"Sapfor version: {sap_version}")
    print(f"Testing directory: {dirp}")
    print(f"Testing suite: {suite}")

    print(f"Getting test IDs")

    try:
        os.mkdir(dirp)
    except OSError as err:
        print ("Creation of the directory %s failed. Error: %s" % (dirp, err))
        return
    else:
        print ("Successfully created the directory %s " % dirp)
    
    tests = []
    if suite == "all":
        tests = get_all_tests(conn)
    else:
        tests = get_suite_tests(conn, suite)

    if len(tests) < 1:
        print("Error! Tests not found!")
        return

    pprint(tests)

    print(f"Start inserting testing info and relations with tests")

    cursor = conn.cursor()

    cursor.execute("INSERT INTO testing_info(name, sys_info, sap_version, root_path) VALUES (?, ?, ?, ?)", (testing_name, sys_info, sap_version, dirp))

    testingID = cursor.lastrowid

    for i, test in enumerate(tests):
        cursor.execute("INSERT INTO testing_queue(testing_id, test_id, test_dir, status) VALUES (?, ?, ?, ?)", (testingID, test[0], dirp + "/" + test[1], 0))
        tests[i] = test + (cursor.lastrowid,)
    pprint(tests)

    conn.commit()
    print(f"Inserting testing info and records in testing queue successfully finished")

    for test in tests:
        r.run_test(conn, test[3], test[1], dirp + "/" + test[1], test[2])

def list_cmd():
    cursor = conn.cursor()

    result = list(cursor.execute("SELECT ID, name, sap_version, start, end FROM testing_info").fetchall())
    print("List of current testings:")
    print("ID     Name             SAPFOR version         Start time             End time             ")
    for row in result:
        print("{:<7}{:<17}{:<23}{:<23}{:<23}".format(row[0], str(row[1]), row[2], row[3], str(row[4])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="CMD", dest="cmd", help="Available commands for testing system. For more information execute \"{} CMD --help\"".format(prog_name))

    parser_a = subparsers.add_parser('add', help='command for adding new tests into database.')

    parser_a.add_argument("-d", "--dir", dest="d", action="store", help="directory with tests. Default: tests", default="tests")

    parser_b = subparsers.add_parser('run', help='command for running tests.')

    parser_b.add_argument("-s", "--suite", dest="s", action="store", help="Specify test suite. Default: run all tests in system", default="all")

    parser_b.add_argument("-d", "--dir", dest="run_dir", action="store", help="Directory for testing. Default: new_testing", default="new_testing")

    parser_b.add_argument("-c", "--config", dest="c", action="store", help="Testing config file. Default: testing.conf", default="testing.conf")

    parser_c = subparsers.add_parser('list', help='command for getting list of testings.')

    args = parser.parse_args()

    cmd = args.cmd
    if cmd is None:
        print("Error! Command not found. Try: {} --help for more information".format(prog_name))
        os._exit(1)

    conn = sqlite3.connect("tests.db")
    try:
        initdb(conn)
    except Exception as e:
        print("Something wrong while init db. Error: {}".format(e))

    try:
        if cmd == "add":
            dirp = args.d
            add_tests(conn, dirp)
        elif cmd == "run":
            dirp = args.run_dir
            suite = args.s 
            config = args.c 
            run(conn, dirp, suite, config)
        elif cmd == "list":
            list_cmd()

    except Exception as e:
        print("\n\n\n-------------------------------------------------\n\n")
        print(f"Something went wrong while executing command '{cmd}'. Error: {e}")
    conn.close()    
