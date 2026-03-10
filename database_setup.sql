-- setup.sql
-- Run this script in your MySQL interface (e.g. phpMyAdmin, MySQL Workbench)
-- to create the necessary tables for the boardgame recommendation system.

CREATE DATABASE IF NOT EXISTS boardgame_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE boardgame_tracker;

-- 1. Players Table: Stores user accounts and their 4-digit PIN for simple login
CREATE TABLE IF NOT EXISTS Players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. BoardGames Table: Stores the core games and their 8 computed ML vector scores
CREATE TABLE IF NOT EXISTS BoardGames (
    game_name VARCHAR(100) PRIMARY KEY,
    strategy FLOAT NOT NULL DEFAULT 0.0,
    luck FLOAT NOT NULL DEFAULT 0.0,
    negotiation FLOAT NOT NULL DEFAULT 0.0,
    deduction FLOAT NOT NULL DEFAULT 0.0,
    deck_building FLOAT NOT NULL DEFAULT 0.0,
    cooperation FLOAT NOT NULL DEFAULT 0.0,
    complexity FLOAT NOT NULL DEFAULT 0.0,
    duration_norm FLOAT NOT NULL DEFAULT 0.0,
    category VARCHAR(50) DEFAULT 'Strategy',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. PlayHistory Table: The most important table. Records every match played.
CREATE TABLE IF NOT EXISTS PlayHistory (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(50) NOT NULL,
    game_name VARCHAR(100) NOT NULL,
    score INT DEFAULT 0,
    is_winner TINYINT(1) DEFAULT 0, -- 1 for True, 0 for False
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_name) REFERENCES Players(player_name) ON DELETE CASCADE,
    FOREIGN KEY (game_name) REFERENCES BoardGames(game_name) ON DELETE CASCADE
);

-- ==========================================
-- (Optional) Quick dummy data to test the DB
-- ==========================================
-- INSERT INTO Players (player_name, pin_code) VALUES ('Alice', '1234');
-- INSERT INTO PlayHistory (player_name, game_name, score, is_winner) VALUES ('Alice', 'Catan', 10, 1);
