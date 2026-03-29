import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from database import init_db
import sqlite3
import config

@pytest.fixture
def app():
    """Create test app with temp database"""
    flask_app.config['TESTING']       = True
    flask_app.config['DATABASE_PATH'] = ':memory:'  # in-memory db for tests

    with flask_app.app_context():
        init_db()

    yield flask_app

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def auth_token(client):
    """Register and login, return token"""
    # register
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    # login
    res = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    return res.get_json()['token']

@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for protected routes"""
    return {'Authorization': f'Bearer {auth_token}'}