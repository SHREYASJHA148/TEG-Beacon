from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Source = Literal['simulated', 'measured']

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Timestamped(Strict):
    timestamp: datetime
    @field_validator('timestamp')
    @classmethod
    def utc(cls, value):
        if value.tzinfo is None:
            raise ValueError('Timestamp must include timezone')
        if value > datetime.now(timezone.utc).replace(microsecond=0) + __import__('datetime').timedelta(seconds=30):
            raise ValueError('Future timestamps beyond 30 seconds are rejected')
        return value.astimezone(timezone.utc)

class Telemetry(Timestamped):
    protocol_version: Literal[1] = 1
    sample_id: str = Field(min_length=1, max_length=120)
    device_id: str = Field(min_length=1, max_length=80)
    experiment_id: str = Field(min_length=1, max_length=80)
    source: Source
    voltage_v: float | None = Field(default=None, ge=0, le=5)
    current_a: float | None = Field(default=None, ge=0, le=.1)
    capacitor_v: float | None = Field(default=None, ge=0, le=5)
    hot_c: float | None = Field(default=None, ge=-20, le=80)
    cold_c: float | None = Field(default=None, ge=-20, le=80)
    measurement_point: Literal['teg_loaded', 'open_circuit', 'converter_output'] = 'teg_loaded'
    quality: Literal['valid', 'invalid', 'disconnected'] = 'valid'
    units: Literal['SI'] = 'SI'

class Event(Timestamped):
    event_id: str = Field(min_length=1, max_length=120)
    device_id: str = Field(min_length=1, max_length=80)
    experiment_id: str = Field(min_length=1, max_length=80)
    source: Source
    event_type: Literal['advertisement', 'brownout', 'restart'] = 'advertisement'
    outcome: Literal['success', 'failure', 'unknown'] = 'unknown'
    capacitor_v: float | None = Field(default=None, ge=0, le=5)
    # Confirmed reception requires an instrument/gateway identifier.
    receiver_id: str | None = Field(default=None, min_length=1, max_length=80)
    @model_validator(mode='after')
    def confirmed(self):
        if self.source == 'measured' and self.outcome == 'success' and not self.receiver_id:
            raise ValueError('Successful measured reception requires receiver_id')
        return self

class Experiment(Strict):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default='', max_length=2000)
    conditions: str = Field(default='', max_length=1000)
    source: Source = 'measured'
    device_id: str = Field(default='ESP32-C3-01', min_length=1, max_length=80)
    module: str = Field(default='TEC1-12706 (candidate)', max_length=100)

class Workout(Strict):
    activity: Literal['Walking', 'Cycling', 'Strength training', 'Running']
    mass_kg: float = Field(ge=20, le=300)
    planned_minutes: float = Field(ge=1, le=360)
    source: Literal['simulated', 'user_entered'] = 'user_entered'

class Transition(Strict):
    action: Literal['pause', 'resume', 'finish']

class Settings(Strict):
    mode: Literal['simulated', 'measured'] = 'simulated'
    capacitance_f: float = Field(default=.47, ge=.22, le=1)
    low_v: float = Field(default=3, ge=0, le=5)
    high_v: float = Field(default=3.3, gt=0, le=5)
    ready_v: float = Field(default=3.25, gt=0, le=5)
    threshold_validated: bool = False
    stale_seconds: int = Field(default=20, ge=5, le=600)
    max_gap_seconds: int = Field(default=15, ge=1, le=600)
    workout_points: int = Field(default=10, ge=0, le=100)
    duration_points: int = Field(default=1, ge=0, le=10)
    duration_cap: int = Field(default=30, ge=0, le=100)
    beacon_points: int = Field(default=2, ge=0, le=100)
    energy_unit_j: float = Field(default=.01, gt=0, le=100)
    energy_points: int = Field(default=1, ge=0, le=100)
    energy_cap: int = Field(default=50, ge=0, le=1000)
    leaderboard: bool = False
    @model_validator(mode='after')
    def window(self):
        if not self.low_v < self.ready_v <= self.high_v:
            raise ValueError('Require low_v < ready_v ≤ high_v')
        return self

class SimulationStart(Strict):
    scenario: Literal['normal', 'low_gradient', 'slow_charging', 'insufficient_voltage', 'failed_ble', 'sensor_disconnect', 'stale_telemetry', 'brownout'] = 'normal'
    speed: int = Field(default=1, ge=1, le=10)
