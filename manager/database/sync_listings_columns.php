<?php
try {
    $sqlitePdo = new PDO('sqlite:c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite');
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Get SQLite listings columns
    $sqliteStmt = $sqlitePdo->query("PRAGMA table_info(listings)");
    $sqliteCols = $sqliteStmt->fetchAll(PDO::FETCH_ASSOC);

    // Get MySQL listings columns
    $mysqlStmt = $mysqlPdo->query("SHOW COLUMNS FROM listings");
    $mysqlCols = array_column($mysqlStmt->fetchAll(PDO::FETCH_ASSOC), 'Field');

    echo "MYSQL LISTINGS EXISTING COLUMNS:\n";
    print_r($mysqlCols);

    // Find missing columns
    foreach ($sqliteCols as $col) {
        $colName = $col['name'];
        if (!in_array($colName, $mysqlCols)) {
            $type = 'VARCHAR(255) NULL';
            if ($colName === 'slug') {
                $type = 'VARCHAR(255) NULL';
            } elseif ($colName === 'attributes') {
                $type = 'LONGTEXT NULL';
            } elseif (in_array($colName, ['commission_agreed', 'show_phone', 'is_featured'])) {
                $type = 'TINYINT(1) DEFAULT 0';
            } elseif (in_array($colName, ['views_count', 'price', 'user_id', 'category_id', 'city_id'])) {
                $type = 'BIGINT UNSIGNED NULL';
            }

            $sql = "ALTER TABLE listings ADD COLUMN `{$colName}` {$type}";
            $mysqlPdo->exec($sql);
            echo "ADDED COLUMN {$colName} TO MYSQL listings TABLE!\n";
        }
    }

    echo "\nSCHEMA SYNC COMPLETED SUCCESSFULLY!\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
