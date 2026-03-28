from flask import Flask, request, jsonify
from flask_cors import CORS
import config
from database import init_db
from auth import register, login, login_required
from search_engine import load_search_engine, search as bm25_search
from spell_check import load_spell_checker, correct_query
from folders import (
    get_folders, create_folder,
    rename_folder, delete_folder
)
from bookmarks import (
    add_bookmark, remove_bookmark, remove_bookmark_by_recipe,
    get_all_bookmarks, get_folder_bookmarks
)
from recommendations import (
    load_recommender,
    get_recommended_for_you,
    get_from_category,
    get_random_recipes,
    get_all_categories,
    get_folder_suggestions
)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})



# initialize database and search engine on startup
with app.app_context():
    init_db()
    load_search_engine()
    load_recommender()
    load_spell_checker()

# healthcheck
@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'message': 'Server is running!'}

# auth routes
@app.route('/api/auth/register', methods=['POST'])
def register_route():
    return register()

@app.route('/api/auth/login', methods=['POST'])
def login_route():
    return login()

# search route
@app.route('/api/search', methods=['GET'])
@login_required
def search_route():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    # spellcheck raw query
    spell_result = correct_query(query)

    # search with stemmed corrected query
    results = bm25_search(spell_result['search_query'])

    return jsonify({
        'original': spell_result['original'],
        'corrected': spell_result['corrected'],
        'has_correction': spell_result['has_correction'],
        'corrections': spell_result['corrections'],
        'count': len(results),
        'results': results
    })


# folders
@app.route('/api/folders', methods=['GET'])
@login_required
def folders_get():
    return get_folders(request.user_id)

@app.route('/api/folders', methods=['POST'])
@login_required
def folders_create():
    return create_folder(request.user_id)

@app.route('/api/folders/<int:folder_id>', methods=['PUT'])
@login_required
def folders_rename(folder_id):
    return rename_folder(request.user_id, folder_id)

@app.route('/api/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def folders_delete(folder_id):
    return delete_folder(request.user_id, folder_id)


# bookmarks
@app.route('/api/bookmarks', methods=['POST'])
@login_required
def bookmarks_add():
    return add_bookmark(request.user_id)

@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@login_required
def bookmarks_remove(bookmark_id):
    return remove_bookmark(request.user_id, bookmark_id)

@app.route('/api/bookmarks', methods=['GET'])
@login_required
def bookmarks_all():
    return get_all_bookmarks(request.user_id)

@app.route('/api/folders/<int:folder_id>/bookmarks', methods=['GET'])
@login_required
def folder_bookmarks(folder_id):
    return get_folder_bookmarks(request.user_id, folder_id)

@app.route('/api/bookmarks/recipe/<int:recipe_id>', methods=['DELETE'])
@login_required
def bookmarks_remove_recipe(recipe_id):
    return remove_bookmark_by_recipe(request.user_id, recipe_id)

# recomendations
@app.route('/api/landing', methods=['GET'])
@login_required
def landing():
    category = request.args.get('category', None)
    return jsonify({
        'recommended_for_you': get_recommended_for_you(request.user_id),
        'from_category': get_from_category(category),
        'random': get_random_recipes(),
    })

@app.route('/api/categories', methods=['GET'])
@login_required
def categories():
    return jsonify({'categories': get_all_categories()})

@app.route('/api/folders/<int:folder_id>/suggestions', methods=['GET'])
@login_required
def folder_suggestions(folder_id):
    result = get_folder_suggestions(request.user_id, folder_id)
    return jsonify(result)


# MAIN HERE ✋😞
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)