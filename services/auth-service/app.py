from flask import Flask, request, jsonify
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from functools import wraps
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-auth",
        user="root",
        password="password",
        database="auth_db",
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'manager', 'client') DEFAULT 'client',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_role (role)
            )
        ''')
        
        # Создание администратора по умолчанию
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT IGNORE INTO users (email, password, role) 
            VALUES (%s, %s, %s)
        ''', ('admin@tender-system.ru', admin_password, 'admin'))
        
        conn.commit()
        logger.info("База данных аутентификации инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@app.route('/auth/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'auth-service'})

@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email и пароль обязательны'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        role = data.get('role', 'client')
        
        # Валидация email
        if '@' not in email or len(email) < 5:
            return jsonify({'error': 'Некорректный email'}), 400
        
        # Валидация пароля
        if len(password) < 6:
            return jsonify({'error': 'Пароль должен содержать минимум 6 символов'}), 400
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO users (email, password, role) VALUES (%s, %s, %s)',
            (email, hashed_password, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        # Генерация токена
        token = jwt.encode({
            'user_id': user_id,
            'role': role,
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        logger.info(f"Зарегистрирован новый пользователь: {email}")
        
        return jsonify({
            'message': 'Пользователь успешно зарегистрирован',
            'user_id': user_id,
            'token': token,
            'role': role
        }), 201
        
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email и пароль обязательны'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT id, email, password, role, is_active 
            FROM users 
            WHERE email = %s
        ''', (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Неверный email или пароль'}), 401
        
        if not user['is_active']:
            return jsonify({'error': 'Учетная запись заблокирована'}), 403
        
        if check_password_hash(user['password'], password):
            token = jwt.encode({
                'user_id': user['id'],
                'role': user['role'],
                'email': user['email'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            logger.info(f"Успешный вход пользователя: {email}")
            
            return jsonify({
                'token': token,
                'user_id': user['id'],
                'role': user['role'],
                'email': user['email']
            })
        
        return jsonify({'error': 'Неверный email или пароль'}), 401
        
    except Exception as e:
        logger.error(f"Ошибка входа: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/auth/verify', methods=['POST'])
def verify_token():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'valid': False, 'error': 'Токен отсутствует'}), 401
        
        token = auth_header.split(' ')[1]
        
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # Проверяем, существует ли пользователь в БД
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT id, is_active FROM users WHERE id = %s', (data['user_id'],))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user or not user['is_active']:
            return jsonify({'valid': False, 'error': 'Пользователь не найден или заблокирован'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': data['user_id'],
            'role': data['role'],
            'email': data['email']
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Срок действия токена истек'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Неверный токен'}), 401
    except Exception as e:
        logger.error(f"Ошибка проверки токена: {str(e)}")
        return jsonify({'valid': False, 'error': 'Ошибка проверки токена'}), 500

# Инициализация БД при запуске
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)