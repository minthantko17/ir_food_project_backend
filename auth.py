import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import request, jsonify
import config
from database import get_db

def create_token(user_id, username):
    payload = {
        'user_id'  : user_id,
        'username' : username,
        'exp'      : datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS)
    }
    token = jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# middleware
def login_required(f):
    """Decorator to protect routes that need login
    Usage:
        @app.route('/api/something')
        @login_required
        def something():
            ...
    """
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # get token from request header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No token provided'}), 401

        # header format: "Bearer <token>"
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = verify_token(token)

        if payload is None:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # attach user info to request
        request.user_id  = payload['user_id']
        request.username = payload['username']
        return f(*args, **kwargs)
    return decorated


def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, hashed.decode('utf-8'))
        )
        conn.commit()

        # get new user id
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        token = create_token(user['id'], username)

        return jsonify({
            'message' : 'Registration successful',
            'token'   : token,
            'username': username
        }), 201

    except Exception as e:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        conn.close()


def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username'].strip()
    password = data['password']

    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            return jsonify({'error': 'User not found'}), 404
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Wrong password'}), 401

        token = create_token(user['id'], username)
        return jsonify({
            'message' : 'Login successful',
            'token'   : token,
            'username': username
        }), 200

    finally:
        conn.close()