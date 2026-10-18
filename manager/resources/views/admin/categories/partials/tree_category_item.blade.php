@php
    $hasChildren = $category->childrenRecursive && $category->childrenRecursive->count() > 0;
    $level = $level ?? 0;
    $collapseId = 'cat_node_' . $category->id;
    $directFiltersCount = $category->filters->count();
    $parentsCount = $category->parents->count();
    $parentIds = $category->parents->pluck('id')->toArray();
@endphp

<div class="category-tree-card mb-2 {{ $level > 0 ? 'ms-3 border-start ps-3' : '' }}">
    <div class="card border shadow-sm rounded-3 overflow-hidden">
        <div class="card-header bg-white py-2.5 px-3 d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center gap-2 flex-grow-1">
                @if($hasChildren)
                    <button 
                        type="button" 
                        class="btn btn-sm btn-light border p-1 me-1 btn-toggle-tree" 
                        data-bs-toggle="collapse" 
                        data-bs-target="#{{ $collapseId }}" 
                        aria-expanded="false"
                        style="width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center;"
                    >
                        <i class="fa-solid fa-chevron-left transition-icon"></i>
                    </button>
                @else
                    <span class="tree-indent-dot text-muted me-1 fs-8 d-inline-block text-center" style="width: 30px;">•</span>
                @endif

                <span class="badge bg-light text-dark border p-2">
                    @if(!empty($category->icon) && (str_starts_with($category->icon, '/') || str_starts_with($category->icon, 'http') || str_contains($category->icon, '.')))
                        <img src="{{ str_starts_with($category->icon, 'http') ? $category->icon : 'https://lelbai.com/' . ltrim($category->icon, '/') }}" alt="Icon" style="width: 24px; height: 24px; object-fit: contain;">
                    @elseif(!empty($category->icon))
                        <i class="fa-solid {{ $category->icon }} text-success fs-6"></i>
                    @else
                        <i class="fa-solid {{ $level === 0 ? 'fa-folder text-warning' : 'fa-folder-tree text-primary' }} fs-6"></i>
                    @endif
                </span>

                <div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="fw-bold text-dark fs-6">{{ $category->name_ar }}</span>
                        @if(!$category->is_active)
                            <span class="badge bg-danger-subtle text-danger fs-9">معطل</span>
                        @endif
                    </div>
                    
                    <div class="d-flex flex-wrap align-items-center gap-1 mt-0.5">
                        @if($hasChildren)
                            <span class="badge bg-secondary-subtle text-secondary fs-9">{{ $category->childrenRecursive->count() }} قسم فرعي</span>
                        @endif

                        @if($directFiltersCount > 0)
                            <span class="badge bg-info-subtle text-info fs-9">{{ $directFiltersCount }} خاصية مباشرة</span>
                        @endif

                        @if($parentsCount > 0)
                            <small class="text-muted fs-9 ms-1">ينتمي لـ: 
                                @foreach($category->parents as $p)
                                    <span class="badge bg-primary-subtle text-primary border border-primary-subtle fs-9 me-0.5">{{ $p->name_ar }}</span>
                                @endforeach
                            </small>
                        @endif
                    </div>
                </div>
            </div>

            <!-- Action Buttons for every level (Uses Shared Modals) -->
            <div class="d-flex align-items-center gap-1.5 ms-2">
                <!-- Add Subcategory Button -->
                <button 
                    class="btn btn-sm btn-outline-primary px-2 py-1 fs-8 btn-action-addsub" 
                    data-id="{{ $category->id }}"
                    data-name="{{ $category->name_ar }}"
                    title="إضافة قسم فرعي تحت هذا القسم"
                >
                    <i class="fa-solid fa-plus me-1"></i> فرعي
                </button>

                <!-- Specs Button -->
                <button 
                    class="btn btn-sm btn-outline-success px-2 py-1 fs-8 btn-action-specs" 
                    data-id="{{ $category->id }}"
                    data-name="{{ $category->name_ar }}"
                    title="الخصائص والمواصفات المخصصة"
                >
                    <i class="fa-solid fa-sliders me-1"></i> الخصائص
                </button>

                <!-- Edit Button -->
                <button 
                    class="btn btn-sm btn-outline-secondary px-2 py-1 fs-8 btn-action-edit" 
                    data-id="{{ $category->id }}"
                    data-name="{{ $category->name_ar }}"
                    data-icon="{{ $category->icon }}"
                    data-sort="{{ $category->sort_order }}"
                    data-active="{{ $category->is_active ? 1 : 0 }}"
                    data-parents='@json($parentIds)'
                    title="تعديل اسم القسم والآباء"
                >
                    <i class="fa-solid fa-pen"></i>
                </button>

                <!-- Delete Button -->
                <form action="{{ route('categories.destroy', $category->id) }}" method="POST" class="d-inline" onsubmit="return confirm('هل أنت متأكد من حذف هذا القسم وكل تفرعاته؟');">
                    @csrf
                    @method('DELETE')
                    <button type="submit" class="btn btn-sm btn-outline-danger px-2 py-1 fs-8" title="حذف القسم">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </form>
            </div>
        </div>

        <!-- Collapsible Body for Direct Filters & Recursive Subcategories -->
        <div id="{{ $collapseId }}" class="collapse">
            <div class="card-body bg-light-subtle p-3 border-top">
                
                <!-- Direct Filters Badges -->
                @if($directFiltersCount > 0)
                    <div class="mb-3 p-2 bg-white rounded border">
                        <span class="fs-8 fw-bold text-muted d-block mb-1">الخصائص المباشرة بهذا القسم:</span>
                        @foreach($category->filters as $filter)
                            <span class="badge bg-success-subtle text-success border border-success-subtle me-1 mb-1 fs-8">
                                {{ $filter->label_ar }} ({{ $filter->type }})
                            </span>
                        @endforeach
                    </div>
                @endif

                <!-- Recursive Subcategories Listing -->
                @if($hasChildren)
                    <div class="subcategories-tree-container">
                        <small class="fw-bold text-muted fs-8 d-block mb-2"><i class="fa-solid fa-diagram-project me-1"></i> الأقسام الفرعية المتفرعة:</small>
                        @foreach($category->childrenRecursive as $child)
                            @include('admin.categories.partials.tree_category_item', [
                                'category' => $child,
                                'level' => $level + 1,
                            ])
                        @endforeach
                    </div>
                @elseif($directFiltersCount == 0)
                    <div class="text-muted fs-8 py-1">لا توجد أفرع فرعية أو خصائص مضافة لهذا القسم. يمكنك إضافة قسم فرعي أو خصائص بواسطة الأزرار بالأعلى.</div>
                @endif

            </div>
        </div>
    </div>
</div>
