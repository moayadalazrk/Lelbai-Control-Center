<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $stmt = $mysqlPdo->query("SELECT id, name, label_ar, type, options FROM category_filters WHERE id IN (201, 202, 204, 205, 206, 207)");
    $filters = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "MYSQL category_filters FOR SPECS 201-207:\n";
    foreach ($filters as $f) {
        echo "ID: " . $f['id'] . " | Name: " . $f['name'] . " | Label: " . $f['label_ar'] . " | Type: " . $f['type'] . " | Options: " . $f['options'] . "\n";
    }
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
