from flask import Flask, request, jsonify
import mysql.connector
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-users",
        user="root",
        password="password",
        database="users_db",
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

def init_db():
    """Инициализация базы данных пользователей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Таблица профилей пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                company VARCHAR(255),
                position VARCHAR(100),
                avatar_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            )
        ''')
        
        # Таблица настроек пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                email_notifications BOOLEAN DEFAULT TRUE,
                sms_notifications BOOLEAN DEFAULT FALSE,
                language VARCHAR(10) DEFAULT 'ru',
                timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        logger.info("База данных пользователей инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации БД пользователей: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@app.route('/users/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user-service'})

@app.route('/users/profile', methods=['GET'])
def get_profile():
    try:
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'error': 'Идентификатор пользователя отсутствует'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT u.id, u.email, u.role, u.created_at,
                   p.first_name, p.last_name, p.phone, p.company, p.position, p.avatar_url,
                   s.email_notifications, s.sms_notifications, s.language, s.timezone
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            LEFT JOIN user_settings s ON u.id = s.user_id
            WHERE u.id = %s
        ''', (user_id,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        return jsonify(user)
        
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/users/profile', methods=['PUT'])
def update_profile():
    try:
        user_id = request.headers.get('X-User-ID')
        data = request.get_json()
        
        if not user_id:
            return jsonify({'error': 'Идентификатор пользователя отсутствует'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновление профиля
        cursor.execute('''
            INSERT INTO user_profiles (user_id, first_name, last_name, phone, company, position)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            first_name = VALUES(first_name),
            last_name = VALUES(last_name),
            phone = VALUES(phone),
            company = VALUES(company),
            position = VALUES(position),
            updated_at = CURRENT_TIMESTAMP
        ''', (
            user_id, 
            data.get('first_name'), 
            data.get('last_name'), 
            data.get('phone'), 
            data.get('company'), 
            data.get('position')
        ))
        
        # Обновление настроек
        if 'email_notifications' in data or 'sms_notifications' in data:
            cursor.execute('''
                INSERT INTO user_settings (user_id, email_notifications, sms_notifications, language, timezone)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                email_notifications = VALUES(email_notifications),
                sms_notifications = VALUES(sms_notifications),
                language = VALUES(language),
                timezone = VALUES(timezone),
                updated_at = CURRENT_TIMESTAMP
            ''', (
                user_id,
                data.get('email_notifications', True),
                data.get('sms_notifications', False),
                data.get('language', 'ru'),
                data.get('timezone', 'Europe/Moscow')
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Профиль пользователя {user_id} обновлен")
        
        return jsonify({'message': 'Профиль успешно обновлен'})
        
    except Exception as e:
        logger.error(f"Ошибка обновления профиля: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/users/list', methods=['GET'])
def get_users():
    try:
        user_role = request.headers.get('X-User-Role')
        
        # Проверка прав доступа
        if user_role not in ['admin', 'manager']:
            return jsonify({'error': 'Недостаточно прав'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Подсчет общего количества
        query_count = '''
            SELECT COUNT(*) as total FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE 1=1
        '''
        params_count = []
        
        if search:
            query_count += ' AND (u.email LIKE %s OR p.first_name LIKE %s OR p.last_name LIKE %s)'
            search_param = f'%{search}%'
            params_count.extend([search_param, search_param, search_param])
        
        cursor.execute(query_count, params_count)
        total = cursor.fetchone()['total']
        
        # Получение пользователей
        query = '''
            SELECT u.id, u.email, u.role, u.created_at, u.is_active,
                   p.first_name, p.last_name, p.phone, p.company
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE 1=1
        '''
        params = []
        
        if search:
            query += ' AND (u.email LIKE %s OR p.first_name LIKE %s OR p.last_name LIKE %s)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        query += ' ORDER BY u.created_at DESC LIMIT %s OFFSET %s'
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/users/<int:target_user_id>', methods=['PUT'])
def update_user_by_admin(target_user_id):
    try:
        user_role = request.headers.get('X-User-Role')
        
        if user_role != 'admin':
            return jsonify({'error': 'Только администратор может изменять пользователей'}), 403
        
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновление роли и статуса пользователя
        if 'role' in data or 'is_active' in data:
            update_fields = []
            update_params = []
            
            if 'role' in data:
                update_fields.append('role = %s')
                update_params.append(data['role'])
            
            if 'is_active' in data:
                update_fields.append('is_active = %s')
                update_params.append(data['is_active'])
            
            update_params.append(target_user_id)
            
            cursor.execute(f'''
                UPDATE users SET {', '.join(update_fields)} 
                WHERE id = %s
            ''', update_params)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Пользователь {target_user_id} обновлен администратором")
        
        return jsonify({'message': 'Пользователь успешно обновлен'})
        
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Инициализация БД при запуске
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)