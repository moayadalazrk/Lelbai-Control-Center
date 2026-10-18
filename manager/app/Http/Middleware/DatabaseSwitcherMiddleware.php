<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\View;
use App\Services\LiveBridgeService;
use Symfony\Component\HttpFoundation\Response;

class DatabaseSwitcherMiddleware
{
    /**
     * Handle an incoming request.
     */
    public function handle(Request $request, Closure $next): Response
    {
        $defaultEnv = env('DEFAULT_DB_ENV', 'local');
        $activeEnv = session('active_db_env', $defaultEnv);

        $dbConnected = false;
        $dbError = null;
        $viaBridge = false;
        $dbHost = '127.0.0.1';
        $dbName = 'souq_al_sham';

        if ($activeEnv === 'production') {
            // Keep framework internal connection on local so framework never hangs on raw TCP socket
            try {
                DB::connection('mysql_local')->getPdo();
                Config::set('database.default', 'mysql_local');
                DB::setDefaultConnection('mysql_local');
            } catch (\Throwable $e2) {}

            $ping = LiveBridgeService::ping();
            if (!empty($ping['connected'])) {
                $dbConnected = true;
                $viaBridge = true;
                $dbHost = 'HTTPS Bridge (api.lelbai.com)';
                $dbName = $ping['database'] ?? 'u762212316_lelbai';
            } else {
                $dbConnected = false;
                $dbError = $ping['error'] ?? 'تعذر الاتصال بالجسر السحابي (bridge.php)';
            }
        } else {
            Config::set('database.default', 'mysql_local');
            DB::setDefaultConnection('mysql_local');
            $dbHost = Config::get("database.connections.mysql_local.host", '127.0.0.1');
            $dbName = Config::get("database.connections.mysql_local.database", 'souq_al_sham');

            try {
                DB::connection('mysql_local')->getPdo();
                $dbConnected = true;
            } catch (\Throwable $e) {
                $dbConnected = false;
                $dbError = $e->getMessage();
            }
        }

        // Share environment details globally with all views
        $pendingComplaintsCount = 0;
        try {
            if ($activeEnv === 'production') {
                $cachedCount = session('pending_complaints_count');
                $cachedTime = session('pending_complaints_count_time', 0);
                if ($cachedCount !== null && (time() - $cachedTime < 30)) {
                    $pendingComplaintsCount = (int)$cachedCount;
                } else {
                    $r = LiveBridgeService::query("SELECT COUNT(*) as c FROM contact_messages WHERE status = 'pending'");
                    $pendingComplaintsCount = (int)($r[0]->c ?? $r[0]['c'] ?? 0);
                    session(['pending_complaints_count' => $pendingComplaintsCount, 'pending_complaints_count_time' => time()]);
                }
            } else {
                $pendingComplaintsCount = \App\Models\ContactMessage::where('status', 'pending')->count();
            }
        } catch (\Throwable $e) {}

        View::share('pendingComplaintsCount', $pendingComplaintsCount);
        View::share('activeDbEnv', $activeEnv);
        View::share('dbConnected', $dbConnected);
        View::share('dbError', $dbError);
        View::share('viaBridge', $viaBridge);
        View::share('activeDbInfo', [
            'env' => $activeEnv,
            'connected' => $dbConnected,
            'via_bridge' => $viaBridge,
            'error' => $dbError,
            'is_production' => ($activeEnv === 'production'),
            'label' => ($activeEnv === 'production') ? 'السيرفر الحقيقي (Hostinger Live)' : 'سيرفر التطوير المحلي (Local DB)',
            'short_label' => ($activeEnv === 'production') ? 'سيرفر حقيقي (Bridge)' : 'سيرفر محلي (Local)',
            'host' => $dbHost,
            'database' => $dbName,
            'badge_class' => $dbConnected ? (($activeEnv === 'production') ? 'bg-primary' : 'bg-success') : 'bg-danger',
        ]);

        return $next($request);
    }
}