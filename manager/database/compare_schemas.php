<?php
try {
    $sqlitePdo = new PDO('sqlite:c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite');
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');

    $sqliteTables = $sqlitePdo->query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")->fetchAll(PDO::FETCH_COLUMN);
    $mysqlTables = $mysqlPdo->query("SHOW TABLES")->fetchAll(PDO::FETCH_COLUMN);

    echo "TABLES IN SQLITE BUT MISSING IN MYSQL:\n";
    $missingInMysql = array_diff($sqliteTables, $mysqlTables);
    print_r($missingInMysql);

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
