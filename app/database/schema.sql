PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edge_identity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    site_id TEXT NOT NULL,
    edge_id TEXT NOT NULL,
    hostname TEXT,
    app_version TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS court (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS camera (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    court_uuid TEXT,
    name TEXT,
    ip_address TEXT,
    rtsp_url TEXT,
    vendor TEXT,
    model TEXT,
    firmware TEXT,
    serial_number TEXT,
    status TEXT DEFAULT 'NEW',
    last_seen DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recording (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_uuid TEXT,
    court_uuid TEXT,
    filename TEXT,
    start_time DATETIME,
    end_time DATETIME,
    duration INTEGER,
    file_size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu REAL,
    ram REAL,
    disk REAL,
    temperature REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    level TEXT,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version(version,description)
VALUES (1,'AI Director Database v1');

INSERT OR IGNORE INTO schema_version(version,description)
VALUES (2,'Tambah domain court dan relasi camera ke court');

CREATE TABLE IF NOT EXISTS camera_calibration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL UNIQUE,
    top_left_x INTEGER NOT NULL,
    top_left_y INTEGER NOT NULL,
    top_right_x INTEGER NOT NULL,
    top_right_y INTEGER NOT NULL,
    bottom_right_x INTEGER NOT NULL,
    bottom_right_y INTEGER NOT NULL,
    bottom_left_x INTEGER NOT NULL,
    bottom_left_y INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version(version,description)
VALUES (3,'Tambah camera court calibration');
