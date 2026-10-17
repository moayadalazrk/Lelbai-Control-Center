<?php
try {
    $sqlitePdo = new PDO('sqlite:c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite');
    
    // Check if category_parent exists in SQLite
    $stmt = $sqlitePdo->query("SELECT sql FROM sqlite_master WHERE type='table' AND name='category_parent'");
    $sqlRow = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "SQLITE category_parent SCHEMA:\n";
    print_r($sqlRow);

    // Get all rows from category_parent in SQLite
    $stmtRows = $sqlitePdo->query("SELECT * FROM category_parent");
    $rows = $stmtRows->fetchAll(PDO::FETCH_ASSOC);
    echo "SQLITE category_parent ROWS COUNT: " . count($rows) . "\n";

    // Create table in MySQL souq_al_sham
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $mysqlPdo->exec("CREATE TABLE IF NOT EXISTS `category_parent` (
        `category_id` BIGINT UNSIGNED NOT NULL,
        `parent_id` BIGINT UNSIGNED NOT NULL,
        PRIMARY KEY (`category_id`, `parent_id`),
        KEY `category_parent_parent_id_foreign` (`parent_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;");

    echo "SUCCESS: Created category_parent table in MySQL!\n";

    if (!empty($rows)) {
        $insertStmt = $mysqlPdo->prepare("INSERT IGNORE INTO category_parent (category_id, parent_id) VALUES (:category_id, :parent_id)");
        foreach ($rows as $row) {
            $insertStmt->execute([
                ':category_id' => $row['category_id'],
                ':parent_id' => $row['parent_id']
            ]);
        }
        echo "SUCCESS: Inserted " . count($rows) . " parent-child relationships into MySQL category_parent!\n";
    }

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
