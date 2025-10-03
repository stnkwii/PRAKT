import pytest
import requests
import time
from datetime import datetime

@pytest.fixture(scope="session")
def api_gateway_url():
    return "http://localhost:5000"

@pytest.fixture(scope="session") 
def frontend_url():
    return "http://localhost:8080"

@pytest.fixture
def test_user():
    """Создание тестового пользователя"""
    return {
        "email": f"test_{int(datetime.now().timestamp())}@example.com",
        "password": "testpassword123",
        "role": "client"
    }

@pytest.fixture
def auth_token(api_gateway_url, test_user):
    """Получение auth token для тестов"""
    # Регистрация пользователя
    response = requests.post(
        f"{api_gateway_url}/api/auth/register",
        json=test_user
    )
    
    if response.status_code == 201:
        return response.json()['token']
    else:
        # Если пользователь уже существует, логинимся
        response = requests.post(
            f"{api_gateway_url}/api/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]}
        )
        return response.json()['token']