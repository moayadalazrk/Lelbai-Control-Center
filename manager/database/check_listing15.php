<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $mysqlPdo->query("SELECT id, title, `condition`, attributes FROM listings WHERE id = 15");
    $listing15 = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "LISTING 15 DETAILS:\n";
    print_r($listing15);
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
