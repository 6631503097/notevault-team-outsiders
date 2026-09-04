"""NoteVault: a persistent, owner-scoped Flask application with a React client."""
import csv
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
import time
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, make_response, request, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parents[1]


def create_app(test_config=None):
    team = json.loads((ROOT / "team.json").read_text())
    app = Flask(__name__, static_folder=None)
    app.config.update(
        DATABASE=os.environ.get("DATABASE", str(ROOT / "instance" / "notevault.db")),
        TEAM_ID=os.environ.get("TEAM_ID", team["id"]),
        TEAM=team,
        COOKIE_NAME="nv_" + team["slug"].replace("-", "_"),
        COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        DEMO_MODE=os.environ.get("DEMO_MODE", "false").lower() == "true",
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_SECONDS=8 * 60 * 60,
        TRUSTED_HOSTS=["localhost", "127.0.0.1", "[::1]"] +
        [h for h in os.environ.get("TRUSTED_HOSTS", "").split(",") if h],
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys=ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        con = g.pop("db", None)
        if con is not None:
            con.close()

    def marker():
        salt = os.environ.get("TEAM_SALT", "notevault-anti-copy-dev-salt")
        return hmac.new(salt.encode(), app.config["TEAM_ID"].encode(), hashlib.sha256).hexdigest()[:12]

    def audit(action, target=None):
        db().execute("INSERT INTO audit (user_id,action,target,created_at) VALUES (?,?,?,?)",
                     (g.user["id"] if getattr(g, "user", None) else None, action, target, int(time.time())))

    def payload():
        if not request.is_json:
            from werkzeug.exceptions import UnsupportedMediaType
            raise UnsupportedMediaType("Use application/json.")
        data = request.get_json()
        if not isinstance(data, dict):
            from werkzeug.exceptions import BadRequest
            raise BadRequest("Expected a JSON object.")
        return data

    def fail(message, status=400):
        return jsonify(error=message), status

    def auth(admin=False):
        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if g.user is None:
                    return fail("Please sign in.", 401)
                if admin and g.user["role"] != "admin":
                    return fail("Administrator access required.", 403)
                return fn(*args, **kwargs)
            return wrapped
        return decorator

    def user_json(row):
        return {k: row[k] for k in ("id", "username", "role")}

    def new_session(user_id):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        old = request.cookies.get(app.config["COOKIE_NAME"], "")
        db().execute("DELETE FROM sessions WHERE token_hash=? OR expires_at<?",
                     (hashlib.sha256(old.encode()).hexdigest(), int(time.time())))
        db().execute("INSERT INTO sessions VALUES (?,?,?,?)",
                     (hashlib.sha256(token.encode()).hexdigest(), user_id, csrf,
                      int(time.time()) + app.config["SESSION_SECONDS"]))
        return token, csrf

    def cookie(resp, token):
        resp.set_cookie(app.config["COOKIE_NAME"], token, httponly=True,
                        secure=app.config["COOKIE_SECURE"], samesite="Strict", path="/",
                        max_age=app.config["SESSION_SECONDS"])
        return resp

    with app.app_context():
        db().executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','admin')),
          created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS notes (
          id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
          title TEXT NOT NULL, body TEXT NOT NULL, collection TEXT NOT NULL,
          pinned INTEGER NOT NULL DEFAULT 0, archived INTEGER NOT NULL DEFAULT 0,
          deleted INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 1,
          created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS notes_owner ON notes(owner_id,updated_at);
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
          csrf TEXT NOT NULL, expires_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
          target INTEGER, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts (bucket TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS attempts_bucket ON attempts(bucket,created_at);
        """)
        existing = db().execute("SELECT value FROM metadata WHERE key='team'").fetchone()
        if existing and existing["value"] != app.config["TEAM_ID"]:
            raise RuntimeError("Database belongs to a different TEAM_ID; choose a separate DATABASE.")
        db().execute("INSERT OR IGNORE INTO metadata VALUES ('team',?)", (app.config["TEAM_ID"],))
        db().execute("INSERT OR IGNORE INTO metadata VALUES ('marker',?)", (marker(),))
        if app.config["DEMO_MODE"] and not db().execute("SELECT 1 FROM users LIMIT 1").fetchone():
            now = int(time.time())
            for name, password, role in [("alice", "alicepw", "user"), ("admin", "admin123", "admin")]:
                db().execute("INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,?,?)",
                             (name, generate_password_hash(password), role, now))
            alice = db().execute("SELECT id FROM users WHERE username='alice'").fetchone()[0]
            admin_id = db().execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
            for note in team["seed_notes"]:
                db().execute("INSERT INTO notes (owner_id,title,body,collection,pinned,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                             (alice, note["title"], note["body"], note["collection"], note["pinned"], now, now))
            db().execute("INSERT INTO notes (owner_id,title,body,collection,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                         (admin_id, "build-tag", f"team={app.config['TEAM_ID']} marker={marker()}", team["collections"][0], now, now))
        db().commit()

    @app.before_request
    def guard():
        g.user, g.session = None, None
        token = request.cookies.get(app.config["COOKIE_NAME"], "")
        if token:
            row = db().execute("SELECT * FROM sessions WHERE token_hash=? AND expires_at>?",
                               (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
            if row:
                g.session = row
                g.user = db().execute("SELECT * FROM users WHERE id=?", (row["user_id"],)).fetchone()
        if request.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
            # Custom JSON header forces cross-origin browser requests to preflight; no CORS granted.
            if request.headers.get("X-NoteVault-Client") != "web":
                return fail("Missing request protection header.", 403)
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                return fail("Cross-origin request rejected.", 403)
            if g.session and not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), g.session["csrf"]):
                return fail("Session protection expired. Refresh and try again.", 403)

    @app.after_request
    def headers(resp):
        resp.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if app.config["COOKIE_SECURE"]:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(HTTPException)
    def http_error(err):
        return fail(err.description, err.code)

    @app.get("/api/health")
    def health():
        db().execute("SELECT 1")
        return jsonify(status="ok")

    @app.get("/api/config")
    def config():
        return jsonify(team=app.config["TEAM_ID"], slug=team["slug"], theme=team["theme"],
                       edition=team["edition"], welcome=team["welcome"], collections=team["collections"],
                       demo=app.config["DEMO_MODE"], marker=db().execute("SELECT value FROM metadata WHERE key='marker'").fetchone()[0])

    @app.get("/api/session")
    def session_info():
        return jsonify(user=user_json(g.user) if g.user else None,
                       csrf=g.session["csrf"] if g.session else None)

    def rate_limit():
        now = int(time.time())
        bucket = hashlib.sha256((request.remote_addr or "unknown").encode()).hexdigest()
        db().execute("BEGIN IMMEDIATE")
        db().execute("DELETE FROM attempts WHERE created_at<?", (now - 900,))
        count = db().execute("SELECT count(*) FROM attempts WHERE bucket=?", (bucket,)).fetchone()[0]
        if count >= 20:
            db().commit()
            return True
        db().execute("INSERT INTO attempts VALUES (?,?)", (bucket, now))
        db().commit()
        return False

    @app.post("/api/register")
    def register():
        data = payload()
        if rate_limit():
            return fail("Too many attempts. Try again in 15 minutes.", 429)
        name, password = data.get("username"), data.get("password")
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{3,32}", name):
            return fail("Use 3–32 letters, numbers, underscores or hyphens for your username.")
        if not isinstance(password, str) or not 12 <= len(password) <= 128:
            return fail("Choose a password with 12–128 characters.")
        try:
            cur = db().execute("INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,'user',?)",
                               (name, generate_password_hash(password), int(time.time())))
        except sqlite3.IntegrityError:
            return fail("That username is unavailable.", 409)
        token, csrf = new_session(cur.lastrowid)
        g.user = db().execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        audit("account.created")
        db().commit()
        return cookie(make_response(jsonify(user=user_json(g.user), csrf=csrf), 201), token)

    # Match the same KDF cost for unknown accounts to reduce username timing disclosure.
    dummy_hash = generate_password_hash(secrets.token_urlsafe(32))

    @app.post("/api/login")
    def login():
        data = payload()
        if rate_limit():
            return fail("Too many attempts. Try again in 15 minutes.", 429)
        name, password = data.get("username", ""), data.get("password", "")
        if not isinstance(name, str) or not isinstance(password, str) or len(name) > 128 or len(password) > 128:
            return fail("Invalid username or password.", 401)
        row = db().execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
        valid = check_password_hash(row["password_hash"] if row else dummy_hash, password)
        if not row or not valid:
            audit("session.failed")
            db().commit()
            return fail("Invalid username or password.", 401)
        g.user = row
        token, csrf = new_session(row["id"])
        audit("session.created")
        db().commit()
        return cookie(jsonify(user=user_json(row), csrf=csrf), token)

    @app.post("/api/logout")
    @auth()
    def logout():
        db().execute("DELETE FROM sessions WHERE token_hash=?", (g.session["token_hash"],))
        audit("session.revoked")
        db().commit()
        resp = jsonify(ok=True)
        resp.delete_cookie(app.config["COOKIE_NAME"], path="/", secure=app.config["COOKIE_SECURE"], httponly=True, samesite="Strict")
        return resp

    @app.get("/api/notes")
    @auth()
    def list_notes():
        term = request.args.get("q", "")
        if len(term) > 200:
            return fail("Search is limited to 200 characters.")
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        rows = db().execute("SELECT * FROM notes WHERE owner_id=? AND (title LIKE ? ESCAPE '\\' OR body LIKE ? ESCAPE '\\') ORDER BY pinned DESC,updated_at DESC,id DESC LIMIT 1001",
                            (g.user["id"], f"%{escaped}%", f"%{escaped}%")).fetchall()
        return jsonify(notes=[dict(r) for r in rows])

    def validate_note(data):
        for key, limit in [("title", 160), ("body", 20000), ("collection", 60)]:
            if not isinstance(data.get(key), str) or len(data[key]) > limit:
                return f"{key.capitalize()} must be text with at most {limit} characters."
        if not data["title"].strip():
            return "Give your note a title."
        if data["collection"] not in team["collections"]:
            return "Choose an available collection."
        for key in ("pinned", "archived", "deleted"):
            if key in data and not isinstance(data[key], bool):
                return f"{key} must be true or false."
        return None

    @app.post("/api/notes")
    @auth()
    def add_note():
        data = payload()
        error = validate_note(data)
        if error:
            return fail(error)
        db().execute("BEGIN IMMEDIATE")
        if db().execute("SELECT count(*) FROM notes WHERE owner_id=?", (g.user["id"],)).fetchone()[0] >= 1000:
            db().rollback()
            return fail("This workspace has reached its 1,000-note limit.", 409)
        now = int(time.time())
        cur = db().execute("INSERT INTO notes (owner_id,title,body,collection,pinned,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                           (g.user["id"], data["title"].strip(), data["body"], data["collection"], data.get("pinned", False), now, now))
        audit("note.created", cur.lastrowid)
        db().commit()
        return jsonify(note=dict(db().execute("SELECT * FROM notes WHERE id=?", (cur.lastrowid,)).fetchone())), 201

    @app.route("/api/notes/<int:nid>", methods=["GET", "PUT"])
    @auth()
    def note(nid):
        row = db().execute("SELECT * FROM notes WHERE id=? AND owner_id=?", (nid, g.user["id"])).fetchone()
        if not row:
            return fail("Note not found.", 404)
        if request.method == "GET":
            return jsonify(note=dict(row))
        data = payload()
        error = validate_note(data)
        if error:
            return fail(error)
        if type(data.get("version")) is not int:
            return fail("A note version is required.")
        cur = db().execute("UPDATE notes SET title=?,body=?,collection=?,pinned=?,archived=?,deleted=?,updated_at=?,version=version+1 WHERE id=? AND owner_id=? AND version=?",
                           (data["title"].strip(), data["body"], data["collection"], data.get("pinned", bool(row["pinned"])),
                            data.get("archived", bool(row["archived"])), data.get("deleted", bool(row["deleted"])),
                            int(time.time()), nid, g.user["id"], data["version"]))
        if cur.rowcount == 0:
            return fail("This note changed in another window. Reload it before saving.", 409)
        audit("note.updated", nid)
        db().commit()
        return jsonify(note=dict(db().execute("SELECT * FROM notes WHERE id=? AND owner_id=?", (nid, g.user["id"])).fetchone()))

    @app.get("/api/export")
    @auth()
    def export():
        fmt = request.args.get("fmt", "json")
        if fmt not in ("json", "csv", "txt"):
            return fail("Choose JSON, CSV or text.")
        rows = [dict(r) for r in db().execute("SELECT title,body,collection,created_at,updated_at FROM notes WHERE owner_id=? AND deleted=0 ORDER BY id", (g.user["id"],))]
        if fmt == "json":
            content = json.dumps({"team": app.config["TEAM_ID"], "notes": rows}, indent=2)
        elif fmt == "txt":
            content = "\n\n".join(r["title"] + "\n" + r["body"] for r in rows)
        else:
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(["title", "body", "collection", "created_at", "updated_at"])
            for row in rows:
                writer.writerow([("'" + str(v)) if str(v).lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else v for v in row.values()])
            content = out.getvalue()
        audit("notes.exported")
        db().commit()
        resp = make_response(content)
        resp.headers["Content-Type"] = {"json":"application/json", "txt":"text/plain", "csv":"text/csv"}[fmt] + "; charset=utf-8"
        resp.headers["Content-Disposition"] = f'attachment; filename="{team["slug"]}-notes.{fmt}"'
        return resp

    @app.get("/api/admin/users")
    @auth(admin=True)
    def users():
        rows = db().execute("SELECT u.id,u.username,u.role,u.created_at,count(n.id) AS note_count FROM users u LEFT JOIN notes n ON n.owner_id=u.id GROUP BY u.id ORDER BY u.id LIMIT 500")
        return jsonify(users=[dict(r) for r in rows])

    @app.get("/api/activity")
    @auth()
    def activity():
        rows = db().execute("SELECT id,action,target,created_at FROM audit WHERE user_id=? ORDER BY id DESC LIMIT 100", (g.user["id"],))
        return jsonify(events=[dict(r) for r in rows])

    @app.get("/api/team")
    @auth()
    def team_members():
        return jsonify(members=team["members"])

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path="index.html"):
        if path.startswith("api/"):
            return fail("Endpoint not found.", 404)
        return send_from_directory(ROOT / "frontend" / "dist", path)

    return app
