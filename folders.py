from flask import request, jsonify
from database import get_db


def get_folders(user_id):
    conn = get_db()
    try:
        folders = conn.execute(
            '''SELECT f.id, f.name, f.created_at,
                      COUNT(b.id) as bookmark_count
               FROM folders f
               LEFT JOIN bookmarks b ON f.id = b.folder_id
               WHERE f.user_id = ?
               GROUP BY f.id
               ORDER BY f.created_at DESC''',
            (user_id,)
        ).fetchall()

        return jsonify({
            'folders': [dict(f) for f in folders]
        })
    finally:
        conn.close()


def create_folder(user_id):
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Folder name is required'}), 400

    name = data['name'].strip()

    conn = get_db()
    try:
        existing = conn.execute(
            'SELECT id FROM folders WHERE user_id = ? AND name = ?',
            (user_id, name)
        ).fetchone()

        if existing:
            return jsonify({'error': 'Folder name already exists'}), 409

        cursor = conn.execute(
            'INSERT INTO folders (user_id, name) VALUES (?, ?)',
            (user_id, name)
        )
        conn.commit()

        return jsonify({
            'message'  : 'Folder created!',
            'folder_id': cursor.lastrowid,
            'name'     : name
        }), 201
    finally:
        conn.close()


def rename_folder(user_id, folder_id):
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'New folder name is required'}), 400

    name = data['name'].strip()

    conn = get_db()
    try:
        folder = conn.execute(
            'SELECT id FROM folders WHERE id = ? AND user_id = ?',
            (folder_id, user_id)
        ).fetchone()

        if not folder:
            return jsonify({'error': 'Folder not found'}), 404

        conn.execute(
            'UPDATE folders SET name = ? WHERE id = ?',
            (name, folder_id)
        )
        conn.commit()

        return jsonify({'message': 'Folder renamed!', 'name': name})
    finally:
        conn.close()


def delete_folder(user_id, folder_id):
    conn = get_db()
    try:
        folder = conn.execute(
            'SELECT id FROM folders WHERE id = ? AND user_id = ?',
            (folder_id, user_id)
        ).fetchone()

        if not folder:
            return jsonify({'error': 'Folder not found'}), 404

        # delete bookmarks in folder
        conn.execute(
            'DELETE FROM bookmarks WHERE folder_id = ?',
            (folder_id,)
        )
        # delete folder
        conn.execute(
            'DELETE FROM folders WHERE id = ?',
            (folder_id,)
        )
        conn.commit()

        return jsonify({'message': 'Folder deleted!'})
    finally:
        conn.close()