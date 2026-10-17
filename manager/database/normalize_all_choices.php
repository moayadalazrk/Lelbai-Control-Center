<?php
try {
    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $stmt = $mysqlPdo->query("SELECT id, name, label_ar, type, options FROM category_filters WHERE type IN ('select', 'multiselect', 'boolean')");
    $filters = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $updateStmt = $mysqlPdo->prepare("UPDATE category_filters SET options = :options WHERE id = :id");

    $count = 0;
    foreach ($filters as $f) {
        if (empty($f['options'])) continue;
        $opts = json_decode($f['options'], true);
        if (!is_array($opts) || empty($opts['choices']) || !is_array($opts['choices'])) continue;

        $newChoices = [];
        $usedIds = [];

        foreach ($opts['choices'] as $idx => $choice) {
            if (is_array($choice) && isset($choice['id']) && isset($choice['label'])) {
                $newChoices[] = $choice;
            } else {
                $text = is_array($choice) ? ($choice['label'] ?? reset($choice)) : (string)$choice;
                $choiceId = 'opt_' . ($idx + 1);
                
                $originalId = $choiceId;
                $c = 1;
                while (in_array($choiceId, $usedIds)) {
                    $choiceId = $originalId . '_' . $c;
                    $c++;
                }
                $usedIds[] = $choiceId;

                $newChoices[] = [
                    'id' => $choiceId,
                    'label' => $text,
                    'sort_order' => $idx + 1,
                ];
            }
        }

        $opts['choices'] = $newChoices;
        $jsonOptions = json_encode($opts, JSON_UNESCAPED_UNICODE);

        $updateStmt->execute([
            ':options' => $jsonOptions,
            ':id' => $f['id']
        ]);
        $count++;
    }

    echo "SUCCESSFULLY NORMALIZED {$count} CATEGORY FILTERS TO USE CHOICE OBJECTS (id, label, sort_order)!\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
