<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $mysqlPdo->query("SELECT id, name, label_ar, type, options FROM category_filters LIMIT 10");
    $filters = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "MYSQL category_filters options:\n";
    foreach ($filters as $f) {
        echo "ID: " . $f['id'] . " | Name: " . $f['name'] . " | Options: " . $f['options'] . "\n";
    }
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
