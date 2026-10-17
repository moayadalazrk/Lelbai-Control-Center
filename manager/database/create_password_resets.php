<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->exec("CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
        `email` VARCHAR(255) NOT NULL,
        `token` VARCHAR(255) NOT NULL,
        `created_at` TIMESTAMP NULL DEFAULT NULL,
        PRIMARY KEY (`email`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;");
    echo "SUCCESS: Created password_reset_tokens table in MySQL!\n";
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
