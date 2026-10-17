<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $mysqlPdo->query("SELECT id, title, `condition`, attributes FROM listings WHERE id IN (14, 15)");
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "LISTINGS 14 AND 15:\n";
    print_r($rows);
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
