<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $mysqlPdo->query("SHOW COLUMNS FROM categories");
    $cols = array_column($stmt->fetchAll(PDO::FETCH_ASSOC), 'Field');
    echo "MYSQL categories COLUMNS:\n";
    print_r($cols);
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
