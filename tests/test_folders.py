class TestFolders:
    """Integration tests for folder management"""

    def test_create_folder(self, client, auth_headers):
        """Test folder creation"""
        res = client.post('/api/folders',
            json={'name': 'Italian'},
            headers=auth_headers
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data['name'] == 'Italian'
        assert 'folder_id' in data

    def test_create_duplicate_folder(self, client, auth_headers):
        """Test duplicate folder name rejected"""
        client.post('/api/folders',
            json={'name': 'Desserts'},
            headers=auth_headers
        )
        res = client.post('/api/folders',
            json={'name': 'Desserts'},
            headers=auth_headers
        )
        assert res.status_code == 409

    def test_get_folders(self, client, auth_headers):
        """Test get all folders"""
        client.post('/api/folders',
            json={'name': 'Breakfast'},
            headers=auth_headers
        )
        res = client.get('/api/folders', headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 'folders' in data
        assert len(data['folders']) >= 1

    def test_rename_folder(self, client, auth_headers):
        """Test folder rename"""
        create_res = client.post('/api/folders',
            json={'name': 'OldName'},
            headers=auth_headers
        )
        folder_id = create_res.get_json()['folder_id']

        res = client.put(f'/api/folders/{folder_id}',
            json={'name': 'NewName'},
            headers=auth_headers
        )
        assert res.status_code == 200
        assert res.get_json()['name'] == 'NewName'

    def test_delete_folder(self, client, auth_headers):
        """Test folder deletion"""
        create_res = client.post('/api/folders',
            json={'name': 'ToDelete'},
            headers=auth_headers
        )
        folder_id = create_res.get_json()['folder_id']

        res = client.delete(f'/api/folders/{folder_id}',
            headers=auth_headers
        )
        assert res.status_code == 200

    def test_delete_nonexistent_folder(self, client, auth_headers):
        """Test deleting non-existent folder"""
        res = client.delete('/api/folders/99999',
            headers=auth_headers
        )
        assert res.status_code == 404