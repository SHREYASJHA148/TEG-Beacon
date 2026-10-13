import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app import storage, services, simulator
from app.main import app
from app.calculations import power, integrate, capacitor, calories

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage,'DB',str(tmp_path/'test.sqlite3'))
    monkeypatch.delenv('THERMOTRACK_ADMIN_TOKEN',raising=False)
    with TestClient(app) as client: yield client

def exp(client, source='measured'):
    return client.post('/api/v1/experiments',json={'name':'Test run','source':source,'device_id':'test-device'}).json()['id']

def sample(id, n=0, **values):
    return {'sample_id':f's-{n}','experiment_id':id,'device_id':'test-device','source':'measured','timestamp':(datetime.now(timezone.utc)-timedelta(seconds=20-n)).isoformat(),'voltage_v':.03,'current_a':.001,'capacitor_v':3.2,**values}

def test_si_and_missing_power():
    assert power(.03,.001)==pytest.approx(30e-6)
    assert power(.03,None) is None
    assert power(.03,.001,point='open_circuit') is None
    assert power(.03,.001,quality='invalid') is None

def test_integral_and_gaps():
    samples=[{'timestamp':f'2026-01-01T00:00:{t:02d}+00:00','voltage_v':1,'current_a':p,'quality':'valid','measurement_point':'teg_loaded'} for t,p in [(0,1),(10,3),(40,3)]]
    total,gaps=integrate(samples)
    assert total==20 and gaps==1
    samples[1]['current_a']=None
    assert integrate(samples)==(0,2)
    assert integrate([samples[0],samples[0]])==(0,0)

def test_capacitor_and_met():
    stored,usable=capacitor(.22,3.3,3,3.3)
    assert usable==pytest.approx(.2079)
    assert stored==pytest.approx(1.1979)
    assert capacitor(.47,None,3,3.3)==(None,None)
    assert capacitor(.47,3.5,3,3.3)==(None,None)
    with pytest.raises(ValueError): capacitor(.47,3.3,3.3,3)
    assert calories('Walking',70,600)==pytest.approx(42.875)

def test_health_empty_hardware(client):
    assert client.get('/api/v1/health').json()['database']=='ok'
    summary=client.get('/api/v1/dashboard/summary?source=measured').json()
    assert summary['energy']['status']=='disconnected'
    assert summary['energy']['power_w'] is None
    assert summary['simulation']['running'] is False

def test_ingestion_validation_and_provenance(client):
    id=exp(client)
    item=sample(id)
    assert client.post('/api/v1/telemetry',json=item).status_code==201
    assert client.post('/api/v1/telemetry',json=item).json()['duplicate']
    assert client.post('/api/v1/telemetry',json={**item,'voltage_v':.04}).status_code==409
    assert client.post('/api/v1/telemetry',json={**item,'sample_id':'other'}).status_code==409
    assert client.post('/api/v1/telemetry',json={**item,'source':'simulated'}).status_code==422
    for change in ({'current_a':-1},{'timestamp':'2026-01-01T00:00:00'},{'voltage_v':999},{'units':'mV'},{'unexpected':3}):
        assert client.post('/api/v1/telemetry',json={**item,**change}).status_code==422
    assert client.post('/api/v1/telemetry',json={**item,'timestamp':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}).status_code==422

def test_batch_atomicity_and_missing_current(client):
    id=exp(client)
    first=sample(id,current_a=None)
    assert client.post('/api/v1/telemetry/batch',json=[first,{**sample('does-not-exist',1)}]).status_code==404
    assert client.get(f'/api/v1/telemetry/history?experiment_id={id}').json()==[]
    assert client.post('/api/v1/telemetry',json=first).status_code==201
    energy=client.get(f'/api/v1/energy/summary?experiment_id={id}').json()
    assert energy['power_w'] is None and energy['harvested_j'] is None

def test_reward_idempotency_and_confirmation(client):
    id=exp(client)
    event={'event_id':'e1','experiment_id':id,'device_id':'test-device','source':'measured','timestamp':datetime.now(timezone.utc).isoformat(),'outcome':'success'}
    assert client.post('/api/v1/beacon/events',json=event).status_code==422
    event['receiver_id']='gateway-1'
    assert client.post('/api/v1/beacon/events',json=event).status_code==201
    assert client.post('/api/v1/beacon/events',json=event).json()['duplicate']
    assert client.get('/api/v1/rewards/balance?source=measured').json()['balance']==2
    event.update(event_id='e2',outcome='unknown')
    assert client.post('/api/v1/beacon/events',json=event).status_code==201
    assert client.get('/api/v1/rewards/balance?source=measured').json()['balance']==2

def test_workout_pause_resume_finish_persistence(client):
    item=client.post('/api/v1/workouts',json={'activity':'Walking','mass_kg':70,'planned_minutes':10,'source':'simulated'}).json()
    id=item['id']
    assert client.post('/api/v1/workouts',json={'activity':'Running','mass_kg':70,'planned_minutes':5}).status_code==409
    assert client.patch(f'/api/v1/workouts/{id}',json={'action':'resume'}).status_code==409
    assert client.patch(f'/api/v1/workouts/{id}',json={'action':'pause'}).json()['status']=='paused'
    assert client.patch(f'/api/v1/workouts/{id}',json={'action':'resume'}).json()['status']=='active'
    finished=client.patch(f'/api/v1/workouts/{id}',json={'action':'finish'}).json()
    assert finished['duration_seconds']>=0 and finished['estimated_kcal']>=0
    assert finished['method']=='MET approximation v1'
    assert client.patch(f'/api/v1/workouts/{id}',json={'action':'finish'}).status_code==200
    assert client.get('/api/v1/rewards/balance').json()['balance']==10
    storage.initialize()
    assert client.get(f'/api/v1/workouts/{id}').json()['status']=='completed'
    with storage.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM rewards').fetchone()[0]==1

@pytest.mark.parametrize('scenario',list(simulator.SCENARIOS))
def test_scenarios_deterministic_pause_and_export(client,scenario):
    client.post('/api/v1/simulation/start',json={'scenario':scenario,'speed':10})
    with storage.connect() as db:
        for _ in range(4): simulator.step(db)
        state=services.simulation_state(db)
        rows=storage.records(db,'telemetry',experiment=state['experiment_id'])
        assert len(rows)==40
        assert datetime.fromisoformat(rows[1]['timestamp'])==datetime(2026,1,1,0,0,1,tzinfo=timezone.utc)
    client.post('/api/v1/simulation/pause')
    with storage.connect() as db:
        simulator.step(db)
        assert services.simulation_state(db)['step']==40
    summary=client.get('/api/v1/dashboard/summary').json()
    assert summary['source']=='simulated'
    if scenario=='sensor_disconnect': assert summary['energy']['status']=='disconnected'
    if scenario=='stale_telemetry': assert summary['energy']['status']=='stale'
    if scenario=='normal': assert summary['successes']==1
    if scenario=='failed_ble': assert summary['failures']==1
    if scenario=='brownout': assert any(e['event_type']=='brownout' for e in summary['events'])
    exported=client.get(f'/api/v1/experiments/{state["experiment_id"]}/export')
    assert 'voltage_v,current_a,capacitor_v' in exported.text
    assert 'simulated' in exported.text

def test_config_security_and_reset_preserves_measured(client):
    id=exp(client)
    client.post('/api/v1/telemetry',json=sample(id))
    cfg=client.get('/api/v1/settings').json()
    assert client.put('/api/v1/settings',json={**cfg,'low_v':4}).status_code==422
    assert client.put('/api/v1/settings',json=cfg,headers={'Origin':'https://untrusted.test'}).status_code==403
    client.put('/api/v1/settings',json={**cfg,'mode':'measured'})
    assert client.post('/api/v1/simulation/start',json={}).status_code==409
    client.post('/api/v1/simulation/reset')
    assert len(client.get(f'/api/v1/telemetry/history?experiment_id={id}').json())==1

def test_self_reported_reward_source(client):
    workout=client.post('/api/v1/workouts',json={'activity':'Running','mass_kg':70,'planned_minutes':10}).json()
    client.patch(f'/api/v1/workouts/{workout["id"]}',json={'action':'finish'})
    ledger=client.get('/api/v1/rewards/history?source=measured').json()
    assert ledger[0]['source']=='user_entered'

def test_energy_award_cap(client):
    id=exp(client)
    base=datetime.now(timezone.utc)-timedelta(seconds=20)
    for n in range(3):
        item=sample(id,n,timestamp=(base+timedelta(seconds=n*5)).isoformat(),voltage_v=1,current_a=.1)
        assert client.post('/api/v1/telemetry',json=item).status_code==201
    assert client.get('/api/v1/rewards/balance?source=measured').json()['balance']==50

def test_token_guard(client,monkeypatch):
    monkeypatch.setenv('THERMOTRACK_ADMIN_TOKEN','test-secret')
    assert client.post('/api/v1/experiments',json={'name':'protected'}).status_code==401
    assert client.post('/api/v1/experiments',json={'name':'protected'},headers={'Authorization':'Bearer test-secret'}).status_code==201

def test_playback_speed_does_not_change_energy(client):
    client.post('/api/v1/simulation/start',json={'scenario':'normal','speed':1})
    with storage.connect() as db:
        for _ in range(40): simulator.step(db)
        first=services.summary(db,'simulated')['energy']['harvested_j']
    client.post('/api/v1/simulation/reset')
    client.post('/api/v1/simulation/start',json={'scenario':'normal','speed':10})
    with storage.connect() as db:
        for _ in range(4): simulator.step(db)
        second=services.summary(db,'simulated')['energy']['harvested_j']
    assert first==second

def test_statistics_streak_and_experiment_isolation(client):
    id=exp(client)
    other=exp(client)
    client.post('/api/v1/telemetry',json=sample(id,0,voltage_v=.04))
    client.post('/api/v1/telemetry',json=sample(other,1,voltage_v=.02))
    report=client.get(f'/api/v1/dashboard/summary?source=measured&experiment_id={id}').json()
    assert report['energy']['statistics']['voltage_v']['mean']==.04
    assert len(report['samples'])==1
    assert report['streak_days']==0
    assert report['energy']['duration_seconds']==0

def test_unsafe_capacitor_not_ready(client):
    id=exp(client)
    client.post('/api/v1/telemetry',json=sample(id,timestamp=datetime.now(timezone.utc).isoformat(),capacitor_v=3.5))
    report=client.get(f'/api/v1/energy/summary?experiment_id={id}').json()
    assert report['ready'] is False
    assert report['usable_j'] is None
