PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tests_info (
    ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS test_suites_info (
    ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS test_suites_rel (
    test_id INTEGER NOT NULL,
    test_suite_id INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests_info(ID) ON DELETE CASCADE,
    FOREIGN KEY (test_suite_id) REFERENCES test_suites_info(ID) ON DELETE CASCADE,
    PRIMARY KEY (test_id, test_suite_id)
);

CREATE TABLE IF NOT EXISTS status_description (
    status INTEGER NOT NULL PRIMARY KEY,
    description TEXT NOT NULL
);

INSERT INTO status_description(status, description) VALUES
(0, "Running"),
(1, "Success"),
(-1, "Internal error"),
(-2, "Generation error"),
(-3, "Compilation error"),
(2, "Test with errors") ON CONFLICT(status) DO NOTHING;

CREATE TABLE IF NOT EXISTS testing_info (
    ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NULL,
    sys_info TEXT NOT NULL,
    sap_version TEXT NOT NULL,
    root_path TEXT NOT NULL,
    start TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end TIMESTAMP WITH TIME ZONE NULL
);

CREATE TABLE IF NOT EXISTS testing_queue (
    ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    testing_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    test_dir TEXT NOT NULL,
    start TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end TIMESTAMP WITH TIME ZONE NULL,
    status INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES tests_info(ID) ON DELETE CASCADE,
    FOREIGN KEY (testing_id) REFERENCES testing_info(ID) ON DELETE CASCADE,
    FOREIGN KEY (status) REFERENCES status_description(status)
);

CREATE TABLE IF NOT EXISTS subtests_info (
    ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    queue_id INTEGER NOT NULL,
    var_num INTEGER NOT NULL,
    name TEXT NOT NULL,
    pragma_count INTEGER NOT NULL,
    FOREIGN KEY (queue_id) REFERENCES testing_queue(ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subtest_configs (
    ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    cpu_num INTEGER NOT NULL,
    threads_num INTEGER NOT NULL,
    gpu_num INTEGER NOT NULL,
    cpu_grid TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subtests_queue (
    subtest_id INTEGER NOT NULL,
    config_id INTEGER NOT NULL,
    start TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end TIMESTAMP WITH TIME ZONE NULL,
    status INTEGER NOT NULL,
    exec_time REAL NOT NULL,
    FOREIGN KEY (subtest_id) REFERENCES subtests_info(ID) ON DELETE CASCADE,
    FOREIGN KEY (config_id) REFERENCES subtest_configs(ID) ON DELETE CASCADE,
    FOREIGN KEY (status) REFERENCES status_description(status)
);