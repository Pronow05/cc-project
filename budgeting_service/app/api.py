from flask import Flask, jsonify, request
from flask_cors import CORS
import db
from passlib.hash import pbkdf2_sha256
import time

app = Flask(__name__)
CORS(app)

# Track when the service started
SERVICE_START_TIME = time.time()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    uptime = time.time() - SERVICE_START_TIME
    return jsonify({
        'status': 'healthy',
        'service': 'budgeting',
        'uptime_seconds': uptime
    })

@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get all departments in a hierarchical structure"""
    conn = db.get_db_connection()
    departments = conn.execute('SELECT id, name, parent_id FROM Departments').fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    department_list = [{'id': d['id'], 'name': d['name'], 'parent_id': d['parent_id']} 
                       for d in departments]
    
    return jsonify(department_list)

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate a user with username and password"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    conn = db.get_db_connection()
    user = conn.execute(
        'SELECT id, username, hashed_password, department_id FROM Users WHERE username = ?', 
        (username,)
    ).fetchone()
    conn.close()
    
    if not user or not pbkdf2_sha256.verify(password, user['hashed_password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    return jsonify({
        'user_id': user['id'],
        'username': user['username'],
        'department_id': user['department_id']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 