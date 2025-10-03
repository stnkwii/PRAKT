CREATE DATABASE IF NOT EXISTS tenders_db;
USE tenders_db;

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tender_id INT NOT NULL,
    user_id INT NOT NULL,
    proposal TEXT,
    price DECIMAL(15,2),
    status ENUM('submitted', 'reviewed', 'accepted', 'rejected') DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT IGNORE INTO tenders 
(title, description, customer, budget, status, deadline, created_by) 
VALUES 
('Поставка компьютерной техники', 'Закупка компьютеров и периферии для офиса', 'ООО Ромашка', 500000.00, 'active', DATE_ADD(NOW(), INTERVAL 30 DAY), 1),
('Ремонт офисных помещений', 'Капитальный ремонт офиса площадью 200 кв.м.', 'ЗАО Весна', 1500000.00, 'active', DATE_ADD(NOW(), INTERVAL 45 DAY), 1);