from flask import Flask
from flask_cors import CORS
import config
from database import init_db
from auth import register, login

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

with app.app_context():
    init_db()

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)