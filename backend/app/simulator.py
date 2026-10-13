"""Synthetic trajectories for software demonstration, not an energy-feasibility model."""
from datetime import datetime, timezone, timedelta
from .schemas import Telemetry, Event
from . import services as svc

SCENARIOS = {'normal':'Normal charging + reception','low_gradient':'Low thermal gradient','slow_charging':'Slow charging','insufficient_voltage':'Insufficient reservoir voltage','failed_ble':'Failed advertisement','sensor_disconnect':'Sensor disconnection','stale_telemetry':'Stale telemetry','brownout':'Brownout / restart'}

def start(db, scenario, speed):
    state = svc.simulation_state(db)
    if state['experiment_id'] and state['scenario'] == scenario and state['step'] < 120:
        state.update(running=True,speed=speed)
    else:
        exp = svc.create_experiment(db,{'name':SCENARIOS[scenario], 'description':'Synthetic software test fixture. Not experimental evidence.', 'conditions':'Deterministic trajectory; independent synthetic capacitor and TEG signals, not a conservation-of-energy model.', 'source':'simulated','device_id':'DEMO-C3','module':'TEC1-12706 (candidate)'})
        state = {'running':True,'scenario':scenario,'speed':speed,'step':0,'experiment_id':exp['id'],'base_time':svc.now()}
    svc.save_simulation(db,state)
    return state

def step(db):
    state = svc.simulation_state(db)
    if not state['running']: return state
    scenario = state['scenario']
    for _ in range(state['speed']):
        n = state['step']
        if n >= 120: state['running']=False; break
        # Fixed fixture clock: playback speed never changes integrated energy.
        stamp = (datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(seconds=n)).isoformat()
        received_at=(datetime.now(timezone.utc)-timedelta(minutes=5 if scenario=='stale_telemetry' else 0)).isoformat()
        voltage = .028 + (n % 10)*.0005
        current = .0004
        cap = 3.02 + min(n%40, 28)*.009
        hot,cold,quality = 33.0,28.0,'valid'
        if scenario == 'low_gradient': voltage,current,hot,cold=.003,.00003,30,29.5
        if scenario == 'slow_charging': cap=3.02+n*.0007; current=.00008
        if scenario == 'insufficient_voltage': cap=2.85+n*.0004
        if scenario == 'sensor_disconnect' and n >= 8: voltage=current=cap=hot=cold=None; quality='disconnected'
        if scenario == 'brownout' and n%40==30: cap=2.7
        base={'device_id':'DEMO-C3','experiment_id':state['experiment_id'],'source':'simulated','timestamp':stamp}
        sample=Telemetry(**base,sample_id=f"{state['experiment_id']}:{n}",voltage_v=voltage,current_a=current,capacitor_v=cap,hot_c=hot,cold_c=cold,quality=quality)
        svc.ingest(db,sample,received_at=received_at)
        if n%40==28 and scenario in ('normal','failed_ble','brownout'):
            svc.ingest(db,Event(**base,event_id=f"{state['experiment_id']}:ad:{n}",outcome='failure' if scenario=='failed_ble' else 'success',capacitor_v=cap,receiver_id='synthetic-receiver'),'events')
        if n%40==30 and scenario=='brownout':
            svc.ingest(db,Event(**base,event_id=f"{state['experiment_id']}:brownout:{n}",event_type='brownout',capacitor_v=cap),'events')
        state['step'] += 1
    svc.save_simulation(db,state)
    return state
