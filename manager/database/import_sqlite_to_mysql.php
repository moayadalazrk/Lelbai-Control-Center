<?php
try {
    $sqlitePdo = new PDO('sqlite:c:/xampp/htdocs/projects/AZ/backend/database/database.sqlite');
    $sqlitePdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $mysqlPdo = new PDO('mysql:host=127.0.0.1;dbname=souq_al_sham;charset=utf8mb4', 'root', '');
    $mysqlPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Disable foreign key checks for clean migration
    $mysqlPdo->exec("SET FOREIGN_KEY_CHECKS = 0;");

    // 1. Sync Categories
    echo "--- Syncing Categories ---\n";
    $cats = $sqlitePdo->query("SELECT * FROM categories")->fetchAll(PDO::FETCH_ASSOC);
    if (!empty($cats)) {
        $mysqlPdo->exec("TRUNCATE TABLE categories;");
        $stmt = $mysqlPdo->prepare("INSERT INTO categories (id, parent_id, name_ar, slug, icon, sort_order, created_at, updated_at) VALUES (:id, :parent_id, :name_ar, :slug, :icon, :sort_order, :created_at, :updated_at)");
        foreach ($cats as $cat) {
            $stmt->execute([
                ':id' => $cat['id'],
                ':parent_id' => $cat['parent_id'] ?? null,
                ':name_ar' => $cat['name_ar'],
                ':slug' => $cat['slug'] ?? null,
                ':icon' => $cat['icon'] ?? null,
                ':sort_order' => $cat['sort_order'] ?? 0,
                ':created_at' => $cat['created_at'] ?? date('Y-m-d H:i:s'),
                ':updated_at' => $cat['updated_at'] ?? date('Y-m-d H:i:s'),
            ]);
        }
        echo "Imported " . count($cats) . " categories into MySQL.\n";
    }

    // 2. Sync Category Filters / Specs
    echo "--- Syncing Category Filters ---\n";
    $filters = $sqlitePdo->query("SELECT * FROM category_filters")->fetchAll(PDO::FETCH_ASSOC);
    if (!empty($filters)) {
        $mysqlPdo->exec("TRUNCATE TABLE category_filters;");
        $stmt = $mysqlPdo->prepare("INSERT INTO category_filters (id, category_id, name, label_ar, type, options, sort_order, created_at, updated_at) VALUES (:id, :category_id, :name, :label_ar, :type, :options, :sort_order, :created_at, :updated_at)");
        foreach ($filters as $f) {
            $stmt->execute([
                ':id' => $f['id'],
                ':category_id' => $f['category_id'],
                ':name' => $f['name'],
                ':label_ar' => $f['label_ar'],
                ':type' => $f['type'],
                ':options' => $f['options'],
                ':sort_order' => $f['sort_order'] ?? 0,
                ':created_at' => $f['created_at'] ?? date('Y-m-d H:i:s'),
                ':updated_at' => $f['updated_at'] ?? date('Y-m-d H:i:s'),
            ]);
        }
        echo "Imported " . count($filters) . " category filters/specs into MySQL.\n";
    }

    // 3. Sync Category Parent Relationships
    echo "--- Syncing Category Parent Relationships ---\n";
    $parents = $sqlitePdo->query("SELECT * FROM category_parent")->fetchAll(PDO::FETCH_ASSOC);
    if (!empty($parents)) {
        $mysqlPdo->exec("TRUNCATE TABLE category_parent;");
        $stmt = $mysqlPdo->prepare("INSERT INTO category_parent (category_id, parent_id) VALUES (:category_id, :parent_id)");
        foreach ($parents as $p) {
            $stmt->execute([
                ':category_id' => $p['category_id'],
                ':parent_id' => $p['parent_id'],
            ]);
        }
        echo "Imported " . count($parents) . " category parent relations into MySQL.\n";
    }

    // Re-enable foreign key checks
    $mysqlPdo->exec("SET FOREIGN_KEY_CHECKS = 1;");

    echo "\n=== MIGRATION COMPLETED SUCCESSFULLY! ===\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
