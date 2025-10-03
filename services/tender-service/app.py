from flask import Flask, request, jsonify
import mysql.connector
import logging
from datetime import datetime
import json

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-tenders",
        user="root",
        password="password",
        database="tenders_db",
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

def init_db():
    """Инициализация базы данных тендеров"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Таблица тендеров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                customer VARCHAR(255) NOT NULL,
                budget DECIMAL(15,2),
                currency VARCHAR(3) DEFAULT 'RUB',
                status ENUM('draft', 'active', 'cancelled', 'completed') DEFAULT 'draft',
                tender_type ENUM('open', 'closed', 'limited') DEFAULT 'open',
                deadline DATETIME,
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_deadline (deadline),
                INDEX idx_created_by (created_by)
            )
        ''')
        
        # Таблица заявок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tender_id INT NOT NULL,
                user_id INT NOT NULL,
                proposal TEXT,
                price DECIMAL(15,2),
                status ENUM('submitted', 'reviewed', 'accepted', 'rejected') DEFAULT 'submitted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (tender_id) REFERENCES tenders(id) ON DELETE CASCADE,
                UNIQUE KEY unique_application (tender_id, user_id),
                INDEX idx_tender_id (tender_id),
                INDEX idx_user_id (user_id)
            )
        ''')
        
        # Таблица документов тендера
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tender_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tender_id INT NOT NULL,
                document_name VARCHAR(255) NOT NULL,
                document_path VARCHAR(500),
                file_size INT,
                uploaded_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tender_id) REFERENCES tenders(id) ON DELETE CASCADE
            )
        ''')
        
        # Создание тестовых данных
        cursor.execute('''
            INSERT IGNORE INTO tenders 
            (title, description, customer, budget, status, deadline, created_by) 
            VALUES 
            ('Поставка компьютерной техники', 'Закупка компьютеров и периферии для офиса', 'ООО Ромашка', 500000.00, 'active', DATE_ADD(NOW(), INTERVAL 30 DAY), 1),
            ('Ремонт офисных помещений', 'Капитальный ремонт офиса площадью 200 кв.м.', 'ЗАО Весна', 1500000.00, 'active', DATE_ADD(NOW(), INTERVAL 45 DAY), 1),
            ('Разработка веб-портала', 'Создание корпоративного портала с системой документооборота', 'ИП Иванов', 300000.00, 'draft', DATE_ADD(NOW(), INTERVAL 60 DAY), 1)
        ''')
        
        conn.commit()
        logger.info("База данных тендеров инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации БД тендеров: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@app.route('/tenders/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'tender-service'})

@app.route('/tenders', methods=['GET'])
def get_tenders():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'active')
        search = request.args.get('search', '')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Подсчет общего количества
        query_count = 'SELECT COUNT(*) as total FROM tenders WHERE 1=1'
        params_count = []
        
        if status:
            query_count += ' AND status = %s'
            params_count.append(status)
        
        if search:
            query_count += ' AND (title LIKE %s OR description LIKE %s OR customer LIKE %s)'
            search_param = f'%{search}%'
            params_count.extend([search_param, search_param, search_param])
        
        cursor.execute(query_count, params_count)
        total = cursor.fetchone()['total']
        
        # Получение тендеров
        query = '''
            SELECT t.*, 
                   u.email as creator_email,
                   (SELECT COUNT(*) FROM applications a WHERE a.tender_id = t.id) as applications_count
            FROM tenders t
            LEFT JOIN users u ON t.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND t.status = %s'
            params.append(status)
        
        if search:
            query += ' AND (t.title LIKE %s OR t.description LIKE %s OR t.customer LIKE %s)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        query += ' ORDER BY t.created_at DESC LIMIT %s OFFSET %s'
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        tenders = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'tenders': tenders,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения списка тендеров: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/tenders', methods=['POST'])
def create_tender():
    try:
        user_id = request.headers.get('X-User-ID')
        user_role = request.headers.get('X-User-Role')
        
        if user_role not in ['admin', 'manager']:
            return jsonify({'error': 'Недостаточно прав для создания тендера'}), 403
        
        data = request.get_json()
        
        # Валидация обязательных полей
        required_fields = ['title', 'customer', 'deadline']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле {field} обязательно'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tenders 
            (title, description, customer, budget, currency, status, tender_type, deadline, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['title'],
            data.get('description', ''),
            data['customer'],
            data.get('budget'),
            data.get('currency', 'RUB'),
            data.get('status', 'draft'),
            data.get('tender_type', 'open'),
            data['deadline'],
            user_id
        ))
        
        tender_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Создан новый тендер {tender_id} пользователем {user_id}")
        
        # Здесь будет вызов сервиса уведомлений
        # notification_service.notify_new_tender(tender_id)
        
        return jsonify({
            'message': 'Тендер успешно создан',
            'tender_id': tender_id
        }), 201
        
    except Exception as e:
        logger.error(f"Ошибка создания тендера: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/tenders/<int:tender_id>', methods=['GET'])
def get_tender_detail(tender_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT t.*, u.email as creator_email
            FROM tenders t
            LEFT JOIN users u ON t.created_by = u.id
            WHERE t.id = %s
        ''', (tender_id,))
        
        tender = cursor.fetchone()
        
        if not tender:
            return jsonify({'error': 'Тендер не найден'}), 404
        
        # Получение документов тендера
        cursor.execute('''
            SELECT * FROM tender_documents WHERE tender_id = %s
        ''', (tender_id,))
        documents = cursor.fetchall()
        
        tender['documents'] = documents
        
        cursor.close()
        conn.close()
        
        return jsonify(tender)
        
    except Exception as e:
        logger.error(f"Ошибка получения тендера: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/tenders/<int:tender_id>/applications', methods=['POST'])
def create_application(tender_id):
    try:
        user_id = request.headers.get('X-User-ID')
        data = request.get_json()
        
        if not data.get('proposal') or not data.get('price'):
            return jsonify({'error': 'Предложение и цена обязательны'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли тендер и активен ли он
        cursor.execute('SELECT status FROM tenders WHERE id = %s', (tender_id,))
        tender = cursor.fetchone()
        
        if not tender:
            return jsonify({'error': 'Тендер не найден'}), 404
        
        if tender[0] != 'active':
            return jsonify({'error': 'Тендер не активен'}), 400
        
        # Проверяем, не подавал ли пользователь уже заявку
        cursor.execute('''
            SELECT id FROM applications WHERE tender_id = %s AND user_id = %s
        ''', (tender_id, user_id))
        
        if cursor.fetchone():
            return jsonify({'error': 'Вы уже подали заявку на этот тендер'}), 400
        
        # Создаем заявку
        cursor.execute('''
            INSERT INTO applications (tender_id, user_id, proposal, price)
            VALUES (%s, %s, %s, %s)
        ''', (tender_id, user_id, data['proposal'], data['price']))
        
        application_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Создана заявка {application_id} на тендер {tender_id} пользователем {user_id}")
        
        return jsonify({
            'message': 'Заявка успешно подана',
            'application_id': application_id
        }), 201
        
    except Exception as e:
        logger.error(f"Ошибка создания заявки: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Инициализация БД при запуске
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)