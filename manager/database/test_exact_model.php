<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Test Model 2027 (opt_1)
    $stmt1 = $mysqlPdo->query("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"201\"')) IN ('opt_1', '2027')");
    $res1 = $stmt1->fetchAll(PDO::FETCH_ASSOC);
    echo "FILTER BY MODEL 2027 (opt_1): Found " . count($res1) . " listings.\n";
    print_r($res1);

    // Test Model 2015 (opt_13)
    $stmt2 = $mysqlPdo->query("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"201\"')) IN ('opt_13', '2015')");
    $res2 = $stmt2->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY MODEL 2015 (opt_13): Found " . count($res2) . " listings.\n";
    print_r($res2);

    // Test Model 2012 (2012 / opt_16)
    $stmt3 = $mysqlPdo->query("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"201\"')) IN ('opt_16', '2012')");
    $res3 = $stmt3->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY MODEL 2012 (2012): Found " . count($res3) . " listings.\n";
    print_r($res3);

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
