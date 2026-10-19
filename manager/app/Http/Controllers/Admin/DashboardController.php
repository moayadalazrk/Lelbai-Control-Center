<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Listing;
use App\Models\User;
use App\Models\Message;
use App\Models\Category;
use App\Services\LiveBridgeService;

class DashboardController extends Controller
{
    public function index()
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $stats = [
            'total_listings' => 0,
            'active_listings' => 0,
            'pending_listings' => 0,
            'total_users' => 0,
            'banned_users' => 0,
            'total_messages' => 0,
            'total_categories' => 0,
        ];
        $recentListings = collect();
        $recentUsers = collect();

        if ($activeEnv === 'production') {
            try {
                // Fetch everything in 1 single HTTPS call with 2-minute caching
                $dashData = \Illuminate\Support\Facades\Cache::remember('dashboard_bridge_data', 120, function () {
                    return LiveBridgeService::getDashboardData();
                });

                if (!empty($dashData['success'])) {
                    $stats = $dashData['stats'] ?? $stats;

                    $recentListings = collect($dashData['recent_listings'] ?? [])->map(function ($row) {
                        $listing = new Listing((array)$row);
                        $listing->id = $row['id'] ?? null;
                        if (!empty($row['user_name'])) {
                            $user = new User(['name' => $row['user_name'], 'phone' => $row['user_phone'] ?? '']);
                            $listing->setRelation('user', $user);
                        }
                        if (!empty($row['category_name'])) {
                            $cat = new Category(['name_ar' => $row['category_name']]);
                            $listing->setRelation('category', $cat);
                        }
                        return $listing;
                    });

                    $recentUsers = collect($dashData['recent_users'] ?? [])->map(function ($row) {
                        $user = new User((array)$row);
                        $user->id = $row['id'] ?? null;
                        return $user;
                    });
                }
            } catch (\Throwable $e) {}
        } else {
            // Local DB direct queries
            try {
                $stats = [
                    'total_listings' => Listing::count(),
                    'active_listings' => Listing::where('status', 'active')->count(),
                    'pending_listings' => Listing::where('status', 'pending')->count(),
                    'total_users' => User::count(),
                    'banned_users' => User::where('is_banned', true)->count(),
                    'total_messages' => Message::count(),
                    'total_categories' => Category::count(),
                ];

                $recentListings = Listing::with(['user', 'category'])
                    ->orderBy('id', 'desc')
                    ->limit(6)
                    ->get();

                $recentUsers = User::orderBy('id', 'desc')
                    ->limit(5)
                    ->get();
            } catch (\Throwable $e) {}
        }

        return view('admin.dashboard', compact('stats', 'recentListings', 'recentUsers'));
    }
}