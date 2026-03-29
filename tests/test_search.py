class TestSearch:
    """Integration tests for search"""

    def test_search_requires_auth(self, client):
        """Test search requires authentication"""
        res = client.get('/api/search?q=chicken')
        assert res.status_code == 401

    def test_search_empty_query(self, client, auth_headers):
        """Test empty query rejected"""
        res = client.get('/api/search?q=', headers=auth_headers)
        assert res.status_code == 400

    def test_search_returns_results(self, client, auth_headers):
        """Test search returns results"""
        res = client.get('/api/search?q=chicken', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'results' in data
        assert 'original' in data
        assert 'has_correction' in data

    def test_search_with_typo(self, client, auth_headers):
        """Test spell correction works"""
        res = client.get('/api/search?q=chiken', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data['has_correction'] == True
        assert data['corrected'] != data['original']

    def test_search_skip_correction(self, client, auth_headers):
        """Test skip correction flag works"""
        res = client.get(
            '/api/search?q=chiken&skip_correction=true',
            headers=auth_headers
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['has_correction'] == False