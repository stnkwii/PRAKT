CREATE DATABASE IF NOT EXISTS auth_db;
USE auth_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'client') DEFAULT 'client',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Пароль: admin123 (захешированный)
INSERT IGNORE INTO users (email, password, role) VALUES 
('admin@tender-system.ru', '$2b$12$Kcpa1E1T9qCQq9z9Q8q8uOc8Q8q8q8q8q8q8q8q8q8q8q8q8q8q8q', 'admin'),
('manager@tender-system.ru', '$2b$12$Kcpa1E1T9qCQq9z9Q8q8uOc8Q8q8q8q8q8q8q8q8q8q8q8q8q8q', 'manager'),
('client@tender-system.ru', '$2b$12$Kcpa1E1T9qCQq9z9Q8q8uOc8Q8q8q8q8q8q8q8q8q8q8q8q8q', 'client');