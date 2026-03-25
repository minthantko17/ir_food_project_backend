from flask import Flask, request, jsonify
from flask_cors import CORS
import config
from database import init_db
from auth import register, login, login_required
from search_engine import load_search_engine, search as bm25_search

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# initialize database and search engine on startup
with app.app_context():
    init_db()
    load_search_engine()

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

    results = bm25_search(query)

    return jsonify({
        'query'  : query,
        'count'  : len(results),
        'results': results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)