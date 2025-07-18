import pytest
from flask import Flask
import supabase_api

class DummySupabase:
    pass

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    supabase_api.supabase = DummySupabase()
    app.register_blueprint(supabase_api.supabase_api_blueprint)
    with app.test_client() as client:
        yield client

def test_missing_authorization_header(client):
    resp = client.get('/pairings')
    assert resp.status_code == 401
    assert resp.get_json()['error'] == 'Authorization header missing'

def test_malformed_authorization_header(client):
    resp = client.get('/pairings', headers={'Authorization': 'Bearer'})
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'Malformed authorization header'
