from functools import wraps
from flask import request, jsonify
import jwt
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1] if ' ' in token else token
            jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'dev-secret'), algorithms=['HS256'])
        except Exception:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated
