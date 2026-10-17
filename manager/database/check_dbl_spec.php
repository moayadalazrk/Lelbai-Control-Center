<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    
    // Check filter 206 (دبل)
    $stmt1 = $mysqlPdo->query("SELECT id, name, label_ar, type, options FROM category_filters WHERE id = 206 OR name = 'dbl' OR label_ar = 'دبل'");
    $filter206 = $stmt1->fetch(PDO::FETCH_ASSOC);
    echo "SPEC 206 (دبل) IN CATEGORY_FILTERS:\n";
    print_r($filter206);

    // Check Listing 15 attributes
    $stmt2 = $mysqlPdo->query("SELECT id, title, attributes FROM listings WHERE id = 15");
    $l15 = $stmt2->fetch(PDO::FETCH_ASSOC);
    echo "\nLISTING 15 ATTRS:\n";
    print_r($l15);

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
