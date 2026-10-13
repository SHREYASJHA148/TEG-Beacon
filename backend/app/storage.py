import json, os, sqlite3
from contextlib import contextmanager
from pathlib import Path
from .schemas import Settings

DB = os.getenv('THERMOTRACK_DB', str(Path(__file__).resolve().parents[1] / 'thermotrack.sqlite3'))

@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def initialize():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
        INSERT OR IGNORE INTO schema_version VALUES(1);
        CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS experiments(id TEXT PRIMARY KEY, name TEXT, source TEXT, device_id TEXT, created_at TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS telemetry(id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id), device_id TEXT, source TEXT, timestamp TEXT, data TEXT, UNIQUE(experiment_id,device_id,timestamp));
        CREATE INDEX IF NOT EXISTS telemetry_time ON telemetry(experiment_id,timestamp);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, experiment_id TEXT REFERENCES experiments(id), source TEXT, timestamp TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS workouts(id TEXT PRIMARY KEY, source TEXT, status TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS rewards(id TEXT PRIMARY KEY, source TEXT, points INTEGER, timestamp TEXT, explanation TEXT, entity_id TEXT);
        CREATE TABLE IF NOT EXISTS simulation(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT);
        ''')
        db.execute('INSERT OR IGNORE INTO config VALUES(1,?)', (json.dumps(Settings().model_dump()),))

def settings(db):
    return json.loads(db.execute('SELECT data FROM config WHERE id=1').fetchone()[0])

def records(db, table, source=None, experiment=None):
    # Table names are only supplied by trusted application code.
    query, args = f'SELECT data FROM {table}', []
    where = []
    if source:
        where.append('source=?'); args.append(source)
    if experiment:
        where.append('experiment_id=?'); args.append(experiment)
    if where: query += ' WHERE ' + ' AND '.join(where)
    if table in ('telemetry', 'events'): query += ' ORDER BY timestamp'
    return [json.loads(row[0]) for row in db.execute(query, args)]
