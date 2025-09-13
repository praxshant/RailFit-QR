# backend/services/auth_service.py
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
import hashlib
from functools import wraps

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        # Demo users; in production use a database
        self.users = {
            'manufacturer': {
                'password': hashlib.sha256('mfg123'.encode()).hexdigest(),
                'role': 'manufacturer',
                'name': 'Railway Parts Manufacturer'
            },
            'vendor': {
                'password': hashlib.sha256('vendor123'.encode()).hexdigest(),
                'role': 'vendor',
                'name': 'Parts Vendor'
            },
            'official': {
                'password': hashlib.sha256('rail123'.encode()).hexdigest(),
                'role': 'railway_official',
                'name': 'Railway Official'
            }
        }

    def authenticate_user(self, username, password, role):
        if username in self.users:
            user = self.users[username]
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user['password'] == password_hash and user['role'] == role:
                payload = {
                    'user': username,
                    'role': user['role'],
                    'name': user['name'],
                    'exp': datetime.utcnow() + timedelta(hours=8)
                }
                token = jwt.encode(payload, self.secret_key, algorithm='HS256')
                return {
                    'success': True,
                    'token': token,
                    'user': {
                        'username': username,
                        'role': user['role'],
                        'name': user['name']
                    }
                }
        return {'success': False, 'message': 'Invalid credentials'}

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'success': True, 'user': payload}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid token'}


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Token missing'}), 401
            try:
                token = token.split(' ')[1] if ' ' in token else token
                auth_service = AuthService(current_app.config['JWT_SECRET_KEY'])
                result = auth_service.verify_token(token)
                if not result['success']:
                    return jsonify({'error': result['message']}), 401
                if result['user']['role'] != required_role:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                # Attach user to request for handlers
                request.user = result['user']
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 401
        return decorated
    return decorator
