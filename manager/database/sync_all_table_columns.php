<?php
try {
    $sqlitePdo = new PDO('sqlite:c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite');
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $tables = ['users', 'listings', 'listing_images', 'comments', 'messages', 'notifications', 'favorites', 'reports'];

    foreach ($tables as $tbl) {
        $sqliteStmt = $sqlitePdo->query("PRAGMA table_info({$tbl})");
        $sqliteCols = $sqliteStmt->fetchAll(PDO::FETCH_ASSOC);

        $mysqlStmt = $mysqlPdo->query("SHOW COLUMNS FROM `{$tbl}`");
        $mysqlCols = array_column($mysqlStmt->fetchAll(PDO::FETCH_ASSOC), 'Field');

        foreach ($sqliteCols as $col) {
            $colName = $col['name'];
            if (!in_array($colName, $mysqlCols)) {
                $type = 'VARCHAR(255) NULL';
                if ($colName === 'attributes' || $colName === 'payload' || $colName === 'data' || $colName === 'content' || $colName === 'description') {
                    $type = 'LONGTEXT NULL';
                } elseif ($colName === 'is_featured' || $colName === 'is_admin' || $colName === 'is_read' || $colName === 'show_phone' || $colName === 'commission_agreed') {
                    $type = 'TINYINT(1) DEFAULT 0';
                } elseif (str_ends_with($colName, '_id') || str_ends_with($colName, '_count')) {
                    $type = 'BIGINT UNSIGNED NULL';
                }

                $sql = "ALTER TABLE `{$tbl}` ADD COLUMN `{$colName}` {$type}";
                $mysqlPdo->exec($sql);
                echo "ADDED COLUMN {$colName} TO TABLE {$tbl}!\n";
            }
        }
    }

    echo "ALL TABLE COLUMNS SYNCED!\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
