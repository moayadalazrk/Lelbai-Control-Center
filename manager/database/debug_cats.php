<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');

    $stmt = $mysqlPdo->query("SELECT id, name_ar, parent_id FROM categories WHERE id IN (45, 84, 85)");
    $cats = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "CATEGORIES 45, 84, 85:\n";
    print_r($cats);

    $stmt2 = $mysqlPdo->query("SELECT id, title, category_id FROM listings WHERE id IN (13, 14, 15)");
    $listings = $stmt2->fetchAll(PDO::FETCH_ASSOC);
    echo "\nLISTINGS 13, 14, 15 CATEGORIES:\n";
    print_r($listings);

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
