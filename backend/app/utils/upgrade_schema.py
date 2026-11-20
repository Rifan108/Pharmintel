import sqlite3
import os

def upgrade_schema_for_db(db_path):
    if not os.path.exists(db_path):
        return
    print(f"--- Upgrading schema for {db_path} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cols_to_add = [
        ('route_of_administration', "VARCHAR(100) DEFAULT 'Oral'"),
        ('atc_code', 'VARCHAR(50)'),
        ('is_combination', 'BOOLEAN DEFAULT 0'),
        ('active_substances_json', 'TEXT'),
        ('aliases_json', 'TEXT'),
        ('completeness_score', 'FLOAT DEFAULT 1.0'),
        ('verification_status', "VARCHAR(50) DEFAULT 'VERIFIED_REGULATORY'"),
        ('external_reference_id', 'VARCHAR(100)')
    ]

    existing_cols = [c[1] for c in cursor.execute('PRAGMA table_info(medicines)').fetchall()]
    for col_name, col_type in cols_to_add:
        if col_name not in existing_cols:
            cursor.execute(f'ALTER TABLE medicines ADD COLUMN {col_name} {col_type}')
            print(f'Added column {col_name} to medicines')

    # Create unidentified_medicine_logs table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS unidentified_medicine_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_input_name VARCHAR(255) NOT NULL,
        normalized_input VARCHAR(255),
        candidate_matches_json TEXT,
        diagnostic_status VARCHAR(100) NOT NULL,
        requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        resolved_status VARCHAR(50) DEFAULT 'PENDING',
        resolved_medicine_id INTEGER,
        patient_session_id VARCHAR(100)
    );
    ''')

    # Create medicine_audit_logs table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medicine_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        action VARCHAR(50) NOT NULL,
        changed_by_user_id INTEGER,
        changes_json TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        reason TEXT
    );
    ''')

    conn.commit()
    conn.close()
    print(f"Schema upgrade for {db_path} completed successfully.")

if __name__ == '__main__':
    for db_p in ['pharmintel.db', 'backend/pharmintel.db']:
        upgrade_schema_for_db(db_p)
