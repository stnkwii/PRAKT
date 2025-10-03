from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import random

app = Flask(__name__)
app.secret_key = 'dev-key-for-testing'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Главная страница
@app.route('/')
def index():
    breadcrumbs = [{'name': 'Главная', 'url': '#'}]
    return render_template('index.html', breadcrumbs=breadcrumbs)

# Все остальные страницы
@app.route('/about')
def about():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'О системе', 'url': '#'}
    ]
    return render_template('about.html', breadcrumbs=breadcrumbs)

@app.route('/contact')
def contact():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Контакты', 'url': '#'}
    ]
    return render_template('contact.html', breadcrumbs=breadcrumbs)

@app.route('/documentation')
def documentation():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Документация', 'url': '#'}
    ]
    return render_template('documentation.html', breadcrumbs=breadcrumbs)

@app.route('/faq')
def faq():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'FAQ', 'url': '#'}
    ]
    return render_template('faq.html', breadcrumbs=breadcrumbs)

@app.route('/news')
def news():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Новости', 'url': '#'}
    ]
    return render_template('news.html', breadcrumbs=breadcrumbs)

@app.route('/tenders')
def tenders():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Тендеры', 'url': '#'}
    ]
    return render_template('tenders.html', breadcrumbs=breadcrumbs)

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

@app.route('/login')
def login():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Вход', 'url': '#'}
    ]
    return render_template('login.html', breadcrumbs=breadcrumbs)

@app.route('/register')
def register():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Регистрация', 'url': '#'}
    ]
    return render_template('register.html', breadcrumbs=breadcrumbs)

@app.route('/dashboard')
def dashboard():
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Личный кабинет', 'url': '#'}
    ]
    return render_template('user_dashboard.html', breadcrumbs=breadcrumbs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Mock API endpoints для тестирования
@app.route('/api/auth/login', methods=['POST'])
def mock_login():
    return jsonify({
        'token': 'mock-jwt-token-123',
        'user_id': 1,
        'role': 'client',
        'email': 'test@example.com'
    })

@app.route('/api/auth/register', methods=['POST'])
def mock_register():
    return jsonify({
        'message': 'User registered successfully',
        'user_id': random.randint(1000, 9999),
        'token': 'mock-jwt-token-456',
        'role': 'client'
    })

@app.route('/api/tenders')
def mock_tenders():
    return jsonify({
        'tenders': [
            {
                'id': 1,
                'title': 'Тестовый тендер 1',
                'description': 'Описание тестового тендера',
                'customer': 'Тестовая компания',
                'budget': 100000,
                'currency': 'RUB',
                'status': 'active',
                'deadline': '2024-12-31T23:59:59',
                'created_at': '2024-01-01T10:00:00',
                'applications_count': 5
            },
            {
                'id': 2,
                'title': 'Тестовый тендер 2',
                'description': 'Еще один тестовый тендер',
                'customer': 'Другая компания',
                'budget': 500000,
                'currency': 'RUB', 
                'status': 'active',
                'deadline': '2024-12-25T23:59:59',
                'created_at': '2024-01-02T10:00:00',
                'applications_count': 3
            }
        ],
        'total': 2,
        'page': 1,
        'per_page': 10,
        'total_pages': 1
    })

if __name__ == '__main__':
    # Принудительно перезагружаем шаблоны
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=True)