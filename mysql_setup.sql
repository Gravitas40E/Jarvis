CREATE DATABASE IF NOT EXISTS jarvis_memory;

CREATE USER IF NOT EXISTS 'jarvis'@'localhost'
IDENTIFIED WITH mysql_native_password BY 'jarvis_admin';

GRANT ALL PRIVILEGES ON jarvis_memory.* TO 'jarvis'@'localhost';
FLUSH PRIVILEGES;

USE jarvis_memory;

CREATE TABLE IF NOT EXISTS memories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    importance INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
