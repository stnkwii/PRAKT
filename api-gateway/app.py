from flask import Flask, request, jsonify
import requests
import jwt
from functools import wraps
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Конфигурация сервисов
SERVICES = {
    'auth': 'http://auth-service:5001',
    'users': 'http://user-service:5002',
    'tenders': 'http://tender-service:5003',
    'documents': 'http://document-service:5004',
    'notifications': 'http://notification-service:5005',
    'analytics': 'http://analytics-service:5006'
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401
        
        try:
            # Извлекаем токен из формата "Bearer TOKEN"
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            # Декодируем токен
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = data['user_id']
            request.user_role = data['role']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Срок действия токена истек'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Неверный токен'}), 401
        except Exception as e:
            logger.error(f"Ошибка проверки токена: {str(e)}")
            return jsonify({'error': 'Ошибка аутентификации'}), 401
        
        return f(*args, **kwargs)
    return decorated

@app.before_request
def log_request_info():
    logger.info(f'{datetime.now()} - {request.method} {request.path}')

# Публичные маршруты (не требуют аутентификации)
@app.route('/api/auth/register', methods=['POST'])
def register():
    return proxy_to_service('auth', 'auth/register')

@app.route('/api/auth/login', methods=['POST'])
def login():
    return proxy_to_service('auth', 'auth/login')

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    return proxy_to_service('auth', 'auth/verify')

@app.route('/api/tenders', methods=['GET'])
def get_public_tenders():
    return proxy_to_service('tenders', 'tenders')

@app.route('/api/tenders/<int:tender_id>', methods=['GET'])
def get_tender_detail(tender_id):
    return proxy_to_service('tenders', f'tenders/{tender_id}')

# Защищенные маршруты (требуют аутентификации)
@app.route('/api/users/profile', methods=['GET'])
@token_required
def get_user_profile():
    return proxy_to_service('users', 'users/profile')

@app.route('/api/users/profile', methods=['PUT'])
@token_required
def update_user_profile():
    return proxy_to_service('users', 'users/profile')

@app.route('/api/users/list', methods=['GET'])
@token_required
def get_users_list():
    return proxy_to_service('users', 'users/list')

@app.route('/api/tenders', methods=['POST'])
@token_required
def create_tender():
    return proxy_to_service('tenders', 'tenders')

@app.route('/api/tenders/<int:tender_id>/applications', methods=['POST'])
@token_required
def create_application(tender_id):
    return proxy_to_service('tenders', f'tenders/{tender_id}/applications')

def proxy_to_service(service_name, path):
    if service_name not in SERVICES:
        return jsonify({'error': 'Сервис не найден'}), 404
    
    service_url = f"{SERVICES[service_name]}/{path}"
    
    try:
        # Проксирование запроса к соответствующему сервису
        headers = {
            key: value for key, value in request.headers 
            if key.lower() not in ['host', 'content-length']
        }
        
        # Добавляем информацию о пользователе в заголовки для защищенных маршрутов
        if hasattr(request, 'user_id'):
            headers['X-User-ID'] = str(request.user_id)
            headers['X-User-Role'] = request.user_role
        
        response = requests.request(
            method=request.method,
            url=service_url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30
        )
        
        # Логируем ответ
        logger.info(f'Response from {service_name}: {response.status_code}')
        
        # Возвращаем ответ от сервиса
        return (response.content, response.status_code, dict(response.headers))
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Таймаут запроса к сервису'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Сервис недоступен'}), 503
    except Exception as e:
        logger.error(f"Ошибка проксирования: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Health check endpoints
@app.route('/health')
def health_check():
    health_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            health_status[service_name] = 'healthy' if response.status_code == 200 else 'unhealthy'
        except:
            health_status[service_name] = 'unreachable'
    
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'services': health_status
    })

@app.route('/')
def api_home():
    return jsonify({
        'message': 'Tender System API Gateway',
        'version': '1.0',
        'endpoints': {
            'auth': {
                'POST /api/auth/register': 'Регистрация пользователя',
                'POST /api/auth/login': 'Вход в систему',
                'POST /api/auth/verify': 'Проверка токена'
            },
            'tenders': {
                'GET /api/tenders': 'Получить список тендеров',
                'GET /api/tenders/{id}': 'Получить детали тендера',
                'POST /api/tenders': 'Создать тендер (требует аутентификации)',
                'POST /api/tenders/{id}/applications': 'Подать заявку (требует аутентификации)'
            },
            'users': {
                'GET /api/users/profile': 'Получить профиль (требует аутентификации)',
                'PUT /api/users/profile': 'Обновить профиль (требует аутентификации)',
                'GET /api/users/list': 'Список пользователей (только для admin/manager)'
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)