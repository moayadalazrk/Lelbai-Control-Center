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
                <span class="fs-4 fw-extrabold text-dark">{{ number_format($counts['all']) }}</span>
                <span class="badge bg-light text-dark border">الكل</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-success">
            <div class="text-muted fs-8 fw-bold mb-1">إعلانات نشطة</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-success">{{ number_format($counts['active']) }}</span>
                <span class="badge bg-success bg-opacity-10 text-success">مقبول</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-warning">
            <div class="text-muted fs-8 fw-bold mb-1">بانتظار المراجعة</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-warning">{{ number_format($counts['pending']) }}</span>
                <span class="badge bg-warning bg-opacity-10 text-dark">معلق</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-info">
            <div class="text-muted fs-8 fw-bold mb-1">إعلانات اليوم (24h)</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-info">{{ number_format($counts['today']) }}</span>
                <span class="badge bg-info bg-opacity-10 text-info">جديد</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-danger">
            <div class="text-muted fs-8 fw-bold mb-1">أوشكت على الحذف (30يوم)</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-danger">{{ number_format($counts['expiring_soon']) }}</span>
                <span class="badge bg-danger bg-opacity-10 text-danger">&lt; 5 أيام</span>
            </div>
        </div>
    </div>
    <div class="col-6 col-md-4 col-xl-2">
        <div class="card border-0 shadow-sm rounded-3 p-3 bg-white h-100 border-start border-4 border-danger border-opacity-50">
            <div class="text-muted fs-8 fw-bold mb-1">مخالفات AI / مرفوض</div>
            <div class="d-flex align-items-baseline justify-content-between">
                <span class="fs-4 fw-extrabold text-danger">{{ number_format($counts['rejected'] + $counts['flagged']) }}</span>
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
                        <img src="{{ asset($cat->icon) }}" style="width: 18px; height: 18px; object-fit: contain; margin-left: 4px;" alt="">
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

                            $primaryImg = $listing->primaryImage ? asset('storage/' . ltrim($listing->primaryImage->image_path, '/')) : ($listing->category?->icon ? asset($listing->category->icon) : null);
                        @endphp
                        <tr>
                            <!-- Checkbox -->
                            <td class="text-center">
                                <input type="checkbox" name="listing_ids[]" value="{{ $listing->id }}" class="form-check-input listing-checkbox cursor-pointer">
                            </td>

                            <!-- # and Thumbnail -->
                            <td class="col-cell-0">
                                <div class="d-flex align-items-center gap-2">
                                    @if($primaryImg)
                                        <img src="{{ $primaryImg }}" class="rounded-3 border shadow-xs" style="width: 46px; height: 46px; object-fit: cover; flex-shrink: 0;" alt="">
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
                            <td class="col-cell-6">
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
                            <td>
                                <div class="d-flex align-items-center justify-content-center gap-1">
                                    <!-- معاينة بالمنصة -->
                                    <a href="http://localhost:3000/listings/{{ $listing->uuid ?: $listing->id }}/details" target="_blank" class="btn btn-sm btn-outline-primary fw-bold px-2 py-1" title="فتح الإعلان ومعاينته بالمنصة">
                                        <i class="fa-solid fa-arrow-up-right-from-square"></i> معاينة
                                    </a>

                                    @if($listing->status !== 'active')
                                        <button type="submit" form="quickStatusForm_{{ $listing->id }}_active" class="btn btn-sm btn-success fw-bold px-2 py-1" title="قبول وتفعيل الإعلان">
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
                                        <button type="submit" form="quickStatusForm_{{ $listing->id }}_suspended" class="btn btn-sm btn-outline-secondary fw-bold px-2 py-1" title="إيقاف مؤقت">
                                            <i class="fa-solid fa-ban"></i>
                                        </button>
                                    @endif

                                    <!-- زر حذف نهائي -->
                                    <button type="button" class="btn btn-sm btn-outline-danger fw-bold px-2 py-1 btn-open-delete-modal" data-id="{{ $listing->id }}" data-title="{{ $listing->title }}" title="حذف الإعلان نهائياً">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </div>

                                <!-- Hidden forms for instant action -->
                                <form id="quickStatusForm_{{ $listing->id }}_active" method="POST" action="{{ route('admin.listings.updateStatus', $listing->id) }}" style="display:none;">
                                    @csrf
                                    <input type="hidden" name="status" value="active">
                                </form>
                                <form id="quickStatusForm_{{ $listing->id }}_suspended" method="POST" action="{{ route('admin.listings.updateStatus', $listing->id) }}" style="display:none;">
                                    @csrf
                                    <input type="hidden" name="status" value="suspended">
                                </form>
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

<script>
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
});

function submitBulkAction(action) {
    if (action === 'delete') {
        if (!confirm('هل أنت متأكد من حذف كافة الإعلانات المحددة نهائياً؟')) {
            return;
        }
    }
    document.getElementById('bulkActionInput').value = action;
    document.getElementById('bulkActionForm').submit();
}
</script>
@endsection
