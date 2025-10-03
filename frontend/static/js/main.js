// Управление темной темой
document.addEventListener('DOMContentLoaded', function() {
    const themeSwitch = document.getElementById('theme-checkbox');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Устанавливаем текущую тему
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    if (currentTheme === 'dark') {
        themeSwitch.checked = true;
    }
    
    // Обработчик переключения темы
    themeSwitch.addEventListener('change', function() {
        if (this.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Инициализация всех компонентов
    initializeComponents();
});

function initializeComponents() {
    // Инициализация tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Инициализация popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Утилиты для работы с API
const ApiClient = {
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },
    
    async get(url) {
        return this.request(url);
    },
    
    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
};

// Утилиты для уведомлений
const Notifications = {
    show(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Добавляем уведомление в начало контента
        const main = document.querySelector('main .container');
        if (main) {
            main.insertBefore(alert, main.firstChild);
            
            // Автоматически скрываем через 5 секунд
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }
};

// Функция для проверки доступности API
async function checkApiHealth() {
    try {
        const response = await fetch('/api/tenders');
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Функция для безопасного входа
async function safeLogin(email, password) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.token) {
            // Сохраняем токен и данные пользователя
            localStorage.setItem('token', data.token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_role', data.role);
            localStorage.setItem('user_email', data.email);
            if (data.name) {
                localStorage.setItem('user_name', data.name);
            }
            
            return { success: true, data: data };
        } else {
            return { 
                success: false, 
                error: data.error || 'Ошибка входа. Проверьте email и пароль.' 
            };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { 
            success: false, 
            error: 'Сервер недоступен. Используются демо-данные.' 
        };
    }
}

// Функция для безопасной регистрации
async function safeRegister(email, password, role) {
    try {
        const response = await ApiClient.post('/api/auth/register', {
            email: email,
            password: password,
            role: role
        });
        
        if (response.token) {
            // Сохраняем токен
            localStorage.setItem('token', response.token);
            localStorage.setItem('user_id', response.user_id);
            localStorage.setItem('user_role', response.role);
            localStorage.setItem('user_email', response.email);
            
            return { success: true, data: response };
        } else {
            return { success: false, error: response.error || 'Ошибка регистрации' };
        }
    } catch (error) {
        return { 
            success: false, 
            error: 'Сервер недоступен. Попробуйте позже.' 
        };
    }
}

// Экспортируем утилиты для использования в других скриптах
window.ApiClient = ApiClient;
window.Notifications = Notifications;
window.safeLogin = safeLogin;
window.safeRegister = safeRegister;
window.checkApiHealth = checkApiHealth;