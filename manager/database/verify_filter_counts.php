<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');

    // Spec 204: opt_1 (جديد)
    $stmt1 = $mysqlPdo->query("SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"204\"')) = 'opt_1'");
    echo "SPEC 204 = opt_1 (جديد): " . count($stmt1->fetchAll(PDO::FETCH_ASSOC)) . " listings.\n";

    // Spec 204: opt_2 (مستعمل)
    $stmt2 = $mysqlPdo->query("SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"204\"')) = 'opt_2'");
    echo "SPEC 204 = opt_2 (مستعمل): " . count($stmt2->fetchAll(PDO::FETCH_ASSOC)) . " listings.\n";

    // Spec 204: opt_4 (قطع غيار)
    $stmt4 = $mysqlPdo->query("SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"204\"')) = 'opt_4'");
    echo "SPEC 204 = opt_4 (قطع غيار): " . count($stmt4->fetchAll(PDO::FETCH_ASSOC)) . " listings.\n";

    // Spec 205: opt_2 (قير اوتوماتيك)
    $stmt205 = $mysqlPdo->query("SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"205\"')) = 'opt_2'");
    echo "SPEC 205 = opt_2 (قير اوتوماتيك): " . count($stmt205->fetchAll(PDO::FETCH_ASSOC)) . " listings.\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
