<?php
$dbPath = 'c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite';
try {
    $pdo = new PDO('sqlite:' . $dbPath);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $stmt = $pdo->query("PRAGMA table_info(category_filters)");
    $columns = array_column($stmt->fetchAll(PDO::FETCH_ASSOC), 'name');

    if (!in_array('sort_order', $columns)) {
        $pdo->exec("ALTER TABLE category_filters ADD COLUMN sort_order INTEGER DEFAULT 0");
        echo "SUCCESS: Added sort_order column to category_filters!\n";
    } else {
        echo "INFO: sort_order column already exists.\n";
    }
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
