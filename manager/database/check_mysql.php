<?php
try {
    $pdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $pdo->query("SELECT id, title, status FROM listings");
    $mysqlListings = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "TOTAL LISTINGS IN MYSQL (souq_al_sham): " . count($mysqlListings) . "\n";
    print_r($mysqlListings);
} catch (Exception $e) {
    echo "MYSQL ERROR: " . $e->getMessage() . "\n";
}
