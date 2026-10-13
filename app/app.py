from __future__ import annotations

import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template_string, request, url_for

APP_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DATABASE_PATH", APP_DIR / "data" / "events.db"))
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "classroom-demo-change-me")

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>EventPass | Live events</title><style>
:root{color-scheme:light;--ink:#17233c;--muted:#66738b;--blue:#275efe;--paper:#f4f7fc}*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,sans-serif;color:var(--ink);background:var(--paper)}header{background:#101b35;color:white;padding:22px max(24px,calc((100vw - 1050px)/2));display:flex;justify-content:space-between;align-items:center}header a{color:#cbd7ff;text-decoration:none;margin-left:18px}.brand{font-weight:800;font-size:1.25rem}.hero{padding:58px 24px 40px;background:linear-gradient(120deg,#14264d,#2455c8);color:white}.hero>div,main{max-width:1050px;margin:auto}.hero p{color:#d7e3ff;margin-bottom:0}.hero h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.08;margin:0}.wrap{max-width:1050px;margin:32px auto;padding:0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:18px}.card{background:white;border:1px solid #e1e8f3;border-radius:16px;padding:22px;box-shadow:0 8px 24px #18274c0a}.tag{color:var(--blue);font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}.card h2{margin:8px 0}.muted{color:var(--muted)}.row{display:flex;justify-content:space-between;margin:18px 0}.btn{border:0;border-radius:9px;background:var(--blue);color:white;padding:11px 16px;font-weight:700;cursor:pointer}.btn:disabled{background:#a9b5ca}.notice{background:#e8f2ff;color:#1b448b;border-radius:10px;padding:12px 16px;margin-bottom:18px}.empty{text-align:center;padding:42px;color:var(--muted)}footer{text-align:center;color:var(--muted);padding:28px}
</style></head><body><header><a class="brand" href="/">✦ EventPass</a><nav><a href="/">Events</a><a href="/admin">Organizer view</a><a href="/health">Health</a></nav></header><section class="hero"><div><h1>Make a night<br>worth remembering.</h1><p>Discover local events and save your place in seconds.</p></div></section><main class="wrap">{% with messages=get_flashed_messages() %}{% if messages %}<div class="notice">{{ messages[0] }}</div>{% endif %}{% endwith %}<h2>Upcoming events</h2><div class="grid">{% for e in events %}<article class="card"><div class="tag">{{ e['category'] }}</div><h2>{{ e['name'] }}</h2><div class="muted">{{ e['venue'] }} · {{ e['event_date'] }}</div><p>{{ e['description'] }}</p><div class="row"><strong>${{ '%.2f'|format(e['price_cents']/100) }}</strong><span>{{ e['tickets_left'] }} tickets left</span></div><form method="post" action="/book/{{ e['id'] }}"><button class="btn" {% if e['tickets_left'] == 0 %}disabled{% endif %}>Reserve a ticket</button></form></article>{% else %}<div class="empty">No events yet. Add one from the organizer view.</div>{% endfor %}</div></main><footer>EventPass · A classroom deployment project · No real payments are collected</footer></body></html>"""

ADMIN = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Organizer | EventPass</title><style>body{font:16px system-ui;background:#f4f7fc;color:#17233c;margin:0}.wrap{max-width:950px;margin:36px auto;padding:0 22px}a{color:#275efe}.box{background:white;padding:22px;border-radius:14px;margin:18px 0}input,textarea{width:100%;padding:10px;margin:5px 0 12px;border:1px solid #ccd5e3;border-radius:7px}button{background:#275efe;color:white;padding:10px 15px;border:0;border-radius:7px;font-weight:bold}li{padding:6px}</style></head><body><main class="wrap"><a href="/">← Back to events</a><h1>Organizer view</h1><p>Demo admin page. Keep this classroom app on trusted networks.</p>{% with messages=get_flashed_messages() %}{% if messages %}<p>{{ messages[0] }}</p>{% endif %}{% endwith %}<section class="box"><h2>Add an event</h2><form method="post" action="/admin/events"><label>Event name</label><input name="name" required><label>Category</label><input name="category" value="Live music" required><label>Venue</label><input name="venue" required><label>Date</label><input name="event_date" type="date" required><label>Ticket price (USD)</label><input name="price" type="number" min="0" step="0.01" value="25" required><label>Ticket quantity</label><input name="quantity" type="number" min="1" value="100" required><label>Description</label><textarea name="description" rows="3"></textarea><button>Add event</button></form></section><section class="box"><h2>Recent bookings</h2>{% if bookings %}<ul>{% for b in bookings %}<li>{{ b['event_name'] }} — {{ b['confirmation_code'] }} — {{ b['booked_at'] }}</li>{% endfor %}</ul>{% else %}<p>No bookings yet. Make one from the events page.</p>{% endif %}</section></main></body></html>"""


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
              venue TEXT NOT NULL, event_date TEXT NOT NULL, description TEXT NOT NULL,
              price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
              tickets_left INTEGER NOT NULL CHECK(tickets_left >= 0)
            );
            CREATE TABLE IF NOT EXISTS bookings (
              id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES events(id),
              confirmation_code TEXT NOT NULL UNIQUE, booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        if db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
            db.executemany("INSERT INTO events(name,category,venue,event_date,description,price_cents,tickets_left) VALUES(?,?,?,?,?,?,?)", [
                ("Neon City Sessions", "Live music", "The Foundry, Austin", "2026-11-14", "An intimate night of indie, electronic, and local sounds.", 3200, 120),
                ("Taste of the Coast", "Food festival", "Harbor Park, San Diego", "2026-11-21", "Local chefs, small-batch makers, and sunset views.", 1800, 240),
                ("Build Something Better", "Technology", "Studio Hall, Seattle", "2026-12-03", "A one-day gathering for people who make useful things.", 4900, 85),
            ])


@app.get("/")
def home():
    with connect() as db:
        events = db.execute("SELECT * FROM events ORDER BY event_date").fetchall()
    return render_template_string(PAGE, events=events)


@app.post("/book/<int:event_id>")
def book(event_id: int):
    code = "EP-" + secrets.token_hex(3).upper()
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        changed = db.execute("UPDATE events SET tickets_left=tickets_left-1 WHERE id=? AND tickets_left>0", (event_id,)).rowcount
        if not changed:
            abort(404)
        db.execute("INSERT INTO bookings(event_id,confirmation_code) VALUES(?,?)", (event_id, code))
    flash(f"Your ticket is reserved! Confirmation: {code}. This demo does not collect payment.")
    return redirect(url_for("home"))


@app.get("/admin")
def admin():
    with connect() as db:
        bookings = db.execute("SELECT b.confirmation_code,b.booked_at,e.name AS event_name FROM bookings b JOIN events e ON e.id=b.event_id ORDER BY b.id DESC LIMIT 20").fetchall()
    return render_template_string(ADMIN, bookings=bookings)


@app.post("/admin/events")
def add_event():
    try:
        price = round(float(request.form["price"]) * 100)
        quantity = int(request.form["quantity"])
        if price < 0 or quantity < 1:
            raise ValueError
    except ValueError:
        abort(400)
    with connect() as db:
        db.execute("INSERT INTO events(name,category,venue,event_date,description,price_cents,tickets_left) VALUES(?,?,?,?,?,?,?)", (request.form["name"], request.form["category"], request.form["venue"], request.form["event_date"], request.form.get("description", ""), price, quantity))
    flash("Event added.")
    return redirect(url_for("admin"))


@app.get("/health")
def health():
    with connect() as db:
        db.execute("SELECT 1")
    return {"status": "ok", "service": "eventpass"}


initialize()
