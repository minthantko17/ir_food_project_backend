class TestBookmarks:
    """Integration tests for bookmarks"""

    def setup_folder(self, client, auth_headers):
        """Helper to create a folder"""
        res = client.post('/api/folders',
            json={'name': 'TestFolder'},
            headers=auth_headers
        )
        return res.get_json()['folder_id']

    def test_add_bookmark(self, client, auth_headers):
        """Test adding a bookmark"""
        folder_id = self.setup_folder(client, auth_headers)
        res = client.post('/api/bookmarks',
            json={
                'recipe_id': 12345,
                'folder_id': folder_id,
                'rating'   : 4
            },
            headers=auth_headers
        )
        assert res.status_code == 201

    def test_add_bookmark_invalid_rating(self, client, auth_headers):
        """Test invalid rating rejected"""
        folder_id = self.setup_folder(client, auth_headers)
        res = client.post('/api/bookmarks',
            json={
                'recipe_id': 12345,
                'folder_id': folder_id,
                'rating'   : 6  # invalid!
            },
            headers=auth_headers
        )
        assert res.status_code == 400

    def test_get_all_bookmarks(self, client, auth_headers):
        """Test get all bookmarks"""
        folder_id = self.setup_folder(client, auth_headers)
        client.post('/api/bookmarks',
            json={
                'recipe_id': 12345,
                'folder_id': folder_id,
                'rating'   : 5
            },
            headers=auth_headers
        )
        res = client.get('/api/bookmarks', headers=auth_headers)
        assert res.status_code == 200
        assert 'bookmarks' in res.get_json()

    def test_remove_bookmark(self, client, auth_headers):
        """Test removing a bookmark"""
        folder_id = self.setup_folder(client, auth_headers)
        client.post('/api/bookmarks',
            json={
                'recipe_id': 12345,
                'folder_id': folder_id,
                'rating'   : 3
            },
            headers=auth_headers
        )
        # get bookmark id
        res       = client.get('/api/folders/{}/bookmarks'.format(folder_id),
            headers=auth_headers
        )
        bookmark_id = res.get_json()['bookmarks'][0]['id']

        # remove
        res = client.delete(f'/api/bookmarks/{bookmark_id}',
            headers=auth_headers
        )
        assert res.status_code == 200