@extends('layouts.admin')

@section('content')
<div class="container-fluid px-0">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
        <div>
            <h4 class="fw-bold mb-1"><i class="fa-brands fa-whatsapp text-success me-2"></i>إدارة وتوثيق طلبات الواتساب 📱</h4>
            <p class="text-muted small mb-0">استعراض طلبات التحقق الواردة، الرموز، والرسائل مع إمكانية التحقق والتفعيل اليدوي الفوري للمستخدمين.</p>
        </div>
        <div class="d-flex gap-2">
            <a href="{{ route('admin.whatsapp.index', ['tab' => $activeTab]) }}" class="btn btn-outline-secondary btn-sm px-3">
                <i class="fa-solid fa-rotate me-1"></i> تحديث الصفحة
            </a>
        </div>
    </div>

    <!-- Navigation Tabs -->
    <ul class="nav nav-pills gap-2 mb-4 p-2 bg-white rounded-4 shadow-sm border" id="waTabs" role="tablist">
        <li class="nav-item" role="presentation">
            <button class="nav-link rounded-3 fw-bold px-4 py-2 {{ $activeTab === 'verifications' ? 'active bg-success text-white' : 'text-dark' }}" 
                    id="verifications-tab" data-bs-toggle="pill" data-bs-target="#verifications-pane" type="button" role="tab">
                <i class="fa-solid fa-clipboard-check me-2"></i> طلبات ورموز التحقق
                @if($pendingVerifications > 0)
                    <span class="badge bg-warning text-dark ms-1">{{ $pendingVerifications }}</span>
                @endif
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link rounded-3 fw-bold px-4 py-2 {{ $activeTab === 'logs' ? 'active bg-success text-white' : 'text-dark' }}" 
                    id="logs-tab" data-bs-toggle="pill" data-bs-target="#logs-pane" type="button" role="tab">
                <i class="fa-solid fa-comments me-2"></i> سجل الرسائل الواردة
                <span class="badge bg-secondary ms-1">{{ $totalLogs }}</span>
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link rounded-3 fw-bold px-4 py-2 {{ $activeTab === 'gateway' ? 'active bg-success text-white' : 'text-dark' }}" 
                    id="gateway-tab" data-bs-toggle="pill" data-bs-target="#gateway-pane" type="button" role="tab">
                <i class="fa-solid fa-robot me-2"></i> بوابة الربط والـ QR
            </button>
        </li>
    </ul>

    <div class="tab-content" id="waTabsContent">

        <!-- ========================================================================= -->
        <!-- TAB 1: VERIFICATIONS & OTP CODES & MANUAL VERIFICATION                    -->
        <!-- ========================================================================= -->
        <div class="tab-pane fade {{ $activeTab === 'verifications' ? 'show active' : '' }}" id="verifications-pane" role="tabpanel">
            
            <!-- Quick Stats -->
            <div class="row g-3 mb-4">
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm rounded-4 p-3 text-center bg-white">
                        <div class="text-muted small fw-bold mb-1">إجمالي الطلبات</div>
                        <h3 class="fw-bold text-dark mb-0">{{ $totalVerifications }}</h3>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm rounded-4 p-3 text-center" style="background-color: #FEFCE8; border: 1px solid #FEF08A !important;">
                        <div class="text-warning small fw-bold mb-1" style="color: #854D0E !important;">قيد الانتظار ⏳</div>
                        <h3 class="fw-bold mb-0" style="color: #854D0E;">{{ $pendingVerifications }}</h3>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm rounded-4 p-3 text-center" style="background-color: #F0FDF4; border: 1px solid #BBF7D0 !important;">
                        <div class="text-success small fw-bold mb-1">تم التحقق والتفعيل ✅</div>
                        <h3 class="fw-bold text-success mb-0">{{ $verifiedVerifications }}</h3>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="card border-0 shadow-sm rounded-4 p-3 text-center bg-light border">
                        <div class="text-muted small fw-bold mb-1">منتهية الصلاحية ⏱️</div>
                        <h3 class="fw-bold text-secondary mb-0">{{ $expiredVerifications }}</h3>
                    </div>
                </div>
            </div>

            <!-- Filters and Search Bar -->
            <div class="card border-0 shadow-sm rounded-4 p-3 mb-4 bg-white">
                <form action="{{ route('admin.whatsapp.index') }}" method="GET" class="row g-2 align-items-center justify-content-between">
                    <input type="hidden" name="tab" value="verifications" />
                    <div class="col-md-6 d-flex flex-wrap gap-2 align-items-center">
                        <span class="text-muted fw-bold small me-1">تصفية:</span>
                        <a href="{{ route('admin.whatsapp.index', ['tab' => 'verifications', 'status' => 'all', 'search' => $search]) }}" 
                           class="btn btn-sm rounded-pill fw-bold {{ $statusFilter === 'all' ? 'btn-success' : 'btn-outline-secondary' }}">
                            الكل ({{ $totalVerifications }})
                        </a>
                        <a href="{{ route('admin.whatsapp.index', ['tab' => 'verifications', 'status' => 'pending', 'search' => $search]) }}" 
                           class="btn btn-sm rounded-pill fw-bold {{ $statusFilter === 'pending' ? 'btn-warning text-dark' : 'btn-outline-warning text-dark' }}">
                            قيد الانتظار ⏳ ({{ $pendingVerifications }})
                        </a>
                        <a href="{{ route('admin.whatsapp.index', ['tab' => 'verifications', 'status' => 'verified', 'search' => $search]) }}" 
                           class="btn btn-sm rounded-pill fw-bold {{ $statusFilter === 'verified' ? 'btn-success' : 'btn-outline-success' }}">
                            تم التحقق ✅ ({{ $verifiedVerifications }})
                        </a>
                        <a href="{{ route('admin.whatsapp.index', ['tab' => 'verifications', 'status' => 'expired', 'search' => $search]) }}" 
                           class="btn btn-sm rounded-pill fw-bold {{ $statusFilter === 'expired' ? 'btn-secondary text-white' : 'btn-outline-secondary' }}">
                            منتهية ⏱️ ({{ $expiredVerifications }})
                        </a>
                    </div>

                    <div class="col-md-5 d-flex gap-2">
                        <input type="hidden" name="status" value="{{ $statusFilter }}" />
                        <input type="text" name="search" value="{{ $search }}" class="form-control form-control-sm rounded-3 text-end" placeholder="بحث بالرقم أو الاسم أو كود التحقق..." />
                        <button type="submit" class="btn btn-success btn-sm px-3 rounded-3 fw-bold">
                            <i class="fa-solid fa-magnifying-glass me-1"></i> بحث
                        </button>
                        @if($search !== '' || $statusFilter !== 'all')
                            <a href="{{ route('admin.whatsapp.index', ['tab' => 'verifications']) }}" class="btn btn-outline-secondary btn-sm px-2 rounded-3" title="إلغاء الفلتر">
                                <i class="fa-solid fa-xmark"></i>
                            </a>
                        @endif
                    </div>
                </form>
            </div>

            <!-- Verifications Table -->
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white mb-4">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0 text-end">
                        <thead class="table-light">
                            <tr class="text-secondary small fw-bold">
                                <th class="py-3 px-3">رقم الجوال</th>
                                <th class="py-3">اسم المستخدم</th>
                                <th class="py-3">نوع الطلب</th>
                                <th class="py-3 text-center">رمز التحقق (OTP)</th>
                                <th class="py-3">العبارة المطلوبة</th>
                                <th class="py-3">الحالة</th>
                                <th class="py-3">وقت الإنشاء</th>
                                <th class="py-3 text-center">الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            @forelse($verifications as $v)
                                @php
                                    $cleanPhone = $v->phone;
                                    $intlPhone = str_starts_with($cleanPhone, '0') ? '963' . substr($cleanPhone, 1) : $cleanPhone;
                                    $waLink = "https://wa.me/{$intlPhone}";
                                    $isExpired = !$v->is_verified && $v->expires_at && $v->expires_at->isPast();
                                @endphp
                                <tr>
                                    <!-- Phone Number -->
                                    <td class="px-3">
                                        <div class="d-flex align-items-center gap-2">
                                            <span class="fw-bold text-dark dir-ltr font-monospace">{{ $v->phone }}</span>
                                            <a href="{{ $waLink }}" target="_blank" class="text-success text-decoration-none" title="فتح المحادثة عبر واتساب">
                                                <i class="fa-brands fa-whatsapp fs-5"></i>
                                            </a>
                                        </div>
                                    </td>

                                    <!-- Name -->
                                    <td>
                                        <span class="fw-semibold text-dark">{{ $v->name ?: 'مستخدم جديد' }}</span>
                                    </td>

                                    <!-- Type -->
                                    <td>
                                        @if($v->type === 'register')
                                            <span class="badge rounded-pill bg-success-subtle text-success border border-success-subtle px-2 py-1 fw-bold">
                                                تسجيل جديد 🟢
                                            </span>
                                        @else
                                            <span class="badge rounded-pill bg-primary-subtle text-primary border border-primary-subtle px-2 py-1 fw-bold">
                                                استعادة كلمة المرور 🔵
                                            </span>
                                        @endif
                                    </td>

                                    <!-- Verification Code (OTP) -->
                                    <td class="text-center">
                                        <div class="d-inline-flex align-items-center gap-2 bg-light px-3 py-1 rounded-3 border">
                                            <span class="font-monospace fs-5 fw-bold text-dark tracking-wider">{{ $v->verification_code }}</span>
                                            <button type="button" class="btn btn-link btn-sm p-0 text-muted" onclick="copyText('{{ $v->verification_code }}')" title="نسخ الرمز">
                                                <i class="fa-regular fa-copy"></i>
                                            </button>
                                        </div>
                                    </td>

                                    <!-- Phrase -->
                                    <td>
                                        <small class="text-muted d-inline-block text-truncate" style="max-width: 180px;" title="{{ $v->verification_phrase }}">
                                            {{ $v->verification_phrase }}
                                        </small>
                                    </td>

                                    <!-- Status -->
                                    <td>
                                        @if($v->is_verified)
                                            <span class="badge bg-success px-2 py-1 rounded-pill fw-bold">
                                                ✅ تم التحقق والتفعيل
                                            </span>
                                        @elseif(!$isExpired)
                                            <span class="badge bg-warning text-dark px-2 py-1 rounded-pill fw-bold">
                                                ⏳ بانتظار رسالة الواتساب
                                            </span>
                                        @else
                                            <span class="badge bg-secondary px-2 py-1 rounded-pill fw-bold">
                                                ⏱️ منتهية الصلاحية
                                            </span>
                                        @endif
                                    </td>

                                    <!-- Date -->
                                    <td>
                                        <small class="text-muted">{{ $v->created_at ? $v->created_at->format('Y-m-d H:i') : '-' }}</small>
                                    </td>

                                    <!-- Actions -->
                                    <td class="text-center">
                                        <div class="d-inline-flex gap-1 align-items-center">
                                            @if(!$v->is_verified)
                                                <button type="button" class="btn btn-success btn-sm fw-bold px-3 rounded-3" 
                                                        onclick="openManualVerifyModal('{{ $v->id }}', '{{ $v->phone }}', '{{ $v->name }}')">
                                                    <i class="fa-solid fa-bolt me-1"></i> تفعيل يدوي
                                                </button>
                                            @endif

                                            <button type="button" class="btn btn-outline-danger btn-sm rounded-3" 
                                                    onclick="openDeleteModal('{{ $v->id }}', '{{ $v->phone }}')" title="حذف الجلسة">
                                                <i class="fa-regular fa-trash-can"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            @empty
                                <tr>
                                    <td colspan="8" class="text-center py-5 text-muted fw-bold">
                                        لا توجد طلبات تحقق مطابقة للبحث أو الفلتر المحدد.
                                    </td>
                                </tr>
                            @endforelse
                        </tbody>
                    </table>
                </div>

                @if($verifications->hasPages())
                    <div class="p-3 border-top d-flex justify-content-center">
                        {{ $verifications->appends(['tab' => 'verifications', 'status' => $statusFilter, 'search' => $search])->links('pagination::bootstrap-5') }}
                    </div>
                @endif
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 2: INBOUND WHATSAPP MESSAGE LOGS                                      -->
        <!-- ========================================================================= -->
        <div class="tab-pane fade {{ $activeTab === 'logs' ? 'show active' : '' }}" id="logs-pane" role="tabpanel">
            
            <!-- Search Logs -->
            <div class="card border-0 shadow-sm rounded-4 p-3 mb-4 bg-white">
                <form action="{{ route('admin.whatsapp.index') }}" method="GET" class="row g-2 align-items-center justify-content-between">
                    <input type="hidden" name="tab" value="logs" />
                    <div class="col-md-6">
                        <h6 class="fw-bold mb-1 text-dark"><i class="fa-solid fa-list-check text-primary me-2"></i>سجل جميع الرسائل الواردة لخادم الواتساب</h6>
                        <small class="text-muted">يوثق آلياً كل رسالة واردة لرقم البوت مع كود التحقق وحالة المطابقة.</small>
                    </div>

                    <div class="col-md-5 d-flex gap-2">
                        <input type="text" name="logs_search" value="{{ $logsSearch }}" class="form-control form-control-sm rounded-3 text-end" placeholder="بحث برقم المرسل أو نص الرسالة أو الكود..." />
                        <button type="submit" class="btn btn-primary btn-sm px-3 rounded-3 fw-bold">
                            <i class="fa-solid fa-magnifying-glass me-1"></i> بحث
                        </button>
                        @if($logsSearch !== '')
                            <a href="{{ route('admin.whatsapp.index', ['tab' => 'logs']) }}" class="btn btn-outline-secondary btn-sm px-2 rounded-3" title="إلغاء البحث">
                                <i class="fa-solid fa-xmark"></i>
                            </a>
                        @endif
                    </div>
                </form>
            </div>

            <!-- Message Logs Table -->
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white mb-4">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0 text-end">
                        <thead class="table-light">
                            <tr class="text-secondary small fw-bold">
                                <th class="py-3 px-3">الوقت والتاريخ</th>
                                <th class="py-3">رقم المرسل</th>
                                <th class="py-3">نص الرسالة الواردة</th>
                                <th class="py-3 text-center">الرمز المستخرج</th>
                                <th class="py-3">حالة المطابقة</th>
                                <th class="py-3">التفاصيل والملاحظات</th>
                            </tr>
                        </thead>
                        <tbody>
                            @forelse($messageLogs as $log)
                                <tr>
                                    <td class="px-3">
                                        <small class="text-muted fw-semibold">{{ $log->created_at ? $log->created_at->format('Y-m-d H:i:s') : '-' }}</small>
                                    </td>
                                    <td>
                                        <span class="fw-bold text-dark dir-ltr font-monospace">{{ $log->sender_phone }}</span>
                                    </td>
                                    <td>
                                        <span class="text-dark fw-semibold d-inline-block" style="max-width: 280px; word-break: break-word;">
                                            {{ $log->message_body }}
                                        </span>
                                    </td>
                                    <td class="text-center">
                                        @if($log->extracted_code)
                                            <span class="badge bg-light text-dark border font-monospace fs-6 px-2 py-1">
                                                {{ $log->extracted_code }}
                                            </span>
                                        @else
                                            <span class="text-muted">-</span>
                                        @endif
                                    </td>
                                    <td>
                                        @if($log->status === 'verified')
                                            <span class="badge bg-success px-2 py-1 rounded-pill fw-bold">
                                                ✅ مطابقة وتفعيل ناجح
                                            </span>
                                        @elseif($log->status === 'unmatched')
                                            <span class="badge bg-danger px-2 py-1 rounded-pill fw-bold">
                                                ❌ غير مطابق
                                            </span>
                                        @else
                                            <span class="badge bg-secondary px-2 py-1 rounded-pill fw-bold">
                                                {{ $log->status }}
                                            </span>
                                        @endif
                                    </td>
                                    <td>
                                        <small class="text-muted">{{ $log->details ?: '-' }}</small>
                                    </td>
                                </tr>
                            @empty
                                <tr>
                                    <td colspan="6" class="text-center py-5 text-muted fw-bold">
                                        لا توجد رسائل واردة مسجلة في السجل حتى الآن.
                                    </td>
                                </tr>
                            @endforelse
                        </tbody>
                    </table>
                </div>

                @if($messageLogs->hasPages())
                    <div class="p-3 border-top d-flex justify-content-center">
                        {{ $messageLogs->appends(['tab' => 'logs', 'logs_search' => $logsSearch])->links('pagination::bootstrap-5') }}
                    </div>
                @endif
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 3: MULTI-ACCOUNT GATEWAY CONNECTION & QR POOL & NUMBER TESTER         -->
        <!-- ========================================================================= -->
        <div class="tab-pane fade {{ $activeTab === 'gateway' ? 'show active' : '' }}" id="gateway-pane" role="tabpanel">
            
            <!-- Gateway Overview & Add Account Bar -->
            <div class="card border-0 shadow-sm rounded-4 p-4 mb-4 bg-white">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 pb-3 border-bottom mb-3">
                    <div>
                        <h5 class="fw-bold mb-1 text-dark">
                            <i class="fa-solid fa-server text-success me-2"></i>بوابة أرقام الواتساب المتعددة (Multi-Account WhatsApp Gateway) 🌐
                        </h5>
                        <p class="text-muted small mb-0">
                            يمكنك ربط عدد غير محدود من أرقام الواتساب بالتوازي مع نظام <strong>التبديل والاحتياط التلقائي (Automatic Failover)</strong> في حال انقطاع أي رقم.
                        </p>
                    </div>
                    <div class="d-flex gap-2">
                        <button id="btn-add-account" class="btn btn-success fw-bold px-3 rounded-3 shadow-sm">
                            <i class="fa-solid fa-plus me-1"></i> إضافة رقم واتساب جديد 📱
                        </button>
                    </div>
                </div>

                <!-- Automatic Failover Info Alert -->
                <div class="alert alert-success border-0 rounded-4 p-3 d-flex align-items-center gap-3 mb-0" style="background-color: #ECFDF5; border-right: 4px solid #10B981 !important;">
                    <div class="fs-4 text-success"><i class="fa-solid fa-shield-halved"></i></div>
                    <div class="small">
                        <strong class="text-success d-block mb-1">⚡ نظام التبديل التلقائي والحماية من التوقف نشط:</strong>
                        <span class="text-muted">يقوم النظام بتوزيع الرسائل وتأكيد الأرقام تلقائياً، وإذا فصل أي رقم أو حدث به خلل ينتقل فورياً في نفس اللحظة إلى الرقم التالي دون أي تأثير على المستخدمين.</span>
                    </div>
                </div>
            </div>

            <!-- Multi-Account Cards Grid -->
            <div id="accounts-grid" class="row g-4 mb-4">
                <!-- Dynamically rendered via JavaScript -->
                <div class="col-12 text-center py-5">
                    <div class="spinner-border text-success mb-2" role="status"></div>
                    <div class="text-muted fw-bold">جاري تحميل قائمة حسابات وأرقام الواتساب...</div>
                </div>
            </div>

            <!-- Syrian Phone Number Tester -->
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                <h5 class="fw-bold mb-1">فحص وتجربة الأرقام (09 / 05) 🔍</h5>
                <p class="text-muted small mb-3">يمكنك فحص أي رقم للتأكد من تسجيله على واتساب وجاهزيته لاستقبال وإرسال رموز التحقق عبر الحسابات النشطة.</p>

                <div class="row g-2 align-items-center">
                    <div class="col-md-8">
                        <input type="tel" id="test-phone-input" class="form-control form-control-lg text-end dir-ltr" placeholder="أدخل رقم الجوال للتجربة (مثال: 0912345678 أو 0512345678)" maxlength="15" />
                    </div>
                    <div class="col-md-4">
                        <button id="btn-check-number" class="btn btn-success btn-lg w-100 fw-bold" disabled>
                            فحص الرقم على واتساب
                        </button>
                    </div>
                </div>

                <div id="check-result-box" class="mt-3 d-none alert p-3 rounded-3 fw-bold"></div>
            </div>

        </div>

    </div>
</div>

<!-- ========================================================================= -->
<!-- MODALS                                                                    -->
<!-- ========================================================================= -->

<!-- 1. Manual Verify Modal -->
<div class="modal fade" id="manualVerifyModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0 shadow">
            <div class="modal-header border-0 pb-0">
                <h5 class="modal-title fw-bold text-success">
                    <i class="fa-solid fa-bolt me-2"></i> تأكيد التحقق والتفعيل اليدوي
                </h5>
                <button type="button" class="btn-close ms-0 me-auto" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-4 text-end">
                <p class="mb-2">هل أنت متأكد من رغبتك في تأكيد طلب التحقق وتفعيل حساب المستخدم يدوياً؟</p>
                <div class="bg-light p-3 rounded-3 border">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="text-muted">رقم الجوال:</span>
                        <strong id="mv-modal-phone" class="dir-ltr font-monospace text-dark"></strong>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">اسم المستخدم:</span>
                        <strong id="mv-modal-name" class="text-dark"></strong>
                    </div>
                </div>
                <small class="text-muted mt-2 d-block">
                    ⚡ سيتم فوراً تفعيل حسابه وتأكيد كلمة المرور وتسجيل دخوله في المتصفح تلقائياً.
                </small>
            </div>
            <div class="modal-footer border-0 pt-0">
                <form id="manual-verify-form" method="POST" action="">
                    @csrf
                    <button type="button" class="btn btn-light rounded-3 px-3 fw-bold" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-success rounded-3 px-4 fw-bold">
                        <i class="fa-solid fa-check me-1"></i> نعم، تفعيل وتحقق يدوي
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- 2. Delete Verification Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0 shadow">
            <div class="modal-header border-0 pb-0">
                <h5 class="modal-title fw-bold text-danger">
                    <i class="fa-solid fa-trash-can me-2"></i> حذف جلسة التحقق
                </h5>
                <button type="button" class="btn-close ms-0 me-auto" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body py-4 text-end">
                <p class="mb-2">هل أنت متأكد من حذف جلسة التحقق للرقم التالي؟</p>
                <div class="bg-light p-3 rounded-3 border">
                    <strong id="del-modal-phone" class="dir-ltr font-monospace text-danger fs-5"></strong>
                </div>
            </div>
            <div class="modal-footer border-0 pt-0">
                <form id="delete-form" method="POST" action="">
                    @csrf
                    @method('DELETE')
                    <button type="button" class="btn btn-light rounded-3 px-3 fw-bold" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-danger rounded-3 px-4 fw-bold">
                        نعم، حذف الجلسة
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Toast notification helper for copy -->
<div class="position-fixed bottom-0 start-50 translate-middle-x p-3" style="z-index: 99999;">
    <div id="copyToast" class="toast align-items-center text-white bg-dark border-0 rounded-4 shadow" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
            <div class="toast-body fw-bold py-2 px-3">
                <i class="fa-solid fa-check text-success me-2"></i> تم نسخ رمز التحقق بنجاح!
            </div>
        </div>
    </div>
</div>

<script>
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        const toastEl = document.getElementById('copyToast');
        const toast = new bootstrap.Toast(toastEl, { delay: 2000 });
        toast.show();
    });
}

function openManualVerifyModal(id, phone, name) {
    document.getElementById('mv-modal-phone').innerText = phone;
    document.getElementById('mv-modal-name').innerText = name || 'مستخدم جديد';
    document.getElementById('manual-verify-form').action = "{{ url('whatsapp/verifications') }}/" + id + "/manual-verify";
    const modal = new bootstrap.Modal(document.getElementById('manualVerifyModal'));
    modal.show();
}

function openDeleteModal(id, phone) {
    document.getElementById('del-modal-phone').innerText = phone;
    document.getElementById('delete-form').action = "{{ url('whatsapp/verifications') }}/" + id;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

document.addEventListener('DOMContentLoaded', function () {
    const accountsGrid = document.getElementById('accounts-grid');
    const btnAddAccount = document.getElementById('btn-add-account');
    const testInput = document.getElementById('test-phone-input');
    const btnCheck = document.getElementById('btn-check-number');
    const checkResultBox = document.getElementById('check-result-box');

    let isFetching = false;
    let lastSessionsHash = '';
    let knownSessions = [];
    let emptyPollCount = 0;

    function renderAccounts(sessions, forceEmpty = false) {
        if (!sessions || sessions.length === 0) {
            // Anti-flicker: If we previously had accounts, do not wipe immediately on a single transient drop
            if (!forceEmpty && knownSessions.length > 0) {
                return;
            }
            if (lastSessionsHash === 'empty') return;
            accountsGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="p-4 bg-light rounded-4 border d-inline-block shadow-sm" style="max-width: 500px;">
                        <i class="fa-brands fa-whatsapp text-secondary fs-1 mb-3"></i>
                        <h5 class="fw-bold text-dark mb-2">لا توجد حسابات واتساب مربوطة حالياً</h5>
                        <p class="text-muted small mb-4">يمكنك إضافة رقم الواتساب الخاص بك للبدء في إرسال واستقبال رموز التحقق فورياً.</p>
                        <button onclick="createNewAccount()" class="btn btn-success fw-bold px-4 py-2 rounded-3 shadow-sm">
                            <i class="fa-solid fa-plus me-1"></i> إضافة رقم واتساب جديد 📱
                        </button>
                    </div>
                </div>
            `;
            lastSessionsHash = 'empty';
            knownSessions = [];
            return;
        }

        knownSessions = sessions;
        emptyPollCount = 0;

        // Anti-flicker: If the serialized status & QR haven't changed, don't recreate the DOM
        const currentHash = sessions.map(s => `${s.id}:${s.status}:${s.phone || ''}:${(s.qr || '').length}:${s.pairing_code || ''}`).join('|');
        const activeElem = document.activeElement;
        const isUserTyping = activeElem && activeElem.id && activeElem.id.startsWith('pair-phone-');

        if (currentHash === lastSessionsHash || isUserTyping) {
            return;
        }
        lastSessionsHash = currentHash;

        let html = '';
        sessions.forEach((s, idx) => {
            const isActive = s.is_active;
            const isConnected = s.status === 'connected';
            const isQrReady = s.status === 'qr_ready' && s.qr;
            const isStandby = s.status === 'standby';

            let badgeHtml = '';
            if (isActive && isConnected) {
                badgeHtml = `<span class="badge bg-success px-3 py-2 rounded-pill fw-bold fs-6"><i class="fa-solid fa-circle-check me-1"></i> الفعّال والنشط حالياً</span>`;
            } else if (isActive && isQrReady) {
                badgeHtml = `<span class="badge bg-warning text-dark px-3 py-2 rounded-pill fw-bold fs-6"><i class="fa-solid fa-qrcode me-1"></i> بانتظار الربط</span>`;
            } else if (isStandby) {
                badgeHtml = `<span class="badge bg-secondary-subtle text-secondary px-3 py-2 rounded-pill fw-bold fs-6"><i class="fa-solid fa-shield-halved me-1"></i> احتياطي جاهز (Standby)</span>`;
            } else {
                badgeHtml = `<span class="badge bg-danger px-3 py-2 rounded-pill fw-bold fs-6"><i class="fa-solid fa-circle-xmark me-1"></i> غير متصل</span>`;
            }

            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="card border-0 shadow-sm rounded-4 h-100 bg-white overflow-hidden" style="border-top: 4px solid ${isActive ? (isConnected ? '#10B981' : '#F59E0B') : '#9CA3AF'} !important;">
                        <div class="card-body p-4 d-flex flex-column justify-content-between">
                            
                            <!-- Card Header -->
                            <div>
                                <div class="d-flex justify-content-between align-items-start mb-3">
                                    <div>
                                        <h5 class="fw-bold text-dark mb-1">
                                             ${s.name || `حساب #${idx + 1}`}
                                        </h5>
                                        <small class="text-muted font-monospace">${s.id}</small>
                                    </div>
                                    <div>${badgeHtml}</div>
                                </div>

                                <!-- Connected Phone Info -->
                                ${isConnected && s.phone ? `
                                    <div class="bg-light p-3 rounded-3 border mb-3 text-center">
                                        <div class="text-muted small fw-bold mb-1">رقم الواتساب المرتبط:</div>
                                        <div class="fw-bold text-success fs-5 dir-ltr font-monospace">+${s.phone}</div>
                                        <div class="d-flex justify-content-around mt-2 pt-2 border-top small text-muted">
                                            <span>وارد: <strong>${s.messagesReceived || 0}</strong></span>
                                            <span>صادر: <strong>${s.messagesSent || 0}</strong></span>
                                        </div>
                                    </div>
                                ` : ''}

                                <!-- Standby Info -->
                                ${isStandby ? `
                                    <div class="bg-light p-3 rounded-3 border mb-3 text-center text-muted">
                                        <i class="fa-solid fa-shield-halved fs-3 mb-2 text-secondary"></i>
                                        <div class="small fw-bold">هذا الرقم في وضع الاستعداد</div>
                                        <div class="small mt-1">يتم تفعيله وتشغيله تلقائياً في حال فصل الرقم الفعّال.</div>
                                    </div>
                                ` : ''}

                                <!-- QR Code & Direct Pairing Section -->
                                ${isActive && !isConnected ? `
                                    <div class="text-center py-2 mb-3">
                                        ${s.qr ? `
                                            <div class="d-inline-block bg-white p-2 rounded-3 border border-2 border-warning border-dashed shadow-sm mb-2">
                                                <img src="${s.qr}" alt="QR Code" style="width: 170px; height: 170px; display: block;" />
                                            </div>
                                            <div class="small text-muted fw-bold mb-3">1️⃣ مسح الباركود من تطبيق واتساب 📱</div>
                                        ` : `
                                            <div class="spinner-border text-warning mb-2" role="status"></div>
                                            <div class="small text-muted mb-2">جاري تهيئة الباركود...</div>
                                        `}

                                        <!-- Direct Pairing Code -->
                                        <div class="p-3 bg-light rounded-3 border text-start mt-2">
                                            <div class="fw-bold small text-dark mb-1">
                                                <i class="fa-solid fa-key text-primary me-1"></i> 2️⃣ أو الربط المباشر برمز الهاتف (Pairing Code)
                                            </div>
                                            <div class="text-muted small mb-2" style="font-size: 11px;">
                                                أدخل رقم هاتفك لتوليد كود من 8 خانات وتدخله في الواتساب مباشرة:
                                            </div>
                                            <div class="input-group input-group-sm mb-2">
                                                <input type="tel" id="pair-phone-${s.id}" class="form-control text-end dir-ltr font-monospace" placeholder="مثال: 0912345678 أو 0512345678" />
                                                <button onclick="requestPairingCode('${s.id}')" id="btn-pair-${s.id}" class="btn btn-primary fw-bold px-3">
                                                    طلب الكود 🔑
                                                </button>
                                            </div>
                                            <div id="pair-code-box-${s.id}" class="small d-none p-2 rounded-3 text-center"></div>
                                        </div>
                                    </div>
                                ` : ''}
                            </div>

                            <!-- Card Actions -->
                            <div class="d-flex gap-2 pt-3 border-top mt-3">
                                ${!isActive ? `
                                    <button onclick="activateAccount('${s.id}')" class="btn btn-outline-success btn-sm flex-fill rounded-3 fw-bold" title="تعيين كرقم فعّال">
                                        <i class="fa-solid fa-bolt me-1"></i> تشغيل كرقم فعّال
                                    </button>
                                ` : `
                                    <button onclick="restartAccount('${s.id}')" class="btn btn-outline-secondary btn-sm flex-fill rounded-3 fw-bold" title="إعادة تشغيل الجلسة">
                                        <i class="fa-solid fa-rotate me-1"></i> إعادة تشغيل
                                    </button>
                                `}
                                <button onclick="deleteAccount('${s.id}', '${s.name || s.id}')" class="btn btn-outline-danger btn-sm rounded-3 fw-bold" title="فصل وحذف هذا الحساب">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>

                        </div>
                    </div>
                </div>
            `;
        });

        accountsGrid.innerHTML = html;
    }

    function fetchStatus() {
        if (isFetching) return;
        isFetching = true;

        fetch("{{ route('admin.whatsapp.status') }}")
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data.sessions) && data.sessions.length > 0) {
                    emptyPollCount = 0;
                    renderAccounts(data.sessions);
                } else if (Array.isArray(data.sessions) && data.sessions.length === 0) {
                    emptyPollCount++;
                    // Only transition to empty UI after multiple confirmed empty responses
                    if (emptyPollCount >= 3 || knownSessions.length === 0) {
                        renderAccounts([], true);
                    }
                }
            })
            .catch(() => {
                // Keep known accounts visible during temporary network hiccups
            })
            .finally(() => {
                isFetching = false;
            });
    }

    // Auto poll status smoothly every 4 seconds
    fetchStatus();
    pollTimer = setInterval(fetchStatus, 4000);

    // Request 8-Digit Pairing Code
    window.requestPairingCode = function(sessionId) {
        const phoneInput = document.getElementById(`pair-phone-${sessionId}`);
        const codeBox = document.getElementById(`pair-code-box-${sessionId}`);
        const btnPair = document.getElementById(`btn-pair-${sessionId}`);
        const phone = phoneInput ? phoneInput.value.trim() : '';

        if (!phone) {
            alert('يرجى إدخال رقم الهاتف أولاً.');
            if (phoneInput) phoneInput.focus();
            return;
        }

        if (btnPair) btnPair.disabled = true;
        if (codeBox) {
            codeBox.classList.remove('d-none', 'alert-danger', 'alert-success');
            codeBox.classList.add('alert', 'alert-info');
            codeBox.innerHTML = '<div class="spinner-border spinner-border-sm text-primary me-1"></div> جاري طلب كود الربط من سيرفر الواتساب...';
        }

        fetch(`{{ url('whatsapp/sessions') }}/${sessionId}/pairing-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ phone: phone })
        })
        .then(res => res.json())
        .then(data => {
            if (btnPair) btnPair.disabled = false;
            if (data.success && data.pairing_code) {
                if (codeBox) {
                    codeBox.classList.remove('alert-info', 'alert-danger');
                    codeBox.classList.add('alert', 'alert-success');
                    codeBox.innerHTML = `
                        <div class="fw-bold text-dark mb-1">كود ربط واتساب للرقم (+${data.phone}):</div>
                        <div class="display-6 fw-bold font-monospace text-primary my-2 dir-ltr" style="letter-spacing: 4px;">${data.pairing_code}</div>
                        <button class="btn btn-sm btn-outline-primary fw-bold mb-2" onclick="navigator.clipboard.writeText('${data.pairing_code}'); alert('تم نسخ كود الربط!');">
                            <i class="fa-regular fa-copy me-1"></i> نسخ الرمز
                        </button>
                        <div class="small text-muted text-start mt-2 border-top pt-2" style="line-height: 1.6; font-size: 11px;">
                            <strong>طريقة التفعيل في هاتفك:</strong><br>
                            1. افتح واتساب ➡️ خيارات (الثلاث نقاط) ➡️ <strong>الأجهزة المرتبطة</strong><br>
                            2. اضغط <strong>ربط جهاز</strong> ➡️ <strong>الربط برقم الهاتف بدلاً من ذلك</strong><br>
                            3. أدخل الرمز الظاهر أعلاه 🔑
                        </div>
                    `;
                }
            } else {
                if (codeBox) {
                    codeBox.classList.remove('alert-info', 'alert-success');
                    codeBox.classList.add('alert', 'alert-danger');
                    codeBox.innerHTML = `<span>${data.message || 'فشل توليد كود الربط.'}</span>`;
                }
            }
        })
        .catch(err => {
            if (btnPair) btnPair.disabled = false;
            if (codeBox) {
                codeBox.classList.remove('alert-info', 'alert-success');
                codeBox.classList.add('alert', 'alert-danger');
                codeBox.innerHTML = `<span>حدث خطأ أثناء الاتصال بالخادم.</span>`;
            }
        });
    };

    // Create New Account
    window.createNewAccount = function () {
        const name = prompt('أدخل اسماً أو وصفاً لرقم الواتساب الجديد (مثال: رقم الطوارئ 2):', '');
        if (name === null) return;

        // Show immediate loading notification
        accountsGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-success mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
                <h5 class="fw-bold text-dark">جاري إنشاء الجلسة السحابية وتوليد كود الـ QR...</h5>
                <p class="text-muted small">يرجى الانتظار 3 ثوانٍ فقط وسيظهر الباركود لمسحه من تطبيق الواتساب 📱</p>
            </div>
        `;

        fetch("{{ route('admin.whatsapp.createSession') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ name: name.trim() || null })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                setTimeout(fetchStatus, 1500);
            } else {
                alert(data.message || 'حدث خطأ أثناء إنشاء الحساب.');
                fetchStatus();
            }
        })
        .catch(() => {
            fetchStatus();
        });
    };

    btnAddAccount.addEventListener('click', window.createNewAccount);

    // Activate Account
    window.activateAccount = function (sessionId) {
        fetch(`{{ url('whatsapp/sessions') }}/${sessionId}/activate`, {
            method: 'POST',
            headers: {
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            }
        })
        .then(res => res.json())
        .then(() => {
            fetchStatus();
        });
    };

    // Restart Account
    window.restartAccount = function (sessionId) {
        fetch(`{{ url('whatsapp/sessions') }}/${sessionId}/restart`, {
            method: 'POST',
            headers: {
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            }
        })
        .then(res => res.json())
        .then(() => {
            fetchStatus();
        });
    };

    // Delete Account
    window.deleteAccount = function (sessionId, sessionName) {
        if (!confirm(`هل أنت متأكد من رغبتك في فصل وحذف (${sessionName})؟`)) return;

        fetch(`{{ url('whatsapp/sessions') }}/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            }
        })
        .then(res => res.json())
        .then(() => {
            fetchStatus();
        })
        .catch(() => {
            fetchStatus();
        });
    };

    // Phone Tester
    testInput.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '').slice(0, 15);
        btnCheck.disabled = this.value.length < 8;
    });

    btnCheck.addEventListener('click', function () {
        const phone = testInput.value;
        if (phone.length < 8) return;

        btnCheck.disabled = true;
        btnCheck.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> جاري الفحص عبر الحسابات النشطة...';
        checkResultBox.classList.add('d-none');

        fetch("{{ route('admin.whatsapp.checkNumber') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': '{{ csrf_token() }}',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ phone: phone })
        })
        .then(res => res.json())
        .then(data => {
            checkResultBox.classList.remove('d-none', 'alert-success', 'alert-danger');
            if (data.exists) {
                checkResultBox.classList.add('alert-success');
                checkResultBox.innerHTML = '<i class="fa-solid fa-circle-check me-2"></i> ' + data.message + (data.checked_by ? ` (تم الفحص بنجاح عبر الرقم +${data.checked_by})` : '');
            } else {
                checkResultBox.classList.add('alert-danger');
                checkResultBox.innerHTML = '<i class="fa-solid fa-circle-xmark me-2"></i> ' + data.message;
            }
        })
        .catch(() => {
            checkResultBox.classList.remove('d-none', 'alert-success');
            checkResultBox.classList.add('alert-danger');
            checkResultBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation me-2"></i> فشل الاتصال بخادم الواتساب للفحص.';
        })
        .finally(() => {
            btnCheck.disabled = false;
            btnCheck.innerHTML = 'فحص الرقم على واتساب';
        });
    });
});
</script>
@endsection
