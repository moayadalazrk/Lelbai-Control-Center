<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $updated = $mysqlPdo->exec("UPDATE listings SET published_at = created_at WHERE published_at IS NULL");
    echo "UPDATED {$updated} LISTINGS WHERE published_at WAS NULL!\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
