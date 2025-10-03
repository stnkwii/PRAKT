#!/usr/bin/env python3
"""
Скрипт запуска тестов для системы тендерных закупок
"""

import unittest
import sys
import os
import time
import requests

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(__file__))

def check_services_availability():
    """Проверка доступности сервисов перед тестированием"""
    print("ПРОВЕРКА ДОСТУПНОСТИ СЕРВИСОВ...")
    
    services = {
        "API Gateway": "http://localhost:5000/health",
        "Frontend": "http://localhost:8080",
        "Auth Service": "http://localhost:5001/auth/health",
        "User Service": "http://localhost:5002/users/health", 
        "Tender Service": "http://localhost:5003/tenders/health"
    }
    
    all_available = True
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   [OK] {service_name}: Доступен")
            else:
                print(f"   [ERROR] {service_name}: Недоступен (код: {response.status_code})")
                all_available = False
        except Exception as e:
            print(f"   [ERROR] {service_name}: Ошибка подключения - {e}")
            all_available = False
    
    return all_available

def run_all_tests():
    """Запуск всех тестов через discovery"""
    print("АВТОМАТИЧЕСКИЙ ПОИСК И ЗАПУСК ТЕСТОВ...")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Используем базовый runner без специальных символов
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result

if __name__ == '__main__':
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ ТЕНДЕРНЫХ ЗАКУПОК")
    print("=" * 60)
    
    # Проверяем доступность сервисов
    if not check_services_availability():
        print("\nВНИМАНИЕ: Не все сервисы доступны. Тесты могут завершиться с ошибками.")
        print("   Запустите сервисы командой: docker-compose up -d")
        response = input("   Продолжить тестирование? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Запускаем тесты
    start_time = time.time()
    
    try:
        main_result = run_all_tests()
    except UnicodeEncodeError as e:
        print(f"ОШИБКА КОДИРОВКИ: {e}")
        print("Перезапустите с правильной кодировкой или используйте PowerShell")
        sys.exit(1)
    
    end_time = time.time()
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    if main_result:
        total_tests = main_result.testsRun
        total_failures = len(main_result.failures)
        total_errors = len(main_result.errors)
        
        print(f"Общее время выполнения: {end_time - start_time:.2f} сек.")
        print(f"Всего тестов: {total_tests}")
        print(f"Успешно: {total_tests - total_failures - total_errors}")
        print(f"Провалено: {total_failures}")
        print(f"Ошибок: {total_errors}")
        
        if total_failures == 0 and total_errors == 0:
            print("\nВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            sys.exit(0)
        else:
            print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            sys.exit(1)
    else:
        print("НЕ УДАЛОСЬ ЗАПУСТИТЬ ТЕСТЫ")
        sys.exit(1)