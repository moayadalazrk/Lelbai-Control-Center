<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم | AZ Market Manager</title>
    <!-- Cairo Font & Bootstrap RTL -->
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        body {
            font-family: 'Cairo', sans-serif;
            background-color: #F8F9FA;
            color: #1C2418;
        }
        .admin-sidebar {
            width: 260px;
            min-height: 100vh;
            background-color: #1C2418;
            color: #FFFFFF;
            position: fixed;
            top: 0;
            right: 0;
            z-index: 100;
        }
        .admin-brand {
            padding: 1.5rem;
            font-size: 1.3rem;
            font-weight: 800;
            color: #C8A951;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .nav-link-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.85rem 1.5rem;
            color: #CBD5E1;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s;
        }
        .nav-link-item:hover, .nav-link-item.active {
            background-color: #2D5016;
            color: #FFFFFF;
            border-right: 4px solid #C8A951;
        }
        .admin-main {
            margin-right: 260px;
            padding: 2rem;
        }
        .stat-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
        }
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
        }
        .badge-active { background-color: #DCFCE7; color: #15803D; }
        .badge-pending { background-color: #FEF9C3; color: #A16207; }

        /* Environment Switcher Styles */
        .env-switcher-btn {
            background: #FFFFFF;
            border: 1.5px solid #E2E8F0;
            border-radius: 50rem;
            padding: 0.45rem 1.1rem;
            font-size: 0.85rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            cursor: pointer;
            text-decoration: none;
            color: #1E293B;
        }
        .env-switcher-btn:hover, .env-switcher-btn:focus {
            background: #F8FAFC;
            border-color: #CBD5E1;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            color: #0F172A;
        }
        .env-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            position: relative;
        }
        .env-dot.dot-local {
            background-color: #10B981;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.25);
            animation: pulse-green 2s infinite;
        }
        .env-dot.dot-production {
            background-color: #3B82F6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
            animation: pulse-blue 2s infinite;
        }
        .env-dot.dot-error {
            background-color: #EF4444;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.25);
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
            70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        @keyframes pulse-blue {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5); }
            70% { box-shadow: 0 0 0 6px rgba(59, 130, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        }
        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
            70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        .env-dropdown-menu {
            min-width: 320px;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            padding: 0.6rem;
        }
        .env-item {
            border-radius: 10px;
            padding: 0.75rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: background 0.15s;
            text-decoration: none;
            color: #1E293B;
            border: 1px solid transparent;
        }
        .env-item:hover {
            background-color: #F8FAFC;
        }
        .env-item.active {
            background-color: #F0FDF4;
            border-color: #BBF7D0;
        }
        .env-item.active.prod-active {
            background-color: #EFF6FF;
            border-color: #BFDBFE;
        }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <aside class="admin-sidebar d-flex flex-column justify-content-between">
        <div>
            <div class="admin-brand">
                <i class="fa-solid fa-shield-halved"></i>
                <span>للبيع Manager</span>
            </div>
            <nav class="mt-3">
                <a href="{{ route('admin.dashboard') }}" class="nav-link-item {{ request()->routeIs('admin.dashboard') ? 'active' : '' }}">
                    <i class="fa-solid fa-chart-pie"></i>
                    <span>الإحصائيات العامة</span>
                </a>
                <a href="{{ route('admin.listings.index') }}" class="nav-link-item {{ request()->routeIs('admin.listings.*') ? 'active' : '' }}">
                    <i class="fa-solid fa-box-archive"></i>
                    <span>إدارة وتدقيق الإعلانات</span>
                </a>
                <a href="#" class="nav-link-item">
                    <i class="fa-solid fa-users"></i>
                    <span>إدارة المستخدمين</span>
                </a>
                <a href="{{ route('admin.complaints.index') }}" class="nav-link-item {{ request()->routeIs('admin.complaints.*') ? 'active' : '' }}">
                    <i class="fa-solid fa-headset text-warning fs-5"></i>
                    <span>الشكاوى والرسائل</span>
                    @if(!empty($pendingComplaintsCount) && $pendingComplaintsCount > 0)
                        <span class="badge bg-danger rounded-pill ms-auto fs-8">{{ $pendingComplaintsCount }}</span>
                    @endif
                </a>
                <a href="{{ route('categories.index') }}" class="nav-link-item {{ request()->routeIs('categories.*') ? 'active' : '' }}">
                    <i class="fa-solid fa-layer-group"></i>
                    <span>إدارة التصنيفات والخصائص</span>
                </a>
                <a href="{{ route('admin.whatsapp.index') }}" class="nav-link-item {{ request()->routeIs('admin.whatsapp.*') ? 'active' : '' }}">
                    <i class="fa-brands fa-whatsapp text-success fs-5"></i>
                    <span>توثيق ورسائل واتساب 📱</span>
                </a>
            </nav>
        </div>

        <!-- Sidebar Footer Env Info -->
        <div class="p-3 border-top border-secondary border-opacity-25">
            <div class="d-flex align-items-center justify-content-between bg-dark bg-opacity-50 p-2 rounded-3">
                <div class="d-flex align-items-center gap-2">
                    <span class="env-dot {{ !($dbConnected ?? true) ? 'dot-error' : (($activeDbEnv ?? 'local') === 'production' ? 'dot-production' : 'dot-local') }}"></span>
                    <div style="line-height: 1.2;">
                        <small class="d-block text-white fw-bold" style="font-size: 0.75rem;">
                            {{ ($activeDbEnv ?? 'local') === 'production' ? 'سيرفر حقيقي (Hostinger)' : 'سيرفر محلي (Local DB)' }}
                        </small>
                        <small class="{{ !($dbConnected ?? true) ? 'text-danger fw-bold' : 'text-white-50' }}" style="font-size: 0.68rem;">
                            {{ !($dbConnected ?? true) ? '⚠️ غير متصل' : ($activeDbInfo['database'] ?? 'souq_al_sham') }}
                        </small>
                    </div>
                </div>
                <a href="{{ route('admin.switchEnvironment', ($activeDbEnv ?? 'local') === 'production' ? 'local' : 'production') }}" 
                   class="btn btn-sm btn-outline-light py-0 px-2 fs-8 fw-semibold" 
                   title="تبديل السيرفر">
                    تبديل
                </a>
            </div>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="admin-main">
        <!-- Topbar -->
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
            <div>
                <h4 class="fw-bold mb-1">لوحة تحكم المدير</h4>
                <small class="text-muted">مربوط بالمباشر مع قاعدة بيانات منصة للبيع</small>
            </div>
            <div class="d-flex align-items-center gap-2">
                <!-- Environment Switcher Dropdown -->
                <div class="dropdown">
                    <button class="env-switcher-btn dropdown-toggle {{ !($dbConnected ?? true) ? 'border-danger text-danger' : '' }}" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <span class="env-dot {{ !($dbConnected ?? true) ? 'dot-error' : (($activeDbEnv ?? 'local') === 'production' ? 'dot-production' : 'dot-local') }}"></span>
                        <span>{{ ($activeDbEnv ?? 'local') === 'production' ? '🌐 السيرفر الحقيقي (Hostinger)' : '💻 سيرفر التطوير المحلي' }}</span>
                        @if(!($dbConnected ?? true))
                            <span class="badge bg-danger px-2 py-1 fs-8">
                                غير متصل ⚠️
                            </span>
                        @else
                            <span class="badge {{ ($activeDbEnv ?? 'local') === 'production' ? 'bg-primary' : 'bg-success' }} px-2 py-1 fs-8">
                                {{ $activeDbInfo['database'] ?? 'souq_al_sham' }}
                            </span>
                        @endif
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end env-dropdown-menu shadow">
                        <li class="px-3 py-2 border-bottom mb-2">
                            <span class="fw-bold fs-7 text-muted d-block"><i class="fa-solid fa-server me-1"></i> اختيار سيرفر وقاعدة البيانات:</span>
                        </li>
                        
                        <!-- Local DB Option -->
                        <li>
                            <a href="{{ route('admin.switchEnvironment', 'local') }}" 
                               class="env-item {{ ($activeDbEnv ?? 'local') === 'local' ? 'active' : '' }}">
                                <div class="d-flex align-items-center gap-2">
                                    <div class="stat-icon bg-success-subtle text-success" style="width: 38px; height: 38px; font-size: 1.1rem;">
                                        <i class="fa-solid fa-laptop-code"></i>
                                    </div>
                                    <div>
                                        <span class="fw-bold d-block fs-7 text-dark">سيرفر التطوير المحلي (Local)</span>
                                        <small class="text-muted fs-8">127.0.0.1 • souq_al_sham</small>
                                    </div>
                                </div>
                                @if(($activeDbEnv ?? 'local') === 'local')
                                    @if($dbConnected ?? true)
                                        <span class="badge bg-success-subtle text-success fs-8 fw-bold px-2 py-1">
                                            <i class="fa-solid fa-check me-1"></i> متصل
                                        </span>
                                    @else
                                        <span class="badge bg-danger-subtle text-danger fs-8 fw-bold px-2 py-1">
                                            <i class="fa-solid fa-triangle-exclamation me-1"></i> غير متصل
                                        </span>
                                    @endif
                                @else
                                    <span class="btn btn-sm btn-outline-secondary py-0 px-2 fs-8">اتصال</span>
                                @endif
                            </a>
                        </li>

                        <!-- Hostinger Production DB Option -->
                        <li class="mt-1">
                            <a href="{{ route('admin.switchEnvironment', 'production') }}" 
                               class="env-item {{ ($activeDbEnv ?? 'local') === 'production' ? 'active prod-active' : '' }}">
                                <div class="d-flex align-items-center gap-2">
                                    <div class="stat-icon bg-primary-subtle text-primary" style="width: 38px; height: 38px; font-size: 1.1rem;">
                                        <i class="fa-solid fa-cloud"></i>
                                    </div>
                                    <div>
                                        <span class="fw-bold d-block fs-7 text-dark">السيرفر الحقيقي (Hostinger Live)</span>
                                        <small class="text-muted fs-8">srv1941.hstgr.io • u762212316_Lelbai</small>
                                    </div>
                                </div>
                                @if(($activeDbEnv ?? 'local') === 'production')
                                    @if($dbConnected ?? true)
                                        <span class="badge bg-primary-subtle text-primary fs-8 fw-bold px-2 py-1">
                                            <i class="fa-solid fa-check me-1"></i> متصل
                                        </span>
                                    @else
                                        <span class="badge bg-danger-subtle text-danger fs-8 fw-bold px-2 py-1">
                                            <i class="fa-solid fa-triangle-exclamation me-1"></i> غير متصل
                                        </span>
                                    @endif
                                @else
                                    <span class="btn btn-sm btn-outline-primary py-0 px-2 fs-8">اتصال</span>
                                @endif
                            </a>
                        </li>
                    </ul>
                </div>

                <!-- Quick Switch Action Button -->
                <a href="{{ route('admin.switchEnvironment', ($activeDbEnv ?? 'local') === 'production' ? 'local' : 'production') }}" 
                   class="btn btn-sm {{ ($activeDbEnv ?? 'local') === 'production' ? 'btn-outline-success' : 'btn-outline-primary' }} rounded-pill px-3 py-2 fw-bold d-flex align-items-center gap-1 shadow-sm"
                   title="التبديل الفوري بين السيرفرين">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>تبديل إلى {{ ($activeDbEnv ?? 'local') === 'production' ? 'المحلي' : 'الحقيقي' }}</span>
                </a>
            </div>
        </div>

        @if(session('success'))
            <div class="alert alert-success alert-dismissible fade show rounded-3 shadow-sm mb-4 fw-bold" role="alert">
                <i class="fa-solid fa-circle-check me-2"></i> {{ session('success') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        @endif

        @if(session('error'))
            <div class="alert alert-danger alert-dismissible fade show rounded-3 shadow-sm mb-4 fw-bold" role="alert">
                <i class="fa-solid fa-triangle-exclamation me-2"></i> {{ session('error') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        @endif

        @if(session('info'))
            <div class="alert alert-info alert-dismissible fade show rounded-3 shadow-sm mb-4 fw-bold" role="alert">
                <i class="fa-solid fa-circle-info me-2"></i> {{ session('info') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        @endif

        @if(isset($dbConnected) && !$dbConnected)
            <div class="card border-0 shadow-sm rounded-4 mb-4" style="background: linear-gradient(135deg, #FEF2F2 0%, #FFF5F5 100%); border-right: 6px solid #DC2626 !important;">
                <div class="card-body p-4">
                    <div class="d-flex align-items-start gap-3">
                        <div class="stat-icon bg-danger text-white rounded-3 shadow-sm flex-shrink-0" style="width: 48px; height: 48px; font-size: 1.4rem;">
                            <i class="fa-solid fa-triangle-exclamation"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-1">
                                <h5 class="fw-bold text-danger mb-0">
                                    تنبيه: تعذر الاتصال بقاعدة بيانات {{ ($activeDbEnv ?? 'local') === 'production' ? 'السيرفر الحقيقي (Hostinger)' : 'سيرفر التطوير المحلي (Local)' }}
                                </h5>
                                <span class="badge bg-danger fs-8 fw-semibold px-2 py-1">انقطاع الاتصال ⚠️</span>
                            </div>
                            <p class="text-secondary mb-2 fs-7" style="line-height: 1.6;">
                                <strong>تفاصيل الخطأ:</strong> <code class="text-danger fw-bold" style="word-break: break-all;">{{ $dbError }}</code>
                            </p>
                            
                            @if(($activeDbEnv ?? 'local') === 'local')
                                <div class="p-2 rounded-3 bg-white bg-opacity-75 border border-danger-subtle mb-3 fs-8 text-dark">
                                    <i class="fa-solid fa-lightbulb text-warning me-1"></i> <strong>سبب شائع:</strong> خادم MySQL في برنامج <strong>XAMPP</strong> مغلق أو لم يتم تشغيله على جهازك. يمكنك تشغيل MySQL في XAMPP أو الضغط على الزر أدناه للتبديل للعمل على السيرفر الحقيقي (Hostinger) مباشرة.
                                </div>
                            @else
                                <div class="p-2 rounded-3 bg-white bg-opacity-75 border border-danger-subtle mb-3 fs-8 text-dark">
                                    <i class="fa-solid fa-lightbulb text-warning me-1"></i> <strong>سبب شائع:</strong> استضافة <strong>Hostinger</strong> تتطلب السماح بالاتصال عن بُعد (Remote MySQL). تأكد من الدخول إلى لوحة الاستضافة hPanel ⬅️ Remote MySQL وإضافة الرمز <code>%</code> في خانة IP.
                                </div>
                            @endif

                            <div class="d-flex align-items-center gap-2 flex-wrap">
                                <a href="{{ route('admin.switchEnvironment', ($activeDbEnv ?? 'local') === 'production' ? 'local' : 'production') }}" 
                                   class="btn btn-sm btn-danger fw-bold rounded-pill px-3 py-2 shadow-sm">
                                    <i class="fa-solid fa-arrows-rotate me-1"></i> التبديل فوراً إلى {{ ($activeDbEnv ?? 'local') === 'production' ? 'السيرفر المحلي (Local DB)' : 'السيرفر الحقيقي (Hostinger)' }}
                                </a>
                                <a href="javascript:location.reload()" class="btn btn-sm btn-outline-secondary rounded-pill px-3 py-2 fw-semibold">
                                    <i class="fa-solid fa-rotate-right me-1"></i> إعادة المحاولة
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        @endif

        @yield('content')
    </main>

    <!-- Bootstrap JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
