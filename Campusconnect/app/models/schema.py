"""SQLite schema DDL statements."""

USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

STUDENT_PROFILES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    branch TEXT NULL,
    year INTEGER NULL,
    cgpa REAL NULL,
    skills TEXT NOT NULL DEFAULT '[]',
    phone TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

OPPORTUNITIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    eligible_branches TEXT NOT NULL DEFAULT '[]',
    eligible_years TEXT NOT NULL DEFAULT '[]',
    min_cgpa REAL NULL,
    required_skills TEXT NOT NULL DEFAULT '[]',
    deadline TEXT NOT NULL,
    link TEXT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

APPLICATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'submitted' CHECK (
        status IN ('submitted', 'shortlisted', 'accepted', 'rejected', 'withdrawn')
    ),
    note TEXT NULL,
    admin_remarks TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(opportunity_id, user_id)
);
"""

BOOKMARKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    UNIQUE(opportunity_id, user_id)
);
"""

SCHEMA_STATEMENTS = [
    USERS_TABLE_SQL,
    STUDENT_PROFILES_TABLE_SQL,
    OPPORTUNITIES_TABLE_SQL,
    APPLICATIONS_TABLE_SQL,
    BOOKMARKS_TABLE_SQL,
]
