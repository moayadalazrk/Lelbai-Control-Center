<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Listing;
use App\Models\Category;
use App\Models\City;
use App\Services\LiveBridgeService;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class ListingController extends Controller
{
    public function index(Request $request)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $listings = new \Illuminate\Pagination\LengthAwarePaginator([], 0, 20);
        $categories = collect();
        $cities = collect();
        $counts = [
            'all' => 0,
            'active' => 0,
            'pending' => 0,
            'rejected' => 0,
            'suspended' => 0,
            'expiring_soon' => 0,
            'flagged' => 0,
            'today' => 0,
        ];
        $isAiAutoEnabled = true;
        $selectedCategoryObj = null;

        if ($activeEnv === 'production') {
            try {
                // 1. جلب شجرة الأقسام وإحصائياتها المباشرة من الإنتاج
                $catRows = LiveBridgeService::query("SELECT id, name_ar, slug, icon, parent_id, sort_order FROM categories ORDER BY sort_order ASC, name_ar ASC");
                $directCountRows = LiveBridgeService::query("SELECT category_id, COUNT(*) as count FROM listings WHERE deleted_at IS NULL GROUP BY category_id");
                
                $directCounts = [];
                foreach ($directCountRows as $d) {
                    $cId = is_array($d) ? ($d['category_id'] ?? null) : ($d->category_id ?? null);
                    $cCount = is_array($d) ? ($d['count'] ?? 0) : ($d->count ?? 0);
                    if ($cId) {
                        $directCounts[$cId] = (int)$cCount;
                    }
                }

                $childrenByParent = [];
                $rawCategories = collect($catRows)->map(function ($row) use (&$childrenByParent) {
                    $r = (array)$row;
                    $cat = new Category();
                    $cat->forceFill($r);
                    $cat->id = (int)$r['id'];
                    $cat->parent_id = !empty($r['parent_id']) ? (int)$r['parent_id'] : null;
                    if ($cat->parent_id) {
                        $childrenByParent[$cat->parent_id][] = $cat->id;
                    }
                    return $cat;
                });
                $categoryMap = $rawCategories->keyBy('id');

                $calcTotalCount = function ($catId, $visited = []) use (&$calcTotalCount, $childrenByParent, $directCounts) {
                    if (in_array($catId, $visited)) return 0;
                    $visited[] = $catId;
                    $total = $directCounts[$catId] ?? 0;
                    if (isset($childrenByParent[$catId])) {
                        foreach ($childrenByParent[$catId] as $childId) {
                            $total += $calcTotalCount($childId, $visited);
                        }
                    }
                    return $total;
                };

                foreach ($rawCategories as $cat) {
                    $cat->direct_listings_count = $directCounts[$cat->id] ?? 0;
                    $cat->total_listings_count = $calcTotalCount($cat->id);
                    if ($cat->parent_id && $categoryMap->has($cat->parent_id)) {
                        $cat->setRelation('parents', collect([$categoryMap->get($cat->parent_id)]));
                    } else {
                        $cat->setRelation('parents', collect());
                    }

                    $childModels = collect();
                    if (isset($childrenByParent[$cat->id])) {
                        foreach ($childrenByParent[$cat->id] as $childId) {
                            if ($categoryMap->has($childId)) {
                                $childModels->push($categoryMap->get($childId));
                            }
                        }
                    }
                    $cat->setRelation('children', $childModels);
                }
                $categories = $rawCategories->whereNull('parent_id')->values();

                // 2. جلب المدن
                $cityRows = LiveBridgeService::query("SELECT id, name_ar, slug, is_active FROM cities WHERE is_active = 1 ORDER BY name_ar ASC");
                $cities = collect($cityRows)->map(function ($row) {
                    return new City((array)$row);
                });

                // 3. حساب عدادات الحالات الشاملة
                $cutoff30Days = Carbon::now()->subDays(30)->toDateTimeString();
                $cutoffExpiringSoon = Carbon::now()->subDays(25)->toDateTimeString();
                $todayCutoff = Carbon::now()->subHours(24)->toDateTimeString();

                $countRow = LiveBridgeService::query("
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
                ", [$todayCutoff, $cutoffExpiringSoon, $cutoff30Days])[0] ?? [];

                $cArr = (array)$countRow;
                $counts = [
                    'all' => (int)($cArr['total_all'] ?? 0),
                    'active' => (int)($cArr['total_active'] ?? 0),
                    'pending' => (int)($cArr['total_pending'] ?? 0),
                    'rejected' => (int)($cArr['total_rejected'] ?? 0),
                    'suspended' => (int)($cArr['total_suspended'] ?? 0),
                    'flagged' => (int)($cArr['total_flagged'] ?? 0),
                    'today' => (int)($cArr['total_today'] ?? 0),
                    'expiring_soon' => (int)($cArr['total_expiring_soon'] ?? 0),
                ];

                // 4. بناء شروط الفلترة
                $whereClauses = ['l.deleted_at IS NULL'];
                $bindings = [];

                if ($request->filled('category_id')) {
                    $catId = (int)$request->category_id;
                    $selectedCategoryObj = $categoryMap->get($catId);
                    $allCatIds = [$catId];
                    if ($selectedCategoryObj) {
                        $gatherChildren = function ($cId) use (&$gatherChildren, $childrenByParent) {
                            $ids = [];
                            if (isset($childrenByParent[$cId])) {
                                foreach ($childrenByParent[$cId] as $childId) {
                                    $ids[] = $childId;
                                    $ids = array_merge($ids, $gatherChildren($childId));
                                }
                            }
                            return $ids;
                        };
                        $allCatIds = array_merge($allCatIds, $gatherChildren($catId));
                    }
                    $placeholders = implode(',', array_fill(0, count($allCatIds), '?'));
                    $whereClauses[] = "l.category_id IN ({$placeholders})";
                    $bindings = array_merge($bindings, $allCatIds);
                }

                if ($request->filled('city_id')) {
                    $whereClauses[] = "l.city_id = ?";
                    $bindings[] = (int)$request->city_id;
                }

                $status = $request->input('status');
                if ($status === 'expiring_soon') {
                    $whereClauses[] = "l.created_at <= ? AND l.created_at >= ?";
                    $bindings[] = $cutoffExpiringSoon;
                    $bindings[] = $cutoff30Days;
                } elseif ($status && in_array($status, ['active', 'pending', 'rejected', 'suspended'])) {
                    $whereClauses[] = "l.status = ?";
                    $bindings[] = $status;
                }

                if ($request->input('ai_status') === 'flagged') {
                    $whereClauses[] = "l.ai_status = 'flagged'";
                } elseif ($request->filled('ai_status')) {
                    $whereClauses[] = "l.ai_status = ?";
                    $bindings[] = $request->ai_status;
                }

                $source = $request->input('source');
                if ($source === 'organic') {
                    $whereClauses[] = "l.is_scraped = 0";
                } elseif ($source === 'bot') {
                    $whereClauses[] = "l.is_scraped = 1";
                } elseif ($source === 'facebook') {
                    $whereClauses[] = "l.source_url LIKE '%facebook.com%'";
                }

                if ($request->filled('search')) {
                    $search = trim($request->search);
                    $searchLike = "%{$search}%";
                    $whereClauses[] = "(l.title LIKE ? OR l.description LIKE ? OR l.id = ? OR l.uuid = ? OR l.contact_phone LIKE ? OR u.name LIKE ? OR u.phone LIKE ? OR c.name_ar LIKE ?)";
                    $bindings[] = $searchLike;
                    $bindings[] = $searchLike;
                    $bindings[] = is_numeric($search) ? (int)$search : 0;
                    $bindings[] = $search;
                    $bindings[] = $searchLike;
                    $bindings[] = $searchLike;
                    $bindings[] = $searchLike;
                    $bindings[] = $searchLike;
                }

                $whereSql = implode(' AND ', $whereClauses);

                // إجمالي النتائج بعد الفلترة
                $countSql = "
                    SELECT COUNT(*) as total
                    FROM listings l
                    LEFT JOIN users u ON l.user_id = u.id
                    LEFT JOIN categories c ON l.category_id = c.id
                    LEFT JOIN cities ci ON l.city_id = ci.id
                    WHERE {$whereSql}
                ";
                $countRes = LiveBridgeService::query($countSql, $bindings);
                $totalFiltered = (int)(is_array($countRes[0] ?? null) ? ($countRes[0]['total'] ?? 0) : ($countRes[0]->total ?? 0));

                // الترتيب
                $sort = $request->input('sort', 'newest_created');
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

                $page = max(1, (int)$request->input('page', 1));
                $perPage = 20;
                $offset = ($page - 1) * $perPage;

                $dataSql = "
                    SELECT 
                        l.*,
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
                $rows = LiveBridgeService::query($dataSql, $bindings);

                $items = collect($rows)->map(function ($row) use ($categoryMap) {
                    $rowArr = (array)$row;
                    $listing = new Listing();
                    $listing->forceFill($rowArr);
                    $listing->id = (int)$rowArr['id'];
                    $listing->created_at = !empty($rowArr['created_at']) ? Carbon::parse($rowArr['created_at']) : null;
                    $listing->updated_at = !empty($rowArr['updated_at']) ? Carbon::parse($rowArr['updated_at']) : null;
                    $listing->published_at = !empty($rowArr['published_at']) ? Carbon::parse($rowArr['published_at']) : null;
                    $listing->expires_at = !empty($rowArr['expires_at']) ? Carbon::parse($rowArr['expires_at']) : null;

                    // User relation
                    if (!empty($rowArr['user_name']) || !empty($rowArr['user_id'])) {
                        $user = new \App\Models\User([
                            'name' => $rowArr['user_name'] ?? '',
                            'phone' => $rowArr['user_phone'] ?? '',
                            'username' => $rowArr['user_username'] ?? '',
                            'is_bot' => (bool)($rowArr['user_is_bot'] ?? false),
                        ]);
                        $user->id = $rowArr['user_id'] ?? null;
                        $listing->setRelation('user', $user);
                    } else {
                        $listing->setRelation('user', null);
                    }

                    // Category relation
                    $catId = !empty($rowArr['category_id']) ? (int)$rowArr['category_id'] : null;
                    if ($catId && $categoryMap->has($catId)) {
                        $listing->setRelation('category', $categoryMap->get($catId));
                    } elseif (!empty($rowArr['category_name_ar'])) {
                        $cat = new Category();
                        $cat->forceFill([
                            'id' => $catId,
                            'name_ar' => $rowArr['category_name_ar'],
                            'slug' => $rowArr['category_slug'] ?? '',
                            'icon' => $rowArr['category_icon'] ?? '',
                        ]);
                        $cat->id = $catId;
                        $cat->setRelation('parents', collect());
                        $cat->setRelation('children', collect());
                        $listing->setRelation('category', $cat);
                    } else {
                        $listing->setRelation('category', null);
                    }

                    // City relation
                    if (!empty($rowArr['city_id']) || !empty($rowArr['city_name_ar'])) {
                        $city = new City([
                            'name_ar' => $rowArr['city_name_ar'] ?? '',
                            'slug' => $rowArr['city_slug'] ?? '',
                        ]);
                        $city->id = $rowArr['city_id'] ?? null;
                        $listing->setRelation('city', $city);
                    } else {
                        $listing->setRelation('city', null);
                    }

                    // Primary Image relation
                    if (!empty($rowArr['primary_image_path'])) {
                        $pImg = new \App\Models\ListingImage([
                            'image_path' => $rowArr['primary_image_path'],
                            'is_primary' => true,
                        ]);
                        $listing->setRelation('primaryImage', $pImg);
                        $listing->setRelation('images', collect([$pImg]));
                    } else {
                        $listing->setRelation('primaryImage', null);
                        $listing->setRelation('images', collect());
                    }

                    return $listing;
                });

                $listings = new \Illuminate\Pagination\LengthAwarePaginator(
                    $items,
                    $totalFiltered,
                    $perPage,
                    $page,
                    ['path' => $request->url(), 'query' => $request->query()]
                );
            } catch (\Throwable $e) {
                \Illuminate\Support\Facades\Log::error("Production ListingController error: " . $e->getMessage());
            }
        } else {
            // Local Database direct queries
            try {
                $query = Listing::with(['user', 'category.parents', 'city', 'primaryImage', 'images']);

                $directCounts = DB::table('listings')
                    ->select('category_id', DB::raw('count(*) as count'))
                    ->whereNull('deleted_at')
                    ->groupBy('category_id')
                    ->pluck('count', 'category_id')
                    ->toArray();

                $rawCategories = Category::with(['children.children', 'parents'])->orderBy('sort_order')->get();
                $categoryMap = $rawCategories->keyBy('id');

                $calcTotalCount = function ($cat) use (&$calcTotalCount, $categoryMap, $directCounts) {
                    $total = $directCounts[$cat->id] ?? 0;
                    if ($cat->children && $cat->children->isNotEmpty()) {
                        foreach ($cat->children as $child) {
                            $fullChild = $categoryMap->get($child->id) ?? $child;
                            $total += $calcTotalCount($fullChild);
                        }
                    }
                    return $total;
                };

                foreach ($rawCategories as $cat) {
                    $cat->direct_listings_count = $directCounts[$cat->id] ?? 0;
                    $cat->total_listings_count = $calcTotalCount($cat);
                }

                $categories = $rawCategories->whereNull('parent_id')->values();

                if ($request->filled('category_id')) {
                    $catId = (int)$request->category_id;
                    $selectedCategoryObj = $categoryMap->get($catId) ?? Category::find($catId);
                    if ($selectedCategoryObj) {
                        $allCatIds = array_values(array_unique(array_merge([$selectedCategoryObj->id], $selectedCategoryObj->getAllChildrenIds())));
                        $query->whereIn('category_id', $allCatIds);
                    }
                }

                if ($request->filled('city_id')) {
                    $query->where('city_id', $request->city_id);
                }

                $status = $request->input('status');
                $cutoff30Days = Carbon::now()->subDays(30);
                $cutoffExpiringSoon = Carbon::now()->subDays(25);

                if ($status === 'expiring_soon') {
                    $query->where('created_at', '<=', $cutoffExpiringSoon)
                          ->where('created_at', '>=', $cutoff30Days);
                } elseif ($status && in_array($status, ['active', 'pending', 'rejected', 'suspended'])) {
                    $query->where('status', $status);
                }

                if ($request->input('ai_status') === 'flagged') {
                    $query->where('ai_status', 'flagged');
                } elseif ($request->filled('ai_status')) {
                    $query->where('ai_status', $request->ai_status);
                }

                $source = $request->input('source');
                if ($source === 'organic') {
                    $query->where('is_scraped', false);
                } elseif ($source === 'bot') {
                    $query->where('is_scraped', true);
                } elseif ($source === 'facebook') {
                    $query->where('source_url', 'like', '%facebook.com%');
                }

                if ($request->filled('search')) {
                    $search = trim($request->search);
                    $query->where(function ($q) use ($search) {
                        $q->where('title', 'like', "%{$search}%")
                          ->orWhere('description', 'like', "%{$search}%")
                          ->orWhere('id', $search)
                          ->orWhere('uuid', $search)
                          ->orWhere('contact_phone', 'like', "%{$search}%")
                          ->orWhereHas('user', function ($u) use ($search) {
                              $u->where('name', 'like', "%{$search}%")
                                ->orWhere('phone', 'like', "%{$search}%")
                                ->orWhere('username', 'like', "%{$search}%");
                          })
                          ->orWhereHas('category', function ($c) use ($search) {
                              $c->where('name_ar', 'like', "%{$search}%");
                          });
                    });
                }

                $sort = $request->input('sort', 'newest_created');
                if ($sort === 'oldest_created') {
                    $query->orderBy('created_at', 'asc')->orderBy('id', 'asc');
                } elseif ($sort === 'most_viewed') {
                    $query->orderBy('views_count', 'desc')->orderBy('id', 'desc');
                } elseif ($sort === 'most_impressions') {
                    $query->orderBy('impressions_count', 'desc')->orderBy('id', 'desc');
                } elseif ($sort === 'price_desc') {
                    $query->orderBy('price', 'desc')->orderBy('id', 'desc');
                } elseif ($sort === 'price_asc') {
                    $query->orderBy('price', 'asc')->orderBy('id', 'desc');
                } else {
                    $query->orderBy('created_at', 'desc')->orderBy('id', 'desc');
                }

                $listings = $query->paginate(20)->withQueryString();

                $counts = [
                    'all' => Listing::count(),
                    'active' => Listing::where('status', 'active')->count(),
                    'pending' => Listing::where('status', 'pending')->count(),
                    'rejected' => Listing::where('status', 'rejected')->count(),
                    'suspended' => Listing::where('status', 'suspended')->count(),
                    'expiring_soon' => Listing::where('created_at', '<=', $cutoffExpiringSoon)->where('created_at', '>=', $cutoff30Days)->count(),
                    'flagged' => Listing::where('ai_status', 'flagged')->count(),
                    'today' => Listing::where('created_at', '>=', Carbon::now()->subHours(24))->count(),
                ];

                $cities = City::where('is_active', true)->orderBy('name_ar')->get();
                $aiAutoSetting = \App\Models\Setting::get('ai_auto_moderation_enabled', '1');
                $isAiAutoEnabled = filter_var($aiAutoSetting, FILTER_VALIDATE_BOOLEAN) || $aiAutoSetting === '1';
            } catch (\Throwable $e) {
                // Handled gracefully
            }
        }

        return view('admin.listings.index', compact(
            'listings',
            'categories',
            'cities',
            'counts',
            'isAiAutoEnabled',
            'selectedCategoryObj'
        ));
    }

    public function toggleAiAutoModeration(Request $request)
    {
        $current = \App\Models\Setting::get('ai_auto_moderation_enabled', '1');
        $isCurrentlyEnabled = filter_var($current, FILTER_VALIDATE_BOOLEAN) || $current === '1';
        $newVal = $isCurrentlyEnabled ? '0' : '1';

        \App\Models\Setting::set('ai_auto_moderation_enabled', $newVal);

        $msg = $newVal === '1' 
            ? 'تم تفعيل الفحص التلقائي بالذكاء الاصطناعي بنجاح 🤖✅' 
            : 'تم إيقاف الفحص التلقائي بالذكاء الاصطناعي ⏸️';

        return redirect()->back()->with('success', $msg);
    }

    public function updateStatus(Request $request, $id)
    {
        $request->validate([
            'status' => 'required|in:active,suspended,pending,rejected',
            'rejection_reason' => 'nullable|string|max:500',
        ]);

        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $status = $request->status;
        $reason = $request->input('rejection_reason');

        if ($activeEnv === 'production') {
            if ($status === 'rejected') {
                LiveBridgeService::statement(
                    "UPDATE listings SET status = 'rejected', rejection_reason = ?, previous_rejection_reason = ? WHERE id = ?",
                    [$reason, $reason, (int)$id]
                );
            } elseif ($status === 'active') {
                LiveBridgeService::statement(
                    "UPDATE listings SET status = 'active', rejection_reason = NULL, previous_rejection_reason = NULL, published_at = COALESCE(published_at, NOW()) WHERE id = ?",
                    [(int)$id]
                );
            } else {
                LiveBridgeService::statement(
                    "UPDATE listings SET status = ? WHERE id = ?",
                    [$status, (int)$id]
                );
            }

            $statusText = [
                'active' => 'تم قبول وتفعيل الإعلان بنجاح على السيرفر.',
                'suspended' => 'تم إيقاف الإعلان فورياً على السيرفر.',
                'rejected' => 'تم رفض الإعلان وحجبه عن الظهور على السيرفر.',
                'pending' => 'تم نقل الإعلان بانتظار المراجعة.',
            ];

            return redirect()->back()->with('success', $statusText[$status] ?? 'تم تحديث حالة الإعلان.');
        }

        $listing = Listing::findOrFail($id);
        $wasPreviouslyRejected = !empty($listing->previous_rejection_reason) || $listing->status === 'rejected';
        $listing->status = $request->status;

        if ($request->status === 'rejected') {
            $listing->rejection_reason = $reason;
            $listing->previous_rejection_reason = $reason;
            $listing->timestamps = false;
            $listing->save();
            $listing->timestamps = true;
        } elseif ($request->status === 'active') {
            $listing->rejection_reason = null;
            $listing->previous_rejection_reason = null;

            if (empty($listing->published_at)) {
                $listing->published_at = now();
                $listing->updated_at = now();
                $listing->save();
            } else {
                $listing->timestamps = false;
                $listing->save();
                $listing->timestamps = true;
            }
        } else {
            $listing->timestamps = false;
            $listing->save();
            $listing->timestamps = true;
        }

        $statusText = [
            'active' => 'تم قبول وتفعيل الإعلان بنجاح.',
            'suspended' => 'تم إيقاف الإعلان فورياً.',
            'rejected' => 'تم رفض الإعلان وحجبه عن الظهور.',
            'pending' => 'تم نقل الإعلان بانتظار المراجعة.',
        ];

        return redirect()->back()->with('success', $statusText[$request->status] ?? 'تم تحديث حالة الإعلان.');
    }

    public function bulkAction(Request $request)
    {
        $request->validate([
            'action' => 'required|in:delete,activate,suspend',
            'listing_ids' => 'required|array',
            'listing_ids.*' => 'integer',
        ]);

        $ids = $request->input('listing_ids', []);
        $action = $request->input('action');
        $count = count($ids);

        if ($count === 0) {
            return redirect()->back()->with('warning', 'لم تقم بتحديد أي إعلان لتطبيق الإجراء عليه.');
        }

        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            $placeholders = implode(',', array_fill(0, count($ids), '?'));
            if ($action === 'delete') {
                LiveBridgeService::statement("UPDATE listings SET deleted_at = NOW() WHERE id IN ({$placeholders})", $ids);
                return redirect()->back()->with('success', "تم حذف {$count} إعلان بنجاح من السيرفر.");
            } elseif ($action === 'activate') {
                LiveBridgeService::statement("UPDATE listings SET status = 'active', rejection_reason = NULL, previous_rejection_reason = NULL, published_at = COALESCE(published_at, NOW()) WHERE id IN ({$placeholders})", $ids);
                return redirect()->back()->with('success', "تم قبول وتفعيل {$count} إعلان بنجاح على السيرفر.");
            } elseif ($action === 'suspend') {
                LiveBridgeService::statement("UPDATE listings SET status = 'suspended' WHERE id IN ({$placeholders})", $ids);
                return redirect()->back()->with('success', "تم إيقاف {$count} إعلان بنجاح على السيرفر.");
            }
        }

        if ($action === 'delete') {
            $listings = Listing::with('images')->whereIn('id', $ids)->get();
            foreach ($listings as $listing) {
                if ($listing->images) {
                    foreach ($listing->images as $img) {
                        $imgPath = ltrim($img->image_path, '/');
                        $fullPublic = public_path('storage/' . $imgPath);
                        if (file_exists($fullPublic)) @unlink($fullPublic);
                        $img->delete();
                    }
                }
                $listing->delete();
            }
            return redirect()->back()->with('success', "تم حذف {$count} إعلان بنجاح.");
        } elseif ($action === 'activate') {
            Listing::whereIn('id', $ids)->update([
                'status' => 'active',
                'rejection_reason' => null,
                'previous_rejection_reason' => null,
            ]);
            return redirect()->back()->with('success', "تم قبول وتفعيل {$count} إعلان بنجاح.");
        } elseif ($action === 'suspend') {
            Listing::whereIn('id', $ids)->update(['status' => 'suspended']);
            return redirect()->back()->with('success', "تم إيقاف {$count} إعلان بنجاح.");
        }

        return redirect()->back();
    }

    public function recheckAiModeration($id)
    {
        $listing = Listing::with('images')->findOrFail($id);
        $result = \App\Services\AiModerationService::moderateListingDirect($listing);

        $isSafe = $result['is_safe'] ?? false;
        $summary = $result['summary'] ?? ($isSafe ? 'الإعلان سليم ومطابق للشروط' : 'تم رصد مخالفة');

        $msg = $isSafe 
            ? "تم فحص الإعلان #{$listing->id} بالذكاء الاصطناعي: {$summary} ✅" 
            : "تنبيه ذكاء اصطناعي للإعلان #{$listing->id} ⚠️: {$summary}";

        return redirect()->back()->with($isSafe ? 'success' : 'warning', $msg);
    }

    public function destroy($id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            LiveBridgeService::statement("UPDATE listings SET deleted_at = NOW() WHERE id = ?", [(int)$id]);
            return redirect()->back()->with('success', 'تم حذف الإعلان بنجاح من السيرفر.');
        }

        $listing = Listing::with('images')->findOrFail($id);

        if ($listing->images) {
            foreach ($listing->images as $img) {
                $imgPath = ltrim($img->image_path, '/');
                $fullPublic = public_path('storage/' . $imgPath);
                if (file_exists($fullPublic)) @unlink($fullPublic);
                $img->delete();
            }
        }

        $listing->delete();

        return redirect()->back()->with('success', 'تم حذف الإعلان وصوره بنجاح.');
    }
}
