<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Sync main condition column with attributes->204 if available
    $stmt = $mysqlPdo->query("SELECT id, `condition`, attributes FROM listings");
    $listings = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $up = $mysqlPdo->prepare("UPDATE listings SET `condition` = :cond WHERE id = :id");

    foreach ($listings as $l) {
        if (empty($l['attributes'])) continue;
        $attrs = json_decode($l['attributes'], true);
        if (!is_array($attrs)) continue;

        // Spec 204 is الحالة
        $stateVal = $attrs['204'] ?? $attrs['alhal'] ?? null;
        if ($stateVal) {
            $newCond = 'used';
            if ($stateVal === 'opt_1' || $stateVal === 'جديد' || $stateVal === 'جديدة (صفر كم)') {
                $newCond = 'new';
            }
            $up->execute([':cond' => $newCond, ':id' => $l['id']]);
            echo "UPDATED LISTING {$l['id']} CONDITION TO '{$newCond}'!\n";
        }
    }

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
