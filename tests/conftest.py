import pytest
import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    from app import app as flask_app
    flask_app.config['TESTING']       = True
    flask_app.config['DATABASE_PATH'] = db_path

    import config
    original_path        = config.DATABASE_PATH
    config.DATABASE_PATH = db_path

    with flask_app.app_context():
        from database import init_db
        init_db()

    yield flask_app

    # cleanup after test
    config.DATABASE_PATH = original_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_token(client):
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    res = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    return res.get_json()['token']

@pytest.fixture
def auth_headers(auth_token):
    return {'Authorization': f'Bearer {auth_token}'}