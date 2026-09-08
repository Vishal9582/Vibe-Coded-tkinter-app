-- ============================================================
--  Gate Pass Management System - Database Schema
--  Run this once in MySQL before starting the Python app.
--  e.g.  mysql -u root -p < gate_pass_schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS gate_pass_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gate_pass_db;

CREATE TABLE IF NOT EXISTS gate_entries (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    visitor_name    VARCHAR(120)  NOT NULL,
    phone           VARCHAR(20),
    pass_type       VARCHAR(30)   NOT NULL DEFAULT 'Visitor',
    purpose         VARCHAR(255),
    person_to_meet  VARCHAR(120),
    department      VARCHAR(80),
    vehicle_number  VARCHAR(30),
    entry_time      DATETIME      NOT NULL,
    exit_time       DATETIME      NULL,
    status          ENUM('IN','OUT') NOT NULL DEFAULT 'IN',
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_status (status),
    INDEX idx_name   (visitor_name),
    INDEX idx_entry  (entry_time)
);
