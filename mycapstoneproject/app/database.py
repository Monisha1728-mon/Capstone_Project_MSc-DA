import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB = Path(__file__).resolve().parent / "at_abandonment.db"


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn, table, column, definition):
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_conn()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, password_hash TEXT NOT NULL, role TEXT DEFAULT 'user', verified INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, year INTEGER, age TEXT, scenario TEXT, setting TEXT, sex TEXT, device_needed TEXT, disability_type TEXT, device_source TEXT, assessed INTEGER, appropriate_fit INTEGER, user_trained INTEGER, locally_manufactured INTEGER, maintenance_available INTEGER, device_broken INTEGER, cost_affordable INTEGER, insurance_covered INTEGER, financial_barrier INTEGER, availability_barrier INTEGER, distance_barrier INTEGER, functional_improvement INTEGER, independence_improved INTEGER, participation_improved INTEGER, satisfaction INTEGER, unmet_need INTEGER, risk TEXT, risk_score REAL, status TEXT DEFAULT 'new', is_bookmarked INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, email TEXT, subject TEXT, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_read INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS auth_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, purpose TEXT NOT NULL, target TEXT, code TEXT NOT NULL, expires_at TIMESTAMP NOT NULL, used INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    for column, definition in {
        "user_id": "INTEGER",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "year": "INTEGER",
        "age": "TEXT",
        "scenario": "TEXT",
        "setting": "TEXT",
        "sex": "TEXT",
        "device_needed": "TEXT",
        "disability_type": "TEXT",
        "device_source": "TEXT",
        "assessed": "INTEGER",
        "appropriate_fit": "INTEGER",
        "user_trained": "INTEGER",
        "locally_manufactured": "INTEGER",
        "maintenance_available": "INTEGER",
        "device_broken": "INTEGER",
        "cost_affordable": "INTEGER",
        "insurance_covered": "INTEGER",
        "financial_barrier": "INTEGER",
        "availability_barrier": "INTEGER",
        "distance_barrier": "INTEGER",
        "functional_improvement": "INTEGER",
        "independence_improved": "INTEGER",
        "participation_improved": "INTEGER",
        "satisfaction": "INTEGER",
        "unmet_need": "INTEGER",
        "risk": "TEXT",
        "risk_score": "REAL",
        "status": "TEXT DEFAULT 'new'",
        "is_bookmarked": "INTEGER DEFAULT 0",
        "explanation": "TEXT",
        "action_plan": "TEXT",
        "user_message": "TEXT",
        "reviewed_at": "TIMESTAMP",
    }.items():
        _ensure_column(conn, "predictions", column, definition)
    _ensure_column(conn, "messages", "is_read", "INTEGER DEFAULT 0")
    _ensure_column(conn, "users", "verified", "INTEGER DEFAULT 1")
    conn.commit()
    conn.close()


def create_user(name, email, password, phone="", role="user"):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (name,email,phone,password_hash,role,verified) VALUES (?,?,?,?,?,0)",
            (name, email.lower(), phone, generate_password_hash(password), role),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user_by_email(email):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE lower(email)=lower(?)", (email.strip(),)
    ).fetchone()
    conn.close()
    return row


def get_user_by_login(value):
    conn = get_conn()
    value = value.strip()
    row = conn.execute(
        "SELECT * FROM users WHERE lower(email)=lower(?) OR lower(name)=lower(?)",
        (value, value),
    ).fetchone()
    conn.close()
    return row


def get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def update_user(user_id, name, email, phone):
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE users SET name=?, email=?, phone=? WHERE id=?",
            (name, email.lower(), phone, user_id),
        )
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok


def update_password(user_id, password):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        (generate_password_hash(password), user_id),
    )
    conn.commit()
    conn.close()


def verify_password(user, password):
    return bool(user) and check_password_hash(user["password_hash"], password)


def set_verified(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET verified=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def save_auth_code(user_id, purpose, target, code, expires_at):
    conn = get_conn()
    conn.execute(
        "UPDATE auth_codes SET used=1 WHERE user_id=? AND purpose=? AND used=0",
        (user_id, purpose),
    )
    conn.execute(
        "INSERT INTO auth_codes (user_id,purpose,target,code,expires_at) VALUES (?,?,?,?,?)",
        (user_id, purpose, target, code, expires_at),
    )
    conn.commit()
    conn.close()


def verify_auth_code(user_id, purpose, code):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM auth_codes WHERE user_id=? AND purpose=? AND code=? AND used=0 AND expires_at>CURRENT_TIMESTAMP ORDER BY id DESC LIMIT 1",
        (user_id, purpose, code.strip()),
    ).fetchone()
    if row:
        conn.execute("UPDATE auth_codes SET used=1 WHERE id=?", (row["id"],))
        conn.commit()
    conn.close()
    return bool(row)


PREDICTION_FIELDS = [
    "user_id",
    "year",
    "age",
    "scenario",
    "setting",
    "sex",
    "device_needed",
    "disability_type",
    "device_source",
    "assessed",
    "appropriate_fit",
    "user_trained",
    "locally_manufactured",
    "maintenance_available",
    "device_broken",
    "cost_affordable",
    "insurance_covered",
    "financial_barrier",
    "availability_barrier",
    "distance_barrier",
    "functional_improvement",
    "independence_improved",
    "participation_improved",
    "satisfaction",
    "unmet_need",
    "risk",
    "risk_score",
    "status",
]


def save_submission(data):
    conn = get_conn()
    values = [data.get(field) for field in PREDICTION_FIELDS]
    cur = conn.execute(
        f"INSERT INTO predictions ({','.join(PREDICTION_FIELDS)}) VALUES ({','.join(['?']*len(PREDICTION_FIELDS))})",
        values,
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def save_prediction(data):
    data = dict(data)
    data.setdefault("status", "predicted")
    return save_submission(data)


def update_prediction_result(
    prediction_id, risk, risk_score, explanation="", action_plan="", user_message=""
):
    conn = get_conn()
    conn.execute(
        "UPDATE predictions SET risk=?,risk_score=?,status='predicted',explanation=?,action_plan=?,user_message=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
        (risk, risk_score, explanation, action_plan, user_message, prediction_id),
    )
    conn.commit()
    conn.close()


def get_user_predictions(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM predictions WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_prediction(prediction_id, user_id=None):
    conn = get_conn()
    row = conn.execute(
        "SELECT predictions.*,users.name username,users.email FROM predictions LEFT JOIN users ON users.id=predictions.user_id WHERE predictions.id=?"
        + (" AND predictions.user_id=?" if user_id is not None else ""),
        (prediction_id, user_id) if user_id is not None else (prediction_id,),
    ).fetchone()
    conn.close()
    return row


def get_all_predictions():
    conn = get_conn()
    rows = conn.execute(
        "SELECT predictions.*,users.name username,users.email FROM predictions LEFT JOIN users ON predictions.user_id=users.id ORDER BY predictions.created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def update_prediction_state(prediction_id, status=None, is_bookmarked=None):
    conn = get_conn()
    updates = []
    values = []
    if status is not None:
        updates.append("status=?")
        values.append(status)
    if is_bookmarked is not None:
        updates.append("is_bookmarked=?")
        values.append(is_bookmarked)
    if updates:
        values.append(prediction_id)
        conn.execute(f"UPDATE predictions SET {','.join(updates)} WHERE id=?", values)
        conn.commit()
    conn.close()


def get_stats():
    conn = get_conn()
    result = {
        "total": conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0],
        "pending": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE status='submitted'"
        ).fetchone()[0],
        "reviewed": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE status='predicted'"
        ).fetchone()[0],
        "not_applicable": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE status='not_applicable'"
        ).fetchone()[0],
        "high": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE risk='High'"
        ).fetchone()[0],
        "medium": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE risk='Medium'"
        ).fetchone()[0],
        "low": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE risk='Low'"
        ).fetchone()[0],
        "users": conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='user'"
        ).fetchone()[0],
        "today": conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE DATE(created_at)=DATE('now')"
        ).fetchone()[0],
    }
    conn.close()
    return result


def save_message(user_id, name, email, subject, message):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (user_id,name,email,subject,message) VALUES (?,?,?,?,?)",
        (user_id, name, email, subject, message),
    )
    conn.commit()
    conn.close()


def get_messages(unread_only=False):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE is_read=0 ORDER BY created_at DESC"
        if unread_only
        else "SELECT * FROM messages ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def mark_messages_read():
    conn = get_conn()
    conn.execute("UPDATE messages SET is_read=1 WHERE is_read=0")
    conn.commit()
    conn.close()
