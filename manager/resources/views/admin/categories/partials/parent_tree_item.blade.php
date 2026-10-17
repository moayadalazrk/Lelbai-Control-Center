@foreach($categories as $c)
    @if(!isset($excludeId) || $c->id !== $excludeId)
        @php
            $hasChildren = $c->childrenRecursive && $c->childrenRecursive->count() > 0;
            $isChecked = isset($selectedIds) && in_array($c->id, $selectedIds);
            $uniqueCollapseId = 'p_tree_' . ($prefix ?? 'modal') . '_' . $c->id;
        @endphp
        <div class="tree-select-node mb-1">
            <div class="d-flex align-items-center justify-content-between py-1 px-2 rounded hover-bg-light border-bottom border-light">
                <div class="d-flex align-items-center gap-1 flex-grow-1">
                    @if($hasChildren)
                        <button 
                            type="button" 
                            class="btn btn-sm btn-link p-0 me-1 text-secondary text-decoration-none btn-toggle-tree" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#{{ $uniqueCollapseId }}" 
                            aria-expanded="false"
                            style="width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center;"
                        >
                            <i class="fa-solid fa-chevron-left fa-xs transition-icon"></i>
                        </button>
                    @else
                        <span class="text-muted me-1 fs-9 d-inline-block text-center" style="width: 20px;">•</span>
                    @endif

                    <div class="form-check m-0">
                        <input 
                            class="form-check-input parent-checkbox" 
                            type="checkbox" 
                            name="parent_ids[]" 
                            value="{{ $c->id }}" 
                            id="chk_{{ $prefix ?? '' }}_{{ $c->id }}" 
                            {{ $isChecked ? 'checked' : '' }}
                        >
                        <label class="form-check-label fs-7 fw-semibold cursor-pointer" for="chk_{{ $prefix ?? '' }}_{{ $c->id }}">
                            {{ $c->name_ar }}
                        </label>
                    </div>
                </div>

                @if($hasChildren)
                    <span class="badge bg-secondary-subtle text-secondary fs-9" style="font-size: 0.65rem;">
                        {{ $c->childrenRecursive->count() }} فرعي
                    </span>
                @endif
            </div>

            @if($hasChildren)
                <div class="collapse ms-3 border-start ps-2 my-1" id="{{ $uniqueCollapseId }}">
                    @include('admin.categories.partials.parent_tree_item', [
                        'categories' => $c->childrenRecursive,
                        'excludeId' => $excludeId ?? null,
                        'selectedIds' => $selectedIds ?? [],
                        'prefix' => $prefix ?? 'modal'
                    ])
                </div>
            @endif
        </div>
    @endif
@endforeach
