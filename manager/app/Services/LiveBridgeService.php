<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class LiveBridgeService
{
    public static function getBridgeUrl(): string
    {
        return env('LIVE_BRIDGE_URL', 'https://api.lelbai.com/public/bridge.php');
    }

    public static function getBridgeSecret(): string
    {
        return env('BRIDGE_SECRET', 'lelbai_bridge_secure_key_2026_9984');
    }

    /**
     * Check connection and stats from Live Bridge over HTTPS (cached for 45 seconds).
     */
    public static function ping(): array
    {
        $cached = session('live_bridge_ping');
        if ($cached && isset($cached['_time']) && (time() - $cached['_time'] < 45)) {
            return $cached;
        }

        $url = self::getBridgeUrl();
        $secret = self::getBridgeSecret();

        try {
            $res = Http::timeout(3)
                ->withHeaders(['X-Bridge-Secret' => $secret])
                ->get($url, [
                    'action' => 'ping',
                    'bridge_secret' => $secret,
                ]);

            if ($res->successful()) {
                $data = $res->json();
                if (!empty($data['connected'])) {
                    $data['_time'] = time();
                    session(['live_bridge_ping' => $data]);
                    return $data;
                }
            }
        } catch (\Throwable $e) {}

        return [
            'success' => false,
            'connected' => false,
            'error' => 'تعذر الاتصال بملف الجسر على السيرفر (bridge.php).',
        ];
    }

    /**
     * Fetch complete dashboard data (all stats, recent listings, recent users) in a single fast call (<300ms).
     */
    public static function getDashboardData(): array
    {
        $url = self::getBridgeUrl();
        $secret = self::getBridgeSecret();

        try {
            $res = Http::timeout(4)
                ->withHeaders(['X-Bridge-Secret' => $secret])
                ->get($url, [
                    'action' => 'dashboard_data',
                    'bridge_secret' => $secret,
                ]);

            if ($res->successful()) {
                return $res->json();
            }
        } catch (\Throwable $e) {
            Log::error("LiveBridge getDashboardData error: " . $e->getMessage());
        }

        return [];
    }

    /**
     * Execute a SELECT query against live database over HTTPS.
     */
    public static function query(string $sql, array $bindings = []): array
    {
        $url = self::getBridgeUrl();
        $secret = self::getBridgeSecret();

        try {
            $res = Http::timeout(8)
                ->withHeaders(['X-Bridge-Secret' => $secret])
                ->asJson()
                ->post($url, [
                    'action' => 'query',
                    'bridge_secret' => $secret,
                    'sql' => $sql,
                    'bindings' => $bindings,
                ]);

            if ($res->successful()) {
                $data = $res->json();
                return $data['rows'] ?? [];
            }
        } catch (\Throwable $e) {
            Log::error("LiveBridge query error: " . $e->getMessage());
        }

        return [];
    }

    /**
     * Execute an INSERT/UPDATE/DELETE statement against live database over HTTPS.
     */
    public static function statement(string $sql, array $bindings = []): int
    {
        $url = self::getBridgeUrl();
        $secret = self::getBridgeSecret();

        try {
            $res = Http::timeout(8)
                ->withHeaders(['X-Bridge-Secret' => $secret])
                ->asJson()
                ->post($url, [
                    'action' => 'statement',
                    'bridge_secret' => $secret,
                    'sql' => $sql,
                    'bindings' => $bindings,
                ]);

            if ($res->successful()) {
                $data = $res->json();
                return (int)($data['affected'] ?? 0);
            }
        } catch (\Throwable $e) {
            Log::error("LiveBridge statement error: " . $e->getMessage());
        }

        return 0;
    }
}