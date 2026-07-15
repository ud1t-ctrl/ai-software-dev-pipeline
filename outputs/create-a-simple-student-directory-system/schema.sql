CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    enrollment_id TEXT UNIQUE NOT NULL,
    major TEXT,
    sub_group TEXT,
    email_address TEXT UNIQUE NOT NULL
);