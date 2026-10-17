<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\DB;
use App\Services\LiveBridgeService;

class EnvironmentController extends Controller
{
    /**
     * Switch the active database environment (local vs production).
     */
    public function switch(Request $request, string $env)
    {
        $allowed = ['local', 'production'];

        if (!in_array($env, $allowed)) {
            return redirect()->to('/')->with('error', 'البيئة المحددة غير صالحة.');
        }

        $connectionName = ($env === 'production') ? 'mysql_production' : 'mysql_local';
        $envTitle = ($env === 'production') ? 'السيرفر الحقيقي (Hostinger Live)' : 'سيرفر التطوير المحلي (Local DB)';

        // Save active environment selection in session
        session(['active_db_env' => $env]);

        if ($env === 'production') {
            // 1. Check HTTPS Live Bridge First (Instantaneous response < 300ms)
            $ping = LiveBridgeService::ping();
            if (!empty($ping['connected'])) {
                $liveDbName = $ping['database'] ?? 'u762212316_lelbai';
                $listingsCount = $ping['listings_count'] ?? 0;
                $usersCount = $ping['users_count'] ?? 0;
                return redirect()->to('/')->with('success', "تم الاتصال بنجاح بـ: {$envTitle} عبر جسر HTTPS السحابي 🚀 (قاعدة البيانات: {$liveDbName} | الإعلانات: {$listingsCount} | المستخدمين: {$usersCount})");
            }

            // 2. Direct PDO check fallback
            try {
                DB::purge($connectionName);
                $pdo = DB::connection($connectionName)->getPdo();
                $dbName = DB::connection($connectionName)->getDatabaseName();
                return redirect()->to('/')->with('success', "تم التبديل والاتصال بنجاح بـ: {$envTitle} (قاعدة البيانات: {$dbName}) 🚀");
            } catch (\Throwable $e) {
                return redirect()->to('/')->with('warning', "تم التبديل إلى {$envTitle}، ولكن تعذر الاتصال المباشر. يرجى التأكد من رفع ملف bridge.php إلى مجلد public على السيرفر.");
            }
        }

        // Local environment switch
        try {
            DB::purge($connectionName);
            $pdo = DB::connection($connectionName)->getPdo();
            $dbName = DB::connection($connectionName)->getDatabaseName();

            return redirect()->to('/')->with('success', "تم التبديل والاتصال بنجاح بـ: {$envTitle} (قاعدة البيانات: {$dbName}) 🚀");
        } catch (\Throwable $e) {
            return redirect()->to('/')->with('error', "تم التبديل إلى {$envTitle}، لكن تعذر الاتصال: " . $e->getMessage());
        }
    }
}