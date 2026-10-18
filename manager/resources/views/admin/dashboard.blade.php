@extends('layouts.admin')

@section('content')
<!-- KPI Stat Cards Grid -->
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">إجمالي الإعلانات</span>
                <h3 class="fw-bold mb-0">{{ number_format($stats['total_listings']) }}</h3>
            </div>
            <div class="stat-icon bg-light text-success">
                <i class="fa-solid fa-boxes-stacked"></i>
            </div>
        </div>
    </div>
    
    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">بانتظار الموافقة</span>
                <h3 class="fw-bold mb-0 text-warning">{{ number_format($stats['pending_listings']) }}</h3>
            </div>
            <div class="stat-icon bg-warning-subtle text-warning">
                <i class="fa-solid fa-clock"></i>
            </div>
        </div>
    </div>

    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">إجمالي المستخدمين</span>
                <h3 class="fw-bold mb-0">{{ number_format($stats['total_users']) }}</h3>
            </div>
            <div class="stat-icon bg-info-subtle text-info">
                <i class="fa-solid fa-users"></i>
            </div>
        </div>
    </div>

    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">إجمالي الرسائل</span>
                <h3 class="fw-bold mb-0">{{ number_format($stats['total_messages']) }}</h3>
            </div>
            <div class="stat-icon bg-secondary-subtle text-secondary">
                <i class="fa-solid fa-comments"></i>
            </div>
        </div>
    </div>
</div>

<!-- Recent Listings Table -->
<div class="card border-0 shadow-sm rounded-3 mb-4">
    <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
        <h6 class="fw-bold mb-0">أحدث الإعلانات المضافة للمراجعة والتدقيق</h6>
        <a href="{{ route('admin.listings.index') }}" class="btn btn-sm btn-outline-dark fw-bold">عرض كافة الإعلانات</a>
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table align-middle table-hover mb-0 text-nowrap">
                <thead class="table-light fs-7">
                    <tr>
                        <th>#</th>
                        <th>عنوان الإعلان</th>
                        <th>البائع</th>
                        <th>السعر</th>
                        <th>الحالة</th>
                        <th>التاريخ</th>
                        <th class="text-center">إجراء الإدارة المباشر</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($recentListings as $listing)
                        <tr>
                            <td class="fw-bold">#{{ $listing->id }}</td>
                            <td class="fw-semibold">
                                <a href="https://lelbai.com/listings/{{ $listing->uuid ?: $listing->id }}/details" target="_blank" class="text-dark text-decoration-none" title="معاينة الإعلان على الدومين الحقيقي (lelbai.com)">
                                    {{ $listing->title }}
                                    <i class="fa-solid fa-arrow-up-right-from-square text-primary ms-1 fs-8"></i>
                                </a>
                            </td>
                            <td>{{ $listing->user->name ?? 'غير معروف' }}</td>
                            <td class="fw-bold text-success">{{ number_format($listing->price) }} ل.س</td>
                            <td>
                                @if($listing->status === 'active')
                                    <span class="badge badge-active px-2 py-1"><i class="fa-solid fa-check me-1"></i> نشط</span>
                                @elseif($listing->status === 'suspended' || $listing->status === 'rejected')
                                    <span class="badge bg-danger-subtle text-danger px-2 py-1"><i class="fa-solid fa-ban me-1"></i> موقوف</span>
                                @else
                                    <span class="badge badge-pending px-2 py-1"><i class="fa-solid fa-clock me-1"></i> بانتظار المراجعة</span>
                                @endif
                            </td>
                            <td class="text-muted fs-7">{{ $listing->created_at ? $listing->created_at->format('Y-m-d H:i') : '' }}</td>
                            <td>
                                <div class="d-flex align-items-center justify-content-center gap-2">
                                    @if($listing->status !== 'active')
                                        <form method="POST" action="{{ route('admin.listings.updateStatus', $listing->id) }}" class="d-inline">
                                            @csrf
                                            <input type="hidden" name="status" value="active">
                                            <button type="submit" class="btn btn-sm btn-success fw-bold px-2 py-1 fs-7">
                                                <i class="fa-solid fa-check me-1"></i> موافقة
                                            </button>
                                        </form>
                                    @endif

                                    @if($listing->status !== 'suspended')
                                        <form method="POST" action="{{ route('admin.listings.updateStatus', $listing->id) }}" class="d-inline">
                                            @csrf
                                            <input type="hidden" name="status" value="suspended">
                                            <button type="submit" class="btn btn-sm btn-outline-danger fw-bold px-2 py-1 fs-7">
                                                <i class="fa-solid fa-ban me-1"></i> إيقاف
                                            </button>
                                        </form>
                                    @endif
                                </div>
                            </td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="7" class="text-center py-4 text-muted">لا توجد إعلانات بعد.</td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>
</div>
@endsection
