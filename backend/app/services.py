import json, uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from . import storage as store
from .calculations import power, integrate, capacitor, calories

def now(): return datetime.now(timezone.utc).isoformat()
def identifier(): return str(uuid.uuid4())
def award(db, key, source, points, explanation, entity):
    if points > 0:
        db.execute('INSERT OR IGNORE INTO rewards VALUES(?,?,?,?,?,?)', (key, source, points, now(), explanation, entity))

def create_experiment(db, data, experiment_id=None):
    item = {**data, 'id': experiment_id or identifier(), 'created_at': now()}
    db.execute('INSERT INTO experiments VALUES(?,?,?,?,?,?)', (item['id'], item['name'], item['source'], item['device_id'], item['created_at'], json.dumps(item)))
    return item

def experiment(db, id):
    row = db.execute('SELECT data FROM experiments WHERE id=?', (id,)).fetchone()
    if not row: raise HTTPException(404, 'Experiment not found')
    return json.loads(row[0])

def ingest(db, model, kind='telemetry', received_at=None):
    item = model.model_dump(mode='json')
    exp = experiment(db, item['experiment_id'])
    if exp['source'] != item['source'] or exp['device_id'] != item['device_id']:
        raise HTTPException(422, 'Device and provenance must match the experiment')
    id = item['sample_id'] if kind == 'telemetry' else item['event_id']
    row = db.execute(f'SELECT data FROM {kind} WHERE id=?', (id,)).fetchone()
    if row:
        existing=json.loads(row[0]); existing.pop('received_at',None)
        if existing != item: raise HTTPException(409, 'Identifier already belongs to a different payload')
        return {'duplicate': True, 'id': id}
    if kind == 'telemetry':
        item['received_at']=received_at or now()
        collision = db.execute('SELECT id FROM telemetry WHERE experiment_id=? AND device_id=? AND timestamp=?', (item['experiment_id'], item['device_id'], item['timestamp'])).fetchone()
        if collision: raise HTTPException(409, 'Duplicate measurement timestamp')
        db.execute('INSERT INTO telemetry VALUES(?,?,?,?,?,?)', (id,item['experiment_id'],item['device_id'],item['source'],item['timestamp'],json.dumps(item)))
    else:
        db.execute('INSERT INTO events VALUES(?,?,?,?,?)', (id,item['experiment_id'],item['source'],item['timestamp'],json.dumps(item)))
        if item['event_type'] == 'advertisement' and item['outcome'] == 'success':
            cfg = store.settings(db)
            award(db, f'beacon:{id}', item['source'], cfg['beacon_points'], f"Unique confirmed advertisement; {cfg['beacon_points']} points (configured rule)", item['experiment_id'])
    if kind == 'telemetry':
        cfg = store.settings(db)
        total, _ = integrate(store.records(db, 'telemetry', experiment=item['experiment_id']), cfg['max_gap_seconds'])
        target = min(int(total / cfg['energy_unit_j']) * cfg['energy_points'], cfg['energy_cap'])
        previous = db.execute("SELECT COALESCE(SUM(points),0) FROM rewards WHERE entity_id=? AND id LIKE 'energy:%'", (item['experiment_id'],)).fetchone()[0]
        award(db, f'energy:{id}', item['source'], target-previous, f"Integrated loaded TEG energy: {total:.6f} J; {cfg['energy_points']} points per {cfg['energy_unit_j']} J, cap {cfg['energy_cap']}", item['experiment_id'])
    return {'duplicate': False, 'id': id}

def energy(db, samples):
    cfg = store.settings(db)
    total, gaps = integrate(samples, cfg['max_gap_seconds'])
    latest = samples[-1] if samples else None
    valid = latest and latest['quality'] == 'valid'
    voltage = latest['capacitor_v'] if valid else None
    stored, usable = capacitor(cfg['capacitance_f'], voltage, cfg['low_v'], cfg['high_v'])
    dt = None
    if valid and latest['hot_c'] is not None and latest['cold_c'] is not None:
        dt = latest['hot_c'] - latest['cold_c']
    rate = None
    if len(samples) > 1 and valid and samples[-2]['quality'] == 'valid':
        prev = samples[-2]
        seconds = (datetime.fromisoformat(latest['timestamp']) - datetime.fromisoformat(prev['timestamp'])).total_seconds()
        if 0 < seconds <= cfg['max_gap_seconds'] and prev['capacitor_v'] is not None and voltage is not None and voltage <= cfg['high_v'] and prev['capacitor_v'] <= cfg['high_v']:
            rate = .5 * cfg['capacitance_f'] * (voltage**2 - prev['capacitor_v']**2) / seconds
    freshness_time=latest.get('received_at',latest['timestamp']) if latest and latest['source']=='simulated' else latest['timestamp'] if latest else None
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(freshness_time)).total_seconds() if freshness_time else None
    status = 'disconnected' if not latest or latest['quality'] == 'disconnected' else 'invalid' if not valid else 'stale' if age > cfg['stale_seconds'] else 'fresh'
    return {'harvested_j': total if samples and any(power(s['voltage_v'],s['current_a'],s['quality'],s['measurement_point']) is not None for s in samples) else None, 'gaps': gaps, 'stored_j': stored, 'usable_j': usable, 'power_w': power(latest['voltage_v'],latest['current_a'],latest['quality'],latest['measurement_point']) if latest else None, 'delta_c':dt,'charging_w':rate,'latest':latest,'status':status,'age_seconds':age,'ready': bool(status == 'fresh' and voltage is not None and cfg['ready_v'] <= voltage <= cfg['high_v']), 'readiness_basis':'Voltage threshold only; no guarantee of a BLE event', 'threshold_validated': cfg['threshold_validated']}

def workout_view(item):
    duration = item['elapsed_seconds']
    if item['status'] == 'active': duration += max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(item['segment_start'])).total_seconds())
    return {**item, 'duration_seconds': duration, 'estimated_kcal': calories(item['activity'],item['mass_kg'],duration)}

def summary(db, source, experiment_id=None):
    exps = [json.loads(row[0]) for row in db.execute('SELECT data FROM experiments WHERE source=? ORDER BY created_at DESC', (source,))]
    selected = experiment_id or (exps[0]['id'] if exps else None)
    if selected and experiment(db, selected)['source'] != source: raise HTTPException(422, 'Experiment source mismatch')
    samples = store.records(db,'telemetry',source,selected) if selected else []
    events = store.records(db,'events',source,selected) if selected else []
    workouts = [workout_view(w) for w in store.records(db,'workouts') if w['source'] == ('simulated' if source == 'simulated' else 'user_entered')]
    rewards = [dict(row) for row in db.execute('SELECT * FROM rewards WHERE source=? OR source=? ORDER BY timestamp DESC',(source,'user_entered' if source=='measured' else source))]
    today = datetime.now(timezone.utc).date()
    completed = [w for w in workouts if w['status'] == 'completed']
    total_points = sum(r['points'] for r in rewards)
    energy_summary = energy(db,samples)
    days={datetime.fromisoformat(w['completed_at']).date() for w in completed}
    cursor=today if today in days else today-timedelta(days=1)
    streak=0
    while cursor in days:
        streak+=1; cursor-=timedelta(days=1)
    stats={}
    for key in ('voltage_v','current_a','capacitor_v','hot_c','cold_c'):
        values=[s[key] for s in samples if s['quality']=='valid' and s[key] is not None]
        stats[key]={'min':min(values),'max':max(values),'mean':sum(values)/len(values),'count':len(values)} if values else None
    energy_summary['statistics']=stats
    energy_summary['duration_seconds']=(datetime.fromisoformat(samples[-1]['timestamp'])-datetime.fromisoformat(samples[0]['timestamp'])).total_seconds() if len(samples)>1 else 0
    return {'source':source,'energy':energy_summary,'samples':samples,'events':events,'workouts':workouts,'experiments':exps,'selected_experiment':selected,'rewards':rewards,'points':total_points,'kcal_today':sum(w['estimated_kcal'] for w in completed if datetime.fromisoformat(w['completed_at']).date()==today),'successes':sum(e['outcome']=='success' and e['event_type']=='advertisement' for e in events),'failures':sum(e['outcome']=='failure' and e['event_type']=='advertisement' for e in events),'settings':store.settings(db),'simulation':simulation_state(db),'achievements':[{'name':'First session','earned':bool(completed),'description':'Complete one workout'},{'name':'Beacon received','earned':any(e['outcome']=='success' and e['event_type']=='advertisement' for e in events),'description':'One confirmed advertisement in this run'},{'name':'Energy observer','earned':(energy_summary['harvested_j'] or 0) >= .01,'description':'Integrate 10 mJ in this run'}],'weekly_sessions':sum(datetime.fromisoformat(w['completed_at']).isocalendar()[:2]==today.isocalendar()[:2] for w in completed),'active_days':len(days),'streak_days':streak}

def simulation_state(db):
    row = db.execute('SELECT data FROM simulation WHERE id=1').fetchone()
    return json.loads(row[0]) if row else {'running':False,'scenario':'normal','step':0,'speed':1,'experiment_id':None}

def save_simulation(db, data):
    db.execute('INSERT OR REPLACE INTO simulation VALUES(1,?)',(json.dumps(data),))
