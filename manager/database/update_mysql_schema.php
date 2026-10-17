<?php
try {
    $pdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Check columns in category_filters
    $stmt = $pdo->query("SHOW COLUMNS FROM category_filters LIKE 'sort_order'");
    $col = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$col) {
        $pdo->exec("ALTER TABLE category_filters ADD COLUMN sort_order INT DEFAULT 0");
        echo "SUCCESS: Added sort_order column to MySQL category_filters table!\n";
    } else {
        echo "INFO: sort_order column already exists in MySQL category_filters.\n";
    }
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
