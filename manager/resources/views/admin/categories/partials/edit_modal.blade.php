<!-- Modal: Edit Category -->
<div class="modal fade" id="editModal-{{ $category->id }}" tabindex="-1">
    <div class="modal-dialog">
        <form action="{{ route('categories.update', $category->id) }}" method="POST" enctype="multipart/form-data" class="modal-content">
            @csrf
            @method('PUT')
            <div class="modal-header">
                <h6 class="modal-title fw-bold">تعديل القسم ({{ $category->name_ar }})</h6>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">اسم القسم (بالعربي)</label>
                    <input type="text" name="name_ar" value="{{ $category->name_ar }}" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7 d-block mb-1">الآباء الذي ينتمي إليهم القسم (اضغط على ▶ لعرض الأبناء واستخدام خيار الآباء المتعددين):</label>
                    <div class="p-2 border rounded bg-light style-scroll" style="max-height: 220px; overflow-y: auto;">
                        @php
                            $currentParentIds = $category->parents->pluck('id')->toArray();
                        @endphp
                        @include('admin.categories.partials.parent_tree_item', [
                            'categories' => $treeCategories,
                            'excludeId' => $category->id,
                            'selectedIds' => $currentParentIds,
                            'prefix' => 'edit_' . $category->id
                        ])
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">رفع أيقونة/صورة مخصصة للقسم (SVG, PNG, JPG)</label>
                    <input type="file" name="icon_file" accept=".svg,.png,.jpg,.jpeg,.webp" class="form-control mb-2">
                    @if(!empty($category->icon) && (str_starts_with($category->icon, '/') || str_starts_with($category->icon, 'http') || str_contains($category->icon, '.')))
                        <div class="p-2 border rounded bg-white d-inline-block">
                            <small class="text-muted d-block mb-1">الأيقونة المرفوعة حالياً:</small>
                            <img src="{{ str_starts_with($category->icon, 'http') ? $category->icon : 'https://lelbai.com/' . ltrim($category->icon, '/') }}" alt="Icon" style="height: 35px; object-fit: contain;">
                        </div>
                    @endif
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold fs-7">أو اسم الأيقونة (FontAwesome)</label>
                    <input type="text" name="icon" value="{{ $category->icon }}" class="form-control" placeholder="مثال: fa-car, fa-mobile-screen">
                </div>
                <div class="form-check form-switch mb-2">
                    <input class="form-check-input" type="checkbox" name="is_active" id="activeEdit{{ $category->id }}" {{ $category->is_active ? 'checked' : '' }}>
                    <label class="form-check-input-label fw-bold fs-7" for="activeEdit{{ $category->id }}">تفعيل القسم</label>
                </div>
            </div>
            <div class="modal-footer">
                <button type="submit" class="btn btn-primary fw-bold px-4">حفظ التعديلات</button>
            </div>
        </form>
    </div>
</div>
