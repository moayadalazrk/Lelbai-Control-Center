<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Let's test listing #15 attributes
    $stmt = $mysqlPdo->query("SELECT id, title, category_id, attributes FROM listings WHERE id = 15");
    $listing15 = $stmt->fetch(PDO::FETCH_ASSOC);
    echo "LISTING 15:\n";
    print_r($listing15);

    // Test query for alhal = opt_1
    $q1 = "SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"204\"')) = 'opt_1' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"alhal\"')) = 'opt_1'";
    $res1 = $mysqlPdo->query($q1)->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY alhal=opt_1: Found " . count($res1) . " listings.\n";
    print_r($res1);

    // Test query for alkyr = opt_2
    $q2 = "SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"205\"')) = 'opt_2' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"alkyr\"')) = 'opt_2'";
    $res2 = $mysqlPdo->query($q2)->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY alkyr=opt_2: Found " . count($res2) . " listings.\n";
    print_r($res2);

    // Test query for dbl = opt_1
    $q3 = "SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"206\"')) = 'opt_1' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"dbl\"')) = 'opt_1'";
    $res3 = $mysqlPdo->query($q3)->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY dbl=opt_1: Found " . count($res3) . " listings.\n";
    print_r($res3);

    // Test query for alokod = opt_3
    $q4 = "SELECT id, title FROM listings WHERE JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"207\"')) = 'opt_3' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"alokod\"')) = 'opt_3'";
    $res4 = $mysqlPdo->query($q4)->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY alokod=opt_3: Found " . count($res4) . " listings.\n";
    print_r($res4);

    // Test COMBINED query (alhal AND alkyr AND dbl AND alokod)
    $qAll = "SELECT id, title FROM listings WHERE 
        (JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"204\"')) = 'opt_1' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"alhal\"')) = 'opt_1')
        AND (JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"205\"')) = 'opt_2' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"alkyr\"')) = 'opt_2')
        AND (JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"206\"')) = 'opt_1' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"dbl\"')) = 'opt_1')
        AND (JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"207\"')) = 'opt_3' OR JSON_UNQUOTE(JSON_EXTRACT(attributes, '$.\"alokod\"')) = 'opt_3')";
    $resAll = $mysqlPdo->query($qAll)->fetchAll(PDO::FETCH_ASSOC);
    echo "\nFILTER BY ALL COMBINED: Found " . count($resAll) . " listings.\n";
    print_r($resAll);

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
