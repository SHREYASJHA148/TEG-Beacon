import asyncio, csv, io, json, os, sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from . import storage as store, services as svc, simulator
from .schemas import Telemetry, Event, Experiment, Workout, Transition, Settings, SimulationStart

FRONTEND_DIST=Path(os.getenv('THERMOTRACK_FRONTEND_DIST', str(Path(__file__).resolve().parents[2]/'frontend'/'dist'))).resolve()

async def playback():
    while True:
        await asyncio.sleep(1)
        with store.connect() as db: simulator.step(db)

@asynccontextmanager
async def lifespan(app):
    store.initialize()
    # Application restart pauses persisted simulations explicitly.
    with store.connect() as db:
        state=svc.simulation_state(db); state['running']=False; svc.save_simulation(db,state)
    task=asyncio.create_task(playback())
    yield
    task.cancel()
    try: await task
    except asyncio.CancelledError: pass

app=FastAPI(title='ThermoTrack',version='1.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('THERMOTRACK_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','),allow_methods=['GET','POST','PATCH','PUT'],allow_headers=['Content-Type','Authorization'])

@app.middleware('http')
async def local_guard(request: Request, call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'):
        token=os.getenv('THERMOTRACK_ADMIN_TOKEN')
        if token:
            if request.headers.get('authorization') != f'Bearer {token}': return JSONResponse({'detail':'Administrator token required'},status_code=401)
        elif request.client and request.client.host not in ('127.0.0.1','::1','testclient'):
            return JSONResponse({'detail':'Mutations restricted to loopback; configure administrator token'},status_code=403)
        origin=request.headers.get('origin')
        allowed=os.getenv('THERMOTRACK_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',')
        parsed_origin=urlsplit(origin) if origin else None
        same_origin=bool(parsed_origin and parsed_origin.scheme in ('http','https') and parsed_origin.netloc==request.url.netloc and parsed_origin.path=='')
        if origin and origin not in allowed and not same_origin: return JSONResponse({'detail':'Origin not allowed'},status_code=403)
        length=request.headers.get('content-length')
        if length and int(length)>2_000_000: return JSONResponse({'detail':'Payload exceeds 2 MB'},status_code=413)
    return await call_next(request)

@app.exception_handler(sqlite3.Error)
async def database_error(request, exception):
    return JSONResponse({'detail':'Database operation failed. Check disk space and database path.'},status_code=503)

@app.get('/api/v1/health')
def health():
    with store.connect() as db: db.execute('SELECT 1').fetchone()
    return {'status':'ok','database':'ok','hardware':'not validated','version':'1.0.0'}

@app.get('/api/v1/dashboard/summary')
def dashboard(source: str=Query('simulated',pattern='^(simulated|measured)$'), experiment_id: str | None=None):
    with store.connect() as db: return svc.summary(db,source,experiment_id)

@app.get('/api/v1/settings')
def settings():
    with store.connect() as db: return store.settings(db)

@app.put('/api/v1/settings')
def save_settings(payload: Settings):
    with store.connect() as db:
        db.execute('UPDATE config SET data=? WHERE id=1',(payload.model_dump_json(),))
        if payload.mode=='measured':
            state=svc.simulation_state(db); state['running']=False; svc.save_simulation(db,state)
    return payload

@app.post('/api/v1/telemetry',status_code=201)
def telemetry(payload: Telemetry):
    with store.connect() as db: return svc.ingest(db,payload)

@app.post('/api/v1/telemetry/batch',status_code=201)
def batch(payload: list[Telemetry]):
    if not 1 <= len(payload) <= 1000: raise HTTPException(422,'Batch must contain 1–1000 samples')
    with store.connect() as db: return [svc.ingest(db,item) for item in payload]

@app.get('/api/v1/telemetry/history')
def history(experiment_id: str):
    with store.connect() as db:
        svc.experiment(db,experiment_id)
        return store.records(db,'telemetry',experiment=experiment_id)

@app.get('/api/v1/telemetry/latest')
def latest(experiment_id: str):
    data=history(experiment_id)
    return data[-1] if data else None

@app.post('/api/v1/beacon/events',status_code=201)
def event(payload: Event):
    with store.connect() as db: return svc.ingest(db,payload,'events')

@app.get('/api/v1/beacon/events')
def events(experiment_id: str):
    with store.connect() as db:
        svc.experiment(db,experiment_id)
        return store.records(db,'events',experiment=experiment_id)

@app.get('/api/v1/beacon/status')
def beacon_status(source: str=Query('simulated',pattern='^(simulated|measured)$')):
    data=dashboard(source)
    return {key:data[key] for key in ('source','energy','successes','failures','events')}

@app.get('/api/v1/energy/summary')
def energy_summary(experiment_id: str):
    with store.connect() as db: return svc.energy(db,history(experiment_id))

@app.get('/api/v1/energy/history')
def energy_history(experiment_id: str): return history(experiment_id)

@app.post('/api/v1/experiments',status_code=201)
def create_experiment(payload: Experiment):
    with store.connect() as db: return svc.create_experiment(db,payload.model_dump())

@app.get('/api/v1/experiments')
def experiments():
    with store.connect() as db: return [json.loads(row[0]) for row in db.execute('SELECT data FROM experiments ORDER BY created_at DESC')]

@app.get('/api/v1/experiments/{id}')
def experiment(id: str):
    with store.connect() as db:
        return {'experiment':svc.experiment(db,id),'energy':svc.energy(db,store.records(db,'telemetry',experiment=id)),'events':store.records(db,'events',experiment=id)}

@app.get('/api/v1/experiments/{id}/export')
def export(id: str):
    with store.connect() as db:
        exp=svc.experiment(db,id); samples=store.records(db,'telemetry',experiment=id)
    fields=['sample_id','device_id','experiment_id','source','timestamp','voltage_v','current_a','capacitor_v','hot_c','cold_c','measurement_point','quality','units']
    output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(samples)
    return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="thermotrack-{exp["source"]}-{id}.csv"'})

@app.post('/api/v1/workouts',status_code=201)
def create_workout(payload: Workout):
    with store.connect() as db:
        if any(w['status'] in ('active','paused') for w in store.records(db,'workouts')): raise HTTPException(409,'Finish the existing session first')
        item={**payload.model_dump(),'id':svc.identifier(),'status':'active','started_at':svc.now(),'segment_start':svc.now(),'elapsed_seconds':0,'estimated_kcal':0,'method':'MET approximation v1','met':0}
        from .calculations import MET
        item['met']=MET[payload.activity]
        db.execute('INSERT INTO workouts VALUES(?,?,?,?)',(item['id'],item['source'],item['status'],json.dumps(item)))
        return svc.workout_view(item)

@app.get('/api/v1/workouts')
def workouts():
    with store.connect() as db: return [svc.workout_view(w) for w in store.records(db,'workouts')]

@app.get('/api/v1/workouts/{id}')
def workout(id: str):
    with store.connect() as db:
        row=db.execute('SELECT data FROM workouts WHERE id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Workout not found')
        return svc.workout_view(json.loads(row[0]))

@app.patch('/api/v1/workouts/{id}')
def transition(id: str, payload: Transition):
    with store.connect() as db:
        row=db.execute('SELECT data FROM workouts WHERE id=?',(id,)).fetchone()
        if not row: raise HTTPException(404,'Workout not found')
        item=json.loads(row[0]); action=payload.action
        if item['status']=='completed':
            if action=='finish': return svc.workout_view(item)
            raise HTTPException(409,'Completed session cannot transition')
        if action=='pause' and item['status']!='active' or action=='resume' and item['status']!='paused': raise HTTPException(409,'Invalid session transition')
        item['elapsed_seconds']=svc.workout_view(item)['duration_seconds']
        item['segment_start']=svc.now()
        item['status']={'pause':'paused','resume':'active','finish':'completed'}[action]
        if action=='finish':
            item['completed_at']=svc.now(); cfg=store.settings(db)
            points=cfg['workout_points']+min(int(item['elapsed_seconds']/60)*cfg['duration_points'],cfg['duration_cap'])
            # A user-entered workout is a self-report, never hardware-verified.
            award_source='simulated' if item['source']=='simulated' else 'user_entered'
            svc.award(db,f'workout:{id}',award_source,points,f"Self-reported completion: {cfg['workout_points']} + capped duration points; no activity sensor verification",id)
        item=svc.workout_view(item)
        db.execute('UPDATE workouts SET status=?,data=? WHERE id=?',(item['status'],json.dumps(item),id))
        return item

@app.get('/api/v1/rewards/history')
def rewards(source: str=Query('simulated',pattern='^(simulated|measured)$')):
    with store.connect() as db: return [dict(r) for r in db.execute('SELECT * FROM rewards WHERE source=? OR source=? ORDER BY timestamp DESC',(source,'user_entered' if source=='measured' else source))]

@app.get('/api/v1/rewards/balance')
def balance(source: str=Query('simulated',pattern='^(simulated|measured)$')): return {'source':source,'balance':sum(r['points'] for r in rewards(source))}

@app.get('/api/v1/rewards/achievements')
def achievements(source: str=Query('simulated',pattern='^(simulated|measured)$')): return dashboard(source)['achievements']

@app.get('/api/v1/simulation/scenarios')
def scenarios(): return simulator.SCENARIOS

@app.post('/api/v1/simulation/start')
def start(payload: SimulationStart):
    with store.connect() as db:
        if store.settings(db)['mode']!='simulated': raise HTTPException(409,'Select simulation mode explicitly in Settings')
        return simulator.start(db,payload.scenario,payload.speed)

@app.post('/api/v1/simulation/pause')
def pause():
    with store.connect() as db:
        state=svc.simulation_state(db); state['running']=False; svc.save_simulation(db,state); return state

@app.post('/api/v1/simulation/reset')
def reset():
    # Only synthetic records are reset. Physical experiment records are never removed.
    with store.connect() as db:
        for table in ('rewards','events','telemetry','workouts','experiments'): db.execute(f"DELETE FROM {table} WHERE source='simulated'")
        svc.save_simulation(db,{'running':False,'scenario':'normal','step':0,'speed':1,'experiment_id':None})
    return {'status':'Synthetic demo records reset'}

# Registered after API routes: unknown API URLs must never receive frontend HTML.
@app.get('/{path:path}',include_in_schema=False)
def frontend(path: str):
    if path=='api' or path.startswith('api/'):
        raise HTTPException(404,'API endpoint not found')
    if path.strip('/') in ('','workout','energy','beacon','rewards','experiments','settings'):
        target=FRONTEND_DIST/'index.html'
        if not target.is_file(): raise HTTPException(503,'Frontend not built. Run npm ci and npm run build in frontend.')
        return FileResponse(target,headers={'Cache-Control':'no-cache'})
    target=(FRONTEND_DIST/path).resolve()
    if not target.is_relative_to(FRONTEND_DIST) or not target.is_file():
        raise HTTPException(404,'File not found')
    return FileResponse(target,headers={'Cache-Control':'public, max-age=31536000, immutable' if path.startswith('assets/') else 'no-cache'})
