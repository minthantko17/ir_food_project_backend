from flask import request, jsonify
from database import get_db
from search_engine import df_recipes


def get_recipe_details(recipe_id):
    if df_recipes is None:
        return None
    recipe = df_recipes[df_recipes['RecipeId'] == recipe_id]
    if recipe.empty:
        return None
    recipe = recipe.iloc[0]
    return {
        'recipe_id': int(recipe['RecipeId']),
        'name': recipe['Name'],
        'description': recipe['Description'],
        'category': recipe['RecipeCategory'],
        'rating': float(recipe['AggregatedRating']),
        'review_count': int(recipe['ReviewCount']),
        'image_url': recipe['image_url'],
        'ingredients': recipe['ingredients_str'],
        'instructions': recipe['instructions_str'],
    }

#bookmark recipes to folder with rating
def add_bookmark(user_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    recipe_id = data.get('recipe_id')
    folder_id = data.get('folder_id')
    rating = data.get('rating', 0)

    if not recipe_id or not folder_id:
        return jsonify({'error': 'recipe_id and folder_id required'}), 400
    if rating not in [0, 1, 2, 3, 4, 5]:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

    conn = get_db()
    try:
        folder = conn.execute(
            'SELECT id FROM folders WHERE id = ? AND user_id = ?',
            (folder_id, user_id)
        ).fetchone()

        if not folder:
            return jsonify({'error': 'Folder not found'}), 404

        conn.execute(
            '''INSERT INTO bookmarks (user_id, folder_id, recipe_id, rating)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(folder_id, recipe_id)
               DO UPDATE SET rating = ?''', #update if already exists
            (user_id, folder_id, recipe_id, rating, rating)
        )
        conn.commit()

        return jsonify({'message': 'Bookmarked!'}), 201
    finally:
        conn.close()


def remove_bookmark(user_id, bookmark_id):
    conn = get_db()
    try:
        bookmark = conn.execute(
            'SELECT id FROM bookmarks WHERE id = ? AND user_id = ?',
            (bookmark_id, user_id)
        ).fetchone()

        if not bookmark:
            return jsonify({'error': 'Bookmark not found'}), 404

        conn.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        conn.commit()

        return jsonify({'message': 'Bookmark removed!'})
    finally:
        conn.close()


# all bookmarks in one place :")
def get_all_bookmarks(user_id):
    conn = get_db()
    try:
        bookmarks = conn.execute(
            '''SELECT b.id, b.recipe_id, b.rating, b.created_at,
                      f.name as folder_name, f.id as folder_id
               FROM bookmarks b
               JOIN folders f ON b.folder_id = f.id
               WHERE b.user_id = ?
               ORDER BY b.rating DESC, b.created_at DESC''',
            (user_id,)
        ).fetchall()

        results = []
        for b in bookmarks:
            b_dict  = dict(b)
            details = get_recipe_details(b_dict['recipe_id'])
            if details:
                b_dict.update(details)
            results.append(b_dict)

        return jsonify({'bookmarks': results})
    finally:
        conn.close()


# bookmark from specific folder
def get_folder_bookmarks(user_id, folder_id):
    conn = get_db()
    try:
        folder = conn.execute(
            'SELECT id, name FROM folders WHERE id = ? AND user_id = ?',
            (folder_id, user_id)
        ).fetchone()

        if not folder:
            return jsonify({'error': 'Folder not found'}), 404

        bookmarks = conn.execute(
            '''SELECT b.id, b.recipe_id, b.rating, b.created_at
               FROM bookmarks b
               WHERE b.folder_id = ? AND b.user_id = ?
               ORDER BY b.rating DESC''',
            (folder_id, user_id)
        ).fetchall()

        results = []
        for b in bookmarks:
            b_dict  = dict(b)
            details = get_recipe_details(b_dict['recipe_id'])
            if details:
                b_dict.update(details)
            results.append(b_dict)

        return jsonify({
            'folder'   : dict(folder),
            'bookmarks': results
        })
    finally:
        conn.close()