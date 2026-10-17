<?php
try {
    $pdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $pdo->query("SHOW TABLES");
    $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
    echo "MYSQL TABLES IN souq_al_sham:\n";
    print_r($tables);
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
