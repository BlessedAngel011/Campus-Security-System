import sqlite3
import os

from werkzeug.security import generate_password_hash


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "campus_security.db"
)


# =========================================================
# CONNECT TO DATABASE
# =========================================================

conn = sqlite3.connect(
    DATABASE_PATH
)

cursor = conn.cursor()


# =========================================================
# CREATE USERS TABLE
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        full_name TEXT,

        student_number TEXT,

        email TEXT,

        email_verified INTEGER
            NOT NULL DEFAULT 0,

        password TEXT NOT NULL,

        role TEXT NOT NULL,

        disabled INTEGER NOT NULL DEFAULT 0

    )
""")


# =========================================================
# MIGRATE EXISTING USERS TABLE
# =========================================================

cursor.execute(
    "PRAGMA table_info(users)"
)

user_columns = [
    column[1]
    for column in cursor.fetchall()
]


if "full_name" not in user_columns:

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN full_name TEXT
    """)

    print(
        "Added full_name column to users table."
    )


if "student_number" not in user_columns:

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN student_number TEXT
    """)

    print(
        "Added student_number column to users table."
    )


if "email" not in user_columns:

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN email TEXT
    """)

    print(
        "Added email column to users table."
    )


# Existing accounts are trusted during this one-time migration.
# This UPDATE runs only when the column is first added.
if "email_verified" not in user_columns:

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN email_verified INTEGER
        NOT NULL DEFAULT 0
    """)

    cursor.execute("""
        UPDATE users
        SET email_verified = 1
    """)

    print(
        "Added email_verified column to users table."
    )

    print(
        "Marked existing accounts as verified."
    )


if "disabled" not in user_columns:

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN disabled INTEGER
        NOT NULL DEFAULT 0
    """)

    print(
        "Added disabled column to users table."
    )


# =========================================================
# UNIQUE STUDENT NUMBER
# =========================================================

cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    idx_users_student_number

    ON users(student_number)

    WHERE student_number IS NOT NULL
""")


# =========================================================
# UNIQUE EMAIL ADDRESS
# =========================================================

cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    idx_users_email

    ON users(email COLLATE NOCASE)

    WHERE email IS NOT NULL
""")


# =========================================================
# EMAIL VERIFICATION CODES
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS
    email_verification_codes (

        user_id INTEGER PRIMARY KEY,

        code_hash TEXT NOT NULL,

        expires_at INTEGER NOT NULL,

        last_sent_at INTEGER NOT NULL,

        FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

    )
""")


# =========================================================
# PASSWORD RESET CODES
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS
    password_reset_codes (

        user_id INTEGER PRIMARY KEY,

        code_hash TEXT NOT NULL,

        expires_at INTEGER NOT NULL,

        last_sent_at INTEGER NOT NULL,

        FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

    )
""")


# =========================================================
# EMAIL CHANGE CODES
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS
    email_change_codes (

        user_id INTEGER PRIMARY KEY,

        new_email TEXT NOT NULL,

        code_hash TEXT NOT NULL,

        expires_at INTEGER NOT NULL,

        last_sent_at INTEGER NOT NULL,

        FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

    )
""")


# =========================================================
# CREATE INCIDENTS TABLE
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        full_name TEXT NOT NULL,

        student_number TEXT NOT NULL,

        incident_type TEXT NOT NULL,

        location TEXT NOT NULL,

        description TEXT NOT NULL,

        priority TEXT NOT NULL DEFAULT 'Low',

        status TEXT NOT NULL DEFAULT 'Pending',

        is_anonymous INTEGER NOT NULL DEFAULT 0,

        date_reported TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id)
            REFERENCES users(id)

    )
""")


# =========================================================
# MIGRATE EXISTING INCIDENTS TABLE
# =========================================================

cursor.execute(
    "PRAGMA table_info(incidents)"
)

incident_columns = [
    column[1]
    for column in cursor.fetchall()
]


if "user_id" not in incident_columns:

    cursor.execute("""
        ALTER TABLE incidents
        ADD COLUMN user_id INTEGER
    """)

    print(
        "Added user_id column to incidents table."
    )


if "priority" not in incident_columns:

    cursor.execute("""
        ALTER TABLE incidents
        ADD COLUMN priority TEXT
        NOT NULL DEFAULT 'Low'
    """)

    print(
        "Added priority column to incidents table."
    )


if "is_anonymous" not in incident_columns:

    cursor.execute("""
        ALTER TABLE incidents
        ADD COLUMN is_anonymous INTEGER
        NOT NULL DEFAULT 0
    """)

    print(
        "Added is_anonymous column to incidents table."
    )



# =========================================================
# COMPLETE PROFILE + EMERGENCY/GIS/NOTIFICATION SCHEMA
# =========================================================

# Profile v2 fields. full_name/student_number are retained for backward compatibility.
cursor.execute("PRAGMA table_info(users)")
user_columns = [column[1] for column in cursor.fetchall()]
for column_name, definition in [
    ("first_name", "TEXT"),
    ("last_name", "TEXT"),
    ("student_staff_number", "TEXT"),
    ("phone_number", "TEXT"),
]:
    if column_name not in user_columns:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {definition}")
        print(f"Added {column_name} column to users table.")

# Backfill profile v2 from existing accounts without destroying old data.
cursor.execute("""
    UPDATE users
    SET student_staff_number = COALESCE(student_staff_number, student_number)
    WHERE student_staff_number IS NULL OR student_staff_number = ''
""")
cursor.execute("SELECT id, full_name, first_name, last_name FROM users")
for uid, full_name, first_name, last_name in cursor.fetchall():
    if full_name and not first_name:
        parts = full_name.strip().split()
        first = parts[0] if parts else ''
        last = ' '.join(parts[1:]) if len(parts) > 1 else ''
        cursor.execute("UPDATE users SET first_name=?, last_name=? WHERE id=?", (first, last, uid))

cursor.execute("""
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    incident_id INTEGER,
    location_text TEXT,
    latitude REAL,
    longitude REAL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    assigned_officer_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP,
    responding_at TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(incident_id) REFERENCES incidents(id),
    FOREIGN KEY(assigned_officer_id) REFERENCES security_officers(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS security_officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    availability TEXT NOT NULL DEFAULT 'OFF_DUTY',
    latitude REAL,
    longitude REAL,
    location_updated_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
""")

# Create officer records for existing Security Officer accounts.
cursor.execute("""
    INSERT OR IGNORE INTO security_officers(user_id, availability)
    SELECT id, 'OFF_DUTY' FROM users WHERE role='Security Officer'
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS incident_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'GENERAL',
    related_id INTEGER,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS campus_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    latitude REAL,
    longitude REAL,
    description TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# GPS columns for ordinary incidents as well.
cursor.execute("PRAGMA table_info(incidents)")
incident_columns = [column[1] for column in cursor.fetchall()]
for column_name, definition in [("latitude", "REAL"), ("longitude", "REAL")]:
    if column_name not in incident_columns:
        cursor.execute(f"ALTER TABLE incidents ADD COLUMN {column_name} {definition}")
        print(f"Added {column_name} column to incidents table.")

# Helpful indexes.
cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_emergency_status ON emergency_alerts(status)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)")

# =========================================================
# DEFAULT DEVELOPMENT ACCOUNTS
# =========================================================

default_users = [

    (
        "security",
        "admin123",
        "Security Officer"
    ),

    (
        "admin",
        "admin456",
        "Admin"
    ),

    (
        "student",
        "student123",
        "Student"
    )

]


for username, password, role in default_users:

    cursor.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, (
        username,
    ))

    existing_user = (
        cursor.fetchone()
    )


    if existing_user is None:

        hashed_password = (
            generate_password_hash(
                password
            )
        )


        cursor.execute("""
            INSERT INTO users
            (
                username,
                password,
                role,
                disabled,
                email_verified
            )
            VALUES (?, ?, ?, 0, 1)
        """, (
            username,
            hashed_password,
            role
        ))


        print(
            f"Created account: {username}"
        )


# =========================================================
# SAVE DATABASE
# =========================================================

conn.commit()

conn.close()


print(
    "Database setup complete."
)
