@extends('layouts.admin')

@section('content')
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
<div class="card border-0 shadow-sm rounded-3 mb-4 overflow-hidden">
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
<div class="card border-0 shadow-sm rounded-3 mb-4">
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
<div class="card border-0 shadow-sm rounded-3 overflow-hidden">
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
                        <th class="col-cell-0" style="min-width: 140px;"># والصورة</th>
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
                                    @if($primaryImg)
                                        <a href="{{ $primaryImg }}" target="_blank" title="عرض الصورة بالحجم الكامل">
                                            <img src="{{ $primaryImg }}" class="rounded-3 border shadow-xs" style="width: 46px; height: 46px; object-fit: cover; flex-shrink: 0;" alt="" onerror="this.onerror=null; this.src='https://lelbai.com/icons/cars.svg';">
                                        </a>
                                    @else
                                        <div class="rounded-3 border bg-light d-flex align-items-center justify-content-center text-muted" style="width: 46px; height: 46px; flex-shrink: 0;">
                                            <i class="fa-solid fa-image"></i>
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
                                            data-city-id="{{ $listing->city_id }}"
                                            data-phone="{{ $listing->contact_phone ?: ($listing->user?->phone ?: '') }}"
                                            data-description="{{ $listing->description }}"
                                            data-status="{{ $listing->status }}"
                                            data-featured="{{ $listing->is_featured ? 1 : 0 }}"
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

<!-- Modal تعديل الإعلان المباشر -->
<div class="modal fade" id="editListingModal" tabindex="-1" aria-labelledby="editListingModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <form id="editListingForm" method="POST" action="">
                @csrf
                <div class="modal-header bg-warning bg-opacity-10 border-bottom py-3 px-4">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fa-solid fa-pen-to-square text-warning fs-5"></i>
                        <h5 class="modal-title fw-bold text-dark mb-0" id="editListingModalLabel">تعديل الإعلان رقم #<span id="modalListingIdDisplay"></span></h5>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                </div>
                <div class="modal-body p-4">
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
                                    <i class="fa-solid fa-folder-tree me-1"></i> تصفح الشجرة الهرمية
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
                <div class="modal-footer bg-light border-top py-3 px-4 d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary rounded-pill px-4 fw-bold" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-success rounded-pill px-4 fw-bold shadow-sm">
                        <i class="fa-solid fa-floppy-disk me-1"></i> حفظ التعديلات الآن
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Modal اختيار وتصفح القسم الهرمي التفاعلي (بوب اب الأقسام) -->
<div class="modal fade" id="categoryPickerModal" tabindex="-1" aria-labelledby="categoryPickerModalLabel" aria-hidden="true" style="z-index: 1070;">
    <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <div class="modal-header bg-dark text-white py-3 px-4">
                <div class="d-flex align-items-center gap-2">
                    <i class="fa-solid fa-layer-group text-warning fs-5"></i>
                    <div>
                        <h6 class="modal-title fw-bold mb-0" id="categoryPickerModalLabel">اختيار وتحديد تصنيف الإعلان</h6>
                        <small class="text-white-50 fs-8">اختر القسم الرئيسي ثم تفرع وصولاً لأصغر قسم فرعي مناسب</small>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="إغلاق"></button>
            </div>
            
            <div class="p-3 bg-light border-bottom">
                <!-- شريط المسار والرجوع Breadcrumbs -->
                <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap mb-2">
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb mb-0 py-1 px-3 bg-white border rounded-pill shadow-xs fs-7 fw-semibold" id="categoryPickerBreadcrumbs">
                            <li class="breadcrumb-item active"><i class="fa-solid fa-house me-1"></i> الرئيسية</li>
                        </ol>
                    </nav>
                    <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-3 fw-bold shadow-xs" id="btnPickerBack" style="display: none;" onclick="navigatePickerBack()">
                        <i class="fa-solid fa-arrow-right me-1"></i> رجوع للخلف
                    </button>
                </div>

                <!-- شريط البحث السريع في الأقسام -->
                <div class="input-group">
                    <span class="input-group-text bg-white border-end-0"><i class="fa-solid fa-magnifying-glass text-muted"></i></span>
                    <input type="text" id="categoryPickerSearch" class="form-control border-start-0 py-2 fs-7 fw-semibold" placeholder="ابحث عن أي قسم بسرعة (مثال: سيراتو، كيا، شقق، كنبايات...)" oninput="filterCategoryPicker(this.value)">
                    <button type="button" class="btn btn-outline-secondary px-3" onclick="document.getElementById('categoryPickerSearch').value=''; filterCategoryPicker('');" title="مسح البحث">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            </div>

            <div class="modal-body p-3 bg-white" style="min-height: 380px; max-height: 520px; overflow-y: auto;">
                <!-- زر اعتماد القسم الأب الحالي إذا أراد المستخدم التوقف عنده -->
                <div id="pickerCurrentParentAction" class="mb-3" style="display: none;"></div>

                <!-- شبكة الأقسام المعروضة -->
                <div id="categoryPickerGrid" class="row g-2"></div>

                <!-- في حال لا توجد نتائج بحث -->
                <div id="categoryPickerEmpty" class="text-center py-5 text-muted" style="display: none;">
                    <i class="fa-solid fa-folder-open fs-1 text-secondary mb-2 d-block"></i>
                    <span class="fw-bold fs-7">لم يتم العثور على أي قسم مطابق لكلمة البحث.</span>
                </div>
            </div>

            <div class="modal-footer bg-light py-2 px-3 d-flex justify-content-between align-items-center">
                <span class="text-muted fs-8"><i class="fa-solid fa-circle-info text-primary me-1"></i> النقر على أصغر قسم فرعي (أصغر ابن) يقوم باختياره فورياً وتثبيته.</span>
                <button type="button" class="btn btn-secondary btn-sm rounded-pill px-4 fw-bold" data-bs-dismiss="modal">إلغاء</button>
            </div>
        </div>
    </div>
</div>

<script>
// Categories Data and Hierarchical Maps
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

function openCategoryPicker() {
    const searchInp = document.getElementById('categoryPickerSearch');
    if (searchInp) searchInp.value = '';

    renderPickerLevel('root', []);

    const modalEl = document.getElementById('categoryPickerModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

function renderPickerLevel(parentId, trail) {
    pickerCurrentPid = parentId;
    pickerTrail = trail || [];

    const searchInp = document.getElementById('categoryPickerSearch');
    if (searchInp) searchInp.value = '';

    const backBtn = document.getElementById('btnPickerBack');
    if (backBtn) {
        backBtn.style.display = (parentId !== 'root' && pickerTrail.length > 0) ? 'inline-block' : 'none';
    }

    const bcEl = document.getElementById('categoryPickerBreadcrumbs');
    if (bcEl) {
        let html = '<li class="breadcrumb-item cursor-pointer text-primary" onclick="renderPickerLevel(\'root\', [])"><i class="fa-solid fa-house me-1"></i> الرئيسية</li>';
        pickerTrail.forEach((item, idx) => {
            if (idx === pickerTrail.length - 1) {
                html += '<li class="breadcrumb-item active text-dark fw-bold" aria-current="page">' + escapeHtml(item.name_ar) + '</li>';
            } else {
                html += '<li class="breadcrumb-item cursor-pointer text-primary" onclick="goToPickerBreadcrumb(' + idx + ')">' + escapeHtml(item.name_ar) + '</li>';
            }
        });
        bcEl.innerHTML = html;
    }

    const parentActionEl = document.getElementById('pickerCurrentParentAction');
    if (parentActionEl) {
        if (parentId !== 'root' && catMap[parentId]) {
            const curObj = catMap[parentId];
            parentActionEl.innerHTML = `
                <div class="alert alert-info py-2 px-3 d-flex align-items-center justify-content-between mb-0 border-0 rounded-3 shadow-xs">
                    <span class="fs-7 fw-semibold"><i class="fa-solid fa-circle-info me-1"></i> هل تريد اعتماد هذا القسم (${escapeHtml(curObj.name_ar)}) مباشرة؟</span>
                    <button type="button" class="btn btn-sm btn-success fw-bold px-3 rounded-pill" onclick="selectCategoryFinal(${curObj.id})">
                        <i class="fa-solid fa-check me-1"></i> اعتماد: ${escapeHtml(curObj.name_ar)}
                    </button>
                </div>
            `;
            parentActionEl.style.display = 'block';
        } else {
            parentActionEl.style.display = 'none';
        }
    }

    const items = childrenMap[parentId] || [];
    renderCategoryGrid(items, false);
}

function goToPickerBreadcrumb(index) {
    if (index < 0 || index >= pickerTrail.length) {
        renderPickerLevel('root', []);
        return;
    }
    const targetItem = pickerTrail[index];
    const newTrail = pickerTrail.slice(0, index + 1);
    renderPickerLevel(targetItem.id, newTrail);
}

function navigatePickerBack() {
    if (pickerTrail.length <= 1) {
        renderPickerLevel('root', []);
    } else {
        const newTrail = pickerTrail.slice(0, -1);
        const prevItem = newTrail[newTrail.length - 1];
        renderPickerLevel(prevItem.id, newTrail);
    }
}

function renderCategoryGrid(items, isSearchResult) {
    const gridEl = document.getElementById('categoryPickerGrid');
    const emptyEl = document.getElementById('categoryPickerEmpty');

    if (!items || items.length === 0) {
        gridEl.innerHTML = '';
        if (emptyEl) emptyEl.style.display = 'block';
        return;
    }

    if (emptyEl) emptyEl.style.display = 'none';

    let html = '';
    items.forEach(cat => {
        const hasChildren = (childrenMap[cat.id] || []).length > 0;
        const iconSrc = cat.icon || '';
        let iconHtml = '';
        if (iconSrc) {
            iconHtml = '<img src="' + escapeHtml(iconSrc) + '" style="width: 24px; height: 24px; object-fit: contain; flex-shrink: 0;" alt="" onerror="this.onerror=null; this.src=\'https://lelbai.com/icons/cars.svg\';">';
        } else {
            iconHtml = hasChildren 
                ? '<i class="fa-solid fa-folder-tree text-primary fs-5"></i>' 
                : '<i class="fa-solid fa-tag text-success fs-5"></i>';
        }

        if (isSearchResult) {
            const pathText = getCategoryPathText(cat.id);
            html += `
                <div class="col-12">
                    <div class="card p-2.5 border rounded-3 hover-shadow-sm cursor-pointer d-flex flex-row align-items-center justify-content-between" 
                         onclick="selectCategoryFinal(${cat.id})" style="cursor: pointer; transition: all 0.15s ease;">
                        <div class="d-flex align-items-center gap-2">
                            ${iconHtml}
                            <div>
                                <span class="fw-bold text-dark fs-7 d-block">${escapeHtml(cat.name_ar)}</span>
                                <small class="text-muted fs-8">${escapeHtml(pathText)}</small>
                            </div>
                        </div>
                        <span class="badge bg-success-subtle text-success fs-8 px-2 py-1 rounded-pill">
                            اختيار <i class="fa-solid fa-check ms-1"></i>
                        </span>
                    </div>
                </div>
            `;
        } else if (hasChildren) {
            const childCount = (childrenMap[cat.id] || []).length;
            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="card p-3 border rounded-3 hover-bg-light cursor-pointer h-100 d-flex flex-column justify-content-between" 
                         onclick="drillDownCategory(${cat.id})" style="cursor: pointer; transition: all 0.15s ease; border-color: #E2E8F0;">
                        <div class="d-flex align-items-center gap-2 mb-2">
                            ${iconHtml}
                            <span class="fw-bold text-dark fs-6">${escapeHtml(cat.name_ar)}</span>
                        </div>
                        <div class="d-flex align-items-center justify-content-between mt-auto pt-2 border-top">
                            <span class="badge bg-light text-secondary border fs-9">${childCount} قسم فرعي</span>
                            <span class="text-primary fs-8 fw-bold">تفرع <i class="fa-solid fa-chevron-left ms-1"></i></span>
                        </div>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="card p-3 border border-success-subtle rounded-3 bg-success bg-opacity-10 cursor-pointer h-100 d-flex flex-column justify-content-between" 
                         onclick="selectCategoryFinal(${cat.id})" style="cursor: pointer; transition: all 0.15s ease;">
                        <div class="d-flex align-items-center gap-2 mb-2">
                            ${iconHtml}
                            <span class="fw-bold text-dark fs-6">${escapeHtml(cat.name_ar)}</span>
                        </div>
                        <div class="d-flex align-items-center justify-content-between mt-auto pt-2 border-top border-success-subtle">
                            <span class="badge bg-success text-white fs-9 rounded-pill">أصغر قسم (نهائي)</span>
                            <span class="text-success fs-8 fw-bold">اختر هذا <i class="fa-solid fa-check ms-1"></i></span>
                        </div>
                    </div>
                </div>
            `;
        }
    });

    gridEl.innerHTML = html;
}

function drillDownCategory(catId) {
    if (!catMap[catId]) return;
    const cat = catMap[catId];
    renderPickerLevel(cat.id, [...pickerTrail, cat]);
}

function selectCategoryFinal(catId) {
    if (!catMap[catId]) return;
    
    const catInp = document.getElementById('editListingCategory');
    if (catInp) catInp.value = catId;

    const displayEl = document.getElementById('editCategoryDisplayText');
    if (displayEl) {
        const fullPath = getCategoryPathText(catId);
        displayEl.innerHTML = '<span class="badge bg-success bg-opacity-10 text-success border border-success-subtle fs-7 px-2 py-1"><i class="fa-solid fa-check-circle me-1"></i> ' + escapeHtml(fullPath) + '</span>';
    }

    const pickerEl = document.getElementById('categoryPickerModal');
    if (pickerEl) {
        const pickerModal = bootstrap.Modal.getInstance(pickerEl);
        if (pickerModal) pickerModal.hide();
    }
}

function filterCategoryPicker(query) {
    query = (query || '').trim().toLowerCase();
    if (!query) {
        renderPickerLevel(pickerCurrentPid, pickerTrail);
        return;
    }

    const backBtn = document.getElementById('btnPickerBack');
    if (backBtn) backBtn.style.display = 'none';

    const parentActionEl = document.getElementById('pickerCurrentParentAction');
    if (parentActionEl) parentActionEl.style.display = 'none';

    const bcEl = document.getElementById('categoryPickerBreadcrumbs');
    if (bcEl) {
        bcEl.innerHTML = '<li class="breadcrumb-item text-secondary"><i class="fa-solid fa-magnifying-glass me-1"></i> نتائج البحث عن: <strong>' + escapeHtml(query) + '</strong></li>';
    }

    const results = allCategoriesData.filter(c => c.name_ar.toLowerCase().includes(query));
    renderCategoryGrid(results, true);
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

    // Multi-select Checkboxes & Bulk Actions
    const selectAll = document.getElementById('selectAllCheckbox');
    const itemCheckboxes = document.querySelectorAll('.listing-checkbox');
    const bulkToolbar = document.getElementById('bulkActionsToolbar');
    const selectedCountSpan = document.getElementById('selectedCount');

    function updateBulkToolbar() {
        const checked = document.querySelectorAll('.listing-checkbox:checked');
        const count = checked.length;
        if (selectedCountSpan) selectedCountSpan.textContent = count;
        if (bulkToolbar) {
            bulkToolbar.style.setProperty('display', count > 0 ? 'flex' : 'none', 'important');
        }
    }

    if (selectAll) {
        selectAll.addEventListener('change', function() {
            itemCheckboxes.forEach(cb => cb.checked = this.checked);
            updateBulkToolbar();
        });
    }

    itemCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            updateBulkToolbar();
            if (!this.checked && selectAll) selectAll.checked = false;
        });
    });

    // Reject Modal trigger
    const rejectBtns = document.querySelectorAll('.btn-open-reject-modal');
    rejectBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            const title = this.dataset.title;
            const reason = this.dataset.reason || '';
            const aiSuggestion = this.dataset.aiSuggestion || '';

            document.getElementById('modalListingTitle').textContent = title;
            document.getElementById('rejectionReasonInput').value = reason || aiSuggestion;
            document.getElementById('rejectListingForm').action = '{{ url("listings") }}/' + id + '/status';

            const modal = new bootstrap.Modal(document.getElementById('rejectListingModal'));
            modal.show();
        });
    });

    // Edit Modal trigger
    const editBtns = document.querySelectorAll('.btn-edit-listing');
    editBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            const title = this.dataset.title || '';
            const price = this.dataset.price || '';
            const currency = this.dataset.currency || 'SYP';
            const categoryId = this.dataset.categoryId || '';
            const cityId = this.dataset.cityId || '';
            const phone = this.dataset.phone || '';
            const description = this.dataset.description || '';
            const status = this.dataset.status || 'active';
            const featured = this.dataset.featured == '1';

            const modalTitleSpan = document.getElementById('modalListingIdDisplay');
            if (modalTitleSpan) modalTitleSpan.textContent = id;

            const titleInput = document.getElementById('editListingTitle');
            if (titleInput) titleInput.value = title;

            // Set Category
            const catInp = document.getElementById('editListingCategory');
            if (catInp) catInp.value = categoryId;

            const catDisplay = document.getElementById('editCategoryDisplayText');
            if (catDisplay) {
                if (categoryId && catMap[categoryId]) {
                    const fullPath = getCategoryPathText(categoryId);
                    catDisplay.innerHTML = '<span class="badge bg-primary bg-opacity-10 text-primary fs-7 px-2 py-1"><i class="fa-solid fa-folder-tree me-1"></i> ' + escapeHtml(fullPath) + '</span>';
                } else {
                    catDisplay.innerHTML = '<span class="text-muted">اضغط لاختيار القسم...</span>';
                }
            }

            // Set City
            const citySelect = document.getElementById('editListingCity');
            if (citySelect) {
                citySelect.value = String(cityId || '');
            }

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

            const form = document.getElementById('editListingForm');
            if (form) form.action = '{{ url("listings") }}/' + id + '/update';

            const modalEl = document.getElementById('editListingModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
            }
        });
    });

    // Ensure scrolling works properly when closing the category picker over edit modal
    const pickerModalEl = document.getElementById('categoryPickerModal');
    if (pickerModalEl) {
        pickerModalEl.addEventListener('hidden.bs.modal', function () {
            const editModalEl = document.getElementById('editListingModal');
            if (editModalEl && editModalEl.classList.contains('show')) {
                document.body.classList.add('modal-open');
            }
        });
    }

    // Delete Modal trigger
    const deleteBtns = document.querySelectorAll('.btn-open-delete-modal');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            const title = this.dataset.title;

            document.getElementById('deleteModalListingTitle').textContent = title;
            document.getElementById('deleteListingForm').action = '{{ url("listings") }}/' + id;

            const modal = new bootstrap.Modal(document.getElementById('deleteListingModal'));
            modal.show();
        });
    });

    // Toast Notification System
    function showFloatingToast(message, type = 'success') {
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

    const currentUrlParams = new URLSearchParams(window.location.search);
    const activeTabStatus = currentUrlParams.get('status') || '';

    // Quick Status Update (Accept / Suspend) with Optimistic UI
    window.quickUpdateListingStatus = function(id, newStatus, event) {
        if (event) event.preventDefault();
        const row = document.getElementById('listing-row-' + id);
        const oldStatus = row ? row.dataset.status : '';

        // Immediate Optimistic Visual Feedback
        if (row) {
            row.dataset.status = newStatus;
            if (activeTabStatus === 'pending' && newStatus === 'active') {
                row.style.backgroundColor = '#dcfce7';
                updateKpi('pending', -1);
                updateKpi('active', +1);
                fadeOutRow(row);
                showFloatingToast('تم قبول وتفعيل الإعلان #' + id + ' فورياً ✅', 'success');
            } else if (activeTabStatus === 'active' && newStatus === 'suspended') {
                row.style.backgroundColor = '#f1f5f9';
                updateKpi('active', -1);
                fadeOutRow(row);
                showFloatingToast('تم إيقاف الإعلان #' + id + ' مؤقتاً ⏸️', 'info');
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
                showFloatingToast('تم تحديث حالة الإعلان #' + id + ' بنجاح ✅', 'success');
            }
        }

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
            if (!data.success) {
                showFloatingToast(data.message || 'تعذر حفظ الحالة على السيرفر', 'danger');
            }
        })
        .catch(err => {
            showFloatingToast('تنبيه: تم الإجراء محلياً ولكن تعذر الاتصال بالسيرفر: ' + err.message, 'warning');
        });
    };

    // Reject Form Ajax Submission
    const rejectForm = document.getElementById('rejectListingForm');
    if (rejectForm) {
        rejectForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.action;
            const parts = actionUrl.split('/');
            const id = parts[parts.indexOf('listings') + 1];
            const reason = document.getElementById('rejectionReasonInput').value;

            const modalEl = document.getElementById('rejectListingModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

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

            showFloatingToast('تم رفض وحجب الإعلان #' + id + ' فورياً ❌', 'danger');

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
                if (!data.success) {
                    showFloatingToast(data.message || 'تعذر تأكيد الرفض بالسيرفر', 'danger');
                }
            })
            .catch(err => {
                showFloatingToast('خطأ في الاتصال: ' + err.message, 'warning');
            });
        });
    }

    // Delete Form Ajax Submission
    const deleteForm = document.getElementById('deleteListingForm');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.action;
            const parts = actionUrl.split('/');
            const id = parts[parts.indexOf('listings') + 1];

            const modalEl = document.getElementById('deleteListingModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            const row = document.getElementById('listing-row-' + id);
            if (row) {
                updateKpi('all', -1);
                fadeOutRow(row);
            }

            showFloatingToast('تم حذف الإعلان #' + id + ' نهائياً 🗑️', 'info');

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
                if (!data.success) {
                    showFloatingToast(data.message || 'تعذر الحذف بالسيرفر', 'danger');
                }
            })
            .catch(err => {
                showFloatingToast('خطأ في الاتصال: ' + err.message, 'warning');
            });
        });
    }

    // Edit Form Ajax Submission
    const editForm = document.getElementById('editListingForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.action;
            const parts = actionUrl.split('/');
            const id = parts[parts.indexOf('listings') + 1];

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> جاري الحفظ...';
            }

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
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }

                if (data.success) {
                    const modalEl = document.getElementById('editListingModal');
                    if (modalEl) {
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        if (modal) modal.hide();
                    }

                    showFloatingToast(data.message || 'تم حفظ التعديلات بنجاح!', 'success');

                    const row = document.getElementById('listing-row-' + id);
                    if (row && data.data) {
                        const titleEl = row.querySelector('.col-cell-1 .fw-bold');
                        if (titleEl) titleEl.textContent = data.data.title;
                        const statusCell = document.getElementById('status-cell-' + id);
                        if (statusCell) {
                            if (data.data.status === 'active') statusCell.innerHTML = '<span class="badge bg-success bg-opacity-15 text-success border border-success border-opacity-25 px-2 py-1 rounded-pill">نشط ✅</span>';
                            else if (data.data.status === 'pending') statusCell.innerHTML = '<span class="badge bg-warning bg-opacity-20 text-dark border border-warning px-2 py-1 rounded-pill">بانتظار المراجعة ⏳</span>';
                            else if (data.data.status === 'rejected') statusCell.innerHTML = '<span class="badge bg-danger bg-opacity-15 text-danger border border-danger border-opacity-25 px-2 py-1 rounded-pill">مرفوض ❌</span>';
                            else if (data.data.status === 'suspended') statusCell.innerHTML = '<span class="badge bg-secondary px-2 py-1 rounded-pill">موقوف ⏸️</span>';
                        }
                    }
                } else {
                    showFloatingToast(data.message || 'تعذر حفظ التعديلات', 'danger');
                }
            })
            .catch(err => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
                showFloatingToast('خطأ: ' + err.message, 'danger');
            });
        });
    }
});

function submitBulkAction(action) {
    if (action === 'delete') {
        if (!confirm('هل أنت متأكد من حذف كافة الإعلانات المحددة نهائياً؟')) {
            return;
        }
    }
    document.getElementById('bulkActionInput').value = action;
    const form = document.getElementById('bulkActionForm');
    const checked = document.querySelectorAll('.listing-checkbox:checked');
    const ids = Array.from(checked).map(c => c.value);

    // Optimistic UI for bulk action
    checked.forEach(c => {
        const row = document.getElementById('listing-row-' + c.value);
        if (row) {
            row.style.opacity = '0.4';
            if (action === 'delete') row.style.display = 'none';
        }
    });

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
            showFloatingToast(data.message || 'تم تنفيذ الإجراء بنجاح', 'success');
            setTimeout(() => location.reload(), 1200);
        } else {
            showFloatingToast(data.message || 'تعذر تطبيق الإجراء', 'danger');
        }
    })
    .catch(err => {
        form.submit();
    });
}
</script>
@endsection
