from flask import Flask
from flask_cors import CORS
import config
from database import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

# Allow React frontend to call this API
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

with app.app_context():
    init_db()

# --- Health check route (just to test server is running) ---
@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'message': 'Server is running!'}

# Routes will be added here in later commits:
# - auth routes      (feature/auth)
# - search routes    (feature/search)
# - bookmark routes  (feature/folders-bookmarks)
# - recommend routes (feature/recommendations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)