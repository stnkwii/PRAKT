from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['API_GATEWAY_URL'] = 'http://localhost:5000/api'

# Mock данные для тестирования
MOCK_TENDERS = [
    {
        'id': 1,
        'title': 'Разработка системы защиты информации',
        'description': 'Создание комплексной системы информационной безопасности для корпоративной сети предприятия. Включает анализ угроз, проектирование архитектуры безопасности, внедрение и настройку защитных механизмов.',
        'customer': 'ООО "Системная безопасность"',
        'budget': 2500000.00,
        'currency': 'RUB',
        'status': 'active',
        'tender_type': 'open',
        'deadline': '2024-12-31T23:59:59',
        'created_at': '2024-01-15T10:00:00',
        'applications_count': 3,
        'created_by': 1
    },
    {
        'id': 2,
        'title': 'Внедрение SIEM системы',
        'description': 'Установка и настройка системы мониторинга и управления событиями информационной безопасности. Включает интеграцию с существующей инфраструктурой, настройку правил корреляции, обучение персонала.',
        'customer': 'ООО "Системная безопасность"',
        'budget': 1500000.00,
        'currency': 'RUB',
        'status': 'active',
        'tender_type': 'open',
        'deadline': '2024-12-25T23:59:59',
        'created_at': '2024-01-10T14:30:00',
        'applications_count': 5,
        'created_by': 1
    },
    {
        'id': 3,
        'title': 'Аудит информационной безопасности',
        'description': 'Комплексный аудит системы информационной безопасности организации. Проверка соответствия требованиям регуляторов, анализ политик безопасности, тестирование на проникновение.',
        'customer': 'ООО "Системная безопасность"',
        'budget': 800000.00,
        'currency': 'RUB',
        'status': 'active',
        'tender_type': 'closed',
        'deadline': '2024-11-30T23:59:59',
        'created_at': '2024-01-05T09:15:00',
        'applications_count': 2,
        'created_by': 1
    },
    {
        'id': 4,
        'title': 'Разработка мобильного приложения безопасности',
        'description': 'Создание мобильного приложения для управления системами безопасности с функциями двухфакторной аутентификации и мониторинга событий.',
        'customer': 'ООО "Системная безопасность"',
        'budget': 1200000.00,
        'currency': 'RUB',
        'status': 'draft',
        'tender_type': 'open',
        'deadline': '2024-12-15T23:59:59',
        'created_at': '2024-01-20T16:45:00',
        'applications_count': 0,
        'created_by': 1
    }
]

def call_api(endpoint, method='GET', data=None):
    """Универсальная функция для вызова API с обработкой ошибок"""
    try:
        url = f"{app.config['API_GATEWAY_URL']}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=5)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=5)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=5)
        else:
            return None, 'Method not supported'
        
        return response.json(), response.status_code
        
    except requests.exceptions.ConnectionError:
        return None, 'API server is not available'
    except requests.exceptions.Timeout:
        return None, 'API request timeout'
    except Exception as e:
        return None, f'API error: {str(e)}'

# Главная страница
@app.route('/')
def index():
    breadcrumbs = [{'name': 'Главная', 'url': '#'}]
    
    # Пробуем получить тендеры из API, если не получается - используем mock данные
    tenders_data, status = call_api('tenders')
    if tenders_data:
        recent_tenders = tenders_data.get('tenders', [])[:3]
    else:
        recent_tenders = MOCK_TENDERS[:3]
    
    return render_template('index.html', breadcrumbs=breadcrumbs, recent_tenders=recent_tenders)

# Страница тендеров
@app.route('/tenders')
def tenders():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Тендеры', 'url': '#'}
    ]
    
    # Получаем параметры фильтрации
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'active')
    
    # Пробуем получить данные из API
    tenders_data, api_status = call_api(f'tenders?page={page}&status={status_filter}&search={search}')
    
    if tenders_data:
        tenders_list = tenders_data
    else:
        # Используем mock данные если API недоступно
        tenders_list = {
            'tenders': MOCK_TENDERS,
            'total': len(MOCK_TENDERS),
            'page': page,
            'per_page': 10,
            'total_pages': 1
        }
    
    return render_template('tenders.html', breadcrumbs=breadcrumbs, tenders_data=tenders_list)

# Детальная страница тендера
@app.route('/tenders/<int:tender_id>')
def tender_detail(tender_id):
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Тендеры', 'url': '/tenders'},
        {'name': f'Тендер {tender_id}', 'url': '#'}
    ]
    
    # Ищем тендер в mock данных
    tender = next((t for t in MOCK_TENDERS if t['id'] == tender_id), None)
    
    if not tender:
        # Если тендер не найден, показываем 404
        return render_template('404.html', breadcrumbs=breadcrumbs), 404
    
    return render_template('tender_detail.html', 
                         breadcrumbs=breadcrumbs, 
                         tender=tender,
                         now=datetime.now().isoformat())

# Страница услуг
@app.route('/services')
def services():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Услуги', 'url': '#'}
    ]
    return render_template('services.html', breadcrumbs=breadcrumbs)

# Страница о компании
@app.route('/about')
def about():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'О компании', 'url': '#'}
    ]
    return render_template('about.html', breadcrumbs=breadcrumbs)

# Контакты
@app.route('/contact')
def contact():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Контакты', 'url': '#'}
    ]
    return render_template('contact.html', breadcrumbs=breadcrumbs)

# Документация
@app.route('/documentation')
def documentation():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Документация', 'url': '#'}
    ]
    return render_template('documentation.html', breadcrumbs=breadcrumbs)

# FAQ
@app.route('/faq')
def faq():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'FAQ', 'url': '#'}
    ]
    return render_template('faq.html', breadcrumbs=breadcrumbs)

# Новости
@app.route('/news')
def news():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Новости', 'url': '#'}
    ]
    return render_template('news.html', breadcrumbs=breadcrumbs)

# Форма обратной связи
@app.route('/feedback')
def feedback():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Обратная связь', 'url': '#'}
    ]
    return render_template('feedback.html', breadcrumbs=breadcrumbs)

@app.route('/feedback/success')
def feedback_success():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Обратная связь', 'url': '/feedback'},
        {'name': 'Успешно', 'url': '#'}
    ]
    return render_template('feedback_success.html', breadcrumbs=breadcrumbs)

# Вход в систему
@app.route('/login')
def login():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Вход', 'url': '#'}
    ]
    return render_template('login.html', breadcrumbs=breadcrumbs)

# Регистрация
@app.route('/register')
def register():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Регистрация', 'url': '#'}
    ]
    return render_template('register.html', breadcrumbs=breadcrumbs)

# Личный кабинет
@app.route('/dashboard')
def dashboard():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Личный кабинет', 'url': '#'}
    ]
    
    # Проверяем авторизацию
    if not session.get('user_id'):
        return redirect('/login')
    
    # Определяем тип личного кабинета по роли
    user_role = session.get('user_role', 'client')
    
    if user_role == 'admin':
        return render_template('admin_dashboard.html', breadcrumbs=breadcrumbs)
    elif user_role == 'manager':
        return render_template('manager_dashboard.html', breadcrumbs=breadcrumbs)
    else:
        return render_template('user_dashboard.html', breadcrumbs=breadcrumbs)

# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# API endpoints для фронтенда
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Обработчик входа в систему"""
    try:
        data = request.get_json()
        
        # Пробуем отправить запрос к реальному API
        api_response, status = call_api('auth/login', 'POST', data)
        
        if api_response:
            # Если API отвечает, возвращаем его ответ
            # Сохраняем данные в сессию
            session['user_id'] = api_response.get('user_id')
            session['user_role'] = api_response.get('role')
            session['user_email'] = api_response.get('email')
            return jsonify(api_response), status
        else:
            # Если API недоступно, используем mock аутентификацию
            email = data.get('email', '')
            password = data.get('password', '')
            
            # Mock проверка credentials для всех трех учетных записей
            mock_users = {
                'admin@sys-sec.ru': {
                    'password': 'admin123',
                    'user_id': 1,
                    'role': 'admin',
                    'name': 'Администратор'
                },
                'manager@sys-sec.ru': {
                    'password': 'manager123', 
                    'user_id': 2,
                    'role': 'manager',
                    'name': 'Менеджер'
                },
                'client@sys-sec.ru': {
                    'password': 'client123',
                    'user_id': 3,
                    'role': 'client',
                    'name': 'Клиент'
                }
            }
            
            user = mock_users.get(email)
            
            if user and user['password'] == password:
                # Сохраняем данные в сессию
                session['user_id'] = user['user_id']
                session['user_role'] = user['role']
                session['user_email'] = email
                session['user_name'] = user['name']
                
                return jsonify({
                    'token': f'mock-jwt-token-{user["role"]}',
                    'user_id': user['user_id'],
                    'role': user['role'],
                    'email': email,
                    'name': user['name']
                })
            else:
                return jsonify({'error': 'Неверный email или пароль'}), 401
                
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Обработчик регистрации"""
    try:
        data = request.get_json()
        
        # Пробуем отправить запрос к реальному API
        api_response, status = call_api('auth/register', 'POST', data)
        
        if api_response:
            return jsonify(api_response), status
        else:
            # Mock регистрация
            email = data.get('email', '')
            password = data.get('password', '')
            role = data.get('role', 'client')
            
            # Простая валидация
            if not email or not password:
                return jsonify({'error': 'Email и пароль обязательны'}), 400
            
            if len(password) < 6:
                return jsonify({'error': 'Пароль должен содержать минимум 6 символов'}), 400
            
            # "Регистрируем" пользователя
            user_id = 1000  # mock ID
            session['user_id'] = user_id
            session['user_role'] = role
            session['user_email'] = email
            
            return jsonify({
                'message': 'Пользователь успешно зарегистрирован',
                'user_id': user_id,
                'token': 'mock-jwt-token-new-user',
                'role': role
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/api/tenders', methods=['GET'])
def api_tenders():
    """API для получения списка тендеров"""
    try:
        # Получаем параметры запроса
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        # Пробуем получить данные из реального API
        api_response, status_code = call_api('tenders')
        
        if api_response and 'tenders' in api_response:
            # Фильтрация данных от API
            filtered_tenders = api_response['tenders']
            
            if status:
                filtered_tenders = [t for t in filtered_tenders if t.get('status') == status]
            
            if search:
                search_lower = search.lower()
                filtered_tenders = [
                    t for t in filtered_tenders 
                    if search_lower in t.get('title', '').lower() or 
                       search_lower in t.get('description', '').lower() or
                       search_lower in t.get('customer', '').lower()
                ]
            
            # Пагинация
            total = len(filtered_tenders)
            total_pages = (total + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_tenders = filtered_tenders[start_idx:end_idx]
            
            return jsonify({
                'tenders': paginated_tenders,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            })
        else:
            # Возвращаем mock данные
            filtered_tenders = MOCK_TENDERS
            
            # Применяем фильтры к mock данным
            if status:
                filtered_tenders = [t for t in filtered_tenders if t.get('status') == status]
            
            if search:
                search_lower = search.lower()
                filtered_tenders = [
                    t for t in filtered_tenders 
                    if search_lower in t.get('title', '').lower() or 
                       search_lower in t.get('description', '').lower() or
                       search_lower in t.get('customer', '').lower()
                ]
            
            total = len(filtered_tenders)
            total_pages = (total + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_tenders = filtered_tenders[start_idx:end_idx]
            
            return jsonify({
                'tenders': paginated_tenders,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            })
            
    except Exception as e:
        print(f"Error in api_tenders: {e}")
        # Возвращаем mock данные в случае ошибки
        return jsonify({
            'tenders': MOCK_TENDERS,
            'total': len(MOCK_TENDERS),
            'page': 1,
            'per_page': 10,
            'total_pages': 1
        })

@app.route('/api/users/profile', methods=['GET'])
def api_user_profile():
    """API для получения профиля пользователя"""
    # Mock данные профиля
    profile_data = {
        'id': session.get('user_id', 1),
        'email': session.get('user_email', 'user@example.com'),
        'role': session.get('user_role', 'client'),
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'phone': '+7 (999) 123-45-67',
        'company': 'ООО "Рога и копыта"',
        'position': 'Менеджер по закупкам'
    }
    
    return jsonify(profile_data)

# Страница 404
@app.route('/404')
def page_not_found():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Страница не найдена', 'url': '#'}
    ]
    return render_template('404.html', breadcrumbs=breadcrumbs)

# Страница управления пользователями (админка)
@app.route('/admin/users')
def admin_users():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель администратора', 'url': '/dashboard'},
        {'name': 'Управление пользователями', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] != 'admin':
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('admin_users.html', breadcrumbs=breadcrumbs)

# Страница управления тендерами (админка)
@app.route('/admin/tenders')
def admin_tenders():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель администратора', 'url': '/dashboard'},
        {'name': 'Управление тендерами', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] != 'admin':
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('admin_tenders.html', breadcrumbs=breadcrumbs)

# Страница системных настроек (админка)
@app.route('/admin/settings')
def admin_settings():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель администратора', 'url': '/dashboard'},
        {'name': 'Системные настройки', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] != 'admin':
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('admin_settings.html', breadcrumbs=breadcrumbs)

# Страница отчетов и аналитики (админка)
@app.route('/admin/reports')
def admin_reports():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель администратора', 'url': '/dashboard'},
        {'name': 'Отчеты и аналитика', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] != 'admin':
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('admin_reports.html', breadcrumbs=breadcrumbs)

# Страница тендеров менеджера
@app.route('/manager/tenders')
def manager_tenders():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель менеджера', 'url': '/dashboard'},
        {'name': 'Мои тендеры', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] not in ['admin', 'manager']:
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('manager_tenders.html', breadcrumbs=breadcrumbs)

# Страница заявок менеджера
@app.route('/manager/applications')
def manager_applications():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель менеджера', 'url': '/dashboard'},
        {'name': 'Заявки', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] not in ['admin', 'manager']:
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('manager_applications.html', breadcrumbs=breadcrumbs)

# Страница создания тендера
@app.route('/manager/tenders/create')
def create_tender():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Панель менеджера', 'url': '/dashboard'},
        {'name': 'Создать тендер', 'url': '#'}
    ]
    
    # Проверяем авторизацию и права
    auth = check_auth()
    if not auth['is_authenticated']:
        return redirect('/login')
    
    if auth['user_role'] not in ['admin', 'manager']:
        return render_template('403.html', breadcrumbs=breadcrumbs), 403
    
    return render_template('create_tender.html', breadcrumbs=breadcrumbs)

def check_auth():
    """Проверяет авторизацию пользователя"""
    return {
        'is_authenticated': bool(session.get('user_id')),
        'user_id': session.get('user_id'),
        'user_role': session.get('user_role'),
        'user_email': session.get('user_email'),
        'user_name': session.get('user_name')
    }

# Делаем функцию доступной во всех шаблонах
@app.context_processor
def utility_processor():
    return dict(check_auth=check_auth)

# Обработчик для всех несуществующих страниц
@app.errorhandler(404)
def not_found(error):
    return page_not_found()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)