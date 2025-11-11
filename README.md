Руководство по запуску проекта
Предварительные требования
Docker

Docker Compose

Минимум 4 ГБ оперативной памяти

2+ ядра процессора

Быстрый старт
1. Запуск всех сервисов
bash
# Запуск в фоновом режиме
docker-compose up -d

# Или с просмотром логов в реальном времени
docker-compose up
2. Проверка статуса сервисов
bash
# Проверить статус всех контейнеров
docker-compose ps

# Или более подробная информация
docker-compose ps --services
3. Просмотр логов
bash
# Все логи в реальном времени
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f frontend
docker-compose logs -f api-gateway
docker-compose logs -f backend
Доступ к приложению
После успешного запуска откройте в браузере:

Frontend приложение: http://localhost:8080

API Gateway: http://localhost:5000

Health check: http://localhost:5000/health

Тестовые пользователи
Для тестирования системы используйте следующие учетные записи:

Администратор
Email: admin@sys-sec.ru

Пароль: admin123

Доступ: Полные права на управление системой

Менеджер
Email: manager@sys-sec.ru

Пароль: manager123

Доступ: Управление клиентами и отчетность

Клиент
Email: client@sys-sec.ru

Пароль: client123

Доступ: Личный кабинет клиента

Управление сервисами
Остановка сервисов
bash
# Остановка с сохранением данных
docker-compose down

# Полная остановка с удалением volumes
docker-compose down -v
Перезапуск
bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart frontend
Обновление
bash
# Пересборка и перезапуск
docker-compose up -d --build

# Принудительная пересборка
docker-compose build --no-cache
Мониторинг и отладка
Проверка здоровья системы
bash
# Проверить health check
curl http://localhost:5000/health

# Или в браузере
open http://localhost:5000/health
Просмотр ресурсов
bash
# Использование ресурсов контейнерами
docker stats

# Детальная информация о контейнерах
docker-compose ps -a
Возможные проблемы и решения
Порт уже занят
Если порты 8080 или 5000 заняты, измените настройки в docker-compose.yml:

yaml
ports:
  - "8081:8080"  # вместо 8080:8080
Недостаточно памяти
bash
# Очистка неиспользуемых ресурсов
docker system prune

# Очистка volumes
docker volume prune
Проблемы с базой данных
bash
# Пересоздать базу данных
docker-compose down -v
docker-compose up -d
Структура сервисов
frontend: Веб-интерфейс (React/Vue/Angular)

api-gateway: API Gateway на порту 5000

backend: Основной бэкенд сервис

database: База данных PostgreSQL

redis: Кэш и сессии

Разработка
Локальная разработка
bash
# Запуск только базы данных и зависимостей
docker-compose up -d database redis

# Запуск фронтенда в режиме разработки
cd frontend && npm run dev

# Запуск бэкенда в режиме разработки  
cd backend && npm run dev
Переменные окружения
Создайте файл .env для настройки параметров:

env
DATABASE_URL=postgresql://user:pass@database:5432/app
REDIS_URL=redis://redis:6379
JWT_SECRET=your-secret-key
Поддержка
При возникновении проблем:

Проверьте логи: docker-compose logs -f

Убедитесь, что все контейнеры запущены: docker-compose ps

Проверьте health check: http://localhost:5000/health

Перезапустите сервисы: docker-compose restart

Для полной переустановки:

bash
docker-compose down -v
docker-compose up -d
