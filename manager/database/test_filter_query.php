<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Test JSON_EXTRACT for spec 204 (Condition = opt_1)
    $stmt = $mysqlPdo->prepare("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"204\"')) IN ('opt_1', 'جديد')");
    $stmt->execute();
    $res1 = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "TEST 1 (204 IN opt_1/جديد): Found " . count($res1) . " listings.\n";
    print_r($res1);

    // Test JSON_EXTRACT for spec 205 (Transmission = opt_2)
    $stmt = $mysqlPdo->prepare("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"205\"')) IN ('opt_2', 'قير اوتماتيك')");
    $stmt->execute();
    $res2 = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "TEST 2 (205 IN opt_2/قير اوتماتيك): Found " . count($res2) . " listings.\n";
    print_r($res2);

    // Test JSON_EXTRACT for spec 206 (Double = opt_1)
    $stmt = $mysqlPdo->prepare("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"206\"')) IN ('opt_1', 'نعم')");
    $stmt->execute();
    $res3 = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "TEST 3 (206 IN opt_1/نعم): Found " . count($res3) . " listings.\n";
    print_r($res3);

    // Test JSON_EXTRACT for spec 207 (Fuel = opt_3)
    $stmt = $mysqlPdo->prepare("SELECT id, title, attributes FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"207\"')) IN ('opt_3', 'هايبرد')");
    $stmt->execute();
    $res4 = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo "TEST 4 (207 IN opt_3/هايبرد): Found " . count($res4) . " listings.\n";
    print_r($res4);

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
