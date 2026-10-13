import importlib
import pytest
from fastapi.testclient import TestClient
from app import storage
from app.main import app

@pytest.fixture
def hosted(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',str(tmp_path/'hosted.sqlite3'))
    dist=tmp_path/'dist'; dist.mkdir(); (dist/'assets').mkdir()
    (dist/'index.html').write_text('<html><body>ThermoTrack</body></html>')
    (dist/'assets'/'main.js').write_text('console.log("loaded")')
    monkeypatch.setattr(importlib.import_module('app.main'),'FRONTEND_DIST',dist)
    monkeypatch.delenv('THERMOTRACK_ADMIN_TOKEN',raising=False)
    with TestClient(app) as client: yield client

@pytest.mark.parametrize('route',['/','/workout','/energy','/beacon','/rewards','/experiments','/settings','/workout/'])
def test_routes_and_refresh(hosted,route):
    response=hosted.get(route)
    assert response.status_code==200
    assert response.headers['content-type'].startswith('text/html')
    assert 'ThermoTrack' in response.text

def test_assets_and_api_are_separate(hosted):
    asset=hosted.get('/assets/main.js')
    assert asset.status_code==200 and 'javascript' in asset.headers['content-type']
    assert hosted.get('/api/v1/health').json()['status']=='ok'
    assert hosted.get('/api/v1/no-such-route').status_code==404
    assert hosted.get('/assets/missing.js').status_code==404
    assert hosted.get('/unknown-page').status_code==404
    assert hosted.get('/..%2F..%2Frequirements-lock.txt').status_code==404

def test_same_origin_mutation_and_remote_token(hosted,monkeypatch):
    monkeypatch.setenv('THERMOTRACK_ADMIN_TOKEN','test-only')
    assert hosted.post('/api/v1/experiments',json={'name':'Hosted run'},headers={'Origin':'https://testserver','Authorization':'Bearer test-only'}).status_code==201
    assert hosted.post('/api/v1/experiments',json={'name':'Blocked'},headers={'Origin':'https://attacker.example','Authorization':'Bearer test-only'}).status_code==403
    assert hosted.post('/api/v1/experiments',json={'name':'Unauthenticated'},headers={'Origin':'https://testserver'}).status_code==401
