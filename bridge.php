<?php
/**
 * Lelbai High-Speed Standalone Database & API Bridge
 * Provides secure HTTPS access to local database and services.
 */

declare(strict_types=1);

if (!function_exists('getallheaders')) {
    function getallheaders(): array {
        $headers = [];
        foreach ($_SERVER as $name => $value) {
            if (str_starts_with($name, 'HTTP_')) {
                $headerName = str_replace(' ', '-', ucwords(strtolower(str_replace('_', ' ', substr($name, 5)))));
                $headers[$headerName] = $value;
            }
        }
        return $headers;
    }
}

// Fast GZIP HTTP Compression for up to 90% bandwidth & latency reduction
if (!ob_start("ob_gzhandler")) {
    ob_start();
}

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Bridge-Secret, X-Bridge-Key, Accept-Encoding');
header('Connection: keep-alive');
header('Keep-Alive: timeout=30, max=100');

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 1. Load Environment Configuration
$envFile = __DIR__ . '/../.env';
$env = [];
if (file_exists($envFile)) {
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#') || !str_contains($line, '=')) {
            continue;
        }
        [$key, $val] = explode('=', $line, 2);
        $key = trim($key);
        $val = trim($val, " \t\n\r\0\x0B\"'");
        $env[$key] = $val;
    }
}

// 2. Authentication Check
$configuredSecret = $env['BRIDGE_SECRET'] ?? 'lelbai_bridge_secure_key_2026_9984';
$headers = getallheaders();
$incomingSecret = $headers['X-Bridge-Secret'] 
    ?? $headers['x-bridge-secret'] 
    ?? $headers['X-Bridge-Key'] 
    ?? ($_GET['bridge_secret'] ?? null) 
    ?? ($_POST['bridge_secret'] ?? null)
    ?? ($_SERVER['HTTP_X_BRIDGE_SECRET'] ?? null);

$rawBody = file_get_contents('php://input');
$body = json_decode($rawBody, true) ?: [];
if (!$incomingSecret && !empty($body['bridge_secret'])) {
    $incomingSecret = $body['bridge_secret'];
}

if (!$incomingSecret || !hash_equals((string)$configuredSecret, (string)$incomingSecret)) {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'Unauthorized: Invalid Bridge Secret']);
    exit;
}

// 3. Database Connection
$dbHost = $env['DB_HOST'] ?? '127.0.0.1';
$dbPort = $env['DB_PORT'] ?? '3306';
$dbName = $env['DB_DATABASE'] ?? 'u762212316_lelbai';
$dbUser = $env['DB_USERNAME'] ?? 'u762212316_lelbai';
$dbPass = $env['DB_PASSWORD'] ?? 'lAE8EBCK=Zm6';

try {
    $pdo = new PDO(
        "mysql:host={$dbHost};port={$dbPort};dbname={$dbName};charset=utf8mb4",
        $dbUser,
        $dbPass,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_OBJ,
            PDO::ATTR_TIMEOUT => 4,
            PDO::ATTR_PERSISTENT => true,
        ]
    );
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'connected' => false,
        'error' => 'Database connection failed: ' . $e->getMessage()
    ]);
    exit;
}

function bridgeNormalizePhone(string $phone): array {
    $clean = preg_replace('/[^\d]/', '', $phone);
    $local = $clean;
    $intl = $clean;

    if (str_starts_with($clean, '00963') && strlen($clean) === 14) {
        $local = '0' . substr($clean, 5);
        $intl = substr($clean, 2);
    } elseif (str_starts_with($clean, '963') && strlen($clean) === 12) {
        $local = '0' . substr($clean, 3);
        $intl = $clean;
    } elseif (str_starts_with($clean, '09') && strlen($clean) === 10) {
        $local = $clean;
        $intl = '963' . substr($clean, 1);
    } elseif (str_starts_with($clean, '9') && strlen($clean) === 9) {
        $local = '0' . $clean;
        $intl = '963' . $clean;
    } elseif (str_starts_with($clean, '05') && strlen($clean) === 10) {
        $local = $clean;
        $intl = '966' . substr($clean, 1);
    } elseif (str_starts_with($clean, '966') && strlen($clean) === 12) {
        $local = '0' . substr($clean, 3);
        $intl = $clean;
    }

    return [
        'local' => $local,
        'intl' => $intl,
        'variations' => array_values(array_unique([$local, $intl, '+' . $intl, '00' . $intl, $clean, $phone]))
    ];
}

// 4. Action Router
$action = $_GET['action'] ?? $body['action'] ?? 'ping';

try {
    switch ($action) {
        case 'ping':
            try {
                $pdo->exec("CREATE TABLE IF NOT EXISTS contact_messages (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNSIGNED NULL,
                    name VARCHAR(191) NOT NULL,
                    phone VARCHAR(50) NOT NULL,
                    subject VARCHAR(100) NOT NULL DEFAULT 'general',
                    message TEXT NOT NULL,
                    status ENUM('pending', 'in_progress', 'resolved', 'closed') NOT NULL DEFAULT 'pending',
                    admin_notes TEXT NULL,
                    ip_address VARCHAR(45) NULL,
                    user_agent TEXT NULL,
                    created_at TIMESTAMP NULL,
                    updated_at TIMESTAMP NULL,
                    INDEX idx_contact_status (status),
                    INDEX idx_contact_created (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;");
            } catch (\Throwable $eTable) {}

            $stmt1 = $pdo->query("SELECT count(*) as total FROM listings");
            $listingsCount = (int)($stmt1->fetch()->total ?? 0);
            $stmt2 = $pdo->query("SELECT count(*) as total FROM users");
            $usersCount = (int)($stmt2->fetch()->total ?? 0);
            
            echo json_encode([
                'success' => true,
                'connected' => true,
                'database' => $dbName,
                'listings_count' => $listingsCount,
                'users_count' => $usersCount,
                'server_time' => date('c'),
            ]);
            break;

        case 'dashboard_data':
            $lStats = $pdo->query("
                SELECT 
                    COUNT(*) as total_listings,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_listings,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_listings
                FROM listings
            ")->fetch(PDO::FETCH_ASSOC);

            $uStats = $pdo->query("
                SELECT 
                    COUNT(*) as total_users,
                    SUM(CASE WHEN is_banned = 1 THEN 1 ELSE 0 END) as banned_users
                FROM users
            ")->fetch(PDO::FETCH_ASSOC);

            $mTotal = (int)($pdo->query("SELECT COUNT(*) as total FROM messages")->fetch()->total ?? 0);
            $cTotal = (int)($pdo->query("SELECT COUNT(*) as total FROM categories")->fetch()->total ?? 0);

            $recentListings = $pdo->query("
                SELECT l.id, l.title, l.price, l.status, l.created_at, l.user_id, l.category_id,
                       u.name as user_name, u.phone as user_phone, 
                       c.name_ar as category_name
                FROM listings l
                LEFT JOIN users u ON l.user_id = u.id
                LEFT JOIN categories c ON l.category_id = c.id
                ORDER BY l.id DESC
                LIMIT 6
            ")->fetchAll(PDO::FETCH_ASSOC);

            $recentUsers = $pdo->query("
                SELECT id, name, phone, role, is_banned, created_at
                FROM users
                ORDER BY id DESC
                LIMIT 5
            ")->fetchAll(PDO::FETCH_ASSOC);

            echo json_encode([
                'success' => true,
                'stats' => [
                    'total_listings' => (int)($lStats['total_listings'] ?? 0),
                    'active_listings' => (int)($lStats['active_listings'] ?? 0),
                    'pending_listings' => (int)($lStats['pending_listings'] ?? 0),
                    'total_users' => (int)($uStats['total_users'] ?? 0),
                    'banned_users' => (int)($uStats['banned_users'] ?? 0),
                    'total_messages' => $mTotal,
                    'total_categories' => $cTotal,
                ],
                'recent_listings' => $recentListings,
                'recent_users' => $recentUsers,
            ]);
            break;

        case 'query':
            $sql = $body['sql'] ?? $_POST['sql'] ?? '';
            $bindings = $body['bindings'] ?? $_POST['bindings'] ?? [];
            if (empty($sql)) {
                http_response_code(422);
                echo json_encode(['success' => false, 'error' => 'SQL is required']);
                exit;
            }
            $stmt = $pdo->prepare($sql);
            $stmt->execute(is_array($bindings) ? $bindings : []);
            $rows = $stmt->fetchAll(PDO::FETCH_OBJ);
            echo json_encode(['success' => true, 'rows' => $rows]);
            break;

        case 'get_listings_feed':
            $startTime = microtime(true);
            $page = max(1, (int)($body['page'] ?? $_POST['page'] ?? $_GET['page'] ?? 1));
            $perPage = min(100, max(1, (int)($body['per_page'] ?? $_POST['per_page'] ?? $_GET['per_page'] ?? 20)));
            $offset = ($page - 1) * $perPage;

            $status = $body['status'] ?? $_POST['status'] ?? $_GET['status'] ?? null;
            $aiStatus = $body['ai_status'] ?? $_POST['ai_status'] ?? $_GET['ai_status'] ?? null;
            $categoryId = !empty($body['category_id'] ?? $_POST['category_id'] ?? $_GET['category_id'] ?? null) ? (int)($body['category_id'] ?? $_POST['category_id'] ?? $_GET['category_id']) : null;
            $cityId = !empty($body['city_id'] ?? $_POST['city_id'] ?? $_GET['city_id'] ?? null) ? (int)($body['city_id'] ?? $_POST['city_id'] ?? $_GET['city_id']) : null;
            $search = trim((string)($body['search'] ?? $_POST['search'] ?? $_GET['search'] ?? ''));
            $source = $body['source'] ?? $_POST['source'] ?? $_GET['source'] ?? null;
            $sort = $body['sort'] ?? $_POST['sort'] ?? $_GET['sort'] ?? 'newest_created';

            // 1. Overall Status Counts (Cached in server temp for 30s to be 0ms fast)
            $countsCacheFile = sys_get_temp_dir() . '/bridge_status_counts.json';
            $counts = null;
            if (file_exists($countsCacheFile) && (time() - filemtime($countsCacheFile) < 30)) {
                $counts = json_decode(@file_get_contents($countsCacheFile), true);
            }
            if (!$counts || !is_array($counts)) {
                $now = time();
                $todayCutoff = date('Y-m-d H:i:s', $now - 86400);
                $cutoffExpiringSoon = date('Y-m-d H:i:s', $now - (25 * 86400));
                $cutoff30Days = date('Y-m-d H:i:s', $now - (30 * 86400));

                $stmtCounts = $pdo->prepare("
                    SELECT 
                        COUNT(*) as total_all,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as total_active,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as total_pending,
                        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as total_rejected,
                        SUM(CASE WHEN status = 'suspended' THEN 1 ELSE 0 END) as total_suspended,
                        SUM(CASE WHEN ai_status = 'flagged' THEN 1 ELSE 0 END) as total_flagged,
                        SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as total_today,
                        SUM(CASE WHEN created_at <= ? AND created_at >= ? THEN 1 ELSE 0 END) as total_expiring_soon
                    FROM listings
                    WHERE deleted_at IS NULL
                ");
                $stmtCounts->execute([$todayCutoff, $cutoffExpiringSoon, $cutoff30Days]);
                $cRow = $stmtCounts->fetch(PDO::FETCH_ASSOC) ?: [];
                $counts = [
                    'all' => (int)($cRow['total_all'] ?? 0),
                    'active' => (int)($cRow['total_active'] ?? 0),
                    'pending' => (int)($cRow['total_pending'] ?? 0),
                    'rejected' => (int)($cRow['total_rejected'] ?? 0),
                    'suspended' => (int)($cRow['total_suspended'] ?? 0),
                    'flagged' => (int)($cRow['total_flagged'] ?? 0),
                    'today' => (int)($cRow['total_today'] ?? 0),
                    'expiring_soon' => (int)($cRow['total_expiring_soon'] ?? 0),
                ];
                @file_put_contents($countsCacheFile, json_encode($counts));
            }

            // 2. Build Where Clauses
            $whereClauses = ['l.deleted_at IS NULL'];
            $bindings = [];

            if ($categoryId) {
                $childIds = [$categoryId];
                try {
                    $stmtChildren = $pdo->prepare("SELECT id FROM categories WHERE parent_id = ?");
                    $stmtChildren->execute([$categoryId]);
                    $subIds = $stmtChildren->fetchAll(PDO::FETCH_COLUMN);
                    if (!empty($subIds)) {
                        $childIds = array_merge($childIds, $subIds);
                        $inSub = implode(',', array_fill(0, count($subIds), '?'));
                        $stmtGrand = $pdo->prepare("SELECT id FROM categories WHERE parent_id IN ($inSub)");
                        $stmtGrand->execute($subIds);
                        $grandIds = $stmtGrand->fetchAll(PDO::FETCH_COLUMN);
                        if (!empty($grandIds)) {
                            $childIds = array_merge($childIds, $grandIds);
                        }
                    }
                } catch (\Throwable $e) {}
                $inCats = implode(',', array_fill(0, count($childIds), '?'));
                $whereClauses[] = "l.category_id IN ({$inCats})";
                $bindings = array_merge($bindings, $childIds);
            }

            if ($cityId) {
                $whereClauses[] = "l.city_id = ?";
                $bindings[] = $cityId;
            }

            if ($status === 'expiring_soon') {
                $whereClauses[] = "l.created_at <= ? AND l.created_at >= ?";
                $bindings[] = date('Y-m-d H:i:s', time() - (25 * 86400));
                $bindings[] = date('Y-m-d H:i:s', time() - (30 * 86400));
            } elseif ($status && in_array($status, ['active', 'pending', 'rejected', 'suspended'])) {
                $whereClauses[] = "l.status = ?";
                $bindings[] = $status;
            }

            if ($aiStatus === 'flagged') {
                $whereClauses[] = "l.ai_status = 'flagged'";
            } elseif (!empty($aiStatus)) {
                $whereClauses[] = "l.ai_status = ?";
                $bindings[] = $aiStatus;
            }

            if ($source === 'organic') {
                $whereClauses[] = "l.is_scraped = 0";
            } elseif ($source === 'bot') {
                $whereClauses[] = "l.is_scraped = 1";
            } elseif ($source === 'facebook') {
                $whereClauses[] = "l.source_url LIKE '%facebook.com%'";
            }

            if (!empty($search)) {
                $like = "%{$search}%";
                $whereClauses[] = "(l.title LIKE ? OR l.description LIKE ? OR l.id = ? OR l.uuid = ? OR l.contact_phone LIKE ? OR u.name LIKE ? OR u.phone LIKE ? OR c.name_ar LIKE ?)";
                $bindings[] = $like;
                $bindings[] = $like;
                $bindings[] = is_numeric($search) ? (int)$search : 0;
                $bindings[] = $search;
                $bindings[] = $like;
                $bindings[] = $like;
                $bindings[] = $like;
                $bindings[] = $like;
            }

            $whereSql = implode(' AND ', $whereClauses);

            // 3. Total filtered count
            $hasComplex = $categoryId || $cityId || !empty($search) || $source;
            if (!$hasComplex) {
                if (!$status && !$aiStatus) {
                    $totalFiltered = $counts['all'];
                } elseif ($aiStatus === 'flagged') {
                    $totalFiltered = $counts['flagged'];
                } elseif ($status && isset($counts[$status])) {
                    $totalFiltered = $counts[$status];
                } else {
                    $stmtC = $pdo->prepare("SELECT COUNT(*) as total FROM listings l WHERE {$whereSql}");
                    $stmtC->execute($bindings);
                    $totalFiltered = (int)($stmtC->fetch()->total ?? 0);
                }
            } else {
                $stmtC = $pdo->prepare("
                    SELECT COUNT(*) as total
                    FROM listings l
                    LEFT JOIN users u ON l.user_id = u.id
                    LEFT JOIN categories c ON l.category_id = c.id
                    LEFT JOIN cities ci ON l.city_id = ci.id
                    WHERE {$whereSql}
                ");
                $stmtC->execute($bindings);
                $totalFiltered = (int)($stmtC->fetch()->total ?? 0);
            }

            // 4. Sort Order
            $orderSql = "l.created_at DESC, l.id DESC";
            if ($sort === 'oldest_created') {
                $orderSql = "l.created_at ASC, l.id ASC";
            } elseif ($sort === 'most_viewed') {
                $orderSql = "l.views_count DESC, l.id DESC";
            } elseif ($sort === 'most_impressions') {
                $orderSql = "l.impressions_count DESC, l.id DESC";
            } elseif ($sort === 'price_desc') {
                $orderSql = "l.price DESC, l.id DESC";
            } elseif ($sort === 'price_asc') {
                $orderSql = "l.price ASC, l.id DESC";
            }

            // 5. Query 20 Listings with User, Category, City, Image
            $dataSql = "
                SELECT 
                    l.id, l.title, l.slug, l.price, l.currency, l.status, l.ai_status, l.ai_rejection_reason,
                    l.rejection_reason, l.views_count, l.impressions_count, l.is_featured, l.is_scraped,
                    l.source_url, l.contact_phone, l.user_id, l.category_id, l.city_id,
                    l.created_at, l.updated_at, l.published_at, l.expires_at,
                    u.name as user_name, u.phone as user_phone, u.username as user_username, u.avatar as user_avatar, u.is_bot as user_is_bot,
                    c.name_ar as category_name_ar, c.slug as category_slug, c.icon as category_icon, c.parent_id as category_parent_id,
                    ci.name_ar as city_name_ar, ci.slug as city_slug,
                    (SELECT image_path FROM listing_images WHERE listing_id = l.id ORDER BY is_primary DESC, sort_order ASC, id ASC LIMIT 1) as primary_image_path
                FROM listings l
                LEFT JOIN users u ON l.user_id = u.id
                LEFT JOIN categories c ON l.category_id = c.id
                LEFT JOIN cities ci ON l.city_id = ci.id
                WHERE {$whereSql}
                ORDER BY {$orderSql}
                LIMIT {$perPage} OFFSET {$offset}
            ";
            $stmtData = $pdo->prepare($dataSql);
            $stmtData->execute($bindings);
            $rows = $stmtData->fetchAll(PDO::FETCH_ASSOC);

            // Meta categories & cities (if requested)
            $meta = [];
            if (!empty($body['include_meta']) || !empty($_GET['include_meta'])) {
                $meta['categories'] = $pdo->query("SELECT id, name_ar, slug, icon, parent_id, sort_order FROM categories ORDER BY sort_order ASC, name_ar ASC")->fetchAll(PDO::FETCH_ASSOC);
                $meta['cities'] = $pdo->query("SELECT id, name_ar, slug, is_active FROM cities WHERE is_active = 1 ORDER BY name_ar ASC")->fetchAll(PDO::FETCH_ASSOC);
            }

            $execMs = round((microtime(true) - $startTime) * 1000);
            echo json_encode([
                'success' => true,
                'counts' => $counts,
                'total' => $totalFiltered,
                'current_page' => $page,
                'per_page' => $perPage,
                'rows' => $rows,
                'meta' => $meta,
                'server_time_ms' => $execMs,
            ], JSON_UNESCAPED_UNICODE);
            exit;

        case 'quick_update_status':
            $id = (int)($body['id'] ?? $_POST['id'] ?? 0);
            $newStatus = (string)($body['status'] ?? $_POST['status'] ?? '');
            $reason = (string)($body['reason'] ?? $_POST['reason'] ?? '');
            
            if (!$id || !in_array($newStatus, ['active', 'pending', 'rejected', 'suspended'])) {
                http_response_code(422);
                echo json_encode(['success' => false, 'error' => 'Invalid parameters']);
                exit;
            }
            
            if ($newStatus === 'rejected') {
                $stmt = $pdo->prepare("UPDATE listings SET status = 'rejected', rejection_reason = ?, previous_rejection_reason = ?, updated_at = NOW() WHERE id = ?");
                $stmt->execute([$reason, $reason, $id]);
            } elseif ($newStatus === 'active') {
                $stmt = $pdo->prepare("UPDATE listings SET status = 'active', rejection_reason = NULL, previous_rejection_reason = NULL, published_at = COALESCE(published_at, NOW()), updated_at = NOW() WHERE id = ?");
                $stmt->execute([$id]);
            } else {
                $stmt = $pdo->prepare("UPDATE listings SET status = ?, updated_at = NOW() WHERE id = ?");
                $stmt->execute([$newStatus, $id]);
            }
            
            @unlink(sys_get_temp_dir() . '/bridge_status_counts.json');
            
            echo json_encode([
                'success' => true,
                'id' => $id,
                'status' => $newStatus,
                'message' => 'Status updated successfully'
            ]);
            exit;

        case 'batch_query':
            $queries = $body['queries'] ?? $_POST['queries'] ?? [];
            if (!is_array($queries) || empty($queries)) {
                http_response_code(422);
                echo json_encode(['success' => false, 'error' => 'Queries array is required']);
                exit;
            }
            $results = [];
            foreach ($queries as $key => $q) {
                $sql = $q['sql'] ?? '';
                $bindings = $q['bindings'] ?? [];
                if (!empty($sql)) {
                    $stmt = $pdo->prepare($sql);
                    $stmt->execute(is_array($bindings) ? $bindings : []);
                    $results[$key] = $stmt->fetchAll(PDO::FETCH_OBJ);
                }
            }
            echo json_encode(['success' => true, 'results' => $results]);
            exit;

        case 'statement':
            $sql = $body['sql'] ?? $_POST['sql'] ?? '';
            $bindings = $body['bindings'] ?? $_POST['bindings'] ?? [];
            if (empty($sql)) {
                http_response_code(422);
                echo json_encode(['success' => false, 'error' => 'SQL is required']);
                exit;
            }
            $stmt = $pdo->prepare($sql);
            $stmt->execute(is_array($bindings) ? $bindings : []);
            $affected = $stmt->rowCount();
            $lastInsertId = $pdo->lastInsertId();
            echo json_encode([
                'success' => true,
                'affected' => $affected,
                'last_insert_id' => $lastInsertId
            ]);
            break;

        case 'heartbeat':
            $status = $body['status'] ?? $_POST['status'] ?? 'connected';
            $phone = $body['phone'] ?? $_POST['phone'] ?? null;
            $sessions = $body['sessions'] ?? $_POST['sessions'] ?? [];
            $uptime = $body['uptime'] ?? $_POST['uptime'] ?? 0;
            $activeSessionId = $body['active_session_id'] ?? $_POST['active_session_id'] ?? null;
            $qr = $body['qr'] ?? $_POST['qr'] ?? null;
            $pairingCode = $body['pairing_code'] ?? $_POST['pairing_code'] ?? null;

            $statusData = [
                'status' => $status,
                'phone' => $phone,
                'active_session_id' => $activeSessionId,
                'qr' => $qr,
                'pairing_code' => $pairingCode,
                'sessions' => $sessions,
                'uptime' => $uptime,
                'last_seen' => date('c'),
                'last_seen_timestamp' => time(),
            ];

            $statusFile = sys_get_temp_dir() . '/whatsapp_live_status.json';
            $localFile = __DIR__ . '/whatsapp_live_status.json';
            @file_put_contents($statusFile, json_encode($statusData));
            @file_put_contents($localFile, json_encode($statusData));

            echo json_encode([
                'success' => true,
                'message' => 'Heartbeat received and status synchronized.',
                'server_time' => date('c')
            ]);
            break;

        case 'whatsapp_status':
        case 'whatsapp-status':
            $statusFile = sys_get_temp_dir() . '/whatsapp_live_status.json';
            $localFile = __DIR__ . '/whatsapp_live_status.json';

            $cached = null;
            if (file_exists($statusFile)) {
                $cached = json_decode(@file_get_contents($statusFile), true);
            }
            if (!$cached && file_exists($localFile)) {
                $cached = json_decode(@file_get_contents($localFile), true);
            }

            if ($cached && is_array($cached)) {
                $age = time() - ($cached['last_seen_timestamp'] ?? 0);
                if ($age < 180) { // Valid within 3 minutes
                    echo json_encode($cached);
                    break;
                } else {
                    // Stale fallback: keep configured sessions in UI instead of wiping out
                    $cached['status'] = 'disconnected';
                    $cached['is_stale'] = true;
                    echo json_encode($cached);
                    break;
                }
            }

            echo json_encode([
                'status' => 'disconnected',
                'phone' => null,
                'sessions' => [],
                'error' => 'خادم الواتساب غير متصل حالياً بالسيرفر.'
            ]);
            break;

        case 'inbound-webhook':
            $senderPhone = $body['sender_phone'] ?? $body['phone'] ?? $_POST['sender_phone'] ?? $_POST['phone'] ?? '';
            $messageBody = trim((string)($body['message_body'] ?? $body['message'] ?? $_POST['message_body'] ?? $_POST['message'] ?? ''));
            $extractedCode = $body['extracted_code'] ?? $_POST['extracted_code'] ?? null;

            if (empty($senderPhone)) {
                http_response_code(422);
                echo json_encode(['error' => 'Sender phone is required']);
                exit;
            }

            $senderNorm = bridgeNormalizePhone((string)$senderPhone);
            $cleanMsg = strtr($messageBody, [
                '٠'=>'0', '١'=>'1', '٢'=>'2', '٣'=>'3', '٤'=>'4',
                '٥'=>'5', '٦'=>'6', '٧'=>'7', '٨'=>'8', '٩'=>'9'
            ]);

            // Robust code extraction: code after 'كود' or 'الكود' or 'code' specifically first!
            if (!$extractedCode) {
                if (preg_match('/(?:كود|الكود|code)\s*[:：]?\s*(\d{4,6})/iu', $cleanMsg, $matches)) {
                    $extractedCode = $matches[1];
                } elseif (preg_match('/\b(\d{4,6})\b/', $cleanMsg, $matches)) {
                    $extractedCode = $matches[1];
                }
            }

            $verification = null;
            if ($extractedCode) {
                $stmtV = $pdo->prepare("SELECT * FROM whatsapp_inbound_verifications WHERE verification_code = ? AND is_verified = 0 AND expires_at > NOW() ORDER BY id DESC LIMIT 1");
                $stmtV->execute([$extractedCode]);
                $verification = $stmtV->fetch();
            }

            if (!$verification) {
                // Check if sender has an active pending verification to link the unmatched error
                $pendingForSender = null;
                try {
                    $placeholders = implode(',', array_fill(0, count($senderNorm['variations']), '?'));
                    $stmtPending = $pdo->prepare("SELECT id, session_token FROM whatsapp_inbound_verifications WHERE phone IN ($placeholders) AND is_verified = 0 AND expires_at > NOW() ORDER BY id DESC LIMIT 1");
                    $stmtPending->execute($senderNorm['variations']);
                    $pendingForSender = $stmtPending->fetch();
                } catch (Throwable $e) {}

                // Log unmatched
                try {
                    $stmtLog = $pdo->prepare("INSERT INTO whatsapp_message_logs (sender_phone, message_body, extracted_code, matched_verification_id, status, details, created_at, updated_at) VALUES (?, ?, ?, ?, 'unmatched', ?, NOW(), NOW())");
                    $stmtLog->execute([
                        $senderPhone,
                        $messageBody,
                        $extractedCode,
                        $pendingForSender ? $pendingForSender->id : null,
                        $extractedCode ? "كود التحقق غير صحيح ({$extractedCode}) أو غير مطابق للجلسة." : "رسالة واردة لا تحتوي على رمز تحقق صالح."
                    ]);
                } catch (Throwable $e) {}

                echo json_encode([
                    'success' => false,
                    'verified' => false,
                    'invalid_code' => true,
                    'extracted_code' => $extractedCode,
                    'matched_verification_id' => $pendingForSender ? $pendingForSender->id : null,
                    'message' => 'لم يتم العثور على طلب تحقق مطابق لهذا الكود أو انتهت صلاحيته.'
                ]);
                exit;
            }

            // 3. CRITICAL SECURITY CHECK: Does sender phone match registered verification phone?
            $verifNorm = bridgeNormalizePhone((string)$verification->phone);
            if ($senderNorm['local'] !== $verifNorm['local']) {
                // SENDER PHONE MISMATCH: Do NOT verify, do NOT modify password!
                try {
                    $stmtLog = $pdo->prepare("INSERT INTO whatsapp_message_logs (sender_phone, message_body, extracted_code, matched_verification_id, status, details, created_at, updated_at) VALUES (?, ?, ?, ?, 'mismatch', ?, NOW(), NOW())");
                    $stmtLog->execute([
                        $senderPhone,
                        $messageBody,
                        $extractedCode,
                        $verification->id,
                        "تم إرسال الكود من رقم مختلف ({$senderPhone}) بينما الحساب مسجل برقم ({$verification->phone})."
                    ]);

                    // Send security alert notification to account owner if account exists
                    $placeholders = implode(',', array_fill(0, count($verifNorm['variations']), '?'));
                    $stmtOwner = $pdo->prepare("SELECT id FROM users WHERE phone IN ($placeholders) LIMIT 1");
                    $stmtOwner->execute($verifNorm['variations']);
                    $owner = $stmtOwner->fetch();
                    if ($owner && !empty($owner->id)) {
                        $notifId = sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
                            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
                            mt_rand(0, 0xffff),
                            mt_rand(0, 0x0fff) | 0x4000,
                            mt_rand(0, 0x3fff) | 0x8000,
                            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
                        );
                        $notifData = json_encode([
                            'title' => '⚠️ تنبيه أمان: محاولة تحقق برقم مختلف',
                            'body' => "تم استلام كود التحقق من رقم واتساب مختلف ({$senderPhone}) عن رقم حسابك المسجل.",
                            'link' => '/profile',
                        ], JSON_UNESCAPED_UNICODE);
                        $stmtNotif = $pdo->prepare("INSERT INTO notifications (id, type, notifiable_type, notifiable_id, data, created_at, updated_at) VALUES (?, 'App\\\\Notifications\\\\SecurityAlertNotification', 'App\\\\Models\\\\User', ?, ?, NOW(), NOW())");
                        $stmtNotif->execute([$notifId, $owner->id, $notifData]);
                    }
                } catch (Throwable $e) {}

                echo json_encode([
                    'success' => false,
                    'verified' => false,
                    'mismatch' => true,
                    'received_phone' => $senderPhone,
                    'expected_phone' => $verification->phone,
                    'message' => "تم إرسال الرسالة من رقم مختلف ({$senderPhone}). يجب إرسال الرسالة من الرقم المسجل ({$verification->phone})."
                ]);
                exit;
            }

            // 4. PHONE MATCHES! Process activation safely on Hostinger
            $stmtUp = $pdo->prepare("UPDATE whatsapp_inbound_verifications SET is_verified = 1, verified_at = NOW(), updated_at = NOW() WHERE id = ?");
            $stmtUp->execute([$verification->id]);

            $targetPhone = $verifNorm['local'];
            $placeholders = implode(',', array_fill(0, count($verifNorm['variations']), '?'));
            $stmtU = $pdo->prepare("SELECT * FROM users WHERE phone IN ($placeholders) LIMIT 1");
            $stmtU->execute($verifNorm['variations']);
            $existingUser = $stmtU->fetch();

            $userId = null;
            if ($verification->type === 'register') {
                if ($existingUser) {
                    // Existing user during register: ONLY mark verified, DO NOT overwrite password!
                    $stmtUpdateU = $pdo->prepare("UPDATE users SET phone_verified_at = NOW(), updated_at = NOW() WHERE id = ?");
                    $stmtUpdateU->execute([$existingUser->id]);
                    $userId = $existingUser->id;
                } else {
                    $accName = !empty($verification->name) ? $verification->name : 'مستخدم جديد';
                    $cleanDigits = preg_replace('/\D/', '', $targetPhone);
                    $email = 'user_' . $cleanDigits . '@azmarket.local';
                    $username = 'user_' . substr($cleanDigits, -6);
                    $pwd = !empty($verification->password) ? $verification->password : password_hash(uniqid('p_'), PASSWORD_BCRYPT);
                    $stmtInsU = $pdo->prepare("INSERT INTO users (name, phone, username, email, password, role, is_banned, phone_verified_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'user', 0, NOW(), NOW(), NOW())");
                    $stmtInsU->execute([$accName, $targetPhone, $username, $email, $pwd]);
                    $userId = $pdo->lastInsertId();
                }
            } elseif ($verification->type === 'reset_password') {
                if ($existingUser && !empty($verification->password)) {
                    $stmtUpdateP = $pdo->prepare("UPDATE users SET password = ?, phone_verified_at = NOW(), updated_at = NOW() WHERE id = ?");
                    $stmtUpdateP->execute([$verification->password, $existingUser->id]);
                    $userId = $existingUser->id;
                }
            }

            // Insert welcome notification on DB
            if ($userId) {
                try {
                    $notifId = sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
                        mt_rand(0, 0xffff), mt_rand(0, 0xffff),
                        mt_rand(0, 0xffff),
                        mt_rand(0, 0x0fff) | 0x4000,
                        mt_rand(0, 0x3fff) | 0x8000,
                        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
                    );
                    $notifData = json_encode([
                        'title' => '🎉 تم تأكيد وتفعيل الحساب بنجاح',
                        'body' => 'مرحباً بك في منصة للبيع! تم التحقق من هويتك وتفعيل تسجيل دخولك بنجاح.',
                        'link' => '/profile',
                    ], JSON_UNESCAPED_UNICODE);
                    $stmtNotif = $pdo->prepare("INSERT INTO notifications (id, type, notifiable_type, notifiable_id, data, created_at, updated_at) VALUES (?, 'App\\\\Notifications\\\\AuthSuccessNotification', 'App\\\\Models\\\\User', ?, ?, NOW(), NOW())");
                    $stmtNotif->execute([$notifId, $userId, $notifData]);
                } catch (Throwable $e) {}
            }

            // Log successful verified
            try {
                $stmtLog = $pdo->prepare("INSERT INTO whatsapp_message_logs (sender_phone, message_body, extracted_code, matched_verification_id, status, details, created_at, updated_at) VALUES (?, ?, ?, ?, 'verified', ?, NOW(), NOW())");
                $stmtLog->execute([$senderPhone, $messageBody, $extractedCode, $verification->id, "تم التحقق وتفعيل الحساب للرقم ({$targetPhone}) بنجاح."]);
            } catch (Throwable $e) {}

            echo json_encode([
                'success' => true,
                'verified' => true,
                'message' => 'تم التحقق من الحساب وتفعيله بنجاح!',
                'user_id' => $userId
            ]);
            exit;

        case 'validate-token':
            $token = $body['token'] ?? $_POST['token'] ?? $_GET['token'] ?? '';
            $token = trim((string)$token);
            if (empty($token)) {
                echo json_encode(['success' => true, 'authenticated' => false, 'user' => null]);
                exit;
            }

            $userRow = null;
            if (str_contains($token, '|')) {
                [$tId, $tPlain] = explode('|', $token, 2);
                $tHash = hash('sha256', $tPlain);
                $stmt = $pdo->prepare("SELECT u.* FROM users u JOIN personal_access_tokens pat ON pat.tokenable_id = u.id WHERE pat.id = ? AND pat.token = ? AND u.is_banned = 0 LIMIT 1");
                $stmt->execute([(int)$tId, $tHash]);
                $userRow = $stmt->fetch(PDO::FETCH_ASSOC);

                if ($userRow) {
                    try {
                        $pdo->prepare("UPDATE personal_access_tokens SET last_used_at = NOW() WHERE id = ?")->execute([(int)$tId]);
                    } catch (Throwable $e) {}
                }
            } else {
                $tHash = hash('sha256', $token);
                $stmt = $pdo->prepare("SELECT u.* FROM users u JOIN personal_access_tokens pat ON pat.tokenable_id = u.id WHERE (pat.token = ? OR pat.token = ?) AND u.is_banned = 0 LIMIT 1");
                $stmt->execute([$token, $tHash]);
                $userRow = $stmt->fetch(PDO::FETCH_ASSOC);
            }

            if ($userRow) {
                echo json_encode([
                    'success' => true,
                    'authenticated' => true,
                    'user' => [
                        'id' => (int)$userRow['id'],
                        'name' => $userRow['name'],
                        'username' => $userRow['username'] ?? ('user_' . substr(preg_replace('/\D/', '', $userRow['phone']), -6)),
                        'phone' => $userRow['phone'],
                        'role' => $userRow['role'] ?? 'user',
                        'avatar' => !empty($userRow['avatar']) ? (str_starts_with($userRow['avatar'], 'http') ? $userRow['avatar'] : ('https://lelbai.com/' . ltrim($userRow['avatar'], '/'))) : null,
                        'bio' => $userRow['bio'] ?? null,
                        'city_id' => $userRow['city_id'] ?? null,
                        'city_name' => $userRow['city_name'] ?? null,
                        'created_at' => $userRow['created_at'],
                    ]
                ]);
            } else {
                echo json_encode(['success' => true, 'authenticated' => false, 'user' => null]);
            }
            exit;

        case 'login-password':
            $lPhone = $body['phone'] ?? $_POST['phone'] ?? '';
            $lPassword = (string)($body['password'] ?? $_POST['password'] ?? '');
            $lUa = $body['user_agent'] ?? $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown Device';
            $lIp = $body['ip'] ?? $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1';

            if (empty($lPhone) || empty($lPassword)) {
                http_response_code(422);
                echo json_encode(['success' => false, 'message' => 'رقم الجوال وكلمة المرور مطلوبان.']);
                exit;
            }

            $norm = bridgeNormalizePhone((string)$lPhone);
            $pVars = $norm['variations'];
            $pMarks = implode(',', array_fill(0, count($pVars), '?'));

            $stmtUser = $pdo->prepare("SELECT * FROM users WHERE phone IN ({$pMarks}) LIMIT 1");
            $stmtUser->execute($pVars);
            $foundUser = $stmtUser->fetch(PDO::FETCH_ASSOC);

            if (!$foundUser) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'الحساب غير موجود.']);
                exit;
            }

            if (!empty($foundUser['is_banned'])) {
                http_response_code(403);
                echo json_encode(['success' => false, 'message' => 'تم حظر هذا الحساب من قبل الإدارة.']);
                exit;
            }

            $dbPass = (string)($foundUser['password'] ?? '');
            $isMatch = false;

            if (str_starts_with($dbPass, '$2y$') || str_starts_with($dbPass, '$2a$') || str_starts_with($dbPass, '$argon2')) {
                $isMatch = password_verify($lPassword, $dbPass);
            } elseif (strlen($dbPass) === 64) {
                $isMatch = hash('sha256', $lPassword) === $dbPass || $lPassword === $dbPass;
            } else {
                $isMatch = ($lPassword === $dbPass);
            }

            if (!$isMatch) {
                http_response_code(422);
                echo json_encode(['success' => false, 'message' => 'كلمة المرور غير صحيحة.']);
                exit;
            }

            // Create Sanctum Token
            $plainToken = bin2hex(random_bytes(20));
            $tokenHash = hash('sha256', $plainToken);

            $stmtTok = $pdo->prepare("INSERT INTO personal_access_tokens (tokenable_type, tokenable_id, name, token, abilities, ip_address, user_agent, created_at, updated_at) VALUES ('App\\\\Models\\\\User', ?, 'auth_token', ?, '[\"*\"]', ?, ?, NOW(), NOW())");
            $stmtTok->execute([(int)$foundUser['id'], $tokenHash, $lIp, $lUa]);
            $tokId = $pdo->lastInsertId();
            $fullToken = "{$tokId}|{$plainToken}";

            echo json_encode([
                'success' => true,
                'message' => 'تم تسجيل الدخول بنجاح.',
                'access_token' => $fullToken,
                'token_type' => 'Bearer',
                'user' => [
                    'id' => (int)$foundUser['id'],
                    'name' => $foundUser['name'],
                    'username' => $foundUser['username'] ?? ('user_' . substr(preg_replace('/\D/', '', $foundUser['phone']), -6)),
                    'phone' => $foundUser['phone'],
                    'role' => $foundUser['role'] ?? 'user',
                    'avatar' => !empty($foundUser['avatar']) ? (str_starts_with($foundUser['avatar'], 'http') ? $foundUser['avatar'] : ('https://lelbai.com/' . ltrim($foundUser['avatar'], '/'))) : null,
                    'city_id' => $foundUser['city_id'] ?? null,
                    'created_at' => $foundUser['created_at'],
                ]
            ]);
            exit;

        default:
            http_response_code(400);
            echo json_encode(['success' => false, 'error' => 'Unknown action: ' . $action]);
            break;
    }
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Server Error: ' . $e->getMessage()
    ]);
}