@extends('layouts.admin')

@section('content')
<style>
    .btn-toggle-tree[aria-expanded="true"] .transition-icon {
        transform: rotate(-90deg);
    }
    .transition-icon {
        transition: transform 0.2s ease;
        display: inline-block;
    }
    .hover-bg-light:hover {
        background-color: #F1F5F9;
    }
    .style-scroll::-webkit-scrollbar {
        width: 6px;
    }
    .style-scroll::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
</style>

<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-1"><i class="fa-solid fa-layer-group text-success me-2"></i>إدارة التصنيفات والخصائص المخصصة</h4>
        <small class="text-muted">التحكم بالشجرة التفاعلية الأقسام، وتوسيع/طَي الفروع عند الطلب</small>
    </div>
    <div class="d-flex align-items-center gap-2">
        <button type="button" class="btn btn-outline-secondary btn-sm fw-bold px-3" id="btnCollapseAll">
            <i class="fa-solid fa-compress me-1"></i> طَيّ الكل
        </button>
        <button type="button" class="btn btn-outline-primary btn-sm fw-bold px-3" id="btnExpandAll">
            <i class="fa-solid fa-expand me-1"></i> توسيع الكل
        </button>
        <button class="btn btn-success px-4 fw-bold shadow-sm" data-bs-toggle="modal" data-bs-target="#addCategoryModal">
            <i class="fa-solid fa-plus me-1"></i> إضافة قسم رئيسي جديد
        </button>
    </div>
</div>

@if(session('success'))
    <div class="alert alert-success alert-dismissible fade show" role="alert">
        <i class="fa-solid fa-circle-check me-2"></i>{{ session('success') }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
@endif

<!-- Categories Tree View List -->
<div class="categories-master-tree">
    @forelse($mainCategories as $main)
        @include('admin.categories.partials.tree_category_item', [
            'category' => $main,
            'level' => 0
        ])
    @empty
        <div class="card border-0 shadow-sm p-5 text-center text-muted">
            <i class="fa-solid fa-folder-open fa-3x mb-3 text-secondary-subtle"></i>
            <h6 class="fw-bold">لا توجد أي تصنيفات مسجلة حتى الآن.</h6>
            <p class="fs-7 text-muted">اضغط على زر "إضافة قسم رئيسي جديد" بالأعلى لإنشاء أول قسم.</p>
        </div>
    @endforelse
</div>

<!-- Modal: Add Main/New Category -->
<div class="modal fade" id="addCategoryModal" tabindex="-1">
    <div class="modal-dialog">
        <form action="{{ route('categories.store') }}" method="POST" enctype="multipart/form-data" class="modal-content">
            @csrf
            <div class="modal-header">
                <h6 class="modal-title fw-bold">إضافة قسم جديد</h6>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">اسم القسم (بالعربي)</label>
                    <input type="text" name="name_ar" class="form-control" placeholder="مثال: السيارات، العقارات، الجوالات" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7 d-block mb-1">الآباء الذي ينتمي إليهم القسم (اتركه فارغاً إذا كان قسماً رئيسياً):</label>
                    <div class="p-2 border rounded bg-light style-scroll" style="max-height: 220px; overflow-y: auto;">
                        @include('admin.categories.partials.parent_tree_item', [
                            'categories' => $treeCategories,
                            'excludeId' => null,
                            'selectedIds' => [],
                            'prefix' => 'add_main'
                        ])
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">رفع أيقونة/صورة مخصصة للقسم (SVG, PNG, JPG)</label>
                    <input type="file" name="icon_file" accept=".svg,.png,.jpg,.jpeg,.webp" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">أو اسم الأيقونة (FontAwesome)</label>
                    <input type="text" name="icon" class="form-control" placeholder="مثال: fa-car, fa-mobile-screen">
                </div>
                <div class="form-check form-switch mb-2">
                    <input class="form-check-input" type="checkbox" name="is_active" id="activeMain" checked>
                    <label class="form-check-input-label fw-bold fs-7" for="activeMain">تفعيل القسم فوراً</label>
                </div>
            </div>
            <div class="modal-footer">
                <button type="submit" class="btn btn-success fw-bold px-4">إضافة القسم</button>
            </div>
        </form>
    </div>
</div>

<!-- Shared Modal: Add Subcategory -->
<div class="modal fade" id="sharedAddSubModal" tabindex="-1">
    <div class="modal-dialog">
        <form action="{{ route('categories.store') }}" method="POST" enctype="multipart/form-data" class="modal-content">
            @csrf
            <div class="modal-header">
                <h6 class="modal-title fw-bold" id="sharedAddSubTitle">إضافة قسم فرعي</h6>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">اسم القسم الفرعي (بالعربي)</label>
                    <input type="text" name="name_ar" class="form-control" placeholder="مثال: سوناتا، كامري" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7 d-block mb-1">الآباء الذي ينتمي إليهم القسم:</label>
                    <div class="p-2 border rounded bg-light style-scroll" style="max-height: 220px; overflow-y: auto;">
                        @include('admin.categories.partials.parent_tree_item', [
                            'categories' => $treeCategories,
                            'excludeId' => null,
                            'selectedIds' => [],
                            'prefix' => 'shared_addsub'
                        ])
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">رفع أيقونة/صورة مخصصة للقسم</label>
                    <input type="file" name="icon_file" accept=".svg,.png,.jpg,.jpeg,.webp" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">أو اسم الأيقونة (FontAwesome)</label>
                    <input type="text" name="icon" class="form-control" placeholder="مثال: fa-car">
                </div>
                <div class="form-check form-switch mb-2">
                    <input class="form-check-input" type="checkbox" name="is_active" id="activeSubShared" checked>
                    <label class="form-check-input-label fw-bold fs-7" for="activeSubShared">تفعيل القسم فوراً</label>
                </div>
            </div>
            <div class="modal-footer">
                <button type="submit" class="btn btn-primary fw-bold px-4">حفظ القسم الفرعي</button>
            </div>
        </form>
    </div>
</div>

<!-- Shared Modal: Edit Category -->
<div class="modal fade" id="sharedEditModal" tabindex="-1">
    <div class="modal-dialog">
        <form id="sharedEditForm" action="" method="POST" enctype="multipart/form-data" class="modal-content">
            @csrf
            @method('PUT')
            <div class="modal-header">
                <h6 class="modal-title fw-bold" id="sharedEditTitle">تعديل القسم</h6>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">اسم القسم (بالعربي)</label>
                    <input type="text" name="name_ar" id="editNameAr" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7 d-block mb-1">الآباء الذي ينتمي إليهم القسم:</label>
                    <div class="p-2 border rounded bg-light style-scroll" style="max-height: 220px; overflow-y: auto;">
                        @include('admin.categories.partials.parent_tree_item', [
                            'categories' => $treeCategories,
                            'excludeId' => null,
                            'selectedIds' => [],
                            'prefix' => 'shared_edit'
                        ])
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">رفع أيقونة/صورة مخصصة للقسم</label>
                    <input type="file" name="icon_file" accept=".svg,.png,.jpg,.jpeg,.webp" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">أو اسم الأيقونة (FontAwesome)</label>
                    <input type="text" name="icon" id="editIcon" class="form-control">
                </div>
                <div class="form-check form-switch mb-2">
                    <input class="form-check-input" type="checkbox" name="is_active" id="editIsActive">
                    <label class="form-check-input-label fw-bold fs-7" for="editIsActive">تفعيل القسم</label>
                </div>
            </div>
            <div class="modal-footer">
                <button type="submit" class="btn btn-primary fw-bold px-4">حفظ التعديلات</button>
            </div>
        </form>
    </div>
</div>

<!-- Shared Modal: Specs & Filters -->
<div class="modal fade" id="sharedSpecsModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h6 class="modal-title fw-bold" id="sharedSpecsTitle">⚙️ الخصائص والمواصفات المخصصة</h6>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="sharedSpecsBody">
                <div class="text-center py-4">
                    <div class="spinner-border text-success" role="status"></div>
                    <p class="mt-2 text-muted fs-7">جاري تحميل الخصائص والمواصفات...</p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {

    // 1. Add Subcategory Button Listener
    document.querySelectorAll('.btn-action-addsub').forEach(btn => {
        btn.addEventListener('click', function () {
            const catId = this.dataset.id;
            const catName = this.dataset.name;

            document.getElementById('sharedAddSubTitle').innerText = 'إضافة قسم فرعي لـ (' + catName + ')';
            
            // Check parent checkbox in shared_addsub tree
            const treeContainer = document.querySelector('#sharedAddSubModal');
            treeContainer.querySelectorAll('.parent-checkbox').forEach(chk => {
                chk.checked = (chk.value == catId);
            });

            const modal = new bootstrap.Modal(document.getElementById('sharedAddSubModal'));
            modal.show();
        });
    });

    // 2. Edit Category Button Listener
    document.querySelectorAll('.btn-action-edit').forEach(btn => {
        btn.addEventListener('click', function () {
            const catId = this.dataset.id;
            const catName = this.dataset.name;
            const catIcon = this.dataset.icon || '';
            const isActive = this.dataset.active == '1';
            const parents = JSON.parse(this.dataset.parents || '[]');

            document.getElementById('sharedEditTitle').innerText = 'تعديل القسم (' + catName + ')';
            document.getElementById('sharedEditForm').action = '/categories/' + catId;
            document.getElementById('editNameAr').value = catName;
            document.getElementById('editIcon').value = catIcon;
            document.getElementById('editIsActive').checked = isActive;

            // Check parent checkboxes in shared_edit tree
            const modalEl = document.getElementById('sharedEditModal');
            modalEl.querySelectorAll('.parent-checkbox').forEach(chk => {
                chk.checked = parents.map(String).includes(String(chk.value));
            });

            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        });
    });

    // 3. Specs / Filters Button Listener (Dynamic Fetch)
    document.querySelectorAll('.btn-action-specs').forEach(btn => {
        btn.addEventListener('click', function () {
            const catId = this.dataset.id;
            const catName = this.dataset.name;

            document.getElementById('sharedSpecsTitle').innerText = '⚙️ الخصائص والمواصفات المخصصة لـ (' + catName + ')';
            const body = document.getElementById('sharedSpecsBody');
            body.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-success" role="status"></div>
                    <p class="mt-2 text-muted fs-7">جاري تحميل الخصائص والمواصفات...</p>
                </div>
            `;

            const modal = new bootstrap.Modal(document.getElementById('sharedSpecsModal'));
            modal.show();

            // Fetch filters data via AJAX
            fetch('/categories/' + catId + '/filters-data')
                .then(res => res.json())
                .then(data => {
                    renderSpecsContent(catId, catName, data.filters, data.inherited_filters);
                })
                .catch(err => {
                    body.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء تحميل الخصائص.</div>';
                });
        });
    });

    function renderSpecsContent(catId, catName, filters, inheritedFilters) {
        const body = document.getElementById('sharedSpecsBody');
        let html = '';

        // Direct filters list
        html += `<div class="mb-4">
            <h6 class="fw-bold fs-7 text-dark mb-2"><i class="fa-solid fa-list-check text-success me-1"></i>الخصائص المباشرة المضافة لهذا القسم:</h6>`;

        if (filters && filters.length > 0) {
            filters.forEach(f => {
                let optionsObj = {};
                if (typeof f.options === 'string') {
                    try { optionsObj = JSON.parse(f.options); } catch(e) { optionsObj = {}; }
                } else if (f.options && typeof f.options === 'object') {
                    optionsObj = f.options;
                }

                let detailsHtml = '';
                if (optionsObj.choices && Array.isArray(optionsObj.choices) && optionsObj.choices.length > 0) {
                    detailsHtml = `<div class="d-flex flex-wrap gap-1 mt-2">` + 
                        optionsObj.choices.map(c => `<span class="badge bg-white border text-dark fs-9">${c.label || c}</span>`).join('') + 
                    `</div>`;
                } else if (optionsObj.is_slider || optionsObj.is_range || f.type === 'range') {
                    detailsHtml = `<div class="mt-2 text-muted fs-9">
                        <i class="fa-solid fa-sliders text-success me-1"></i>
                        شريط تمرير: من <strong>${optionsObj.min || 0}</strong> إلى <strong>${(optionsObj.max || 0).toLocaleString()}</strong> ${optionsObj.unit || ''}
                    </div>`;
                }

                let choicesCsv = '';
                if (optionsObj.choices && Array.isArray(optionsObj.choices)) {
                    choicesCsv = optionsObj.choices.map(c => (typeof c === 'object' && c.label ? c.label : c)).join(', ');
                }

                html += `<div class="mb-3 bg-white border rounded shadow-sm p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="fw-bold text-dark me-2 fs-6">${f.label_ar}</span>
                            <span class="badge bg-primary-subtle text-primary me-2">نوع: ${f.type}</span>
                            ${f.sort_order ? `<span class="badge bg-secondary-subtle text-secondary">ترتيب: ${f.sort_order}</span>` : ''}
                        </div>
                        <div class="d-flex gap-1.5">
                            <button type="button" class="btn btn-sm btn-outline-primary" data-bs-toggle="collapse" data-bs-target="#editFilter_${f.id}">
                                <i class="fa-solid fa-pen-to-square me-1"></i> تعديل
                            </button>
                            <form action="/categories/filters/${f.id}" method="POST" onsubmit="return confirm('حذف هذه الخاصية؟');">
                                <input type="hidden" name="_token" value="{{ csrf_token() }}">
                                <input type="hidden" name="_method" value="DELETE">
                                <button type="submit" class="btn btn-sm btn-outline-danger">
                                    <i class="fa-solid fa-trash-can me-1"></i> حذف
                                </button>
                            </form>
                        </div>
                    </div>
                    ${detailsHtml}

                    <!-- Inline Edit Form -->
                    <div class="collapse mt-3 border-top pt-3" id="editFilter_${f.id}">
                        <form action="/categories/filters/${f.id}" method="POST">
                            <input type="hidden" name="_token" value="{{ csrf_token() }}">
                            <input type="hidden" name="_method" value="PUT">
                            <h6 class="fw-bold text-primary mb-2 fs-7">✏️ تعديل الخاصية (${f.label_ar}):</h6>
                            <div class="row g-2">
                                <div class="col-md-5">
                                    <label class="form-label fs-8 fw-bold mb-1">اسم الخاصية (بالعربي)</label>
                                    <input type="text" name="label_ar" class="form-control form-control-sm" value="${f.label_ar}" required>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fs-8 fw-bold mb-1">نوع الإدخال</label>
                                    <select name="type" class="form-select form-select-sm" required onchange="
                                        const isSel = (this.value === 'select' || this.value === 'multiselect');
                                        const isNum = (this.value === 'number');
                                        document.getElementById('editChoicesContainer_${f.id}').style.display = isSel ? 'block' : 'none';
                                        document.getElementById('editNumContainer_${f.id}').style.display = isNum ? 'flex' : 'none';
                                    ">
                                        <option value="select" ${f.type === 'select' ? 'selected' : ''}>خيار واحد (Single Select)</option>
                                        <option value="multiselect" ${f.type === 'multiselect' ? 'selected' : ''}>خيارات متعددة (Multi-select)</option>
                                        <option value="number" ${f.type === 'number' || f.type === 'range' ? 'selected' : ''}>رقم / سلايدر (Number/Range)</option>
                                        <option value="text" ${f.type === 'text' ? 'selected' : ''}>نص (Text)</option>
                                        <option value="boolean" ${f.type === 'boolean' ? 'selected' : ''}>سؤال نعم / لا</option>
                                    </select>
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label fs-8 fw-bold mb-1">الترتيب</label>
                                    <input type="number" name="sort_order" class="form-control form-control-sm" value="${f.sort_order || 0}">
                                </div>
                            </div>

                            <!-- Choices for Select/Multiselect -->
                            <div class="mt-2" id="editChoicesContainer_${f.id}" style="display: ${(f.type === 'select' || f.type === 'multiselect') ? 'block' : 'none'};">
                                <label class="form-label fs-8 fw-bold mb-1">الخيارات (افصل بفاصلة , بين الخيارات)</label>
                                <textarea name="raw_options" class="form-control form-control-sm" rows="2">${choicesCsv}</textarea>
                            </div>

                            <!-- Number/Slider options -->
                            <div class="row g-2 mt-1" id="editNumContainer_${f.id}" style="display: ${(f.type === 'number' || f.type === 'range') ? 'flex' : 'none'};">
                                <div class="col-md-4">
                                    <label class="form-label fs-8 fw-bold mb-1">أدنى قيمة (Min)</label>
                                    <input type="number" name="min" class="form-control form-control-sm" value="${optionsObj.min || 0}">
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fs-8 fw-bold mb-1">أقصى قيمة (Max)</label>
                                    <input type="number" name="max" class="form-control form-control-sm" value="${optionsObj.max || ''}">
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fs-8 fw-bold mb-1">الوحدة (Unit)</label>
                                    <input type="text" name="unit" class="form-control form-control-sm" value="${optionsObj.unit || ''}">
                                </div>
                                <div class="col-12">
                                    <div class="form-check form-switch mt-1">
                                        <input class="form-check-input" type="checkbox" name="is_slider" value="1" id="slider_${f.id}" ${optionsObj.is_slider || optionsObj.is_range || f.type === 'range' ? 'checked' : ''}>
                                        <label class="form-check-label fs-8 fw-bold" for="slider_${f.id}">تفعيل شريط التمرير (Slider Bar)</label>
                                    </div>
                                </div>
                            </div>

                            <div class="mt-2 text-end">
                                <button type="submit" class="btn btn-sm btn-primary fw-bold px-3">
                                    <i class="fa-solid fa-check me-1"></i> حفظ التعديل
                                </button>
                            </div>
                        </form>
                    </div>
                </div>`;
            });
        } else {
            html += `<div class="alert alert-light text-muted fs-7 mb-0">لا توجد خصائص مباشرة لهذا القسم بعد. يمكنك إضافة خاصية مخصصة أدناه.</div>`;
        }
        html += `</div>`;

        // Inherited filters list
        if (inheritedFilters && inheritedFilters.length > 0) {
            html += `<div class="mb-4 p-3 bg-warning-subtle border border-warning-subtle rounded">
                <h6 class="fw-bold fs-7 text-warning-emphasis mb-2"><i class="fa-solid fa-sitemap me-1"></i>الخصائص الموروثة من الآباء (تُدعم تلقائياً):</h6>
                <div class="d-flex flex-wrap gap-2">`;
            inheritedFilters.forEach(inh => {
                html += `<div class="bg-white border rounded px-3 py-1.5 shadow-sm">
                    <span class="fw-bold text-dark">${inh.label_ar}</span>
                    <span class="badge bg-secondary-subtle text-secondary ms-1">${inh.type}</span>
                    <small class="text-muted d-block fs-9 mt-0.5">موروثة من: <strong class="text-success">${inh.inherited_from_category_name || ''}</strong></small>
                </div>`;
            });
            html += `</div></div>`;
        }

        html += `<hr>`;

        // Add filter form
        html += `<form action="/categories/${catId}/filters" method="POST">
            <input type="hidden" name="_token" value="{{ csrf_token() }}">
            <h6 class="fw-bold text-success mb-3">+ إضافة خاصية جديدة لهذا القسم:</h6>
            <div class="row g-3">
                <div class="col-md-5">
                    <label class="form-label fs-7 fw-bold">اسم الخاصية (بالعربي)</label>
                    <input type="text" name="label_ar" class="form-control" placeholder="مثال: الموديل، سعة التخزين، نوع الوقود" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label fs-7 fw-bold">نوع الإدخال</label>
                    <select name="type" id="newFilterType" class="form-select" required onchange="
                        const isSelect = (this.value === 'select' || this.value === 'multiselect');
                        const isNum = (this.value === 'number');
                        document.getElementById('choicesContainer').style.display = isSelect ? 'block' : 'none';
                        document.getElementById('numberContainer').style.display = isNum ? 'flex' : 'none';
                    ">
                        <option value="select">خيار واحد من قائمة (Single Select)</option>
                        <option value="multiselect">خيارات متعددة (Multi-select Checkboxes)</option>
                        <option value="number">رقم (Number)</option>
                        <option value="text">نص (Text)</option>
                        <option value="boolean">سؤال نعم / لا</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label fs-7 fw-bold">الترتيب</label>
                    <input type="number" name="sort_order" class="form-control" value="0">
                </div>
            </div>

            <!-- Choices for Select/Multiselect -->
            <div class="mt-3" id="choicesContainer" style="display: block;">
                <label class="form-label fs-7 fw-bold">الخيارات (افصل بين كل خيار بفاصلة , أو سطر جديد)</label>
                <textarea name="raw_options" class="form-control fs-7" rows="2" placeholder="مثال: خيار 1, خيار 2, خيار 3"></textarea>
            </div>

            <!-- Number/Slider options -->
            <div class="row g-3 mt-1" id="numberContainer" style="display: none;">
                <div class="col-md-4">
                    <label class="form-label fs-7 fw-bold">أدنى قيمة (Min)</label>
                    <input type="number" name="min" class="form-control fs-7" placeholder="0">
                </div>
                <div class="col-md-4">
                    <label class="form-label fs-7 fw-bold">أقصى قيمة (Max)</label>
                    <input type="number" name="max" class="form-control fs-7" placeholder="600000">
                </div>
                <div class="col-md-4">
                    <label class="form-label fs-7 fw-bold">الوحدة (Unit)</label>
                    <input type="text" name="unit" class="form-control fs-7" placeholder="مثال: كم، م²">
                </div>
            </div>

            <div class="mt-3 text-end">
                <button type="submit" class="btn btn-success fw-bold px-4">إضافة الخاصية</button>
            </div>
        </form>`;

        body.innerHTML = html;
    }

    // 4. Collapse All & Expand All Handlers
    document.getElementById('btnCollapseAll')?.addEventListener('click', function () {
        document.querySelectorAll('.categories-master-tree .collapse.show').forEach(el => {
            const bsCollapse = bootstrap.Collapse.getInstance(el) || new bootstrap.Collapse(el, { toggle: false });
            bsCollapse.hide();
        });
    });

    document.getElementById('btnExpandAll')?.addEventListener('click', function () {
        document.querySelectorAll('.categories-master-tree .collapse').forEach(el => {
            const bsCollapse = bootstrap.Collapse.getInstance(el) || new bootstrap.Collapse(el, { toggle: false });
            bsCollapse.show();
        });
    });

});
</script>
@endsection
