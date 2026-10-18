@extends('layouts.admin')

@section('content')
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
    <div>
        <h4 class="fw-bold mb-1">
            <i class="fa-solid fa-headset text-success me-2"></i>مركز الشكاوى والرسائل
        </h4>
        <small class="text-muted">متابعة رسائل واستفسارات العملاء المباشرة وبلاغات المحتوى</small>
    </div>
    <div class="d-flex align-items-center gap-2">
        <a href="{{ route('admin.complaints.index', ['tab' => $tab]) }}" class="btn btn-sm btn-outline-secondary rounded-pill px-3 py-2 fw-semibold">
            <i class="fa-solid fa-rotate-right me-1"></i> تحديث
        </a>
    </div>
</div>

<!-- KPI Stat Cards -->
<div class="row g-3 mb-4">
    <div class="col-6 col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">إجمالي الرسائل</span>
                <h3 class="fw-bold mb-0 text-dark">{{ number_format($counts['total_messages']) }}</h3>
            </div>
            <div class="stat-icon bg-light text-primary">
                <i class="fa-solid fa-envelope-open-text"></i>
            </div>
        </div>
    </div>

    <div class="col-6 col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between border-warning border-opacity-50">
            <div>
                <span class="text-muted fs-7 d-block mb-1">بانتظار المعالجة</span>
                <h3 class="fw-bold mb-0 text-warning">{{ number_format($counts['pending_messages']) }}</h3>
            </div>
            <div class="stat-icon bg-warning-subtle text-warning">
                <i class="fa-solid fa-clock"></i>
            </div>
        </div>
    </div>

    <div class="col-6 col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">قيد المعالجة</span>
                <h3 class="fw-bold mb-0 text-info">{{ number_format($counts['in_progress_messages']) }}</h3>
            </div>
            <div class="stat-icon bg-info-subtle text-info">
                <i class="fa-solid fa-arrows-rotate"></i>
            </div>
        </div>
    </div>

    <div class="col-6 col-md-3">
        <div class="stat-card d-flex align-items-center justify-content-between">
            <div>
                <span class="text-muted fs-7 d-block mb-1">تم الرد والحل</span>
                <h3 class="fw-bold mb-0 text-success">{{ number_format($counts['resolved_messages']) }}</h3>
            </div>
            <div class="stat-icon bg-success-subtle text-success">
                <i class="fa-solid fa-circle-check"></i>
            </div>
        </div>
    </div>
</div>

<!-- Tabs Navigation -->
<ul class="nav nav-pills mb-3 gap-2 bg-white p-2 rounded-3 border shadow-sm" role="tablist">
    <li class="nav-item">
        <a class="nav-link fw-bold px-3 py-2 rounded-2 {{ $tab === 'messages' ? 'active bg-success' : 'text-dark' }}" 
           href="{{ route('admin.complaints.index', ['tab' => 'messages']) }}">
            <i class="fa-solid fa-inbox me-1"></i> رسائل واستفسارات الدعم
            @if($counts['pending_messages'] > 0)
                <span class="badge bg-danger rounded-pill ms-1">{{ $counts['pending_messages'] }}</span>
            @endif
        </a>
    </li>
    <li class="nav-item">
        <a class="nav-link fw-bold px-3 py-2 rounded-2 {{ $tab === 'reports' ? 'active bg-success' : 'text-dark' }}" 
           href="{{ route('admin.complaints.index', ['tab' => 'reports']) }}">
            <i class="fa-solid fa-triangle-exclamation me-1"></i> بلاغات الإعلانات والمستخدمين
            @if($counts['pending_reports'] > 0)
                <span class="badge bg-danger rounded-pill ms-1">{{ $counts['pending_reports'] }}</span>
            @endif
        </a>
    </li>
</ul>

<!-- Filter Bar -->
<div class="card border-0 shadow-sm rounded-3 mb-4">
    <div class="card-body p-3">
        <form method="GET" action="{{ route('admin.complaints.index') }}" class="row g-2 align-items-center">
            <input type="hidden" name="tab" value="{{ $tab }}">

            <div class="col-md-3">
                <div class="input-group input-group-sm">
                    <span class="input-group-text bg-light border-end-0"><i class="fa-solid fa-magnifying-glass text-muted"></i></span>
                    <input type="text" name="search" class="form-control border-start-0" placeholder="بحث بالاسم، الهاتف، أو النص..." value="{{ $search }}">
                </div>
            </div>

            <div class="col-md-3">
                <select name="status" class="form-select form-select-sm">
                    <option value="all" {{ $status === 'all' ? 'selected' : '' }}>جميع الحالات</option>
                    <option value="pending" {{ $status === 'pending' ? 'selected' : '' }}>بانتظار المعالجة (جديد)</option>
                    @if($tab === 'messages')
                        <option value="in_progress" {{ $status === 'in_progress' ? 'selected' : '' }}>قيد المعالجة</option>
                        <option value="resolved" {{ $status === 'resolved' ? 'selected' : '' }}>تم الرد والحل</option>
                        <option value="closed" {{ $status === 'closed' ? 'selected' : '' }}>مغلق</option>
                    @else
                        <option value="resolved" {{ $status === 'resolved' ? 'selected' : '' }}>تمت المعالجة</option>
                    @endif
                </select>
            </div>

            @if($tab === 'messages')
                <div class="col-md-3">
                    <select name="subject" class="form-select form-select-sm">
                        <option value="all" {{ $subject === 'all' ? 'selected' : '' }}>جميع الموضوعات</option>
                        <option value="general" {{ $subject === 'general' ? 'selected' : '' }}>استفسار عام</option>
                        <option value="technical" {{ $subject === 'technical' ? 'selected' : '' }}>مشكلة فنية بالموقع</option>
                        <option value="report" {{ $subject === 'report' ? 'selected' : '' }}>بلاغ عن إعلان أو احتيال</option>
                        <option value="suggestion" {{ $subject === 'suggestion' ? 'selected' : '' }}>اقتراح لتطوير المنصة</option>
                        <option value="complaint" {{ $subject === 'complaint' ? 'selected' : '' }}>شكوى رسمية</option>
                    </select>
                </div>
            @endif

            <div class="col-md-auto d-flex gap-2">
                <button type="submit" class="btn btn-sm btn-dark px-3 fw-bold">
                    <i class="fa-solid fa-filter me-1"></i> تصفية
                </button>
                @if($search || $status !== 'all' || $subject !== 'all')
                    <a href="{{ route('admin.complaints.index', ['tab' => $tab]) }}" class="btn btn-sm btn-outline-secondary px-2" title="إعادة ضبط">
                        <i class="fa-solid fa-xmark"></i>
                    </a>
                @endif
            </div>
        </form>
    </div>
</div>

@if($tab === 'messages')
    <!-- Customer Messages Table -->
    <div class="card border-0 shadow-sm rounded-3 mb-4">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
            <h6 class="fw-bold mb-0">قائمة رسائل وشكاوى العملاء ({{ $messages->total() }})</h6>
        </div>
        <div class="card-body p-0">
            @if($messages->isEmpty())
                <div class="text-center py-5">
                    <div class="stat-icon bg-light text-muted mx-auto mb-3" style="width: 64px; height: 64px; font-size: 1.8rem;">
                        <i class="fa-solid fa-inbox"></i>
                    </div>
                    <h5 class="fw-bold text-secondary">لا توجد رسائل أو شكاوى تطابق البحث</h5>
                    <p class="text-muted fs-7 mb-0">عندما يقوم العملاء بإرسال استفسارات من صفحة اتصل بنا، ستظهر هنا فوراً.</p>
                </div>
            @else
                <div class="table-responsive">
                    <table class="table align-middle table-hover mb-0 text-nowrap">
                        <thead class="table-light fs-7">
                            <tr>
                                <th style="width: 60px;">#</th>
                                <th>المرسل ووسيلة التواصل</th>
                                <th>موضوع الرسالة</th>
                                <th>نص الرسالة</th>
                                <th>الحالة</th>
                                <th>تاريخ الإرسال</th>
                                <th class="text-center">إجراءات المتابعة والرد</th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($messages as $msg)
                                @php
                                    $rawPhone = preg_replace('/[^\d]/', '', $msg->phone);
                                    $cleanPhone = $rawPhone;
                                    if (str_starts_with($cleanPhone, '09') && strlen($cleanPhone) === 10) {
                                        $intlPhone = '963' . substr($cleanPhone, 1);
                                    } elseif (str_starts_with($cleanPhone, '963')) {
                                        $intlPhone = $cleanPhone;
                                    } else {
                                        $intlPhone = $cleanPhone;
                                    }
                                    $waGreeting = urlencode("مرحباً بك {$msg->name}، معك الدعم الفني لمنصة للبيع بخصوص استفسارك.");
                                    $waLink = "https://wa.me/{$intlPhone}?text={$waGreeting}";

                                    $subjectBadgeClass = match($msg->subject) {
                                        'technical' => 'bg-danger-subtle text-danger',
                                        'report' => 'bg-warning-subtle text-warning',
                                        'suggestion' => 'bg-info-subtle text-info',
                                        default => 'bg-primary-subtle text-primary',
                                    };
                                @endphp
                                <tr>
                                    <td class="fw-bold text-muted fs-8">#{{ $msg->id }}</td>
                                    <td>
                                        <div class="d-flex align-items-center gap-2">
                                            <div class="stat-icon bg-light text-dark rounded-circle flex-shrink-0" style="width: 38px; height: 38px; font-size: 1rem;">
                                                <i class="fa-solid fa-user"></i>
                                            </div>
                                            <div>
                                                <div class="fw-bold text-dark fs-7">{{ $msg->name }}</div>
                                                <div class="d-flex align-items-center gap-2 mt-1">
                                                    <span class="text-muted fs-8 font-monospace" dir="ltr">{{ $msg->phone }}</span>
                                                    @if($msg->user_id)
                                                        <span class="badge bg-success-subtle text-success fs-8 px-1 py-0" title="مستخدم مسجل في المنصة">مسجل ✓</span>
                                                    @endif
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge {{ $subjectBadgeClass }} px-2 py-1 fs-8 fw-semibold">
                                            {{ $msg->subject_label }}
                                        </span>
                                    </td>
                                    <td style="max-width: 320px; white-space: normal;">
                                        <div class="text-truncate fs-7 text-dark" style="max-width: 300px;" title="{{ $msg->message }}">
                                            {{ $msg->message }}
                                        </div>
                                        @if($msg->admin_notes)
                                            <small class="text-muted d-block mt-1 fs-8">
                                                <i class="fa-solid fa-note-sticky text-warning me-1"></i>{{ Str::limit($msg->admin_notes, 40) }}
                                            </small>
                                        @endif
                                    </td>
                                    <td>
                                        @if($msg->status === 'resolved')
                                            <span class="badge bg-success-subtle text-success px-2 py-1 fs-8 fw-bold">
                                                <i class="fa-solid fa-circle-check me-1"></i>تم الرد والحل
                                            </span>
                                        @elseif($msg->status === 'in_progress')
                                            <span class="badge bg-info-subtle text-info px-2 py-1 fs-8 fw-bold">
                                                <i class="fa-solid fa-spinner me-1"></i>قيد المعالجة
                                            </span>
                                        @elseif($msg->status === 'closed')
                                            <span class="badge bg-secondary-subtle text-secondary px-2 py-1 fs-8 fw-bold">
                                                <i class="fa-solid fa-folder-closed me-1"></i>مغلق
                                            </span>
                                        @else
                                            <span class="badge bg-warning-subtle text-warning px-2 py-1 fs-8 fw-bold">
                                                <i class="fa-solid fa-clock me-1"></i>جديد (بانتظار الرد)
                                            </span>
                                        @endif
                                    </td>
                                    <td>
                                        <span class="fs-8 text-muted d-block">
                                            {{ \Carbon\Carbon::parse($msg->created_at)->diffForHumans() }}
                                        </span>
                                        <small class="fs-8 text-secondary font-monospace">
                                            {{ \Carbon\Carbon::parse($msg->created_at)->format('Y/m/d H:i') }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="d-flex align-items-center justify-content-center gap-1">
                                            <!-- عرض كامل التفاصيل في Modal -->
                                            <button type="button" class="btn btn-sm btn-outline-dark px-2 py-1 fs-8" 
                                                    data-bs-toggle="modal" data-bs-target="#msgModal{{ $msg->id }}" 
                                                    title="عرض كامل الرسالة والملاحظات">
                                                <i class="fa-solid fa-eye me-1"></i>تفاصيل
                                            </button>

                                            <!-- محادثة واتساب سريعة -->
                                            <a href="{{ $waLink }}" target="_blank" rel="noopener noreferrer" 
                                               class="btn btn-sm btn-outline-success px-2 py-1 fs-8" 
                                               title="مراسلة العميل على واتساب">
                                                <i class="fa-brands fa-whatsapp fs-6"></i>
                                            </a>

                                            <!-- اتصال هاتفي -->
                                            <a href="tel:{{ $msg->phone }}" 
                                               class="btn btn-sm btn-outline-primary px-2 py-1 fs-8" 
                                               title="اتصال هاتفي بالعميل">
                                                <i class="fa-solid fa-phone fs-7"></i>
                                            </a>

                                            <!-- حذف الرسالة -->
                                            <form action="{{ route('admin.complaints.destroy', $msg->id) }}" method="POST" 
                                                  onsubmit="return confirm('هل أنت متأكد من حذف هذه الرسالة نهائياً؟');" class="d-inline">
                                                @csrf
                                                @method('DELETE')
                                                <button type="submit" class="btn btn-sm btn-outline-danger px-2 py-1 fs-8" title="حذف">
                                                    <i class="fa-solid fa-trash-can"></i>
                                                </button>
                                            </form>
                                        </div>

                                        <!-- Modal تفاصيل الرسالة وملاحظات الإدارة -->
                                        <div class="modal fade" id="msgModal{{ $msg->id }}" tabindex="-1" aria-hidden="true" style="text-align: right;">
                                            <div class="modal-dialog modal-dialog-centered modal-lg">
                                                <div class="modal-content rounded-4 border-0 shadow-lg">
                                                    <div class="modal-header border-bottom py-3 px-4 bg-light rounded-top-4">
                                                        <div class="d-flex align-items-center gap-2">
                                                            <div class="stat-icon bg-success-subtle text-success rounded-circle" style="width: 40px; height: 40px; font-size: 1.1rem;">
                                                                <i class="fa-solid fa-envelope-open-text"></i>
                                                            </div>
                                                            <div>
                                                                <h6 class="modal-title fw-bold mb-0">تفاصيل الرسالة #{{ $msg->id }}</h6>
                                                                <small class="text-muted">{{ $msg->subject_label }} • المرسلة في {{ \Carbon\Carbon::parse($msg->created_at)->format('Y/m/d H:i') }}</small>
                                                            </div>
                                                        </div>
                                                        <button type="button" class="btn-close m-0" data-bs-dismiss="modal" aria-label="Close"></button>
                                                    </div>
                                                    
                                                    <div class="modal-body p-4">
                                                        <!-- Sender Information Card -->
                                                        <div class="p-3 bg-light rounded-3 mb-3 border">
                                                            <div class="row g-3">
                                                                <div class="col-sm-6">
                                                                    <small class="text-muted d-block fs-8">اسم العميل:</small>
                                                                    <strong class="fs-7 text-dark">{{ $msg->name }}</strong>
                                                                    @if($msg->user_id)
                                                                        <span class="badge bg-success-subtle text-success ms-1 fs-8">عضو مسجل (ID: {{ $msg->user_id }})</span>
                                                                    @endif
                                                                </div>
                                                                <div class="col-sm-6">
                                                                    <small class="text-muted d-block fs-8">رقم الهاتف / وسيلة التواصل:</small>
                                                                    <div class="d-flex align-items-center gap-2 mt-1">
                                                                        <span class="font-monospace fw-bold fs-7" dir="ltr">{{ $msg->phone }}</span>
                                                                        <a href="{{ $waLink }}" target="_blank" class="btn btn-sm btn-success py-0 px-2 fs-8 rounded-pill">
                                                                            <i class="fa-brands fa-whatsapp me-1"></i>محادثة واتساب
                                                                        </a>
                                                                        <a href="tel:{{ $msg->phone }}" class="btn btn-sm btn-primary py-0 px-2 fs-8 rounded-pill">
                                                                            <i class="fa-solid fa-phone me-1"></i>اتصال
                                                                        </a>
                                                                    </div>
                                                                </div>
                                                                @if($msg->ip_address)
                                                                    <div class="col-sm-12 border-top pt-2 mt-2">
                                                                        <small class="text-muted fs-8">
                                                                            <i class="fa-solid fa-network-wired me-1"></i>IP: <code>{{ $msg->ip_address }}</code>
                                                                        </small>
                                                                    </div>
                                                                @endif
                                                            </div>
                                                        </div>

                                                        <!-- Full Message Text -->
                                                        <div class="mb-4">
                                                            <label class="form-label fw-bold text-dark fs-7">
                                                                <i class="fa-solid fa-message text-primary me-1"></i> نص رسالة العميل:
                                                            </label>
                                                            <div class="p-3 rounded-3 border bg-white fs-7 text-dark shadow-sm" style="white-space: pre-wrap; line-height: 1.7; min-height: 80px;">{{ $msg->message }}</div>
                                                        </div>

                                                        <!-- Update Status & Admin Notes Form -->
                                                        <form action="{{ route('admin.complaints.updateStatus', $msg->id) }}" method="POST" class="p-3 rounded-3 border bg-light">
                                                            @csrf
                                                            <h6 class="fw-bold mb-3 fs-7 text-dark">
                                                                <i class="fa-solid fa-user-shield text-success me-1"></i> معالجة الشكوى وملاحظات الإدارة:
                                                            </h6>

                                                            <div class="row g-3 mb-3">
                                                                <div class="col-sm-6">
                                                                    <label class="form-label fs-8 fw-bold text-muted">تحديث حالة المعالجة:</label>
                                                                    <select name="status" class="form-select form-select-sm">
                                                                        <option value="pending" {{ $msg->status === 'pending' ? 'selected' : '' }}>جديد (بانتظار المعالجة)</option>
                                                                        <option value="in_progress" {{ $msg->status === 'in_progress' ? 'selected' : '' }}>قيد المعالجة والمتابعة</option>
                                                                        <option value="resolved" {{ $msg->status === 'resolved' ? 'selected' : '' }}>تم الحل والرد على العميل ✓</option>
                                                                        <option value="closed" {{ $msg->status === 'closed' ? 'selected' : '' }}>إغلاق الشكوى (مغلق)</option>
                                                                    </select>
                                                                </div>
                                                                <div class="col-sm-12">
                                                                    <label class="form-label fs-8 fw-bold text-muted">ملاحظات الإدارة الداخلية (تظهر للمدير فقط):</label>
                                                                    <textarea name="admin_notes" rows="2" class="form-control form-control-sm" placeholder="اكتب ملاحظة داخلية (مثال: تم التواصل مع العميل وحل مشكلته عبر الهاتف)...">{{ $msg->admin_notes }}</textarea>
                                                                </div>
                                                            </div>

                                                            <div class="d-flex justify-content-end gap-2">
                                                                <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                                                                <button type="submit" class="btn btn-sm btn-success fw-bold px-3">
                                                                    <i class="fa-solid fa-floppy-disk me-1"></i> حفظ التحديثات
                                                                </button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                @if($messages->hasPages())
                    <div class="p-3 border-top d-flex justify-content-center">
                        {{ $messages->links('pagination::bootstrap-5') }}
                    </div>
                @endif
            @endif
        </div>
    </div>
@else
    <!-- Reports Table -->
    <div class="card border-0 shadow-sm rounded-3 mb-4">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
            <h6 class="fw-bold mb-0">قائمة بلاغات الإعلانات والمستخدمين ({{ $reports->total() }})</h6>
        </div>
        <div class="card-body p-0">
            @if($reports->isEmpty())
                <div class="text-center py-5">
                    <div class="stat-icon bg-light text-muted mx-auto mb-3" style="width: 64px; height: 64px; font-size: 1.8rem;">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                    </div>
                    <h5 class="fw-bold text-secondary">لا توجد بلاغات تطابق البحث</h5>
                    <p class="text-muted fs-7 mb-0">البلاغات المقدمة من المستخدمين ضد إعلانات أو مستخدمين ستظهر هنا.</p>
                </div>
            @else
                <div class="table-responsive">
                    <table class="table align-middle table-hover mb-0 text-nowrap">
                        <thead class="table-light fs-7">
                            <tr>
                                <th style="width: 60px;">#</th>
                                <th>نوع البلاغ</th>
                                <th>المُبلّغ</th>
                                <th>الهدف المُبلّغ عنه</th>
                                <th>سبب البلاغ والتفاصيل</th>
                                <th>الحالة</th>
                                <th>التاريخ</th>
                                <th class="text-center">الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($reports as $rep)
                                <tr>
                                    <td class="fw-bold text-muted fs-8">#{{ $rep->id }}</td>
                                    <td>
                                        @if($rep->type === 'listing' || $rep->listing_id)
                                            <span class="badge bg-warning-subtle text-warning px-2 py-1 fs-8 fw-semibold">
                                                <i class="fa-solid fa-box-archive me-1"></i>إعلان
                                            </span>
                                        @elseif($rep->type === 'user' || $rep->reported_user_id)
                                            <span class="badge bg-danger-subtle text-danger px-2 py-1 fs-8 fw-semibold">
                                                <i class="fa-solid fa-user-slash me-1"></i>مستخدم
                                            </span>
                                        @else
                                            <span class="badge bg-info-subtle text-info px-2 py-1 fs-8 fw-semibold">
                                                <i class="fa-solid fa-comments me-1"></i>محادثة
                                            </span>
                                        @endif
                                    </td>
                                    <td>
                                        <div class="fw-bold fs-7 text-dark">{{ $rep->reporter->name ?? 'مستخدم غير معروف' }}</div>
                                        <small class="text-muted fs-8 font-monospace" dir="ltr">{{ $rep->reporter->phone ?? '' }}</small>
                                    </td>
                                    <td>
                                        @if($rep->listing)
                                            <div>
                                                <span class="fw-bold fs-7 text-dark">{{ Str::limit($rep->listing->title, 35) }}</span>
                                                <span class="badge bg-light text-secondary fs-8 ms-1">#{{ $rep->listing->id }}</span>
                                            </div>
                                        @elseif($rep->reportedUser)
                                            <div>
                                                <span class="fw-bold fs-7 text-danger">{{ $rep->reportedUser->name }}</span>
                                                <small class="text-muted d-block fs-8" dir="ltr">{{ $rep->reportedUser->phone }}</small>
                                            </div>
                                        @else
                                            <span class="text-muted fs-8">غير محدد</span>
                                        @endif
                                    </td>
                                    <td style="max-width: 280px; white-space: normal;">
                                        <div class="fw-bold text-danger fs-8 mb-1">{{ $rep->reason }}</div>
                                        @if($rep->details)
                                            <div class="text-muted fs-8 text-truncate" style="max-width: 260px;" title="{{ $rep->details }}">
                                                {{ $rep->details }}
                                            </div>
                                        @endif
                                    </td>
                                    <td>
                                        @if($rep->status === 'resolved')
                                            <span class="badge bg-success-subtle text-success px-2 py-1 fs-8 fw-bold">
                                                <i class="fa-solid fa-circle-check me-1"></i>تمت المعالجة
                                            </span>
                                        @else
                                            <span class="badge bg-warning-subtle text-warning px-2 py-1 fs-8 fw-bold">
                                                <i class="fa-solid fa-clock me-1"></i>قيد المراجعة
                                            </span>
                                        @endif
                                    </td>
                                    <td>
                                        <span class="fs-8 text-muted d-block">{{ \Carbon\Carbon::parse($rep->created_at)->diffForHumans() }}</span>
                                        <small class="fs-8 text-secondary font-monospace">{{ \Carbon\Carbon::parse($rep->created_at)->format('Y/m/d H:i') }}</small>
                                    </td>
                                    <td class="text-center">
                                        <div class="d-flex align-items-center justify-content-center gap-1">
                                            @if($rep->status !== 'resolved')
                                                <form action="{{ route('admin.complaints.updateReportStatus', $rep->id) }}" method="POST" class="d-inline">
                                                    @csrf
                                                    <input type="hidden" name="status" value="resolved">
                                                    <button type="submit" class="btn btn-sm btn-success px-2 py-1 fs-8" title="تحديد كـ تمت المعالجة">
                                                        <i class="fa-solid fa-check me-1"></i>حل البلاغ
                                                    </button>
                                                </form>
                                            @endif

                                            <form action="{{ route('admin.complaints.destroyReport', $rep->id) }}" method="POST" 
                                                  onsubmit="return confirm('هل أنت متأكد من حذف هذا البلاغ؟');" class="d-inline">
                                                @csrf
                                                @method('DELETE')
                                                <button type="submit" class="btn btn-sm btn-outline-danger px-2 py-1 fs-8" title="حذف البلاغ">
                                                    <i class="fa-solid fa-trash-can"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>

                @if($reports->hasPages())
                    <div class="p-3 border-top d-flex justify-content-center">
                        {{ $reports->links('pagination::bootstrap-5') }}
                    </div>
                @endif
            @endif
        </div>
    </div>
@endif

@endsection
