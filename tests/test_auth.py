import pytest

class TestAuth:
    """Unit tests for authentication"""

    def test_register_success(self, client):
        """Test successful registration"""
        res = client.post('/api/auth/register', json={
            'username': 'newuser',
            'password': 'password123'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert 'token' in data
        assert data['username'] == 'newuser'

    def test_register_duplicate(self, client):
        """Test duplicate username rejected"""
        client.post('/api/auth/register', json={
            'username': 'dupuser',
            'password': 'password123'
        })
        res = client.post('/api/auth/register', json={
            'username': 'dupuser',
            'password': 'password123'
        })
        assert res.status_code == 409

    def test_register_missing_fields(self, client):
        """Test missing fields rejected"""
        res = client.post('/api/auth/register', json={
            'username': 'nopass'
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        """Test successful login"""
        client.post('/api/auth/register', json={
            'username': 'loginuser',
            'password': 'password123'
        })
        res = client.post('/api/auth/login', json={
            'username': 'loginuser',
            'password': 'password123'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'token' in data

    def test_login_wrong_password(self, client):
        """Test wrong password rejected"""
        client.post('/api/auth/register', json={
            'username': 'passuser',
            'password': 'correctpass'
        })
        res = client.post('/api/auth/login', json={
            'username': 'passuser',
            'password': 'wrongpass'
        })
        assert res.status_code == 401

    def test_login_not_found(self, client):
        """Test non-existent user rejected"""
        res = client.post('/api/auth/login', json={
            'username': 'nobody',
            'password': 'password123'
        })
        assert res.status_code == 404

    def test_protected_route_no_token(self, client):
        """Test protected route without token"""
        res = client.get('/api/search?q=chicken')
        assert res.status_code == 401

    def test_protected_route_invalid_token(self, client):
        """Test protected route with invalid token"""
        res = client.get('/api/search?q=chicken',
            headers={'Authorization': 'Bearer invalid_token'})
        assert res.status_code == 401