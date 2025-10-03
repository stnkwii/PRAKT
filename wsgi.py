import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(__file__))

# Для фронтенда
from frontend.app import app as application

if __name__ == "__main__":
    application.run()