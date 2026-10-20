@extends('layouts.admin')

@section('content')
<!-- مؤشر حالة المزامنة اللحظية مع السيرفر في أعلى اليسار (Top-Left Floating Sync Status Indicator) -->
<div id="syncStatusIndicator" style="position: fixed; top: 18px; left: 24px; z-index: 100050; display: none; pointer-events: auto; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);">
    <div id="syncStatusBadge" class="d-flex align-items-center gap-2 px-3 py-2 rounded-pill shadow-lg fw-bold fs-7 border" style="backdrop-filter: blur(10px); box-shadow: 0 10px 25px rgba(0,0,0,0.25) !important;">
        <i id="syncStatusIcon" class="fa-solid fa-arrows-rotate fa-spin text-warning fs-6"></i>
        <span id="syncStatusText">جاري الحفظ والمزامنة مع السيرفر... ⏳</span>
        <button type="button" id="syncStatusCloseBtn" class="btn btn-sm btn-close btn-close-white p-1 ms-1" style="display: none;" onclick="SyncStatusManager.hide()"></button>
    </div>
</div>

<style>
/* ترويسة وصور الجدول الموسعة - 72px */
.listing-thumb-box {
    position: relative;
    width: 72px;
    height: 72px;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    flex-shrink: 0;
}
.listing-thumb-box:hover {
    transform: scale(1.06);
    box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}
.listing-thumb-box:hover .thumb-overlay-icon {
    opacity: 1;
}
.thumb-overlay-icon {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    opacity: 0;
    transition: opacity 0.2s ease;
    backdrop-filter: blur(1.5px);
}
.listing-thumb-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* تأثير الوميض الأخضر الفوري عند التعديل المحلي Optimistic Flash */
@keyframes rowFlashOptimistic {
    0% { background-color: #dcfce7; }
    50% { background-color: #bbf7d0; }
    100% { background-color: transparent; }
}
.row-optimistic-flash {
    animation: rowFlashOptimistic 1.8s ease;
}

/* كرت مرجع الإعلان الأصلي في نافذة التعديل */
.edit-ref-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
.ref-prop-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 10px;
}
</style>

<!-- Header & Quick Actions -->
<div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
    <div>
        <h4 class="fw-bold mb-1 d-flex align-items-center gap-2">
            <i class="fa-solid fa-layer-group text-primary"></i>
            <span>مراقبة وإدارة الإعلانات وتفاصيل الأقسام</span>
        </h4>
        <p class="text-muted fs-7 mb-0">مراقبة أعداد الإعلانات بكل قسم، وتتبع تواريخ الإنشاء والحذف التلقائي (30 يوماً) مع تحكم كامل</p>
    </div>

    <div class="d-flex align-items-center gap-2">
        <!-- زر تفعيل/إيقاف الفحص التلقائي بالذكاء الاصطناعي -->
        <form method="POST" action="{{ route('admin.listings.toggleAiAuto') }}" class="d-inline m-0">
            @csrf
            <button type="submit" class="btn btn-sm {{ ($isAiAutoEnabled ?? true) ? 'btn-success shadow-sm' : 'btn-outline-secondary' }} fw-bold px-3 py-2 rounded-pill" title="الضغط لتبديل تفعيل أو إيقاف الفحص التلقائي بالذكاء الاصطناعي">
                <i class="fa-solid fa-robot me-1"></i>
                الفحص الذكي: 
                <span class="badge {{ ($isAiAutoEnabled ?? true) ? 'bg-white text-success' : 'bg-secondary text-white' }} ms-1">
                    {{ ($isAiAutoEnabled ?? true) ? 'مفعل ✅' : 'معطل ⏸️' }}
                </span>
            </button>
        </form>

        <!-- قائمة إظهار وإخفاء الأعمدة -->
        <div class="dropdown">
            <button class="btn btn-white border shadow-sm btn-sm dropdown-toggle fw-semibold py-2 px-3 rounded-pill" type="button" id="colToggleDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fa-solid fa-table-columns me-1 text-primary"></i> التحكم بالأعمدة
            </button>
            <ul class="dropdown-menu dropdown-menu-end p-3 shadow border-0" aria-labelledby="colToggleDropdown" style="min-width: 230px;">
                <li class="fw-bold fs-7 mb-2 text-muted border-bottom pb-1">إظهار / إخفاء الأعمدة:</li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="0" checked> # المعرف والصورة</label></li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="1" checked> الإعلان والتصنيف</label></li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="2" checked> المعلن والمصدر</label></li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="3" checked> السعر والمدينة</label></li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="4" checked> تاريخ الإضافة والصلاحية</label></li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="5" checked> التفاعل (مشاهدات/ظهور)</label></li>
                <li><label class="dropdown-item px-1 py-1 rounded cursor-pointer"><input type="checkbox" class="col-toggle me-2" data-col="6" checked> الحالة</label></li>
            </ul>
        </div>
    </div>
</div>

@if($errors->any())
    <div class="alert alert-danger alert-dismissible fade show border-0 shadow-sm rounded-3 mb-4" role="alert">
        <i class="fa-solid fa-circle-exclamation me-2"></i> <strong>تنبيه الأخطاء:</strong>
        <ul class="mb-0 mt-2 fs-7 pe-3">
            @foreach($errors->all() as $error)
                <li>{{ $error }}</li>
            @endforeach
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
@endif

@if(session('success'))
    <div class="alert alert-success alert-dismissible fade show border-0 shadow-sm rounded-3 mb-4" role="alert">
        <i class="fa-solid fa-circle-check me-2"></i> {{ session('success') }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
@endif

@if(session('warning'))
    <div class="alert alert-warning alert-dismissible fade show border-0 shadow-sm rounded-3 mb-4" role="alert">
        <i class="fa-solid fa-triangle-exclamation me-2"></i> {{ session('warning') }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
@endif

<!-- Quick Metrics KPI Cards Row -->
<div class="row g-3 mb-4">
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-dark">
            <div class="text-muted fs-8 fw-bold mb-1">إجمالي الإعلانات</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-dark" id="kpi-count-all">{{ number_format($counts['all']) }}</span>
                <span class="badge bg-light text-dark border">الكل</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-success">
            <div class="text-muted fs-8 fw-bold mb-1">إعلانات نشطة</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-success" id="kpi-count-active">{{ number_format($counts['active']) }}</span>
                <span class="badge bg-success bg-opacity-10 text-success">مقبول</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-warning">
            <div class="text-muted fs-8 fw-bold mb-1">بانتظار المراجعة</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-warning" id="kpi-count-pending">{{ number_format($counts['pending']) }}</span>
                <span class="badge bg-warning bg-opacity-10 text-dark">معلق</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-info">
            <div class="text-muted fs-8 fw-bold mb-1">إعلانات اليوم (24h)</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-info" id="kpi-count-today">{{ number_format($counts['today']) }}</span>
                <span class="badge bg-info bg-opacity-10 text-info">جديد</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-danger">
            <div class="text-muted fs-8 fw-bold mb-1">أوشكت على الحذف (30يوم)</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-danger" id="kpi-count-expiring">{{ number_format($counts['expiring_soon']) }}</span>
                <span class="badge bg-danger bg-opacity-10 text-danger">&lt; 5 أيام</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-danger border-opacity-50">
            <div class="text-muted fs-8 fw-bold mb-1">مخالفات AI / مرفوض</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-danger" id="kpi-count-rejected">{{ number_format($counts['rejected'] + $counts['flagged']) }}</span>
                <span class="badge bg-danger text-white">مرفوض</span>
            </div>
        </div>
    </div>
</div>

<!-- Category Ads Count & Hierarchy Navigation Box -->
<div class="card border-0 shadow-sm rounded-3 mb-4 overflow-hidden" id="categoryHierarchyCard">
    <div class="card-header bg-white py-3 px-4 border-bottom d-flex align-items-center justify-content-between">
        <div class="d-flex align-items-center gap-2">
            <i class="fa-solid fa-chart-pie text-success fs-5"></i>
            <h6 class="fw-bold mb-0 text-dark">إحصائيات وعدد الإعلانات في كل قسم (رئيسي وفرعي)</h6>
        </div>
        @if(request('category_id'))
            <a href="{{ route('admin.listings.index', request()->except(['category_id', 'page'])) }}" class="btn btn-sm btn-outline-danger rounded-pill px-3 py-1 fs-8">
                <i class="fa-solid fa-xmark me-1"></i> إلغاء فلتر القسم (عرض الكل)
            </a>
        @endif
    </div>
    <div class="card-body p-3 bg-white">
        
        <!-- Level 1: Main Categories -->
        <div class="d-flex align-items-center gap-2 overflow-auto pb-2 border-bottom mb-3" style="white-space: nowrap; scrollbar-width: thin;">
            <a href="{{ route('admin.listings.index', request()->except(['category_id', 'page'])) }}" 
               class="btn btn-sm rounded-pill px-3 py-2 fw-bold {{ !request('category_id') ? 'btn-dark' : 'btn-light border text-secondary' }}">
                <i class="fa-solid fa-house me-1"></i> الرئيسية (كل الأقسام)
                <span class="badge {{ !request('category_id') ? 'bg-primary text-white' : 'bg-secondary text-white' }} ms-1">
                    {{ number_format($counts['all']) }}
                </span>
            </a>
            
            @foreach($categories as $cat)
                @php
                    $isMainActive = request('category_id') == $cat->id || ($selectedCategoryObj && in_array($cat->id, array_merge([$selectedCategoryObj->id], ($selectedCategoryObj->relationLoaded('parents') ? $selectedCategoryObj->parents->pluck('id')->toArray() : []))));
                @endphp
                <a href="{{ route('admin.listings.index', array_merge(request()->except(['page']), ['category_id' => $cat->id])) }}" 
                   class="btn btn-sm rounded-pill px-3 py-2 fw-bold {{ $isMainActive ? 'btn-success text-white shadow-sm' : 'btn-light border text-dark' }}">
                    @if($cat->icon)
                        <img src="{{ str_starts_with($cat->icon, 'http') ? $cat->icon : 'https://lelbai.com/' . ltrim($cat->icon, '/') }}" style="width: 18px; height: 18px; object-fit: contain; margin-left: 4px;" alt="">
                    @endif
                    <span>{{ $cat->name_ar }}</span>
                    <span class="badge {{ $isMainActive ? 'bg-white text-success' : 'bg-dark bg-opacity-10 text-dark' }} ms-1 rounded-pill">
                        {{ number_format($cat->total_listings_count ?? 0) }}
                    </span>
                </a>
            @endforeach
        </div>

        <!-- Level 2: Subcategories (Shown if a Category with children is selected) -->
        @php
            $activeSubCategories = collect();
            if ($selectedCategoryObj) {
                $hasChildren = $selectedCategoryObj->relationLoaded('children') && $selectedCategoryObj->children->isNotEmpty();
                $hasParents = $selectedCategoryObj->relationLoaded('parents') && $selectedCategoryObj->parents->isNotEmpty();
                if ($hasChildren) {
                    $activeSubCategories = $selectedCategoryObj->children;
                } elseif ($hasParents) {
                    $parentCat = $selectedCategoryObj->parents->first();
                    $activeSubCategories = ($parentCat && $parentCat->relationLoaded('children')) ? $parentCat->children : collect();
                }
            }
        @endphp

        @if($activeSubCategories->isNotEmpty())
            <div class="d-flex align-items-center gap-2 overflow-auto pt-1" style="white-space: nowrap; scrollbar-width: thin;">
                <span class="text-muted fs-8 fw-bold me-2">الأقسام الفرعية:</span>
                @foreach($activeSubCategories as $subCat)
                    @php
                        $isSubActive = request('category_id') == $subCat->id;
                    @endphp
                    <a href="{{ route('admin.listings.index', array_merge(request()->except(['page']), ['category_id' => $subCat->id])) }}" 
                       class="btn btn-sm rounded-pill px-3 py-1 fw-bold fs-8 {{ $isSubActive ? 'btn-primary text-white shadow-sm' : 'btn-outline-secondary' }}">
                        <span>{{ $subCat->name_ar }}</span>
                        <span class="badge {{ $isSubActive ? 'bg-white text-primary' : 'bg-secondary text-white' }} ms-1 rounded-pill">
                            {{ number_format($subCat->total_listings_count ?? 0) }}
                        </span>
                    </a>
                @endforeach
            </div>
        @endif

    </div>
</div>

<!-- Search, Status Tabs & Filters Bar -->
<div class="card border-0 shadow-sm rounded-3 mb-4" id="filterStatusCard">
    <div class="card-body p-3">
        <!-- Status Filter Tabs -->
        <div class="d-flex flex-wrap gap-2 mb-3 pb-3 border-bottom">
            <a href="{{ route('admin.listings.index', request()->except(['status', 'ai_status', 'page'])) }}" 
               class="btn btn-sm {{ !request('status') && !request('ai_status') ? 'btn-dark' : 'btn-outline-secondary' }} rounded-pill px-3">
                الكل ({{ number_format($counts['all']) }})
            </a>
            <a href="{{ route('admin.listings.index', array_merge(request()->except(['page', 'ai_status']), ['status' => 'active'])) }}" 
               class="btn btn-sm {{ request('status') === 'active' ? 'btn-success text-white' : 'btn-outline-success' }} rounded-pill px-3">
                <i class="fa-solid fa-circle-check me-1"></i> نشط ومقبول ({{ number_format($counts['active']) }})
            </a>
            <a href="{{ route('admin.listings.index', array_merge(request()->except(['page', 'ai_status']), ['status' => 'pending'])) }}" 
               class="btn btn-sm {{ request('status') === 'pending' ? 'btn-warning text-dark' : 'btn-outline-warning' }} rounded-pill px-3 fw-bold">
                <i class="fa-solid fa-clock me-1"></i> بانتظار المراجعة ({{ number_format($counts['pending']) }})
            </a>
            <a href="{{ route('admin.listings.index', array_merge(request()->except(['page', 'ai_status']), ['status' => 'rejected'])) }}" 
               class="btn btn-sm {{ request('status') === 'rejected' ? 'btn-danger text-white' : 'btn-outline-danger' }} rounded-pill px-3">
                <i class="fa-solid fa-circle-xmark me-1"></i> مرفوض ({{ number_format($counts['rejected']) }})
            </a>
            <a href="{{ route('admin.listings.index', array_merge(request()->except(['page', 'ai_status']), ['status' => 'suspended'])) }}" 
               class="btn btn-sm {{ request('status') === 'suspended' ? 'btn-secondary text-white' : 'btn-outline-secondary' }} rounded-pill px-3">
                <i class="fa-solid fa-ban me-1"></i> موقوف ({{ number_format($counts['suspended']) }})
            </a>
            <a href="{{ route('admin.listings.index', array_merge(request()->except(['page', 'ai_status']), ['status' => 'expiring_soon'])) }}" 
               class="btn btn-sm {{ request('status') === 'expiring_soon' ? 'btn-danger text-white shadow-sm' : 'btn-outline-danger' }} rounded-pill px-3 fw-bold">
                <i class="fa-solid fa-hourglass-half me-1"></i> أوشك على الحذف (&lt; 5 أيام) ({{ number_format($counts['expiring_soon']) }})
            </a>
            <a href="{{ route('admin.listings.index', array_merge(request()->except(['page', 'status']), ['ai_status' => 'flagged'])) }}" 
               class="btn btn-sm {{ request('ai_status') === 'flagged' ? 'btn-danger text-white shadow-sm' : 'btn-outline-danger' }} rounded-pill px-3 fw-bold">
                <i class="fa-solid fa-robot me-1"></i> مخالفات AI ⚠️ ({{ number_format($counts['flagged']) }})
            </a>
        </div>

        <!-- Filter Form -->
        <form method="GET" action="{{ route('admin.listings.index') }}" class="row g-2 align-items-center">
            @if(request('category_id'))
                <input type="hidden" name="category_id" value="{{ request('category_id') }}">
            @endif
            @if(request('status'))
                <input type="hidden" name="status" value="{{ request('status') }}">
            @endif
            @if(request('ai_status'))
                <input type="hidden" name="ai_status" value="{{ request('ai_status') }}">
            @endif

            <div class="col-md-4">
                <div class="input-group input-group-sm">
                    <span class="input-group-text bg-light"><i class="fa-solid fa-magnifying-glass text-muted"></i></span>
                    <input type="text" name="search" class="form-control" placeholder="ابحث برقم الإعلان، العنوان، رقم الهاتف، أو اسم المعلن..." value="{{ request('search') }}">
                </div>
            </div>

            <div class="col-md-2">
                <select name="city_id" class="form-select form-select-sm">
                    <option value="">كل المحافظات</option>
                    @foreach($cities ?? [] as $c)
                        <option value="{{ $c->id }}" {{ request('city_id') == $c->id ? 'selected' : '' }}>{{ $c->name_ar }}</option>
                    @endforeach
                </select>
            </div>

            <div class="col-md-2">
                <select name="source" class="form-select form-select-sm">
                    <option value="">كل المصادر</option>
                    <option value="organic" {{ request('source') === 'organic' ? 'selected' : '' }}>مستخدمين حقيقيين</option>
                    <option value="bot" {{ request('source') === 'bot' ? 'selected' : '' }}>بوتات / مستورد</option>
                    <option value="facebook" {{ request('source') === 'facebook' ? 'selected' : '' }}>منشورات فيسبوك</option>
                </select>
            </div>

            <div class="col-md-2">
                <select name="sort" class="form-select form-select-sm">
                    <option value="newest_created" {{ request('sort', 'newest_created') === 'newest_created' ? 'selected' : '' }}>الأحدث إضافة (الافتراضي)</option>
                    <option value="oldest_created" {{ request('sort') === 'oldest_created' ? 'selected' : '' }}>الأقدم إضافة (الأقرب للحذف)</option>
                    <option value="most_viewed" {{ request('sort') === 'most_viewed' ? 'selected' : '' }}>الأكثر مشاهدة 👁️</option>
                    <option value="most_impressions" {{ request('sort') === 'most_impressions' ? 'selected' : '' }}>الأكثر ظهوراً 📊</option>
                    <option value="price_desc" {{ request('sort') === 'price_desc' ? 'selected' : '' }}>الأعلى سعراً</option>
                    <option value="price_asc" {{ request('sort') === 'price_asc' ? 'selected' : '' }}>الأقل سعراً</option>
                </select>
            </div>

            <div class="col-md-2 d-flex gap-2">
                <button type="submit" class="btn btn-primary btn-sm rounded-pill w-100 fw-bold">
                    <i class="fa-solid fa-filter me-1"></i> تصفية
                </button>
                <a href="{{ route('admin.listings.index', array_merge(request()->all(), ['refresh_cache' => 1])) }}" class="btn btn-outline-info btn-sm rounded-pill px-3" title="تحديث مباشر ومسح الكاش">
                    <i class="fa-solid fa-arrows-rotate"></i>
                </a>
                @if(request()->hasAny(['search', 'city_id', 'source', 'sort']))
                    <a href="{{ route('admin.listings.index', request()->only(['category_id', 'status'])) }}" class="btn btn-outline-secondary btn-sm rounded-pill px-3" title="إعادة تعيين">
                        <i class="fa-solid fa-rotate-left"></i>
                    </a>
                @endif
            </div>
        </form>
    </div>
</div>

<!-- Listings Table Card with Bulk Actions -->
<div class="card border-0 shadow-sm rounded-3 overflow-hidden" id="listingsTableCard">
    <div class="card-header bg-white py-3 px-4 border-bottom d-flex flex-wrap align-items-center justify-content-between gap-2">
        <div class="d-flex align-items-center gap-2">
            <span class="fw-bold text-dark fs-6">قائمة الإعلانات التفصيلية</span>
            <span class="badge bg-secondary rounded-pill">{{ $listings->total() }} إعلان</span>
        </div>

        <!-- Bulk Action Controls -->
        <div id="bulkActionsToolbar" class="d-flex align-items-center gap-2" style="display: none !important;">
            <span class="fs-8 text-muted fw-bold"><span id="selectedCount">0</span> إعلان محدد:</span>
            <button type="button" class="btn btn-sm btn-success rounded-pill px-3 fw-bold" onclick="submitBulkAction('activate')">
                <i class="fa-solid fa-check me-1"></i> قبول المحدد
            </button>
            <button type="button" class="btn btn-sm btn-warning rounded-pill px-3 fw-bold text-dark" onclick="submitBulkAction('suspend')">
                <i class="fa-solid fa-ban me-1"></i> إيقاف المحدد
            </button>
            <button type="button" class="btn btn-sm btn-danger rounded-pill px-3 fw-bold" onclick="submitBulkAction('delete')">
                <i class="fa-solid fa-trash me-1"></i> حذف المحدد
            </button>
        </div>
    </div>

    <form id="bulkActionForm" method="POST" action="{{ route('admin.listings.bulkAction') }}">
        @csrf
        <input type="hidden" name="action" id="bulkActionInput" value="">
        
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 text-end">
                <thead class="table-light fs-7 text-muted border-bottom">
                    <tr>
                        <th style="width: 40px;" class="text-center">
                            <input type="checkbox" id="selectAllCheckbox" class="form-check-input cursor-pointer">
                        </th>
                        <th class="col-cell-0" style="min-width: 165px;"># والصورة</th>
                        <th class="col-cell-1" style="min-width: 200px;">الإعلان والتصنيف</th>
                        <th class="col-cell-2" style="min-width: 160px;">المعلن والمصدر</th>
                        <th class="col-cell-3" style="min-width: 130px;">السعر والمدينة</th>
                        <th class="col-cell-4" style="min-width: 170px;">تاريخ الإضافة والصلاحية</th>
                        <th class="col-cell-5" style="min-width: 110px;">التفاعل</th>
                        <th class="col-cell-6" style="min-width: 100px;">الحالة</th>
                        <th style="min-width: 170px;" class="text-center">التحكم والإجراءات</th>
                    </tr>
                </thead>
                <tbody class="fs-7">
                    @forelse($listings as $listing)
                        @php
                            $created = $listing->created_at ? \Carbon\Carbon::parse($listing->created_at) : null;
                            $daysOld = $created ? $created->diffInDays(now()) : 0;
                            $daysRemaining = max(0, 30 - $daysOld);
                            
                            $badgeColor = 'bg-success';
                            if ($daysRemaining <= 3) {
                                $badgeColor = 'bg-danger';
                            } elseif ($daysRemaining <= 7) {
                                $badgeColor = 'bg-warning text-dark';
                            } elseif ($daysRemaining <= 15) {
                                $badgeColor = 'bg-info text-dark';
                            }

                            $primaryImg = null;
                            if ($listing->primaryImage && !empty($listing->primaryImage->image_path)) {
                                $rawP = $listing->primaryImage->image_path;
                                $primaryImg = str_starts_with($rawP, 'http') ? $rawP : 'https://lelbai.com/' . ltrim($rawP, '/');
                            } elseif ($listing->category && !empty($listing->category->icon)) {
                                $rawI = $listing->category->icon;
                                $primaryImg = str_starts_with($rawI, 'http') ? $rawI : 'https://lelbai.com/' . ltrim($rawI, '/');
                            }
                        @endphp
                        <tr id="listing-row-{{ $listing->id }}" data-id="{{ $listing->id }}" data-status="{{ $listing->status }}" style="transition: all 0.3s ease;">
                            <!-- Checkbox -->
                            <td class="text-center">
                                <input type="checkbox" name="listing_ids[]" value="{{ $listing->id }}" class="form-check-input listing-checkbox cursor-pointer">
                            </td>

                            <!-- # and Thumbnail -->
                            <td class="col-cell-0">
                                <div class="d-flex align-items-center gap-2">
                                    @php
                                        $liveUrl = "https://lelbai.com/listings/" . ($listing->uuid ?: $listing->id) . "/details";
                                        $cleanPrice = $listing->price ? number_format($listing->price) . ' ' . ($listing->currency ?: 'ل.س') : 'غير محدد';
                                    @endphp
                                    @if($primaryImg)
                                        <div class="listing-thumb-box border" 
                                             onclick="openImageLightbox('{{ addslashes($primaryImg) }}', '{{ addslashes($listing->title) }}', '{{ $cleanPrice }}', '{{ $listing->id }}', '{{ $liveUrl }}')" 
                                             title="انقر لتكبير ومعاينة الصورة في البوب اب فورياً">
                                            <img src="{{ $primaryImg }}" class="listing-thumb-img" alt="{{ $listing->title }}" onerror="this.onerror=null; this.src='https://lelbai.com/icons/cars.svg';">
                                            <div class="thumb-overlay-icon">
                                                <i class="fa-solid fa-magnifying-glass-plus"></i>
                                            </div>
                                        </div>
                                    @else
                                        <div class="rounded-3 border bg-light d-flex align-items-center justify-content-center text-muted" style="width: 72px; height: 72px; flex-shrink: 0;">
                                            <i class="fa-solid fa-image fs-3 text-secondary opacity-50"></i>
                                        </div>
                                    @endif
                                    <div>
                                        <span class="fw-bold text-dark d-block">#{{ $listing->id }}</span>
                                        @if($listing->is_featured)
                                            <span class="badge bg-warning text-dark fs-9">⭐ مميز</span>
                                        @endif
                                    </div>
                                </div>
                            </td>

                            <!-- Title & Category Hierarchy -->
                            <td class="col-cell-1">
                                <div class="fw-bold text-dark mb-1" style="max-width: 240px; word-break: break-word;" title="{{ $listing->title }}">
                                    {{ \Illuminate\Support\Str::limit($listing->title, 40) }}
                                </div>
                                <div class="fs-8 text-muted d-flex align-items-center gap-1 flex-wrap">
                                    <i class="fa-solid fa-folder-tree text-success fs-9"></i>
                                    @if($listing->category)
                                        @if($listing->category->relationLoaded('parents') && $listing->category->parents->isNotEmpty())
                                            <span>{{ $listing->category->parents->first()->name_ar }} &gt;</span>
                                        @endif
                                        <span class="fw-semibold text-secondary">{{ $listing->category->name_ar }}</span>
                                    @else
                                        <span class="text-muted">بدون تصنيف</span>
                                    @endif
                                </div>
                            </td>

                            <!-- Publisher & Source -->
                            <td class="col-cell-2">
                                <div class="d-flex align-items-center gap-2">
                                    <div>
                                        <span class="fw-bold text-dark d-block fs-8">
                                            {{ $listing->user ? $listing->user->name : 'مستخدم مجهول' }}
                                        </span>
                                        <span class="text-muted fs-8 d-block" dir="ltr">
                                            {{ $listing->contact_phone ?: ($listing->user?->phone ?: '-') }}
                                        </span>
                                        @if($listing->is_scraped || ($listing->user && $listing->user->is_bot))
                                            <span class="badge bg-secondary bg-opacity-25 text-secondary fs-9">🤖 مستورد / بوت</span>
                                        @else
                                            <span class="badge bg-success bg-opacity-25 text-success fs-9">👤 مستخدم حقيقي</span>
                                        @endif

                                        @if(!empty($listing->source_url))
                                            <a href="{{ $listing->source_url }}" target="_blank" class="badge bg-primary bg-opacity-10 text-primary fs-9 text-decoration-none d-inline-block mt-1" title="رابط المنشور الأصلي">
                                                <i class="fa-brands fa-facebook me-1"></i> المصدر
                                            </a>
                                        @endif
                                    </div>
                                </div>
                            </td>

                            <!-- Price & City -->
                            <td class="col-cell-3">
                                <div class="fw-bold text-success fs-7">
                                    @if($listing->price > 0)
                                        {{ number_format($listing->price) }} {{ $listing->currency === 'USD' || $listing->currency === '$' ? '$' : 'ل.س' }}
                                    @else
                                        <span class="text-muted">غير محدد</span>
                                    @endif
                                </div>
                                <div class="fs-8 text-muted mt-1">
                                    <i class="fa-solid fa-location-dot text-danger me-1"></i>
                                    {{ $listing->city ? $listing->city->name_ar : 'غير محدد' }}
                                </div>
                            </td>

                            <!-- Creation Date & Auto-Purge Countdown (30 Days) -->
                            <td class="col-cell-4">
                                <div class="d-flex flex-column gap-1">
                                    <span class="fw-semibold text-dark fs-8" title="{{ $created ? $created->toDateTimeString() : '' }}">
                                        <i class="fa-regular fa-calendar me-1 text-primary"></i>
                                        {{ $created ? $created->format('Y-m-d H:i') : '-' }}
                                    </span>
                                    <span class="text-muted fs-9">
                                        (منذ {{ $daysOld }} يوم)
                                    </span>
                                    <div>
                                        <span class="badge {{ $badgeColor }} fs-9 px-2 py-1 rounded-pill" title="مدة الإعلان 30 يوماً ثم يُحذف تلقائياً">
                                            <i class="fa-solid fa-hourglass-start me-1"></i>
                                            متبقي {{ $daysRemaining }} يوم للحذف
                                        </span>
                                    </div>
                                </div>
                            </td>

                            <!-- Engagement: Views & Impressions -->
                            <td class="col-cell-5">
                                <div class="d-flex flex-column gap-1 fs-8">
                                    <span class="text-dark fw-bold" title="عدد المشاهدات الفعلية لصفحة الإعلان">
                                        <i class="fa-regular fa-eye text-primary me-1"></i> {{ number_format($listing->views_count ?? 0) }}
                                    </span>
                                    <span class="text-muted" title="عدد مرات الظهور في البحث والقوائم">
                                        <i class="fa-solid fa-chart-simple text-secondary me-1"></i> {{ number_format($listing->impressions_count ?? 0) }}
                                    </span>
                                </div>
                            </td>

                            <!-- Status & AI flags -->
                            <td class="col-cell-6" id="status-cell-{{ $listing->id }}">
                                @if($listing->status === 'active')
                                    <span class="badge bg-success bg-opacity-15 text-success border border-success border-opacity-25 px-2 py-1 rounded-pill">نشط ✅</span>
                                @elseif($listing->status === 'pending')
                                    <span class="badge bg-warning bg-opacity-20 text-dark border border-warning px-2 py-1 rounded-pill">بانتظار المراجعة ⏳</span>
                                @elseif($listing->status === 'rejected')
                                    <span class="badge bg-danger bg-opacity-15 text-danger border border-danger border-opacity-25 px-2 py-1 rounded-pill">مرفوض ❌</span>
                                @elseif($listing->status === 'suspended')
                                    <span class="badge bg-secondary px-2 py-1 rounded-pill">موقوف ⏸️</span>
                                @endif

                                @if($listing->ai_status === 'flagged')
                                    <div class="mt-1">
                                        <span class="badge bg-danger text-white fs-9" title="{{ $listing->ai_summary }}">⚠️ مخالفة AI</span>
                                    </div>
                                @endif
                            </td>

                            <!-- Actions -->
                            <td id="actions-cell-{{ $listing->id }}">
                                <div class="d-flex align-items-center justify-content-center gap-1">
                                    <!-- معاينة بالمنصة على الدومين الحقيقي -->
                                    <a href="https://lelbai.com/listings/{{ $listing->uuid ?: $listing->id }}/details" target="_blank" class="btn btn-sm btn-outline-primary fw-bold px-2 py-1" title="معاينة الإعلان مباشرة على الدومين الحقيقي (lelbai.com)">
                                        <i class="fa-solid fa-arrow-up-right-from-square"></i> معاينة
                                    </a>

                                    <!-- زر تعديل الإعلان -->
                                    <button type="button" 
                                            class="btn btn-sm btn-warning fw-bold px-2 py-1 btn-edit-listing text-dark shadow-xs" 
                                            data-id="{{ $listing->id }}" 
                                            data-title="{{ $listing->title }}"
                                            data-price="{{ (float)$listing->price }}"
                                            data-currency="{{ $listing->currency ?: 'SYP' }}"
                                            data-category-id="{{ $listing->category_id }}"
                                            data-category-name="{{ $listing->category ? $listing->category->name_ar : 'بدون تصنيف' }}"
                                            data-city-id="{{ $listing->city_id }}"
                                            data-city-name="{{ $listing->city ? $listing->city->name_ar : 'غير محدد' }}"
                                            data-phone="{{ $listing->contact_phone ?: ($listing->user?->phone ?: '') }}"
                                            data-description="{{ $listing->description }}"
                                            data-status="{{ $listing->status }}"
                                            data-featured="{{ $listing->is_featured ? 1 : 0 }}"
                                            data-image="{{ $primaryImg }}"
                                            data-user-name="{{ $listing->user ? $listing->user->name : 'مستخدم مجهول' }}"
                                            data-views="{{ $listing->views_count ?? 0 }}"
                                            data-created-at="{{ $listing->created_at ? \Carbon\Carbon::parse($listing->created_at)->format('Y-m-d H:i') : '-' }}"
                                            data-live-url="{{ $liveUrl }}"
                                            title="تعديل بيانات وتفاصيل الإعلان">
                                        <i class="fa-solid fa-pen-to-square"></i> تعديل
                                    </button>

                                    @if($listing->status !== 'active')
                                        <button type="button" onclick="quickUpdateListingStatus({{ $listing->id }}, 'active', event)" class="btn btn-sm btn-success fw-bold px-2 py-1 btn-action-active" title="قبول وتفعيل الإعلان فورياً">
                                            <i class="fa-solid fa-check"></i>
                                        </button>
                                    @endif

                                    @if($listing->status !== 'rejected')
                                        <button type="button" 
                                                class="btn btn-sm btn-danger fw-bold px-2 py-1 btn-open-reject-modal" 
                                                data-id="{{ $listing->id }}" 
                                                data-title="{{ $listing->title }}"
                                                data-reason="{{ $listing->rejection_reason ?? '' }}"
                                                data-ai-suggestion="{{ $listing->ai_rejection_suggestion ?? '' }}"
                                                title="رفض الإعلان مع تحديد السبب">
                                            <i class="fa-solid fa-xmark"></i>
                                        </button>
                                    @endif

                                    @if($listing->status === 'active')
                                        <button type="button" onclick="quickUpdateListingStatus({{ $listing->id }}, 'suspended', event)" class="btn btn-sm btn-outline-secondary fw-bold px-2 py-1 btn-action-suspended" title="إيقاف مؤقت فورياً">
                                            <i class="fa-solid fa-ban"></i>
                                        </button>
                                    @endif

                                    <!-- زر حذف نهائي -->
                                    <button type="button" class="btn btn-sm btn-outline-danger fw-bold px-2 py-1 btn-open-delete-modal" data-id="{{ $listing->id }}" data-title="{{ $listing->title }}" title="حذف الإعلان نهائياً">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="9" class="text-center py-5 text-muted">
                                <i class="fa-solid fa-inbox fs-1 d-block mb-2 text-secondary"></i>
                                لا توجد إعلانات مطابقة للاختيارات الحالية.
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </form>

    @if($listings->hasPages())
        <div class="card-footer bg-white py-3 border-top">
            <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                <span class="text-muted fs-8">عرض {{ $listings->firstItem() }} إلى {{ $listings->lastItem() }} من إجمالي {{ $listings->total() }} إعلان</span>
                {{ $listings->links() }}
            </div>
        </div>
    @endif
</div>

<!-- Reject Reason Modal -->
<div class="modal fade" id="rejectListingModal" tabindex="-1" aria-labelledby="rejectListingModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-3">
            <form id="rejectListingForm" method="POST" action="">
                @csrf
                <input type="hidden" name="status" value="rejected">
                <div class="modal-header bg-danger text-white py-2 px-3">
                    <h6 class="modal-title fw-bold mb-0" id="rejectListingModalLabel">
                        <i class="fa-solid fa-triangle-exclamation me-1"></i> رفض الإعلان وحجبه
                    </h6>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                </div>
                <div class="modal-body p-3 text-end">
                    <p class="fs-7 text-muted mb-2">أنت على وشك رفض الإعلان: <strong id="modalListingTitle" class="text-dark"></strong></p>
                    <p class="fs-8 text-secondary mb-3">سيتم حجب الإعلان فورياً، وتنبيه صاحبه بالملاحظة المحددة.</p>
                    
                    <label for="rejectionReasonInput" class="form-label fw-bold fs-7 text-dark mb-1">
                        سبب وملاحظة الرفض للمعلن: <span class="text-danger">*</span>
                    </label>
                    <textarea name="rejection_reason" id="rejectionReasonInput" class="form-control" rows="3" placeholder="اكتب سبب الرفض هنا..." required></textarea>
                </div>
                <div class="modal-footer bg-light py-2 px-3">
                    <button type="button" class="btn btn-secondary btn-sm rounded-pill px-3" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-danger btn-sm rounded-pill px-4 fw-bold">
                        <i class="fa-solid fa-check me-1"></i> تأكيد الرفض
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Single Delete Confirmation Modal -->
<div class="modal fade" id="deleteListingModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-3">
            <form id="deleteListingForm" method="POST" action="">
                @csrf
                @method('DELETE')
                <div class="modal-header bg-danger text-white py-2 px-3">
                    <h6 class="modal-title fw-bold mb-0">
                        <i class="fa-solid fa-trash me-1"></i> حذف الإعلان نهائياً
                    </h6>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                </div>
                <div class="modal-body p-4 text-center">
                    <i class="fa-solid fa-triangle-exclamation text-danger fs-1 mb-3"></i>
                    <h6 class="fw-bold mb-2">هل أنت متأكد من حذف هذا الإعلان نهائياً؟</h6>
                    <p class="text-muted fs-7 mb-0" id="deleteModalListingTitle"></p>
                    <small class="text-danger d-block mt-2">سيتم حذف كافة الصور والبيانات المرتبطة ولا يمكن التراجع.</small>
                </div>
                <div class="modal-footer bg-light py-2 px-3 justify-content-center">
                    <button type="button" class="btn btn-secondary btn-sm rounded-pill px-4" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-danger btn-sm rounded-pill px-4 fw-bold">نعم، احذف الإعلان</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Modal تعديل الإعلان المباشر مع كرت المرجع الأصلي (Edit Modal with Live Reference Card) -->
<div class="modal fade" id="editListingModal" tabindex="-1" aria-labelledby="editListingModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <form id="editListingForm" method="POST" action="">
                @csrf
                <div class="modal-header bg-warning bg-opacity-10 border-bottom py-3 px-4 d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fa-solid fa-pen-to-square text-warning fs-5"></i>
                        <h5 class="modal-title fw-bold text-dark mb-0" id="editListingModalLabel">تعديل الإعلان رقم #<span id="modalListingIdDisplay"></span></h5>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                </div>
                <div class="modal-body p-4 bg-light bg-opacity-50">
                    <div class="row g-4 align-items-start">
                        <!-- اليمين: حقول نموذج التعديل (Edit Form Controls) -->
                        <div class="col-lg-7 col-xl-7 order-1">
                            <div class="p-3 bg-white rounded-3 border shadow-xs">
                                <h6 class="fw-bold text-dark mb-3 pb-2 border-bottom d-flex align-items-center justify-content-between">
                                    <span><i class="fa-solid fa-sliders text-primary me-1"></i> تعديل بيانات ومواصفات الإعلان</span>
                                    <small class="text-muted fs-8">التعديلات تنعكس فورياً في الجدول (0ms)</small>
                                </h6>
                                <div class="row g-3">
                                    <!-- عنوان الإعلان -->
                                    <div class="col-12">
                                        <label class="form-label fw-bold fs-7 text-dark">عنوان الإعلان <span class="text-danger">*</span></label>
                                        <input type="text" name="title" id="editListingTitle" class="form-control fw-bold" required maxlength="255">
                                    </div>

                                    <!-- القسم / التصنيف التفاعلي المبوب -->
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold fs-7 text-dark d-flex align-items-center justify-content-between">
                                            <span>القسم / التصنيف <span class="text-danger">*</span></span>
                                            <a href="javascript:void(0)" onclick="openCategoryPicker()" class="text-decoration-none fs-8 text-primary fw-bold">
                                                <i class="fa-solid fa-folder-tree me-1"></i> تصفح الشجرة
                                            </a>
                                        </label>
                                        <div class="input-group">
                                            <div class="form-control d-flex align-items-center justify-content-between bg-white cursor-pointer py-2 border rounded-end-3" 
                                                 id="editCategoryDisplayBox" 
                                                 onclick="openCategoryPicker()" 
                                                 style="cursor: pointer; min-height: 42px;"
                                                 title="اضغط لاختيار وتحديد القسم بالبوب اب">
                                                <div id="editCategoryDisplayText" class="fw-bold text-dark fs-7 text-truncate">
                                                    <span class="text-muted">اضغط لاختيار القسم...</span>
                                                </div>
                                                <i class="fa-solid fa-chevron-left text-muted fs-8 ms-2"></i>
                                            </div>
                                            <button type="button" class="btn btn-primary fw-bold px-3 rounded-start-3" onclick="openCategoryPicker()" title="فتح نافذة اختيار القسم">
                                                <i class="fa-solid fa-list-check me-1"></i> اختيار
                                            </button>
                                        </div>
                                        <input type="hidden" name="category_id" id="editListingCategory" value="" required>
                                    </div>

                                    <!-- المدينة -->
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold fs-7 text-dark">المدينة <span class="text-danger">*</span></label>
                                        <select name="city_id" id="editListingCity" class="form-select fw-semibold" required>
                                            <option value="">اختر المدينة...</option>
                                            @foreach($cities as $ct)
                                                <option value="{{ $ct->id }}">{{ $ct->name_ar }}</option>
                                            @endforeach
                                        </select>
                                    </div>

                                    <!-- السعر والعملة -->
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold fs-7 text-dark">السعر</label>
                                        <div class="input-group">
                                            <input type="number" step="any" name="price" id="editListingPrice" class="form-control fw-bold" min="0" placeholder="0">
                                            <select name="currency" id="editListingCurrency" class="form-select" style="max-width: 100px;">
                                                <option value="SYP">ل.س</option>
                                                <option value="USD">$</option>
                                            </select>
                                        </div>
                                    </div>

                                    <!-- رقم الهاتف -->
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold fs-7 text-dark">رقم هاتف التواصل</label>
                                        <input type="text" name="contact_phone" id="editListingPhone" class="form-control text-start" dir="ltr" placeholder="09xxxxxxxx">
                                    </div>

                                    <!-- حالة الإعلان -->
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold fs-7 text-dark">حالة الإعلان</label>
                                        <select name="status" id="editListingStatus" class="form-select fw-bold">
                                            <option value="active">نشط ✅</option>
                                            <option value="pending">بانتظار المراجعة ⏳</option>
                                            <option value="suspended">موقوف مؤقتاً ⏸️</option>
                                            <option value="rejected">مرفوض ❌</option>
                                        </select>
                                    </div>

                                    <!-- تمييز الإعلان -->
                                    <div class="col-md-6 d-flex align-items-center">
                                        <div class="form-check form-switch mt-3">
                                            <input class="form-check-input" type="checkbox" name="is_featured" value="1" id="editListingFeatured">
                                            <label class="form-check-label fw-bold text-dark fs-7 ms-2" for="editListingFeatured">
                                                ⭐ إعلان مميز (يظهر في الصدارة)
                                            </label>
                                        </div>
                                    </div>

                                    <!-- الوصف الكامل -->
                                    <div class="col-12">
                                        <label class="form-label fw-bold fs-7 text-dark">وصف الإعلان والمواصفات</label>
                                        <textarea name="description" id="editListingDescription" class="form-control" rows="5" placeholder="أدخل تفاصيل ومواصفات الإعلان..."></textarea>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- اليسار: كرت مرجع الإعلان الأصلي للمقارنة والاستعلام (Sticky Reference Card) -->
                        <div class="col-lg-5 col-xl-5 order-2">
                            <div class="card border-0 shadow-sm rounded-4 h-100 edit-ref-card" style="position: sticky; top: 0;">
                                <div class="card-header bg-dark text-white py-2 px-3 rounded-top-4 d-flex align-items-center justify-content-between">
                                    <div class="d-flex align-items-center gap-2">
                                        <i class="fa-solid fa-file-invoice text-warning"></i>
                                        <span class="fw-bold fs-7">مرجع تفاصيل الإعلان الأصلي</span>
                                    </div>
                                    <span class="badge bg-warning text-dark fw-bold fs-8" id="refCardIdBadge">#</span>
                                </div>
                                <div class="card-body p-3 d-flex flex-column gap-2" style="max-height: 72vh; overflow-y: auto;">
                                    <!-- صورة الإعلان المرجعية (قابلة للنقر للتكبير في البوب اب) -->
                                    <div class="position-relative text-center rounded-3 overflow-hidden border bg-white shadow-xs" style="height: 180px; cursor: pointer;" onclick="openImageLightboxFromRef()" title="انقر لتكبير ومعاينة الصورة في البوب اب">
                                        <img id="refCardImage" src="" alt="صورة الإعلان" class="w-100 h-100" style="object-fit: cover;" onerror="this.onerror=null; this.src='https://lelbai.com/icons/cars.svg';">
                                        <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-75 text-white py-1 px-2 d-flex justify-content-between align-items-center fs-9">
                                            <span><i class="fa-solid fa-magnifying-glass-plus me-1 text-warning"></i> انقر للتكبير بالبوب اب</span>
                                            <span id="refCardViewsBadge" class="badge bg-secondary">👁️ 0</span>
                                        </div>
                                    </div>

                                    <!-- العنوان الأصلي -->
                                    <div class="bg-white p-2 rounded-2 border">
                                        <span class="text-muted fs-9 fw-bold d-block mb-1">العنوان الحالي المسجل:</span>
                                        <div id="refCardTitle" class="fw-bold text-dark fs-7" style="word-break: break-word;"></div>
                                    </div>

                                    <!-- شبكة تفاصيل: السعر، القسم، المدينة، الحالة -->
                                    <div class="row g-2">
                                        <div class="col-6">
                                            <div class="bg-white p-2 rounded-2 border">
                                                <span class="text-muted fs-9 fw-bold d-block">السعر الحالي:</span>
                                                <span id="refCardPrice" class="fw-bold text-success fs-7"></span>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-white p-2 rounded-2 border">
                                                <span class="text-muted fs-9 fw-bold d-block">القسم الأصلي:</span>
                                                <span id="refCardCategory" class="fw-bold text-secondary fs-8 text-truncate d-block"></span>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-white p-2 rounded-2 border">
                                                <span class="text-muted fs-9 fw-bold d-block">المدينة:</span>
                                                <span id="refCardCity" class="fw-bold text-dark fs-8"></span>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="bg-white p-2 rounded-2 border">
                                                <span class="text-muted fs-9 fw-bold d-block">حالة الإعلان:</span>
                                                <span id="refCardStatus"></span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- صاحب الإعلان ورقم الهاتف -->
                                    <div class="bg-white p-2 rounded-2 border">
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <span class="text-muted fs-9 fw-bold"><i class="fa-solid fa-user me-1 text-primary"></i> المعلن:</span>
                                            <span id="refCardUser" class="fw-bold text-dark fs-8"></span>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span class="text-muted fs-9 fw-bold"><i class="fa-solid fa-phone me-1 text-success"></i> الهاتف:</span>
                                            <span id="refCardPhone" class="fw-bold text-dark fs-8" dir="ltr"></span>
                                        </div>
                                    </div>

                                    <!-- تاريخ النشر -->
                                    <div class="bg-white p-2 rounded-2 border d-flex justify-content-between align-items-center fs-8 text-muted">
                                        <span><i class="fa-regular fa-calendar-check me-1"></i> تاريخ الإضافة:</span>
                                        <strong id="refCardCreatedAt" class="text-dark"></strong>
                                    </div>

                                    <!-- الوصف الأصلي الكامل -->
                                    <div>
                                        <span class="text-muted fs-9 fw-bold d-block mb-1">الوصف الأصلي المسجل:</span>
                                        <div id="refCardDescription" class="bg-white p-2 rounded-2 border text-muted fs-8" style="max-height: 110px; overflow-y: auto; white-space: pre-wrap; line-height: 1.5;"></div>
                                    </div>

                                    <!-- رابط المعاينة الحقيقي -->
                                    <div class="mt-auto pt-1">
                                        <a id="refCardLiveUrl" href="#" target="_blank" class="btn btn-sm btn-outline-primary w-100 fw-bold rounded-pill">
                                            <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> فتح الإعلان بالكامل على lelbai.com
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer bg-white border-top py-3 px-4 d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary rounded-pill px-4 fw-bold" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-success rounded-pill px-4 fw-bold shadow-sm">
                        <i class="fa-solid fa-floppy-disk me-1"></i> حفظ التعديلات فورياً
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Modal بوب اب تكبير الصورة المباشر (Image Lightbox Popup) -->
<div class="modal fade" id="imageLightboxModal" tabindex="-1" aria-hidden="true" style="backdrop-filter: blur(8px); background-color: rgba(15, 23, 42, 0.85); z-index: 1080;">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content border-0 shadow-24 rounded-4 overflow-hidden bg-dark text-white">
            <div class="modal-header border-bottom border-secondary py-3 px-4 d-flex justify-content-between align-items-center bg-dark">
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-primary px-2 py-1 fs-8" id="lightboxAdId">#</span>
                    <h6 class="modal-title fw-bold text-truncate mb-0 text-white" id="lightboxAdTitle" style="max-width: 450px;"></h6>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <a href="#" id="lightboxAdUrl" target="_blank" class="btn btn-sm btn-outline-light rounded-pill px-3 fw-bold fs-8" title="فتح الإعلان على lelbai.com">
                        <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> فتح الإعلان
                    </a>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                </div>
            </div>
            <div class="modal-body p-2 text-center bg-black d-flex align-items-center justify-content-center" style="min-height: 380px; max-height: 75vh;">
                <img id="lightboxImg" src="" alt="" class="img-fluid rounded-2" style="max-height: 72vh; width: auto; object-fit: contain;">
            </div>
            <div class="modal-footer border-top border-secondary py-2 px-4 d-flex justify-content-between align-items-center bg-dark">
                <div class="d-flex align-items-center gap-2">
                    <span class="text-white-50 fs-8">السعر:</span>
                    <span class="fw-bold text-success fs-7" id="lightboxAdPrice"></span>
                </div>
                <button type="button" class="btn btn-secondary btn-sm rounded-pill px-4 fw-bold" data-bs-dismiss="modal">
                    إغلاق (Esc)
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Modal اختيار وتصفح القسم الهرمي التفاعلي مع كرت معلومات الإعلان (Category Picker with Ad Info Card) -->
<div class="modal fade" id="categoryPickerModal" tabindex="-1" aria-labelledby="categoryPickerModalLabel" aria-hidden="true" style="z-index: 1070;">
    <div class="modal-dialog modal-fullscreen-xl-down modal-xl modal-dialog-centered modal-dialog-scrollable" style="max-width: 95vw; width: 1250px;">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <div class="modal-header bg-dark text-white py-3 px-4 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-3">
                    <div class="rounded-circle bg-warning bg-opacity-20 p-2 text-warning d-flex align-items-center justify-content-center" style="width: 38px; height: 38px;">
                        <i class="fa-solid fa-layer-group fs-5"></i>
                    </div>
                    <div>
                        <div class="d-flex align-items-center gap-2">
                            <h6 class="modal-title fw-bold mb-0 text-white" id="categoryPickerModalLabel">اختيار وتحديد تصنيف الإعلان</h6>
                            <span class="badge bg-warning text-dark fw-bold fs-8" id="pickerAdIdBadge">#</span>
                        </div>
                        <small class="text-white-50 fs-8" id="pickerAdTitleBadge">اختر وتصفح القسم المناسب لمواصفات وتفاصيل هذا الإعلان</small>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="إغلاق"></button>
            </div>
            
            <div class="modal-body p-3 bg-light bg-opacity-50">
                <div class="row g-3 align-items-start">
                    <!-- اليمين: متصفح وشبكة الأقسام (Category Picker Navigation & Tiles) -->
                    <div class="col-lg-7 col-xl-8 order-1">
                        <div class="bg-white rounded-3 border p-3 shadow-xs h-100 d-flex flex-column">
                            <!-- شريط المسار والرجوع Breadcrumbs -->
                            <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap mb-3">
                                <nav aria-label="breadcrumb">
                                    <ol class="breadcrumb mb-0 py-1 px-3 bg-light border rounded-pill shadow-xs fs-7 fw-semibold" id="categoryPickerBreadcrumbs">
                                        <li class="breadcrumb-item active"><i class="fa-solid fa-house me-1"></i> الرئيسية</li>
                                    </ol>
                                </nav>
                                <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-3 fw-bold shadow-xs" id="btnPickerBack" style="display: none;" onclick="navigatePickerBack()">
                                    <i class="fa-solid fa-arrow-right me-1"></i> رجوع للخلف
                                </button>
                            </div>

                            <!-- شريط البحث السريع في الأقسام -->
                            <div class="input-group mb-3">
                                <span class="input-group-text bg-light border-end-0"><i class="fa-solid fa-magnifying-glass text-muted"></i></span>
                                <input type="text" id="categoryPickerSearch" class="form-control border-start-0 py-2 fs-7 fw-semibold" placeholder="ابحث عن أي قسم بسرعة (مثال: سيراتو، كيا، شقق، كنبايات...)" oninput="filterCategoryPicker(this.value)">
                                <button type="button" class="btn btn-outline-secondary px-3" onclick="document.getElementById('categoryPickerSearch').value=''; filterCategoryPicker('');" title="مسح البحث">
                                    <i class="fa-solid fa-xmark"></i>
                                </button>
                            </div>

                            <!-- زر اعتماد القسم الأب الحالي إذا أراد المستخدم التوقف عنده -->
                            <div id="pickerCurrentParentAction" class="mb-3" style="display: none;"></div>

                            <!-- شبكة الأقسام المعروضة -->
                            <div class="category-scroll-container flex-grow-1" style="min-height: 380px; max-height: 58vh; overflow-y: auto;">
                                <div id="categoryPickerGrid" class="row g-2"></div>

                                <!-- في حال لا توجد نتائج بحث -->
                                <div id="categoryPickerEmpty" class="text-center py-5 text-muted" style="display: none;">
                                    <i class="fa-solid fa-folder-open fs-1 text-secondary mb-2 d-block"></i>
                                    <span class="fw-bold fs-7">لم يتم العثور على أي قسم مطابق لكلمة البحث.</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- اليسار: كرت معلومات الإعلان الأصلي (Reference Card INSIDE Picker) -->
                    <div class="col-lg-5 col-xl-4 order-2">
                        <div class="card border-0 shadow-sm rounded-3 h-100 edit-ref-card" style="position: sticky; top: 0; background-color: #f8fafc; border: 1px solid #e2e8f0;">
                            <div class="card-header bg-dark text-white py-2 px-3 rounded-top-3 d-flex align-items-center justify-content-between">
                                <div class="d-flex align-items-center gap-2">
                                    <i class="fa-solid fa-clipboard-list text-warning"></i>
                                    <span class="fw-bold fs-8">بطاقة تفاصيل الإعلان (للمطابقة)</span>
                                </div>
                                <span class="badge bg-primary px-2 py-1 fs-9" id="pickerRefViewsBadge">👁️ 0</span>
                            </div>
                            <div class="card-body p-3 d-flex flex-column gap-2" style="max-height: 70vh; overflow-y: auto;">
                                <!-- صورة الإعلان المرجعية (قابلة للنقر للتكبير في البوب اب) -->
                                <div class="position-relative text-center rounded-3 overflow-hidden border bg-white shadow-xs" style="height: 160px; cursor: pointer;" onclick="openImageLightboxFromPickerRef()" title="انقر لتكبير ومعاينة الصورة في البوب اب">
                                    <img id="pickerRefImage" src="" alt="صورة الإعلان" class="w-100 h-100" style="object-fit: cover;" onerror="this.onerror=null; this.src='https://lelbai.com/icons/cars.svg';">
                                    <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-75 text-white py-1 px-2 d-flex justify-content-between align-items-center fs-9">
                                        <span><i class="fa-solid fa-magnifying-glass-plus me-1 text-warning"></i> انقر للتكبير</span>
                                        <span class="badge bg-secondary fs-9">معاينة الصورة</span>
                                    </div>
                                </div>

                                <!-- العنوان المسجل -->
                                <div class="bg-white p-2 rounded-2 border">
                                    <span class="text-muted fs-9 fw-bold d-block mb-1">عنوان الإعلان:</span>
                                    <div id="pickerRefTitle" class="fw-bold text-dark fs-7" style="word-break: break-word;"></div>
                                </div>

                                <!-- التصنيف المسجل حالياً -->
                                <div class="bg-white p-2 rounded-2 border">
                                    <span class="text-muted fs-9 fw-bold d-block mb-1">القسم المسجل حالياً:</span>
                                    <span id="pickerRefCategory" class="fw-bold text-primary fs-8 text-truncate d-block"></span>
                                </div>

                                <!-- السعر والمدينة -->
                                <div class="row g-2">
                                    <div class="col-6">
                                        <div class="bg-white p-2 rounded-2 border">
                                            <span class="text-muted fs-9 fw-bold d-block">السعر:</span>
                                            <span id="pickerRefPrice" class="fw-bold text-success fs-8"></span>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="bg-white p-2 rounded-2 border">
                                            <span class="text-muted fs-9 fw-bold d-block">المدينة:</span>
                                            <span id="pickerRefCity" class="fw-bold text-dark fs-8"></span>
                                        </div>
                                    </div>
                                </div>

                                <!-- المعلن والهاتف -->
                                <div class="bg-white p-2 rounded-2 border">
                                    <div class="d-flex justify-content-between align-items-center mb-1">
                                        <span class="text-muted fs-9 fw-bold"><i class="fa-solid fa-user me-1 text-primary"></i> المعلن:</span>
                                        <span id="pickerRefUser" class="fw-bold text-dark fs-8"></span>
                                    </div>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="text-muted fs-9 fw-bold"><i class="fa-solid fa-phone me-1 text-success"></i> الهاتف:</span>
                                        <span id="pickerRefPhone" class="fw-bold text-dark fs-8" dir="ltr"></span>
                                    </div>
                                </div>

                                <!-- الوصف الأصلي الكامل (أهم جزء لتحديد القسم!) -->
                                <div>
                                    <span class="text-muted fs-9 fw-bold d-block mb-1">وصف ومواصفات الإعلان (اقرأه لاختيار القسم بدقة):</span>
                                    <div id="pickerRefDescription" class="bg-white p-2 rounded-2 border text-muted fs-8" style="max-height: 150px; overflow-y: auto; white-space: pre-wrap; line-height: 1.55; border-color: #cbd5e1 !important;"></div>
                                </div>

                                <!-- رابط المعاينة -->
                                <div class="mt-auto pt-1">
                                    <a id="pickerRefLiveUrl" href="#" target="_blank" class="btn btn-sm btn-outline-primary w-100 fw-bold rounded-pill fs-8">
                                        <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> فتح الإعلان بالكامل على lelbai.com
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="modal-footer bg-white border-top py-2 px-3 d-flex justify-content-between align-items-center">
                <span class="text-muted fs-8"><i class="fa-solid fa-circle-info text-primary me-1"></i> النقر على أصغر قسم فرعي (أصغر ابن) يقوم باختياره فورياً وتثبيته في نموذج التعديل.</span>
                <button type="button" class="btn btn-secondary btn-sm rounded-pill px-4 fw-bold" data-bs-dismiss="modal">إغلاق بدون تغيير</button>
            </div>
        </div>
    </div>
</div>

<script>
// 1. Top-Left Floating Sync Status Manager (متاح فورياً على مستوى النافذة)
const SyncStatusManager = {
    pendingCount: 0,
    successTimer: null,

    start: function(text) {
        text = text || 'جاري الحفظ والمزامنة مع السيرفر... ⏳';
        this.pendingCount++;
        if (this.successTimer) {
            clearTimeout(this.successTimer);
            this.successTimer = null;
        }
        this.render('syncing', text);
    },

    success: function(text) {
        text = text || 'تم الحفظ بنجاح على السيرفر ✅';
        this.pendingCount = Math.max(0, this.pendingCount - 1);
        if (this.pendingCount === 0) {
            this.render('success', text);
            if (this.successTimer) clearTimeout(this.successTimer);
            this.successTimer = setTimeout(() => {
                this.hide();
            }, 2000); // ثانيتان بالضبط
        }
    },

    error: function(text) {
        text = text || 'حدث خطأ أثناء المزامنة مع السيرفر';
        this.pendingCount = Math.max(0, this.pendingCount - 1);
        if (this.successTimer) clearTimeout(this.successTimer);
        this.render('error', text);
    },

    render: function(type, text) {
        const indicator = document.getElementById('syncStatusIndicator');
        const badge = document.getElementById('syncStatusBadge');
        const icon = document.getElementById('syncStatusIcon');
        const textEl = document.getElementById('syncStatusText');
        const closeBtn = document.getElementById('syncStatusCloseBtn');

        if (!indicator || !badge) return;

        if (textEl) textEl.textContent = text;
        indicator.style.display = 'block';
        indicator.style.opacity = '1';
        indicator.style.transform = 'translateY(0)';

        if (type === 'syncing') {
            badge.style.backgroundColor = '#0f172a';
            badge.style.borderColor = '#f59e0b';
            badge.style.color = '#ffffff';
            if (icon) icon.className = 'fa-solid fa-arrows-rotate fa-spin text-warning fs-6';
            if (closeBtn) closeBtn.style.display = 'none';
        } else if (type === 'success') {
            badge.style.backgroundColor = '#15803d';
            badge.style.borderColor = '#22c55e';
            badge.style.color = '#ffffff';
            if (icon) icon.className = 'fa-solid fa-circle-check text-white fs-6';
            if (closeBtn) closeBtn.style.display = 'none';
        } else if (type === 'error') {
            badge.style.backgroundColor = '#991b1b';
            badge.style.borderColor = '#ef4444';
            badge.style.color = '#ffffff';
            if (icon) icon.className = 'fa-solid fa-triangle-exclamation text-white fs-6';
            if (closeBtn) closeBtn.style.display = 'inline-block';
        }
    },

    hide: function() {
        const indicator = document.getElementById('syncStatusIndicator');
        if (!indicator) return;
        indicator.style.transition = 'all 0.3s ease';
        indicator.style.opacity = '0';
        indicator.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 320);
    }
};
window.SyncStatusManager = SyncStatusManager;

// 2. Lightbox Popup Functions (متاحة فورياً لجميع عناصر HTML onclick)
function openImageLightbox(imgUrl, title, price, id, liveUrl) {
    const modalEl = document.getElementById('imageLightboxModal');
    if (!modalEl) return;
    const imgEl = document.getElementById('lightboxImg');
    const titleEl = document.getElementById('lightboxAdTitle');
    const priceEl = document.getElementById('lightboxAdPrice');
    const idEl = document.getElementById('lightboxAdId');
    const urlEl = document.getElementById('lightboxAdUrl');

    if (imgEl) imgEl.src = imgUrl || '';
    if (titleEl) titleEl.textContent = title || 'معاينة صورة الإعلان';
    if (priceEl) priceEl.textContent = price || 'غير محدد';
    if (idEl) idEl.textContent = '#' + (id || '');
    if (urlEl) urlEl.href = liveUrl || '#';

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
}
window.openImageLightbox = openImageLightbox;

function openImageLightboxFromRef() {
    const refImg = document.getElementById('refCardImage');
    if (refImg && refImg.src) {
        openImageLightbox(
            refImg.src,
            refImg.dataset.title || '',
            refImg.dataset.price || '',
            refImg.dataset.id || '',
            refImg.dataset.liveUrl || ''
        );
    }
}
window.openImageLightboxFromRef = openImageLightboxFromRef;

// 3. Categories Data and Hierarchical Maps
const allCategoriesData = {!! $categoriesJson ?? '[]' !!};
const catMap = {};
const childrenMap = {};

allCategoriesData.forEach(c => {
    catMap[c.id] = c;
    const pid = c.parent_id ? String(c.parent_id) : 'root';
    if (!childrenMap[pid]) {
        childrenMap[pid] = [];
    }
    childrenMap[pid].push(c);
});

function getCategoryPathText(catId) {
    if (!catId || !catMap[catId]) return '';
    const parts = [];
    let cur = catMap[catId];
    let visited = new Set();
    while (cur && !visited.has(cur.id)) {
        visited.add(cur.id);
        parts.unshift(cur.name_ar);
        cur = cur.parent_id ? catMap[cur.parent_id] : null;
    }
    return parts.join(' > ');
}

let pickerCurrentPid = 'root';
let pickerTrail = [];

function openImageLightboxFromPickerRef() {
    const refImg = document.getElementById('pickerRefImage');
    if (refImg && refImg.src) {
        openImageLightbox(
            refImg.src,
            refImg.dataset.title || '',
            refImg.dataset.price || '',
            refImg.dataset.id || '',
            refImg.dataset.liveUrl || ''
        );
    }
}
window.openImageLightboxFromPickerRef = openImageLightboxFromPickerRef;

function openCategoryPicker() {
    const searchInp = document.getElementById('categoryPickerSearch');
    if (searchInp) searchInp.value = '';

    // تعبئة بطاقة معلومات الإعلان المرجعية داخل بوب اب اختيار القسم فورياً (0ms)
    const adId = document.getElementById('modalListingIdDisplay')?.textContent || '';
    const adTitle = document.getElementById('editListingTitle')?.value || document.getElementById('refCardTitle')?.textContent || '';
    const refImg = document.getElementById('refCardImage');
    const refPrice = document.getElementById('refCardPrice')?.textContent || '';
    const refCat = document.getElementById('editCategoryDisplayText')?.textContent?.trim() || document.getElementById('refCardCategory')?.textContent || '';
    const refCity = document.getElementById('refCardCity')?.textContent || '';
    const refUser = document.getElementById('refCardUser')?.textContent || '';
    const refPhone = document.getElementById('editListingPhone')?.value || document.getElementById('refCardPhone')?.textContent || '';
    const refDesc = document.getElementById('editListingDescription')?.value || document.getElementById('refCardDescription')?.textContent || '';
    const refViews = document.getElementById('refCardViewsBadge')?.textContent || '';
    const refLive = document.getElementById('refCardLiveUrl')?.href || '';

    const pIdBadge = document.getElementById('pickerAdIdBadge');
    if (pIdBadge) pIdBadge.textContent = adId ? '#' + adId : '';

    const pTitleBadge = document.getElementById('pickerAdTitleBadge');
    if (pTitleBadge) pTitleBadge.textContent = adTitle ? ('الإعلان: ' + (adTitle.length > 50 ? adTitle.substring(0, 50) + '...' : adTitle)) : 'اختر وتصفح القسم المناسب لمواصفات وتفاصيل هذا الإعلان';

    const pImg = document.getElementById('pickerRefImage');
    if (pImg && refImg) {
        pImg.src = refImg.src;
        pImg.dataset.title = adTitle;
        pImg.dataset.price = refPrice;
        pImg.dataset.id = adId;
        pImg.dataset.liveUrl = refLive;
    }

    const pViews = document.getElementById('pickerRefViewsBadge');
    if (pViews) pViews.textContent = refViews || '👁️ 0';

    const pTitle = document.getElementById('pickerRefTitle');
    if (pTitle) pTitle.textContent = adTitle;

    const pPrice = document.getElementById('pickerRefPrice');
    if (pPrice) pPrice.textContent = refPrice;

    const pCat = document.getElementById('pickerRefCategory');
    if (pCat) pCat.textContent = refCat && !refCat.includes('اضغط') ? refCat : 'بدون تصنيف';

    const pCity = document.getElementById('pickerRefCity');
    if (pCity) pCity.textContent = refCity;

    const pUser = document.getElementById('pickerRefUser');
    if (pUser) pUser.textContent = refUser;

    const pPhone = document.getElementById('pickerRefPhone');
    if (pPhone) pPhone.textContent = refPhone || '-';

    const pDesc = document.getElementById('pickerRefDescription');
    if (pDesc) pDesc.textContent = refDesc || '(لا يوجد نص وصف مسجل)';

    const pLive = document.getElementById('pickerRefLiveUrl');
    if (pLive) pLive.href = refLive;

    // فتح القسم المختار حالياً إن وجد أو المستوى الرئيسي
    const currentSelectedId = document.getElementById('editListingCategory')?.value;
    if (currentSelectedId && catMap[currentSelectedId]) {
        pickerTrail = [];
        let cur = catMap[currentSelectedId];
        let visited = new Set();
        while (cur && !visited.has(cur.id)) {
            visited.add(cur.id);
            if (cur.parent_id && catMap[cur.parent_id]) {
                pickerTrail.unshift(catMap[cur.parent_id]);
                cur = catMap[cur.parent_id];
            } else {
                break;
            }
        }
        const lastParent = pickerTrail.length > 0 ? pickerTrail[pickerTrail.length - 1].id : 'root';
        renderPickerLevel(lastParent, pickerTrail);
    } else {
        renderPickerLevel('root', []);
    }

    const modalEl = document.getElementById('categoryPickerModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

function renderPickerLevel(parentId, trail) {
    pickerCurrentPid = String(parentId);
    pickerTrail = trail || [];

    const breadcrumbsOl = document.getElementById('categoryPickerBreadcrumbs');
    if (breadcrumbsOl) {
        let bHtml = `<li class="breadcrumb-item"><a href="javascript:void(0)" onclick="goToPickerBreadcrumb(-1)" class="text-decoration-none text-primary"><i class="fa-solid fa-house me-1"></i> الرئيسية</a></li>`;
        pickerTrail.forEach((item, idx) => {
            if (idx === pickerTrail.length - 1) {
                bHtml += `<li class="breadcrumb-item active text-dark fw-bold" aria-current="page">${escapeHtml(item.name_ar)}</li>`;
            } else {
                bHtml += `<li class="breadcrumb-item"><a href="javascript:void(0)" onclick="goToPickerBreadcrumb(${idx})" class="text-decoration-none text-primary">${escapeHtml(item.name_ar)}</a></li>`;
            }
        });
        breadcrumbsOl.innerHTML = bHtml;
    }

    const backBtn = document.getElementById('btnPickerBack');
    if (backBtn) {
        backBtn.style.display = pickerTrail.length > 0 ? 'inline-flex' : 'none';
    }

    const parentActionBox = document.getElementById('pickerCurrentParentAction');
    if (parentActionBox) {
        if (pickerCurrentPid !== 'root' && catMap[pickerCurrentPid]) {
            const currentCat = catMap[pickerCurrentPid];
            parentActionBox.innerHTML = `
                <div class="alert alert-primary d-flex align-items-center justify-content-between p-3 border-0 shadow-xs rounded-3 mb-3">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fa-solid fa-folder-open text-primary fs-5"></i>
                        <div>
                            <span class="fs-8 text-muted d-block">أنت تتصفح الآن قسم:</span>
                            <strong class="text-dark fs-7">${escapeHtml(currentCat.name_ar)}</strong>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-success fw-bold px-3 py-2 rounded-pill shadow-xs" onclick="selectCategoryFinal('${currentCat.id}')">
                        <i class="fa-solid fa-check-double me-1"></i> اعتماد هذا القسم واختياره
                    </button>
                </div>
            `;
            parentActionBox.style.display = 'block';
        } else {
            parentActionBox.innerHTML = '';
            parentActionBox.style.display = 'none';
        }
    }

    const items = childrenMap[pickerCurrentPid] || [];
    renderCategoryGrid(items, false);
}

function goToPickerBreadcrumb(index) {
    if (index === -1) {
        renderPickerLevel('root', []);
    } else if (index < pickerTrail.length) {
        const target = pickerTrail[index];
        const newTrail = pickerTrail.slice(0, index + 1);
        renderPickerLevel(target.id, newTrail);
    }
}

function navigatePickerBack() {
    if (pickerTrail.length > 1) {
        pickerTrail.pop();
        const prev = pickerTrail[pickerTrail.length - 1];
        renderPickerLevel(prev.id, pickerTrail);
    } else {
        renderPickerLevel('root', []);
    }
}

function renderCategoryGrid(items, isSearchResult) {
    const grid = document.getElementById('categoryPickerGrid');
    const emptyBox = document.getElementById('categoryPickerEmpty');
    if (!grid) return;

    if (!items || items.length === 0) {
        grid.innerHTML = '';
        if (emptyBox) emptyBox.style.display = 'block';
        return;
    }

    if (emptyBox) emptyBox.style.display = 'none';

    let html = '';
    items.forEach(c => {
        const hasChildren = (childrenMap[String(c.id)] || []).length > 0;
        let iconUrl = 'https://lelbai.com/icons/cars.svg';
        if (c.icon) {
            iconUrl = c.icon.startsWith('http') ? c.icon : 'https://lelbai.com/' + c.icon.replace(/^\/+/, '');
        }

        const isDirect = !hasChildren;
        const actionFn = hasChildren ? `drillDownCategory('${c.id}')` : `selectCategoryFinal('${c.id}')`;
        const pathBreadcrumb = isSearchResult ? `<div class="fs-9 text-muted mt-1 text-truncate">${escapeHtml(getCategoryPathText(c.id))}</div>` : '';

        html += `
            <div class="col-6 col-md-4 col-lg-3">
                <div class="card h-100 border rounded-3 p-2 text-center cursor-pointer category-picker-item shadow-2xs hover-shadow transition-all ${isDirect ? 'border-success border-opacity-50' : 'border-light'}" 
                     onclick="${actionFn}" 
                     style="cursor: pointer; transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);">
                    <div class="d-flex flex-column align-items-center justify-content-center p-2">
                        <div class="mb-2 position-relative">
                            <img src="${iconUrl}" alt="" class="rounded-circle border p-1" style="width: 44px; height: 44px; object-fit: cover;" onerror="this.onerror=null; this.src='https://lelbai.com/icons/cars.svg';">
                            ${hasChildren ? '<span class="position-absolute bottom-0 end-0 badge bg-primary rounded-circle p-1" style="transform: translate(20%, 20%);"><i class="fa-solid fa-arrow-left fs-9"></i></span>' : '<span class="position-absolute bottom-0 end-0 badge bg-success rounded-circle p-1" style="transform: translate(20%, 20%);"><i class="fa-solid fa-check fs-9"></i></span>'}
                        </div>
                        <h6 class="fw-bold text-dark fs-8 mb-1 text-truncate w-100" title="${escapeHtml(c.name_ar)}">${escapeHtml(c.name_ar)}</h6>
                        ${pathBreadcrumb}
                        <div class="mt-2">
                            ${hasChildren ? '<span class="badge bg-light text-primary border fs-9 fw-semibold"><i class="fa-solid fa-folder-tree me-1"></i> تفرعات</span>' : '<span class="badge bg-success bg-opacity-10 text-success fs-9 fw-bold">قسم نهائي ✓</span>'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    grid.innerHTML = html;
}

function drillDownCategory(catId) {
    const cat = catMap[catId];
    if (cat) {
        const newTrail = [...pickerTrail, cat];
        renderPickerLevel(cat.id, newTrail);
    }
}

function selectCategoryFinal(catId) {
    const cat = catMap[catId];
    if (!cat) return;

    const catInput = document.getElementById('editListingCategory');
    if (catInput) catInput.value = cat.id;

    const catDisplay = document.getElementById('editCategoryDisplayText');
    if (catDisplay) {
        const fullPath = getCategoryPathText(cat.id);
        catDisplay.innerHTML = `<span class="badge bg-primary bg-opacity-10 text-primary fs-7 px-2 py-1"><i class="fa-solid fa-folder-tree me-1"></i> ${escapeHtml(fullPath)}</span>`;
    }

    const modalEl = document.getElementById('categoryPickerModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }
}

function filterCategoryPicker(query) {
    query = (query || '').trim().toLowerCase();
    const parentActionBox = document.getElementById('pickerCurrentParentAction');
    const backBtn = document.getElementById('btnPickerBack');

    if (!query) {
        renderPickerLevel(pickerCurrentPid, pickerTrail);
        return;
    }

    if (parentActionBox) parentActionBox.style.display = 'none';
    if (backBtn) backBtn.style.display = 'none';

    const matched = allCategoriesData.filter(c => {
        const nameAr = (c.name_ar || '').toLowerCase();
        const nameEn = (c.name_en || '').toLowerCase();
        const slug = (c.slug || '').toLowerCase();
        return nameAr.includes(query) || nameEn.includes(query) || slug.includes(query);
    });

    renderCategoryGrid(matched, true);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// 4. دالة تعبئة وفتح مودال تعديل الإعلان وكرت المرجع الأصلي
function openEditModalForListing(btn) {
    if (!btn) return;
    const id = btn.dataset.id;
    const title = btn.dataset.title || '';
    const price = btn.dataset.price || '';
    const currency = btn.dataset.currency || 'SYP';
    const categoryId = btn.dataset.categoryId || '';
    const categoryName = btn.dataset.categoryName || 'بدون تصنيف';
    const cityId = btn.dataset.cityId || '';
    const cityName = btn.dataset.cityName || 'غير محدد';
    const phone = btn.dataset.phone || '';
    const description = btn.dataset.description || '';
    const status = btn.dataset.status || 'active';
    const featured = btn.dataset.featured === '1' || btn.dataset.featured === 1;
    const image = btn.dataset.image || '';
    const userName = btn.dataset.userName || 'مستخدم مجهول';
    const views = btn.dataset.views || '0';
    const createdAt = btn.dataset.createdAt || '-';
    const liveUrl = btn.dataset.liveUrl || ('https://lelbai.com/listings/' + id + '/details');

    // 1. تعبئة حقول نموذج التعديل
    const idDisplay = document.getElementById('modalListingIdDisplay');
    if (idDisplay) idDisplay.textContent = id;

    const titleInput = document.getElementById('editListingTitle');
    if (titleInput) titleInput.value = title;

    const catInput = document.getElementById('editListingCategory');
    if (catInput) catInput.value = categoryId;

    const catDisplay = document.getElementById('editCategoryDisplayText');
    if (catDisplay) {
        if (categoryId && typeof catMap !== 'undefined' && catMap[categoryId]) {
            const fullPath = getCategoryPathText(categoryId);
            catDisplay.innerHTML = `<span class="badge bg-primary bg-opacity-10 text-primary fs-7 px-2 py-1"><i class="fa-solid fa-folder-tree me-1"></i> ${escapeHtml(fullPath)}</span>`;
        } else if (categoryName && categoryName !== 'بدون تصنيف') {
            catDisplay.textContent = categoryName;
        } else {
            catDisplay.innerHTML = '<span class="text-muted">اضغط لاختيار القسم...</span>';
        }
    }

    const citySelect = document.getElementById('editListingCity');
    if (citySelect) citySelect.value = String(cityId || '');

    const priceInput = document.getElementById('editListingPrice');
    if (priceInput) priceInput.value = price;

    const currSelect = document.getElementById('editListingCurrency');
    if (currSelect) currSelect.value = currency;

    const phoneInput = document.getElementById('editListingPhone');
    if (phoneInput) phoneInput.value = phone;

    const statusSelect = document.getElementById('editListingStatus');
    if (statusSelect) statusSelect.value = status;

    const featCheck = document.getElementById('editListingFeatured');
    if (featCheck) featCheck.checked = featured;

    const descText = document.getElementById('editListingDescription');
    if (descText) descText.value = description;

    // 2. تعبئة كرت المرجع الأصلي (Reference Card)
    const refCardId = document.getElementById('refCardIdBadge');
    if (refCardId) refCardId.textContent = '#' + id;

    const cleanFormattedPrice = (price ? Number(price).toLocaleString() : '0') + ' ' + (currency === 'USD' ? '$' : 'ل.س');

    const refImg = document.getElementById('refCardImage');
    if (refImg) {
        refImg.src = image || 'https://lelbai.com/icons/cars.svg';
        refImg.dataset.title = title;
        refImg.dataset.price = cleanFormattedPrice;
        refImg.dataset.id = id;
        refImg.dataset.liveUrl = liveUrl;
    }

    const refViewsBadge = document.getElementById('refCardViewsBadge');
    if (refViewsBadge) refViewsBadge.textContent = '👁️ ' + views;

    const refTitle = document.getElementById('refCardTitle');
    if (refTitle) refTitle.textContent = title;

    const refPrice = document.getElementById('refCardPrice');
    if (refPrice) refPrice.textContent = cleanFormattedPrice;

    const refCategory = document.getElementById('refCardCategory');
    if (refCategory) {
        if (categoryId && typeof catMap !== 'undefined' && catMap[categoryId]) {
            refCategory.textContent = getCategoryPathText(categoryId);
        } else {
            refCategory.textContent = categoryName;
        }
    }

    const refCity = document.getElementById('refCardCity');
    if (refCity) refCity.textContent = cityName;

    const refUser = document.getElementById('refCardUser');
    if (refUser) refUser.textContent = userName;

    const refPhone = document.getElementById('refCardPhone');
    if (refPhone) refPhone.textContent = phone || '-';

    const refCreatedAt = document.getElementById('refCardCreatedAt');
    if (refCreatedAt) refCreatedAt.textContent = createdAt;

    const refDesc = document.getElementById('refCardDescription');
    if (refDesc) refDesc.textContent = description || '(لا يوجد نص وصف مسجل)';

    const refLive = document.getElementById('refCardLiveUrl');
    if (refLive) refLive.href = liveUrl;

    const refStatus = document.getElementById('refCardStatus');
    if (refStatus) {
        let badgeHtml = '<span class="badge bg-secondary">موقوف ⏸️</span>';
        if (status === 'active') badgeHtml = '<span class="badge bg-success bg-opacity-20 text-success border border-success border-opacity-25">نشط ✅</span>';
        else if (status === 'pending') badgeHtml = '<span class="badge bg-warning bg-opacity-20 text-dark border border-warning">بانتظار المراجعة ⏳</span>';
        else if (status === 'rejected') badgeHtml = '<span class="badge bg-danger bg-opacity-20 text-danger border border-danger border-opacity-25">مرفوض ❌</span>';
        refStatus.innerHTML = badgeHtml;
    }

    const form = document.getElementById('editListingForm');
    if (form) form.action = '{{ url("listings") }}/' + id + '/update';

    const modalEl = document.getElementById('editListingModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}
window.openEditModalForListing = openEditModalForListing;

// 5. Toast Notifications & Helpers
function showFloatingToast(message, type) {
    type = type || 'success';
    let container = document.getElementById('floatingToastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'floatingToastContainer';
        container.style.cssText = 'position:fixed;bottom:25px;left:25px;z-index:99999;display:flex;flex-direction:column;gap:10px;pointer-events:none;max-width:380px;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg rounded-4 p-3 mb-0 d-flex align-items-center gap-2 border-0 text-white`;
    toast.style.cssText = `pointer-events:auto;transition:all 0.3s cubic-bezier(0.16, 1, 0.3, 1);transform:translateY(20px);opacity:0;font-size:0.875rem;font-weight:700;background-color:${type === 'success' ? '#15803D' : (type === 'danger' ? '#DC2626' : '#2563EB')};box-shadow:0 10px 25px rgba(0,0,0,0.2) !important;`;
    
    const icon = type === 'success' ? 'fa-circle-check' : (type === 'danger' ? 'fa-circle-xmark' : 'fa-circle-info');
    toast.innerHTML = `<i class="fa-solid ${icon} fs-5"></i> <span>${escapeHtml(message)}</span>`;
    
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    }, 10);

    setTimeout(() => {
        toast.style.transform = 'translateY(20px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 350);
    }, 3500);
}
window.showFloatingToast = showFloatingToast;

function updateKpi(id, delta) {
    const el = document.getElementById('kpi-count-' + id);
    if (el) {
        let current = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10) || 0;
        current = Math.max(0, current + delta);
        el.textContent = current.toLocaleString();
    }
}
window.updateKpi = updateKpi;

function fadeOutRow(row, callback) {
    if (!row) return;
    row.style.transition = 'all 0.35s ease';
    row.style.opacity = '0';
    row.style.transform = 'scale(0.95)';
    setTimeout(() => {
        row.style.display = 'none';
        if (callback) callback();
    }, 360);
}
window.fadeOutRow = fadeOutRow;

// 6. Quick Status Update (Accept / Suspend) with Optimistic UI & Sync Indicator
window.quickUpdateListingStatus = function(id, newStatus, event) {
    if (event) event.preventDefault();
    const currentUrlParams = new URLSearchParams(window.location.search);
    const activeTabStatus = currentUrlParams.get('status') || '';
    const row = document.getElementById('listing-row-' + id);
    const oldStatus = row ? row.dataset.status : '';

    // Immediate Optimistic Visual Feedback (0ms)
    if (row) {
        row.dataset.status = newStatus;
        if (activeTabStatus === 'pending' && newStatus === 'active') {
            row.style.backgroundColor = '#dcfce7';
            updateKpi('pending', -1);
            updateKpi('active', +1);
            fadeOutRow(row);
        } else if (activeTabStatus === 'active' && newStatus === 'suspended') {
            row.style.backgroundColor = '#f1f5f9';
            updateKpi('active', -1);
            fadeOutRow(row);
        } else {
            const statusCell = document.getElementById('status-cell-' + id);
            if (statusCell) {
                if (newStatus === 'active') {
                    statusCell.innerHTML = '<span class="badge bg-success bg-opacity-15 text-success border border-success border-opacity-25 px-2 py-1 rounded-pill">نشط ✅</span>';
                    updateKpi('active', +1);
                    if (oldStatus === 'pending') updateKpi('pending', -1);
                } else if (newStatus === 'suspended') {
                    statusCell.innerHTML = '<span class="badge bg-secondary px-2 py-1 rounded-pill">موقوف ⏸️</span>';
                    updateKpi('active', -1);
                }
            }
            row.classList.remove('row-optimistic-flash');
            void row.offsetWidth; // trigger reflow
            row.classList.add('row-optimistic-flash');
        }
    }

    const actionText = newStatus === 'active' ? 'قبول وتفعيل' : 'إيقاف';
    SyncStatusManager.start(`جاري ${actionText} الإعلان #${id} بالسيرفر... ⏳`);

    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '{{ csrf_token() }}';

    fetch('{{ url("listings") }}/' + id + '/status', {
        method: 'POST',
        headers: {
            'X-CSRF-TOKEN': csrf,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            SyncStatusManager.success(`تم ${actionText} الإعلان #${id} على السيرفر بنجاح ✅`);
        } else {
            SyncStatusManager.error(`فشل ${actionText} للإعلان #${id}: ` + (data.message || ''));
            showFloatingToast(data.message || 'تعذر حفظ الحالة على السيرفر', 'danger');
        }
    })
    .catch(err => {
        SyncStatusManager.error(`فشل الاتصال أثناء ${actionText} للإعلان #${id}`);
        showFloatingToast('تنبيه: تم الإجراء محلياً ولكن تعذر الاتصال بالسيرفر: ' + err.message, 'warning');
    });
};

// 7. Event Delegation for Clicks (Always works on all buttons, initial and dynamic SPA!)
document.addEventListener('click', function(e) {
    // زر التعديل
    const editBtn = e.target.closest('.btn-edit-listing');
    if (editBtn) {
        e.preventDefault();
        openEditModalForListing(editBtn);
        return;
    }

    // زر الحذف
    const deleteBtn = e.target.closest('.btn-open-delete-modal');
    if (deleteBtn) {
        e.preventDefault();
        const id = deleteBtn.getAttribute('data-id');
        const title = deleteBtn.getAttribute('data-title');
        const form = document.getElementById('deleteListingForm');
        if (form) form.action = '{{ url("listings") }}/' + id;
        const tEl = document.getElementById('deleteModalListingTitle');
        if (tEl) tEl.textContent = title;
        const modalEl = document.getElementById('deleteListingModal');
        if (modalEl) new bootstrap.Modal(modalEl).show();
        return;
    }

    // زر الرفض
    const rejectBtn = e.target.closest('.btn-open-reject-modal');
    if (rejectBtn) {
        e.preventDefault();
        const id = rejectBtn.getAttribute('data-id');
        const title = rejectBtn.getAttribute('data-title');
        const reason = rejectBtn.getAttribute('data-reason') || '';
        const aiSuggestion = rejectBtn.getAttribute('data-ai-suggestion') || '';

        const form = document.getElementById('rejectListingForm');
        if (form) form.action = '{{ url("listings") }}/' + id + '/status';
        const tEl = document.getElementById('modalListingTitle');
        if (tEl) tEl.textContent = title;
        const reasonInput = document.getElementById('rejectionReasonInput');
        if (reasonInput) reasonInput.value = reason || aiSuggestion;
        const modalEl = document.getElementById('rejectListingModal');
        if (modalEl) new bootstrap.Modal(modalEl).show();
        return;
    }
});

// 8. DOMContentLoaded Initializations
document.addEventListener('DOMContentLoaded', function() {
    // Column Visibility Toggles
    const checkboxes = document.querySelectorAll('.col-toggle');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            const colIndex = this.dataset.col;
            const cells = document.querySelectorAll('.col-cell-' + colIndex);
            cells.forEach(cell => {
                cell.style.display = this.checked ? '' : 'none';
            });
        });
    });

    // Bulk toolbar helper
    function updateBulkToolbar() {
        const checked = document.querySelectorAll('.listing-checkbox:checked');
        const count = checked.length;
        const selectedCountSpan = document.getElementById('selectedCount');
        const bulkToolbar = document.getElementById('bulkActionsToolbar');
        if (selectedCountSpan) selectedCountSpan.textContent = count;
        if (bulkToolbar) {
            bulkToolbar.style.setProperty('display', count > 0 ? 'flex' : 'none', 'important');
        }
    }
    window.updateBulkToolbar = updateBulkToolbar;

    // Reject Form Ajax Submission with Optimistic UI & Sync Indicator
    const rejectForm = document.getElementById('rejectListingForm');
    if (rejectForm) {
        rejectForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.action;
            const parts = actionUrl.split('/');
            const id = parts[parts.indexOf('listings') + 1];
            const reason = document.getElementById('rejectionReasonInput').value;
            const currentUrlParams = new URLSearchParams(window.location.search);
            const activeTabStatus = currentUrlParams.get('status') || '';

            // 1. إغلاق المودال فورياً في 0ms
            const modalEl = document.getElementById('rejectListingModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            // 2. تطبيق التغيير محلياً فورياً (0ms)
            const row = document.getElementById('listing-row-' + id);
            if (row) {
                if (activeTabStatus === 'pending') {
                    row.style.backgroundColor = '#fee2e2';
                    updateKpi('pending', -1);
                    updateKpi('rejected', +1);
                    fadeOutRow(row);
                } else {
                    const statusCell = document.getElementById('status-cell-' + id);
                    if (statusCell) {
                        statusCell.innerHTML = '<span class="badge bg-danger bg-opacity-15 text-danger border border-danger border-opacity-25 px-2 py-1 rounded-pill">مرفوض ❌</span>';
                    }
                }
            }

            // 3. تشغيل مؤشر المزامنة في أعلى اليسار
            SyncStatusManager.start(`جاري رفض وحجب الإعلان #${id} بالسيرفر... ⏳`);

            const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '{{ csrf_token() }}';

            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'X-CSRF-TOKEN': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: 'rejected', rejection_reason: reason })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    SyncStatusManager.success(`تم رفض وحجب الإعلان #${id} على السيرفر بنجاح ✅`);
                } else {
                    SyncStatusManager.error(`فشل الرفض بالسيرفر للإعلان #${id}: ` + (data.message || ''));
                    showFloatingToast(data.message || 'تعذر تأكيد الرفض بالسيرفر', 'danger');
                }
            })
            .catch(err => {
                SyncStatusManager.error(`فشل الاتصال أثناء رفض الإعلان #${id}`);
                showFloatingToast('خطأ في الاتصال: ' + err.message, 'warning');
            });
        });
    }

    // Delete Form Ajax Submission with Optimistic UI & Sync Indicator
    const deleteForm = document.getElementById('deleteListingForm');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.action;
            const parts = actionUrl.split('/');
            const id = parts[parts.indexOf('listings') + 1];

            // 1. إغلاق المودال فورياً في 0ms
            const modalEl = document.getElementById('deleteListingModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            // 2. حذف السطر محلياً فورياً (0ms)
            const row = document.getElementById('listing-row-' + id);
            if (row) {
                updateKpi('all', -1);
                fadeOutRow(row);
            }

            // 3. تشغيل مؤشر المزامنة في أعلى اليسار
            SyncStatusManager.start(`جاري حذف الإعلان #${id} نهائياً بالسيرفر... ⏳`);

            const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '{{ csrf_token() }}';

            fetch(actionUrl, {
                method: 'DELETE',
                headers: {
                    'X-CSRF-TOKEN': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    SyncStatusManager.success(`تم حذف الإعلان #${id} نهائياً من السيرفر ✅`);
                } else {
                    SyncStatusManager.error(`فشل حذف الإعلان #${id} بالسيرفر: ` + (data.message || ''));
                    showFloatingToast(data.message || 'تعذر الحذف بالسيرفر', 'danger');
                }
            })
            .catch(err => {
                SyncStatusManager.error(`فشل الاتصال أثناء حذف الإعلان #${id}`);
                showFloatingToast('خطأ في الاتصال: ' + err.message, 'warning');
            });
        });
    }

    // Edit Form Full Optimistic Ajax Submission (استجابة فورية 0ms مع مزامنة خلفية)
    const editForm = document.getElementById('editListingForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.action;
            const parts = actionUrl.split('/');
            const id = parts[parts.indexOf('listings') + 1];

            // قراءة القيم الجديدة من الفورم فورياً
            const newTitle = document.getElementById('editListingTitle')?.value || '';
            const newPrice = document.getElementById('editListingPrice')?.value || '';
            const newCurrency = document.getElementById('editListingCurrency')?.value || 'SYP';
            const newCatId = document.getElementById('editListingCategory')?.value || '';
            const catDisplay = document.getElementById('editCategoryDisplayText');
            const newCatText = catDisplay?.textContent?.trim() || '';
            const citySelect = document.getElementById('editListingCity');
            const newCityName = citySelect?.options[citySelect.selectedIndex]?.text || '';
            const newPhone = document.getElementById('editListingPhone')?.value || '';
            const newStatus = document.getElementById('editListingStatus')?.value || 'active';
            const isFeatured = document.getElementById('editListingFeatured')?.checked;
            const newDesc = document.getElementById('editListingDescription')?.value || '';

            // 1. إغلاق نافذة التعديل فورياً في 0ms (بدون أي انتظار لرد السيرفر!)
            const modalEl = document.getElementById('editListingModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            // 2. تحديث بيانات السطر في الجدول محلياً فورياً (0ms Perceived Latency)
            const row = document.getElementById('listing-row-' + id);
            if (row) {
                // تحديث العنوان
                const titleEl = row.querySelector('.col-cell-1 .fw-bold');
                if (titleEl) {
                    titleEl.textContent = newTitle.length > 40 ? newTitle.substring(0, 40) + '...' : newTitle;
                    titleEl.setAttribute('title', newTitle);
                }

                // تحديث التصنيف
                const catEl = row.querySelector('.col-cell-1 .text-secondary');
                if (catEl && newCatText && !newCatText.includes('اختر')) {
                    catEl.textContent = newCatText;
                }

                // تحديث السعر والمدينة
                const priceCell = row.querySelector('.col-cell-3');
                if (priceCell) {
                    const priceFormatted = newPrice ? Number(newPrice).toLocaleString() : '0';
                    const currSymbol = newCurrency === 'USD' ? '$' : 'ل.س';
                    priceCell.innerHTML = `
                        <div class="fw-bold text-success fs-7">
                            ${priceFormatted} ${currSymbol}
                        </div>
                        <div class="fs-8 text-muted d-flex align-items-center gap-1">
                            <i class="fa-solid fa-location-dot text-danger fs-9"></i>
                            <span>${escapeHtml(newCityName)}</span>
                        </div>
                    `;
                }

                // تحديث رقم الهاتف
                const phoneEl = row.querySelector('.col-cell-2 span[dir="ltr"]');
                if (phoneEl) {
                    phoneEl.textContent = newPhone || '-';
                }

                // تحديث شارة الحالة
                const statusCell = document.getElementById('status-cell-' + id);
                if (statusCell) {
                    if (newStatus === 'active') statusCell.innerHTML = '<span class="badge bg-success bg-opacity-15 text-success border border-success border-opacity-25 px-2 py-1 rounded-pill">نشط ✅</span>';
                    else if (newStatus === 'pending') statusCell.innerHTML = '<span class="badge bg-warning bg-opacity-20 text-dark border border-warning px-2 py-1 rounded-pill">بانتظار المراجعة ⏳</span>';
                    else if (newStatus === 'rejected') statusCell.innerHTML = '<span class="badge bg-danger bg-opacity-15 text-danger border border-danger border-opacity-25 px-2 py-1 rounded-pill">مرفوض ❌</span>';
                    else if (newStatus === 'suspended') statusCell.innerHTML = '<span class="badge bg-secondary px-2 py-1 rounded-pill">موقوف ⏸️</span>';
                }

                // تحديث خصائص زر التعديل ليبقى متزامناً مع الفتح القادم
                const editBtn = row.querySelector('.btn-edit-listing');
                if (editBtn) {
                    editBtn.dataset.title = newTitle;
                    editBtn.dataset.price = newPrice;
                    editBtn.dataset.currency = newCurrency;
                    editBtn.dataset.categoryId = newCatId;
                    if (newCatText && !newCatText.includes('اختر')) editBtn.dataset.categoryName = newCatText;
                    editBtn.dataset.cityId = citySelect?.value || '';
                    editBtn.dataset.cityName = newCityName;
                    editBtn.dataset.phone = newPhone;
                    editBtn.dataset.status = newStatus;
                    editBtn.dataset.featured = isFeatured ? '1' : '0';
                    editBtn.dataset.description = newDesc;
                }

                // وميض أخضر فوري لطيف للسطر لتأكيد التعديل
                row.classList.remove('row-optimistic-flash');
                void row.offsetWidth;
                row.classList.add('row-optimistic-flash');
            }

            // 3. تشغيل مؤشر المزامنة في أعلى اليسار
            SyncStatusManager.start(`جاري حفظ تعديلات الإعلان #${id} بالسيرفر... ⏳`);

            // 4. إرسال الطلب في الخلفية بدون تعطيل المستخدم
            const formData = new FormData(this);
            const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '{{ csrf_token() }}';

            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'X-CSRF-TOKEN': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // تم الحفظ بالسيرفر بنجاح! يبقى 2 ثانية ثم يختفي تلقائياً
                    SyncStatusManager.success(`تم حفظ تعديلات الإعلان #${id} على السيرفر بنجاح ✅`);
                } else {
                    SyncStatusManager.error(`فشل حفظ تعديلات #${id}: ` + (data.message || 'خطأ غير معروف'));
                    showFloatingToast(data.message || 'تعذر حفظ التعديلات بالسيرفر', 'danger');
                }
            })
            .catch(err => {
                SyncStatusManager.error(`فشل حفظ تعديلات #${id}: خطأ في الاتصال بالسيرفر`);
                showFloatingToast('خطأ بالاتصال أثناء حفظ الإعلان #' + id + ': ' + err.message, 'danger');
            });
        });
    }

    // Modal scroll fix for category picker
    const pickerModalEl = document.getElementById('categoryPickerModal');
    if (pickerModalEl) {
        pickerModalEl.addEventListener('hidden.bs.modal', function () {
            const editModalEl = document.getElementById('editListingModal');
            if (editModalEl && editModalEl.classList.contains('show')) {
                document.body.classList.add('modal-open');
            }
        });
    }

    initDynamicListingHandlers();
});

// 9. Dynamic SPA & Table Handlers
function loadListingsAsync(url, updateHistory) {
    if (updateHistory === undefined) updateHistory = true;
    const tableCard = document.getElementById('listingsTableCard');
    const catCard = document.getElementById('categoryHierarchyCard');
    const filterCard = document.getElementById('filterStatusCard');

    if (tableCard) {
        tableCard.style.transition = 'opacity 0.15s ease';
        tableCard.style.opacity = '0.35';
        tableCard.style.pointerEvents = 'none';
    }

    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.text())
    .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const newTable = doc.getElementById('listingsTableCard');
        if (newTable && tableCard) {
            tableCard.innerHTML = newTable.innerHTML;
        }

        const newCat = doc.getElementById('categoryHierarchyCard');
        if (newCat && catCard) {
            catCard.innerHTML = newCat.innerHTML;
        }

        const newFilter = doc.getElementById('filterStatusCard');
        if (newFilter && filterCard) {
            filterCard.innerHTML = newFilter.innerHTML;
        }

        const newKpi = doc.querySelector('.row.g-3.mb-4');
        const oldKpi = document.querySelector('.row.g-3.mb-4');
        if (newKpi && oldKpi) {
            oldKpi.innerHTML = newKpi.innerHTML;
        }

        if (updateHistory) {
            window.history.pushState(null, '', url);
        }

        initDynamicListingHandlers();
    })
    .catch(err => {
        window.location.href = url;
    })
    .finally(() => {
        if (tableCard) {
            tableCard.style.opacity = '1';
            tableCard.style.pointerEvents = 'auto';
        }
    });
}

function initDynamicListingHandlers() {
    // 1. اعتراض النقر على تبويبات الحالة والأقسام والترقيم
    const filterLinks = document.querySelectorAll('#filterStatusCard a, #categoryHierarchyCard a, #listingsTableCard .pagination a');
    filterLinks.forEach(link => {
        if (link.href && !link.href.includes('javascript:') && !link.getAttribute('target') && !link.classList.contains('no-ajax')) {
            link.onclick = function(e) {
                e.preventDefault();
                loadListingsAsync(this.href);
            };
        }
    });

    // 2. اعتراض إرسال نموذج البحث والفلترة
    const filterForm = document.querySelector('#filterStatusCard form');
    if (filterForm) {
        filterForm.onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const params = new URLSearchParams(formData);
            const actionUrl = this.action.split('?')[0] + '?' + params.toString();
            loadListingsAsync(actionUrl);
        };
    }

    // 3. إعادة ربط صندوق التحديد للكل
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            document.querySelectorAll('.listing-checkbox').forEach(cb => {
                cb.checked = selectAllCheckbox.checked;
            });
            if (typeof updateBulkToolbar === 'function') updateBulkToolbar();
        });
    }

    document.querySelectorAll('.listing-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            if (typeof updateBulkToolbar === 'function') updateBulkToolbar();
        });
    });
}

window.addEventListener('popstate', () => {
    loadListingsAsync(location.href, false);
});

function submitBulkAction(action) {
    if (action === 'delete') {
        if (!confirm('هل أنت متأكد من حذف كافة الإعلانات المحددة نهائياً؟')) {
            return;
        }
    }
    const input = document.getElementById('bulkActionInput');
    if (input) input.value = action;
    const form = document.getElementById('bulkActionForm');
    const checked = document.querySelectorAll('.listing-checkbox:checked');
    const ids = Array.from(checked).map(c => c.value);

    if (ids.length === 0) {
        showFloatingToast('يرجى تحديد إعلان واحد على الأقل', 'warning');
        return;
    }

    // Optimistic UI for bulk action
    checked.forEach(c => {
        const row = document.getElementById('listing-row-' + c.value);
        if (row) {
            row.style.opacity = '0.4';
            if (action === 'delete') row.style.display = 'none';
        }
    });

    SyncStatusManager.start(`جاري تطبيق الإجراء الجماعي (${action}) على ${ids.length} إعلانات... ⏳`);

    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '{{ csrf_token() }}';

    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRF-TOKEN': csrf,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: action, listing_ids: ids })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            SyncStatusManager.success(`تم تنفيذ الإجراء الجماعي بنجاح على السيرفر ✅`);
            showFloatingToast(data.message || 'تم تنفيذ الإجراء بنجاح', 'success');
            setTimeout(() => location.reload(), 1200);
        } else {
            SyncStatusManager.error(`فشل الإجراء الجماعي: ` + (data.message || ''));
            showFloatingToast(data.message || 'تعذر تطبيق الإجراء', 'danger');
        }
    })
    .catch(err => {
        form.submit();
    });
}

</script>
@endsection
