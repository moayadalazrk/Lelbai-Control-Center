<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Models\WhatsappInboundVerification;
use App\Models\WhatsappMessageLog;
use App\Services\LiveBridgeService;
use Illuminate\Http\Request;
use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class WhatsAppController extends Controller
{
    protected string $whatsappServerUrl;

    public function __construct()
    {
        $this->whatsappServerUrl = rtrim(env('WHATSAPP_SERVER_URL', 'http://127.0.0.1:5001'), '/');
    }

    public function index(Request $request)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $statusFilter = $request->input('status', 'all');
        $search = trim($request->input('search', ''));
        $logsSearch = trim($request->input('logs_search', ''));
        $activeTab = $request->input('tab', 'verifications');

        $perPage = 20;
        $verifPage = max(1, (int)$request->input('verifications_page', 1));
        $logsPage = max(1, (int)$request->input('logs_page', 1));

        $verifications = new LengthAwarePaginator([], 0, $perPage, $verifPage, ['path' => $request->url(), 'query' => $request->query(), 'pageName' => 'verifications_page']);
        $messageLogs = new LengthAwarePaginator([], 0, $perPage, $logsPage, ['path' => $request->url(), 'query' => $request->query(), 'pageName' => 'logs_page']);
        $totalVerifications = 0;
        $pendingVerifications = 0;
        $verifiedVerifications = 0;
        $expiredVerifications = 0;
        $totalLogs = 0;

        if ($activeEnv === 'production') {
            try {
                // 1. Stats Queries via Bridge
                $statsRows = LiveBridgeService::query("
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_verified = 0 AND expires_at > NOW() THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified,
                        SUM(CASE WHEN is_verified = 0 AND (expires_at <= NOW() OR expires_at IS NULL) THEN 1 ELSE 0 END) as expired
                    FROM whatsapp_inbound_verifications
                ");

                if (!empty($statsRows[0])) {
                    $st = (array)$statsRows[0];
                    $totalVerifications = (int)($st['total'] ?? 0);
                    $pendingVerifications = (int)($st['pending'] ?? 0);
                    $verifiedVerifications = (int)($st['verified'] ?? 0);
                    $expiredVerifications = (int)($st['expired'] ?? 0);
                }

                $logsStats = LiveBridgeService::query("SELECT COUNT(*) as total FROM whatsapp_message_logs");
                if (!empty($logsStats[0])) {
                    $totalLogs = (int)(((array)$logsStats[0])['total'] ?? 0);
                }

                // 2. Verifications Table Query with Filter & Search
                $whereClauses = [];
                $bindings = [];

                if ($search !== '') {
                    $whereClauses[] = "(phone LIKE ? OR name LIKE ? OR verification_code LIKE ?)";
                    $bindings[] = "%{$search}%";
                    $bindings[] = "%{$search}%";
                    $bindings[] = "%{$search}%";
                }

                if ($statusFilter === 'pending') {
                    $whereClauses[] = "is_verified = 0 AND expires_at > NOW()";
                } elseif ($statusFilter === 'verified') {
                    $whereClauses[] = "is_verified = 1";
                } elseif ($statusFilter === 'expired') {
                    $whereClauses[] = "is_verified = 0 AND (expires_at <= NOW() OR expires_at IS NULL)";
                }

                $whereSql = !empty($whereClauses) ? ' WHERE ' . implode(' AND ', $whereClauses) : '';

                $countRow = LiveBridgeService::query("SELECT COUNT(*) as cnt FROM whatsapp_inbound_verifications {$whereSql}", $bindings);
                $totalFiltered = (int)(((array)($countRow[0] ?? []))['cnt'] ?? 0);

                $offset = ($verifPage - 1) * $perPage;
                $vRows = LiveBridgeService::query("SELECT * FROM whatsapp_inbound_verifications {$whereSql} ORDER BY id DESC LIMIT {$perPage} OFFSET {$offset}", $bindings);

                $vModels = collect($vRows)->map(function ($row) {
                    $arr = (array)$row;
                    $item = new WhatsappInboundVerification($arr);
                    $item->id = $arr['id'] ?? null;
                    $item->is_verified = (bool)($arr['is_verified'] ?? 0);
                    $item->created_at = !empty($arr['created_at']) ? Carbon::parse($arr['created_at']) : null;
                    $item->updated_at = !empty($arr['updated_at']) ? Carbon::parse($arr['updated_at']) : null;
                    $item->expires_at = !empty($arr['expires_at']) ? Carbon::parse($arr['expires_at']) : null;
                    $item->verified_at = !empty($arr['verified_at']) ? Carbon::parse($arr['verified_at']) : null;
                    return $item;
                });

                $verifications = new LengthAwarePaginator($vModels, $totalFiltered, $perPage, $verifPage, [
                    'path' => $request->url(),
                    'query' => $request->query(),
                    'pageName' => 'verifications_page'
                ]);

                // 3. Message Logs Table Query
                $logWhereClauses = [];
                $logBindings = [];

                if ($logsSearch !== '') {
                    $logWhereClauses[] = "(sender_phone LIKE ? OR message_body LIKE ? OR extracted_code LIKE ?)";
                    $logBindings[] = "%{$logsSearch}%";
                    $logBindings[] = "%{$logsSearch}%";
                    $logBindings[] = "%{$logsSearch}%";
                }

                $logWhereSql = !empty($logWhereClauses) ? ' WHERE ' . implode(' AND ', $logWhereClauses) : '';

                $logCountRow = LiveBridgeService::query("SELECT COUNT(*) as cnt FROM whatsapp_message_logs {$logWhereSql}", $logBindings);
                $totalLogsFiltered = (int)(((array)($logCountRow[0] ?? []))['cnt'] ?? 0);

                $logOffset = ($logsPage - 1) * $perPage;
                $lRows = LiveBridgeService::query("SELECT * FROM whatsapp_message_logs {$logWhereSql} ORDER BY id DESC LIMIT {$perPage} OFFSET {$logOffset}", $logBindings);

                $lModels = collect($lRows)->map(function ($row) {
                    $arr = (array)$row;
                    $item = new WhatsappMessageLog($arr);
                    $item->id = $arr['id'] ?? null;
                    $item->created_at = !empty($arr['created_at']) ? Carbon::parse($arr['created_at']) : null;
                    $item->updated_at = !empty($arr['updated_at']) ? Carbon::parse($arr['updated_at']) : null;
                    return $item;
                });

                $messageLogs = new LengthAwarePaginator($lModels, $totalLogsFiltered, $perPage, $logsPage, [
                    'path' => $request->url(),
                    'query' => $request->query(),
                    'pageName' => 'logs_page'
                ]);

            } catch (\Throwable $e) {
                Log::error("WhatsAppController live bridge error: " . $e->getMessage());
            }
        } else {
            // Local DB direct queries
            try {
                // 1. Verifications Query
                $verificationsQuery = WhatsappInboundVerification::query();

                if ($search !== '') {
                    $verificationsQuery->where(function ($q) use ($search) {
                        $q->where('phone', 'like', "%{$search}%")
                          ->orWhere('name', 'like', "%{$search}%")
                          ->orWhere('verification_code', 'like', "%{$search}%");
                    });
                }

                if ($statusFilter === 'pending') {
                    $verificationsQuery->where('is_verified', false)
                                       ->where('expires_at', '>', now());
                } elseif ($statusFilter === 'verified') {
                    $verificationsQuery->where('is_verified', true);
                } elseif ($statusFilter === 'expired') {
                    $verificationsQuery->where('is_verified', false)
                                       ->where(function($q) {
                                           $q->where('expires_at', '<=', now())
                                             ->orWhereNull('expires_at');
                                       });
                }

                $verifications = $verificationsQuery->orderBy('id', 'desc')->paginate($perPage, ['*'], 'verifications_page');

                // 2. Inbound Message Logs Query
                $logsQuery = WhatsappMessageLog::query();

                if ($logsSearch !== '') {
                    $logsQuery->where(function ($q) use ($logsSearch) {
                        $q->where('sender_phone', 'like', "%{$logsSearch}%")
                          ->orWhere('message_body', 'like', "%{$logsSearch}%")
                          ->orWhere('extracted_code', 'like', "%{$logsSearch}%");
                    });
                }

                $messageLogs = $logsQuery->orderBy('id', 'desc')->paginate($perPage, ['*'], 'logs_page');

                // 3. Stats Calculation
                $now = now();
                $totalVerifications = WhatsappInboundVerification::count();
                $pendingVerifications = WhatsappInboundVerification::where('is_verified', false)
                    ->where('expires_at', '>', $now)
                    ->count();
                $verifiedVerifications = WhatsappInboundVerification::where('is_verified', true)->count();
                $expiredVerifications = WhatsappInboundVerification::where('is_verified', false)
                    ->where(function($q) use ($now) {
                        $q->where('expires_at', '<=', $now)
                          ->orWhereNull('expires_at');
                    })
                    ->count();
                $totalLogs = WhatsappMessageLog::count();
            } catch (\Throwable $e) {
                Log::error("WhatsAppController local query error: " . $e->getMessage());
            }
        }

        return view('admin.whatsapp.index', compact(
            'verifications',
            'messageLogs',
            'statusFilter',
            'search',
            'logsSearch',
            'totalVerifications',
            'pendingVerifications',
            'verifiedVerifications',
            'expiredVerifications',
            'totalLogs',
            'activeTab'
        ));
    }

    public function manualVerify(Request $request, $id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            $rows = LiveBridgeService::query("SELECT * FROM whatsapp_inbound_verifications WHERE id = ? LIMIT 1", [$id]);
            if (empty($rows[0])) {
                if ($request->wantsJson() || $request->ajax()) {
                    return response()->json(['message' => 'طلب التحقق غير موجود.'], 404);
                }
                return back()->with('error', 'طلب التحقق غير موجود.');
            }

            $v = (array)$rows[0];
            if (!empty($v['is_verified'])) {
                if ($request->wantsJson() || $request->ajax()) {
                    return response()->json(['message' => 'هذا الطلب تم التحقق منه مسبقاً.'], 400);
                }
                return back()->with('info', 'هذا الطلب تم التحقق منه مسبقاً.');
            }

            $phone = $v['phone'];
            $name = $v['name'] ?: 'مستخدم جديد';
            $password = $v['password'];
            $type = $v['type'] ?? 'register';

            // Activate on production
            LiveBridgeService::statement("UPDATE whatsapp_inbound_verifications SET is_verified = 1, verified_at = NOW(), updated_at = NOW() WHERE id = ?", [$id]);

            // Handle user record on production
            $userRows = LiveBridgeService::query("SELECT * FROM users WHERE phone = ? LIMIT 1", [$phone]);
            if (!empty($userRows[0])) {
                $u = (array)$userRows[0];
                if ($type === 'reset_password') {
                    LiveBridgeService::statement("UPDATE users SET password = ?, phone_verified_at = NOW(), updated_at = NOW() WHERE phone = ?", [
                        $password, $phone
                    ]);
                } else {
                    LiveBridgeService::statement("UPDATE users SET name = COALESCE(NULLIF(?, ''), name), phone_verified_at = NOW(), updated_at = NOW() WHERE phone = ?", [
                        $name, $phone
                    ]);
                }
            } else {
                $cleanDigits = preg_replace('/[^0-9]/', '', (string)$phone);
                $email = 'user_' . $cleanDigits . '@azmarket.local';
                $username = 'user_' . substr($cleanDigits, -6);
                LiveBridgeService::statement("INSERT INTO users (name, phone, username, email, password, role, is_banned, phone_verified_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'user', 0, NOW(), NOW(), NOW())", [
                    $name, $phone, $username, $email, $password
                ]);
            }

            // Log action on production
            LiveBridgeService::statement("INSERT INTO whatsapp_message_logs (sender_phone, message_body, extracted_code, matched_verification_id, status, details, created_at, updated_at) VALUES (?, ?, ?, ?, 'verified', ?, NOW(), NOW())", [
                $phone,
                '[تفعيل وتحقق يدوي من لوحة تحكم الإدارة]',
                $v['verification_code'] ?? '',
                $id,
                'تم التحقق وتفعيل الحساب يدوياً بنجاح بواسطة المدير عبر لوحة Manager'
            ]);

            if ($request->wantsJson() || $request->ajax()) {
                return response()->json([
                    'success' => true,
                    'message' => 'تم التحقق وتفعيل حساب الرقم (' . $phone . ') يدوياً بنجاح على سيرفر الإنتاج!',
                ]);
            }

            return back()->with('success', 'تم التحقق وتفعيل حساب الرقم (' . $phone . ') يدوياً بنجاح على سيرفر الإنتاج!');
        }

        // Local DB Manual Verify
        $verification = WhatsappInboundVerification::findOrFail($id);

        if ($verification->is_verified) {
            if ($request->wantsJson() || $request->ajax()) {
                return response()->json(['message' => 'هذا الطلب تم التحقق منه مسبقاً.'], 400);
            }
            return back()->with('info', 'هذا الطلب تم التحقق منه مسبقاً.');
        }

        $verification->is_verified = true;
        $verification->verified_at = now();
        $verification->save();

        $phone = $verification->phone;
        $user = User::where('phone', $phone)->first();

        if ($verification->type === 'register') {
            if ($user) {
                $user->name = $verification->name ?: $user->name;
                $user->phone_verified_at = now();
                $user->save();
            } else {
                $accountName = $verification->name ?: 'مستخدم جديد';
                $user = User::create([
                    'phone' => $phone,
                    'name' => $accountName,
                    'username' => User::generateUniqueUsername($accountName, $phone),
                    'email' => 'user_' . preg_replace('/[^0-9]/', '', $phone) . '@azmarket.local',
                    'password' => $verification->password,
                    'role' => 'user',
                    'is_banned' => false,
                    'phone_verified_at' => now(),
                ]);
            }
        } elseif ($verification->type === 'reset_password') {
            if ($user) {
                $user->password = $verification->password;
                $user->save();
            }
        }

        WhatsappMessageLog::create([
            'sender_phone' => $phone,
            'message_body' => '[تفعيل وتحقق يدوي من لوحة تحكم الإدارة]',
            'extracted_code' => $verification->verification_code,
            'matched_verification_id' => $verification->id,
            'status' => 'verified',
            'details' => 'تم التحقق وتفعيل الحساب يدوياً بنجاح بواسطة المدير عبر لوحة Manager',
        ]);

        if ($request->wantsJson() || $request->ajax()) {
            return response()->json([
                'success' => true,
                'message' => 'تم التحقق وتفعيل حساب الرقم (' . $phone . ') يدوياً بنجاح!',
            ]);
        }

        return back()->with('success', 'تم التحقق وتفعيل حساب الرقم (' . $phone . ') يدوياً بنجاح!');
    }

    public function destroyVerification(Request $request, $id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            $rows = LiveBridgeService::query("SELECT phone FROM whatsapp_inbound_verifications WHERE id = ? LIMIT 1", [$id]);
            $phone = !empty($rows[0]) ? (((array)$rows[0])['phone'] ?? $id) : $id;
            LiveBridgeService::statement("DELETE FROM whatsapp_inbound_verifications WHERE id = ?", [$id]);

            if ($request->wantsJson() || $request->ajax()) {
                return response()->json([
                    'success' => true,
                    'message' => 'تم حذف طلب التحقق للرقم (' . $phone . ') بنجاح من سيرفر الإنتاج.',
                ]);
            }

            return back()->with('success', 'تم حذف طلب التحقق للرقم (' . $phone . ') بنجاح من سيرفر الإنتاج.');
        }

        $verification = WhatsappInboundVerification::findOrFail($id);
        $phone = $verification->phone;
        $verification->delete();

        if ($request->wantsJson() || $request->ajax()) {
            return response()->json([
                'success' => true,
                'message' => 'تم حذف طلب التحقق للرقم (' . $phone . ') بنجاح.',
            ]);
        }

        return back()->with('success', 'تم حذف طلب التحقق للرقم (' . $phone . ') بنجاح.');
    }

    /**
     * Ultra-fast WhatsApp Service Query
     * Checks socket probe in <40ms to avoid blocking PHP when local service is off.
     */
    protected function queryWhatsApp(string $endpoint, string $method = 'GET', ?array $body = null, float $timeout = 3.0): array
    {
        $parsed = parse_url($this->whatsappServerUrl);
        $host = $parsed['host'] ?? '127.0.0.1';
        $port = (int)($parsed['port'] ?? 5001);

        // Fast socket probe (40ms) for local hosts
        if ($host === '127.0.0.1' || $host === 'localhost') {
            $probe = @fsockopen($host, $port, $errno, $errstr, 0.05);
            if (!$probe) {
                return ['success' => false, 'status' => 503, 'data' => null];
            }
            fclose($probe);
        }

        $url = rtrim($this->whatsappServerUrl, '/') . $endpoint;
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT_MS, 1000);
        curl_setopt($ch, CURLOPT_TIMEOUT_MS, (int)($timeout * 1000));
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);

        if ($body !== null) {
            $payload = json_encode($body, JSON_UNESCAPED_UNICODE);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Content-Length: ' . strlen($payload)
            ]);
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($response !== false && $httpCode >= 200 && $httpCode < 400) {
            $json = json_decode($response, true);
            if (is_array($json)) {
                return ['success' => true, 'status' => $httpCode, 'data' => $json];
            }
        }

        return ['success' => false, 'status' => 503, 'data' => null];
    }

    public function status()
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        // 1. If active environment is Production (Hostinger Live Server)
        if ($activeEnv === 'production') {
            try {
                $bridgeUrl = LiveBridgeService::getBridgeUrl();
                $secret = LiveBridgeService::getBridgeSecret();

                $bridgeRes = Http::timeout(3.5)
                    ->withHeaders(['X-Bridge-Secret' => $secret])
                    ->get($bridgeUrl, [
                        'action' => 'whatsapp_status',
                        'bridge_secret' => $secret,
                    ]);

                if ($bridgeRes->successful()) {
                    $data = $bridgeRes->json();
                    if (is_array($data) && isset($data['status'])) {
                        // Cache latest successful live status
                        Cache::put('last_valid_whatsapp_status_production', $data, now()->addMinutes(10));
                        return response()->json($data);
                    }
                }
            } catch (\Throwable $e) {
                Log::warning("WhatsApp status bridge query error: " . $e->getMessage());
            }

            // Fallback: Return last known valid production status to prevent UI flickering
            $cachedProd = Cache::get('last_valid_whatsapp_status_production');
            if ($cachedProd && is_array($cachedProd)) {
                $cachedProd['cached'] = true;
                return response()->json($cachedProd);
            }
        }

        // 2. Local socket query (Fast probe in <40ms)
        $res = $this->queryWhatsApp('/status', 'GET', null, 1.2);
        if ($res['success'] && is_array($res['data'])) {
            Cache::put('last_valid_whatsapp_status_local', $res['data'], now()->addMinutes(10));
            return response()->json($res['data']);
        }

        // Fallback for local environment
        if ($activeEnv === 'local') {
            $cachedLocal = Cache::get('last_valid_whatsapp_status_local');
            if ($cachedLocal && is_array($cachedLocal)) {
                $cachedLocal['cached'] = true;
                return response()->json($cachedLocal);
            }
        }

        // Final fallback to any last known production status if available
        $cachedAny = Cache::get('last_valid_whatsapp_status_production');
        if ($cachedAny && is_array($cachedAny)) {
            $cachedAny['cached'] = true;
            return response()->json($cachedAny);
        }

        return response()->json([
            'status' => 'disconnected',
            'qr' => null,
            'phone' => null,
            'total_accounts' => 0,
            'connected_accounts' => 0,
            'sessions' => [],
            'error' => 'خادم الواتساب غير متصل حالياً.',
        ]);
    }

    public function sessions()
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            $statusData = Cache::get('last_valid_whatsapp_status_production');
            if ($statusData && !empty($statusData['sessions'])) {
                return response()->json([
                    'success' => true,
                    'active_session_id' => $statusData['active_session_id'] ?? null,
                    'sessions' => $statusData['sessions'],
                ]);
            }
        }

        $res = $this->queryWhatsApp('/sessions', 'GET', null, 1.5);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data']);
        }

        return response()->json(['success' => false, 'count' => 0, 'sessions' => []], 200);
    }

    public function createSession(Request $request)
    {
        $name = $request->input('name');
        $res = $this->queryWhatsApp('/sessions/create', 'POST', ['name' => $name], 3.0);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json([
            'success' => false,
            'message' => 'خادم الواتساب غير مشغل على لابتوبك حالياً. يرجى تشغيل ملف start_whatsapp.bat أولاً.',
        ], 200);
    }

    public function activateSession(Request $request, $id)
    {
        $res = $this->queryWhatsApp("/sessions/{$id}/activate", 'POST', null, 2.5);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json([
            'success' => false,
            'message' => 'فشل تنشيط الرقم (تأكد من تشغيل خادم الواتساب على لابتوبك).',
        ], 200);
    }

    public function restartSession(Request $request, $id)
    {
        $res = $this->queryWhatsApp("/sessions/{$id}/restart", 'POST', null, 2.5);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json([
            'success' => false,
            'message' => 'فشل إعادة تشغيل الجلسة (تأكد من تشغيل خادم الواتساب).',
        ], 200);
    }

    public function requestPairingCode(Request $request, $id)
    {
        $phone = $request->input('phone');
        $res = $this->queryWhatsApp("/sessions/{$id}/pairing-code", 'POST', ['phone' => $phone], 5.0);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json([
            'success' => false,
            'message' => 'فشل الاتصال بخادم الواتساب لتوليد رمز الربط (تأكد من تشغيل خادم الواتساب).',
        ], 200);
    }

    public function deleteSession(Request $request, $id)
    {
        $res = $this->queryWhatsApp("/sessions/{$id}", 'DELETE', null, 2.5);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json([
            'success' => false,
            'message' => 'فشل الاتصال بخادم الواتساب لحذف الجلسة (تأكد من تشغيل خادم الواتساب على لابتوبك).',
        ], 200);
    }

    public function logout()
    {
        $res = $this->queryWhatsApp('/logout', 'POST', null, 2.0);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json(['message' => 'تم تسجيل الخروج محلياً.'], 200);
    }

    public function checkNumber(Request $request)
    {
        $phone = $request->input('phone');
        $res = $this->queryWhatsApp('/check-number', 'POST', ['phone' => $phone], 3.0);
        if ($res['success'] && is_array($res['data'])) {
            return response()->json($res['data'], 200);
        }

        return response()->json([
            'exists' => false,
            'message' => 'خادم الواتساب غير متصل حالياً (تأكد من تشغيل خادم الواتساب على لابتوبك).',
        ], 200);
    }
}