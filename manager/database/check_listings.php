<?php
$dbPath = 'c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite';
$pdo = new PDO('sqlite:' . $dbPath);
$stmt = $pdo->query("SELECT id, title, status, category_id, city_id FROM listings");
$listings = $stmt->fetchAll(PDO::FETCH_ASSOC);
echo "TOTAL LISTINGS IN SQLITE: " . count($listings) . "\n";
print_r($listings);
