<!-- Modal: Specs / Custom Filters for Category -->
<div class="modal fade" id="specsModal-{{ $category->id }}" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h6 class="modal-title fw-bold">⚙️ الخصائص والمواصفات المخصصة لـ ({{ $category->name_ar }})</h6>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                
                <!-- Direct Filters List -->
                <div class="mb-4">
                    <h6 class="fw-bold fs-7 text-dark mb-2"><i class="fa-solid fa-list-check text-success me-1"></i>الخصائص المباشرة المضافة لهذا القسم:</h6>
                    @forelse($category->filters as $filter)
                        @php
                            $options = $filter->options;
                        @endphp
                        <div class="mb-2 bg-light border rounded p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="fw-bold text-dark me-2">{{ $filter->label_ar }}</span>
                                    <span class="badge bg-primary-subtle text-primary me-2">نوع: {{ $filter->type }}</span>
                                    
                                    @if(!empty($options))
                                        @if(in_array($filter->type, ['select', 'multiselect']))
                                            @php
                                                $rawChoices = isset($options['choices']) ? $options['choices'] : (is_array($options) ? $options : []);
                                                $choiceLabels = array_map(function($c) {
                                                    return is_array($c) ? ($c['label'] ?? $c['id'] ?? '') : $c;
                                                }, $rawChoices);
                                            @endphp
                                            @if(!empty($choiceLabels))
                                                <small class="text-muted d-block mt-1">الخيارات: {{ implode(' ، ', $choiceLabels) }}</small>
                                            @endif
                                        @elseif($filter->type === 'number')
                                            <small class="text-muted d-block mt-1">
                                                @if(isset($options['min'])) النطاق الأدنى: <strong>{{ $options['min'] }}</strong> | @endif
                                                @if(isset($options['max'])) النطاق الأعلى: <strong>{{ $options['max'] }}</strong> | @endif
                                                شريط سحب: <strong>{{ !empty($options['is_slider']) ? 'مفعل ✅' : 'معطل ❌' }}</strong>
                                            </small>
                                        @elseif($filter->type === 'text')
                                            @if(isset($options['placeholder']))
                                                <small class="text-muted d-block mt-1">نص توضيحي: "{{ $options['placeholder'] }}"</small>
                                            @endif
                                        @endif
                                    @endif
                                </div>
                                <div class="d-flex gap-1">
                                    <button type="button" class="btn btn-sm btn-outline-primary" data-bs-toggle="collapse" data-bs-target="#editFilterCollapse-{{ $filter->id }}">
                                        <i class="fa-solid fa-pen-to-square me-1"></i>تعديل
                                    </button>
                                    <form action="{{ route('categories.destroyFilter', $filter->id) }}" method="POST" onsubmit="return confirm('حذف هذه الخاصية؟');">
                                        @csrf
                                        @method('DELETE')
                                        <button type="submit" class="btn btn-sm btn-outline-danger">
                                            <i class="fa-solid fa-xmark"></i>
                                        </button>
                                    </form>
                                </div>
                            </div>

                            <!-- Inline Expandable Edit Form (No Modal Backdrop Freeze) -->
                            <div class="collapse mt-3 w-100" id="editFilterCollapse-{{ $filter->id }}">
                                <form action="{{ route('categories.updateFilter', $filter->id) }}" method="POST" class="p-3 bg-white border border-primary-subtle rounded-3 shadow-sm">
                                    @csrf
                                    @method('PUT')
                                    <h6 class="fw-bold fs-7 text-primary mb-3"><i class="fa-solid fa-pen me-1"></i>تعديل الخاصية: {{ $filter->label_ar }}</h6>
                                    <div class="row g-2">
                                        <div class="col-md-5">
                                            <label class="form-label fs-8 fw-bold">اسم الخاصية (بالعربي)</label>
                                            <input type="text" name="label_ar" class="form-control form-control-sm" value="{{ $filter->label_ar }}" required>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label fs-8 fw-bold">نوع الإدخال</label>
                                            <select name="type" class="form-select form-select-sm" required>
                                                <option value="select" {{ $filter->type === 'select' ? 'selected' : '' }}>خيار واحد من قائمة</option>
                                                <option value="multiselect" {{ $filter->type === 'multiselect' ? 'selected' : '' }}>خيارات متعددة</option>
                                                <option value="number" {{ $filter->type === 'number' ? 'selected' : '' }}>رقم (Number)</option>
                                                <option value="text" {{ $filter->type === 'text' ? 'selected' : '' }}>نص (Text)</option>
                                                <option value="boolean" {{ $filter->type === 'boolean' ? 'selected' : '' }}>سؤال نعم / لا (مثل: دبل، فتحة سقف)</option>
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label fs-8 fw-bold">الترتيب (أولوية العرض)</label>
                                            <input type="number" name="sort_order" class="form-control form-control-sm" value="{{ $filter->sort_order ?? 0 }}" placeholder="مثال: 1 أو 100">
                                        </div>
                                        @if(in_array($filter->type, ['select', 'multiselect']))
                                            <div class="col-12">
                                                <div class="p-3 bg-light border rounded-3 mt-2">
                                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                                        <label class="form-label fs-8 fw-bold text-dark mb-0">خيارات هذه الخاصية (ID / الاسم / الترتيب):</label>
                                                        <button type="button" class="btn btn-sm btn-outline-success fw-bold" onclick="addChoiceRowEdit({{ $filter->id }})">
                                                            <i class="fa-solid fa-plus me-1"></i> إضافة خيار جديد
                                                        </button>
                                                    </div>

                                                    @php
                                                        $rawChoices = isset($options['choices']) ? $options['choices'] : (is_array($options) ? $options : []);
                                                    @endphp

                                                    <div id="editChoicesContainer-{{ $filter->id }}" class="d-flex flex-column gap-2">
                                                        @forelse($rawChoices as $idx => $choice)
                                                            @php
                                                                $cId = is_array($choice) ? ($choice['id'] ?? 'opt_' . ($idx + 1)) : 'opt_' . ($idx + 1);
                                                                $cLabel = is_array($choice) ? ($choice['label'] ?? $choice) : $choice;
                                                                $cOrder = is_array($choice) ? ($choice['sort_order'] ?? ($idx + 1)) : ($idx + 1);
                                                            @endphp
                                                            <div class="row g-2 choice-row align-items-center">
                                                                <div class="col-md-3">
                                                                    <input type="text" name="choice_id[]" class="form-control form-control-sm" value="{{ $cId }}" placeholder="المعرّف ID">
                                                                </div>
                                                                <div class="col-md-6">
                                                                    <input type="text" name="choice_label[]" class="form-control form-control-sm" value="{{ $cLabel }}" placeholder="اسم الخيار">
                                                                </div>
                                                                <div class="col-md-2">
                                                                    <input type="number" name="choice_order[]" class="form-control form-control-sm" value="{{ $cOrder }}" placeholder="الترتيب">
                                                                </div>
                                                                <div class="col-md-1 text-end">
                                                                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeChoiceRow(this)"><i class="fa-solid fa-xmark"></i></button>
                                                                </div>
                                                            </div>
                                                        @empty
                                                            <div class="row g-2 choice-row align-items-center">
                                                                <div class="col-md-3">
                                                                    <input type="text" name="choice_id[]" class="form-control form-control-sm" value="opt_1" placeholder="المعرّف ID">
                                                                </div>
                                                                <div class="col-md-6">
                                                                    <input type="text" name="choice_label[]" class="form-control form-control-sm" placeholder="اسم الخيار">
                                                                </div>
                                                                <div class="col-md-2">
                                                                    <input type="number" name="choice_order[]" class="form-control form-control-sm" value="1" placeholder="الترتيب">
                                                                </div>
                                                                <div class="col-md-1 text-end">
                                                                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeChoiceRow(this)"><i class="fa-solid fa-xmark"></i></button>
                                                                </div>
                                                            </div>
                                                        @endforelse
                                                    </div>
                                                </div>
                                            </div>
                                        @elseif($filter->type === 'number')
                                            <div class="col-md-5">
                                                <label class="form-label fs-8 fw-bold">أقل رقم</label>
                                                <input type="number" name="min" class="form-control form-control-sm" value="{{ $options['min'] ?? '' }}">
                                            </div>
                                            <div class="col-md-5">
                                                <label class="form-label fs-8 fw-bold">أعلى رقم</label>
                                                <input type="number" name="max" class="form-control form-control-sm" value="{{ $options['max'] ?? '' }}">
                                            </div>
                                            <div class="col-md-2 d-flex align-items-end">
                                                <div class="form-check form-switch mb-1">
                                                    <input class="form-check-input" type="checkbox" name="is_slider" value="1" {{ !empty($options['is_slider']) ? 'checked' : '' }}>
                                                    <label class="form-check-label fs-8 fw-bold">سلايدر</label>
                                                </div>
                                            </div>
                                        @elseif($filter->type === 'text')
                                            <div class="col-12">
                                                <label class="form-label fs-8 fw-bold">نص توضيحي (Placeholder)</label>
                                                <input type="text" name="placeholder" class="form-control form-control-sm" value="{{ $options['placeholder'] ?? '' }}">
                                            </div>
                                        @endif
                                        <div class="col-md-7">
                                            <label class="form-label fs-8 fw-bold">الوحدة / النص الثابت (اختياري)</label>
                                            <input type="text" name="unit" class="form-control form-control-sm" value="{{ $options['unit'] ?? '' }}" placeholder="مثال: كم ، م² ، دولار ، ثانية">
                                        </div>
                                        <div class="col-md-5">
                                            <label class="form-label fs-8 fw-bold">موقع النص الثابت</label>
                                            <select name="unit_position" class="form-select form-select-sm">
                                                <option value="after" {{ ($options['unit_position'] ?? 'after') === 'after' ? 'selected' : '' }}>بعد الإجابة (مثال: 50,000 كم)</option>
                                                <option value="before" {{ ($options['unit_position'] ?? '') === 'before' ? 'selected' : '' }}>قبل الإجابة (مثال: $ 500)</option>
                                            </select>
                                        </div>
                                        <div class="col-12 text-end mt-2">
                                            <button type="button" class="btn btn-sm btn-light border me-1" data-bs-toggle="collapse" data-bs-target="#editFilterCollapse-{{ $filter->id }}">إلغاء</button>
                                            <button type="submit" class="btn btn-sm btn-success fw-bold px-3">حفظ التعديلات</button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </div>
                    @empty
                        <div class="alert alert-light text-muted fs-7 mb-0">لا توجد خصائص مباشرة لهذا القسم بعد. يمكنك إضافة خاصية مخصصة أدناه.</div>
                    @endempty
                </div>

                <!-- Inherited Filters List -->
                @php
                    $inheritedFilters = $category->getAllInheritedFilters();
                @endphp
                @if($inheritedFilters->count() > 0)
                    <div class="mb-4 p-3 bg-warning-subtle border border-warning-subtle rounded">
                        <h6 class="fw-bold fs-7 text-warning-emphasis mb-2"><i class="fa-solid fa-sitemap me-1"></i>الخصائص الموروثة من الآباء (تُدعم تلقائياً):</h6>
                        <div class="d-flex flex-wrap gap-2">
                            @foreach($inheritedFilters as $inheritedFilter)
                                <div class="bg-white border rounded px-3 py-1.5 shadow-sm">
                                    <span class="fw-bold text-dark">{{ $inheritedFilter->label_ar }}</span>
                                    <span class="badge bg-secondary-subtle text-secondary ms-1">{{ $inheritedFilter->type }}</span>
                                    <small class="text-muted d-block fs-9 mt-0.5">موروثة من: <strong class="text-success">{{ $inheritedFilter->inherited_from_category_name }}</strong></small>
                                </div>
                            @endforeach
                        </div>
                    </div>
                @endif

                <hr>

                <!-- Add New Filter Form -->
                <form action="{{ route('categories.storeFilter', $category->id) }}" method="POST" id="filterForm-{{ $category->id }}">
                    @csrf
                    <h6 class="fw-bold text-success mb-3">+ إضافة خاصية جديدة لهذا القسم:</h6>
                    
                    <div class="row g-3">
                        <!-- Label -->
                        <div class="col-md-5">
                            <label class="form-label fs-7 fw-bold">اسم الخاصية (بالعربي)</label>
                            <input type="text" name="label_ar" class="form-control" placeholder="مثال: الماركة، سنة الصنع، الممشى، نوع القير" required>
                        </div>

                        <!-- Type Selector -->
                        <div class="col-md-4">
                            <label class="form-label fs-7 fw-bold">نوع الإدخال</label>
                            <select name="type" id="filterTypeSelect-{{ $category->id }}" class="form-select" required onchange="toggleFilterTypeFields({{ $category->id }})">
                                <option value="select">خيار واحد من قائمة (Single Select)</option>
                                <option value="multiselect">خيارات متعددة (Multi-select Checkboxes)</option>
                                <option value="number">رقم (Number)</option>
                                <option value="text">نص (Text)</option>
                                <option value="boolean">سؤال نعم / لا (مثل: دبل، فتحة سقف)</option>
                            </select>
                        </div>

                        <!-- Sort Order -->
                        <div class="col-md-3">
                            <label class="form-label fs-7 fw-bold">الترتيب (أولوية العرض)</label>
                            <input type="number" name="sort_order" class="form-control" value="0" placeholder="مثال: 1 أو 100">
                        </div>

                        <!-- Unit & Unit Position -->
                        <div class="col-md-7">
                            <label class="form-label fs-7 fw-bold">الوحدة / النص الثابت (اختياري)</label>
                            <input type="text" name="unit" class="form-control" placeholder="مثال: كم ، م² ، دولار ، ثانية">
                        </div>
                        <div class="col-md-5">
                            <label class="form-label fs-7 fw-bold">موقع النص الثابت</label>
                            <select name="unit_position" class="form-select">
                                <option value="after">بعد الإجابة (مثال: 50,000 كم)</option>
                                <option value="before">قبل الإجابة (مثال: $ 500)</option>
                            </select>
                        </div>

                        <!-- 1. Text Type Fields -->
                        <div class="col-md-12 type-fields-{{ $category->id }}" id="textFields-{{ $category->id }}" style="display: none;">
                            <div class="p-3 bg-light border rounded">
                                <label class="form-label fs-7 fw-bold">النص التوضيحي داخل الحقل (Placeholder)</label>
                                <input type="text" name="placeholder" class="form-control" placeholder="مثال: اكتب رقم الشاسي هنا">
                            </div>
                        </div>

                        <!-- 2. Number Type Fields -->
                        <div class="col-md-12 type-fields-{{ $category->id }}" id="numberFields-{{ $category->id }}" style="display: none;">
                            <div class="p-3 bg-light border rounded">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label fs-7 fw-bold">أقل رقم (Min Value)</label>
                                        <input type="number" step="any" name="min" class="form-control" placeholder="مثال: 1990 أو 0">
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label fs-7 fw-bold">أعلى رقم (Max Value)</label>
                                        <input type="number" step="any" name="max" class="form-control" placeholder="مثال: 2026 أو 1000000">
                                    </div>
                                    <div class="col-md-12">
                                        <div class="form-check form-switch mt-1">
                                            <input class="form-check-input" type="checkbox" name="is_slider" value="1" id="sliderSwitch-{{ $category->id }}">
                                            <label class="form-check-label fw-bold fs-7" for="sliderSwitch-{{ $category->id }}">أظهر على شكل شريط سحب (Range Slider)</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 3. Select / Multiselect Choices Fields -->
                        <div class="col-md-12 type-fields-{{ $category->id }}" id="choicesFields-{{ $category->id }}">
                            <div class="p-3 bg-light border rounded">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <label class="form-label fs-7 fw-bold mb-0">قائمة الخيارات المتاحة (ID / الاسم / الترتيب):</label>
                                    <button type="button" class="btn btn-sm btn-outline-success fw-bold" onclick="addChoiceRow({{ $category->id }})">
                                        <i class="fa-solid fa-plus me-1"></i> إضافة خيار جديد
                                    </button>
                                </div>

                                <div id="choicesContainer-{{ $category->id }}" class="d-flex flex-column gap-2 mb-2">
                                    <div class="row g-2 choice-row align-items-center">
                                        <div class="col-md-3">
                                            <input type="text" name="choice_id[]" class="form-control form-control-sm" value="opt_1" placeholder="المعرّف ID">
                                        </div>
                                        <div class="col-md-6">
                                            <input type="text" name="choice_label[]" class="form-control form-control-sm" placeholder="اسم الخيار (مثال: جديد)">
                                        </div>
                                        <div class="col-md-2">
                                            <input type="number" name="choice_order[]" class="form-control form-control-sm" value="1" placeholder="الترتيب">
                                        </div>
                                        <div class="col-md-1 text-end">
                                            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeChoiceRow(this)"><i class="fa-solid fa-xmark"></i></button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    <div class="mt-3 text-end">
                        <button type="submit" class="btn btn-success fw-bold px-4">إضافة الخاصية</button>
                    </div>
                </form>

            </div>
        </div>
    </div>
</div>

<script>
    if (typeof window.toggleFilterTypeFields === 'undefined') {
        window.toggleFilterTypeFields = function(categoryId) {
            const selectEl = document.getElementById('filterTypeSelect-' + categoryId);
            if (!selectEl) return;

            const selectedType = selectEl.value;

            // Hide all
            document.querySelectorAll('.type-fields-' + categoryId).forEach(el => el.style.display = 'none');

            // Show relevant
            if (selectedType === 'text') {
                const textEl = document.getElementById('textFields-' + categoryId);
                if (textEl) textEl.style.display = 'block';
            } else if (selectedType === 'number') {
                const numberEl = document.getElementById('numberFields-' + categoryId);
                if (numberEl) numberEl.style.display = 'block';
            } else if (selectedType === 'select' || selectedType === 'multiselect') {
                const choicesEl = document.getElementById('choicesFields-' + categoryId);
                if (choicesEl) choicesEl.style.display = 'block';
            }
        };

        window.addChoiceRow = function(categoryId) {
            const container = document.getElementById('choicesContainer-' + categoryId);
            if (!container) return;

            const count = container.querySelectorAll('.choice-row').length + 1;
            const div = document.createElement('div');
            div.className = 'row g-2 choice-row align-items-center';
            div.innerHTML = `
                <div class="col-md-3">
                    <input type="text" name="choice_id[]" class="form-control form-control-sm" value="opt_${count}" placeholder="المعرّف ID">
                </div>
                <div class="col-md-6">
                    <input type="text" name="choice_label[]" class="form-control form-control-sm" placeholder="اسم الخيار">
                </div>
                <div class="col-md-2">
                    <input type="number" name="choice_order[]" class="form-control form-control-sm" value="${count}" placeholder="الترتيب">
                </div>
                <div class="col-md-1 text-end">
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeChoiceRow(this)"><i class="fa-solid fa-xmark"></i></button>
                </div>
            `;
            container.appendChild(div);
        };

        window.addChoiceRowEdit = function(filterId) {
            const container = document.getElementById('editChoicesContainer-' + filterId);
            if (!container) return;

            const count = container.querySelectorAll('.choice-row').length + 1;
            const div = document.createElement('div');
            div.className = 'row g-2 choice-row align-items-center';
            div.innerHTML = `
                <div class="col-md-3">
                    <input type="text" name="choice_id[]" class="form-control form-control-sm" value="opt_${count}" placeholder="المعرّف ID">
                </div>
                <div class="col-md-6">
                    <input type="text" name="choice_label[]" class="form-control form-control-sm" placeholder="اسم الخيار">
                </div>
                <div class="col-md-2">
                    <input type="number" name="choice_order[]" class="form-control form-control-sm" value="${count}" placeholder="الترتيب">
                </div>
                <div class="col-md-1 text-end">
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeChoiceRow(this)"><i class="fa-solid fa-xmark"></i></button>
                </div>
            `;
            container.appendChild(div);
        };

        window.removeChoiceRow = function(btn) {
            const row = btn.closest('.choice-row');
            if (row) {
                const container = row.parentElement;
                if (container.children.length > 1) {
                    row.remove();
                } else {
                    row.querySelectorAll('input').forEach(i => i.value = '');
                }
            }
        };
    }

    // Trigger toggle on modal show
    document.addEventListener('DOMContentLoaded', function() {
        const modalEl = document.getElementById('specsModal-{{ $category->id }}');
        if (modalEl) {
            modalEl.addEventListener('shown.bs.modal', function() {
                toggleFilterTypeFields({{ $category->id }});
            });
        }
    });
</script>
