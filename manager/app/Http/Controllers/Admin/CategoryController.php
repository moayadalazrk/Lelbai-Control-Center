<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\CategoryFilter;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class CategoryController extends Controller
{
    public function index()
    {
        $mainCategories = collect();
        $treeCategories = collect();

        try {
            // Root categories (categories that have no parents) with full recursive relations
            $mainCategories = Category::with(['childrenRecursive', 'parents', 'filters', 'listings'])
                ->whereDoesntHave('parents')
                ->orderBy('sort_order', 'asc')
                ->get();

            // Tree structure for parent picker in modals
            $treeCategories = Category::with('childrenRecursive')
                ->whereDoesntHave('parents')
                ->orderBy('name_ar', 'asc')
                ->get();
        } catch (\Throwable $e) {
            // Handled gracefully
        }

        return view('admin.categories.index', compact('mainCategories', 'treeCategories'));
    }

    public function getFilters($id)
    {
        $category = Category::with(['filters'])->findOrFail($id);
        $inheritedFilters = $category->getAllInheritedFilters();

        return response()->json([
            'category' => $category,
            'filters' => $category->filters,
            'inherited_filters' => $inheritedFilters,
        ]);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name_ar' => 'required|string|max:255',
            'parent_ids' => 'nullable|array',
            'parent_ids.*' => 'exists:categories,id',
            'icon' => 'nullable|string|max:255',
            'icon_file' => 'nullable|file|mimes:svg,png,jpg,jpeg,webp|max:2048',
            'sort_order' => 'nullable|integer',
        ]);

        $iconPath = $validated['icon'] ?? null;
        if ($request->hasFile('icon_file')) {
            $file = $request->file('icon_file');
            $filename = time() . '_' . Str::slug($validated['name_ar']) . '.' . $file->getClientOriginalExtension();
            $path = $file->storeAs('categories', $filename, 'public');
            $iconPath = '/storage/' . $path;

            // Sync to backend public storage as well so frontend can serve it instantly
            $backendStoragePath = base_path('../backend/storage/app/public/categories');
            if (!file_exists($backendStoragePath)) {
                @mkdir($backendStoragePath, 0777, true);
            }
            @copy(storage_path('app/public/' . $path), $backendStoragePath . '/' . $filename);
        }

        $category = Category::create([
            'name_ar' => $validated['name_ar'],
            'slug' => Str::slug($validated['name_ar']) ?: 'cat-' . time(),
            'icon' => $iconPath,
            'sort_order' => $validated['sort_order'] ?? 0,
            'is_active' => $request->has('is_active'),
        ]);

        if (!empty($validated['parent_ids'])) {
            $category->parents()->sync($validated['parent_ids']);
        }

        return redirect()->back()->with('success', 'تم إضافة القسم والأيقونة بنجاح.');
    }

    public function update(Request $request, $id)
    {
        $category = Category::findOrFail($id);

        $validated = $request->validate([
            'name_ar' => 'required|string|max:255',
            'parent_ids' => 'nullable|array',
            'parent_ids.*' => 'exists:categories,id',
            'icon' => 'nullable|string|max:255',
            'icon_file' => 'nullable|file|mimes:svg,png,jpg,jpeg,webp|max:2048',
            'sort_order' => 'nullable|integer',
        ]);

        $iconPath = $category->icon;
        if ($request->hasFile('icon_file')) {
            $file = $request->file('icon_file');
            $filename = time() . '_' . Str::slug($validated['name_ar']) . '.' . $file->getClientOriginalExtension();
            $path = $file->storeAs('categories', $filename, 'public');
            $iconPath = '/storage/' . $path;

            // Sync to backend public storage as well so frontend can serve it instantly
            $backendStoragePath = base_path('../backend/storage/app/public/categories');
            if (!file_exists($backendStoragePath)) {
                @mkdir($backendStoragePath, 0777, true);
            }
            @copy(storage_path('app/public/' . $path), $backendStoragePath . '/' . $filename);
        } elseif ($request->filled('icon')) {
            $iconPath = $request->input('icon');
        }

        $category->update([
            'name_ar' => $validated['name_ar'],
            'icon' => $iconPath,
            'sort_order' => $validated['sort_order'] ?? $category->sort_order,
            'is_active' => $request->has('is_active'),
        ]);

        $category->parents()->sync($validated['parent_ids'] ?? []);

        return redirect()->back()->with('success', 'تم تحديث القسم والأيقونة بنجاح.');
    }

    public function destroy($id)
    {
        $category = Category::findOrFail($id);
        $category->parents()->detach();
        $category->children()->detach();
        $category->filters()->delete();
        $category->delete();

        return redirect()->back()->with('success', 'تم حذف القسم بنجاح.');
    }

    public function storeFilter(Request $request, $categoryId)
    {
        $category = Category::findOrFail($categoryId);

        $validated = $request->validate([
            'label_ar' => 'required|string|max:255',
            'type' => 'required|in:select,multiselect,number,text,boolean',
            'raw_options' => 'nullable|string',
            'choices' => 'nullable|array',
            'choices.*' => 'nullable|string',
            'min' => 'nullable|numeric',
            'max' => 'nullable|numeric',
            'is_slider' => 'nullable|boolean',
            'placeholder' => 'nullable|string',
            'sort_order' => 'nullable|integer',
        ]);

        $optionsArray = null;
        $unit = $request->input('unit');
        $unitPosition = $request->input('unit_position', 'after');

        if (in_array($validated['type'], ['select', 'multiselect'])) {
            $choiceIds = $request->input('choice_id', []);
            $choiceLabels = $request->input('choice_label', []);
            $choiceOrders = $request->input('choice_order', []);

            $choices = [];
            $usedIds = [];

            // Fallback for legacy raw_options or choices array
            if (empty($choiceLabels)) {
                if (!empty($request->input('choices')) && is_array($request->input('choices'))) {
                    $choiceLabels = array_values(array_filter(array_map('trim', $request->input('choices'))));
                } elseif (!empty($validated['raw_options'])) {
                    $choiceLabels = array_values(array_filter(array_map('trim', explode(',', $validated['raw_options']))));
                }
            }

            foreach ($choiceLabels as $index => $label) {
                $trimmedLabel = trim($label);
                if (empty($trimmedLabel)) continue;

                if (in_array($trimmedLabel, $usedIds)) continue;
                $usedIds[] = $trimmedLabel;

                $sortOrder = isset($choiceOrders[$index]) ? (int)$choiceOrders[$index] : ($index + 1);

                $choices[] = [
                    'id' => $trimmedLabel,
                    'label' => $trimmedLabel,
                    'sort_order' => $sortOrder,
                ];
            }

            // ترتيب الخيارات تصاعدياً بحسب sort_order
            usort($choices, fn($a, $b) => $a['sort_order'] <=> $b['sort_order']);

            $optionsArray = [
                'choices' => $choices,
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        } elseif ($validated['type'] === 'number') {
            $optionsArray = [
                'min' => $request->filled('min') ? (float)$request->input('min') : null,
                'max' => $request->filled('max') ? (float)$request->input('max') : null,
                'is_slider' => $request->has('is_slider') || $request->input('is_slider') == '1',
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        } elseif ($validated['type'] === 'text') {
            $optionsArray = [
                'placeholder' => $request->input('placeholder'),
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        } elseif ($validated['type'] === 'boolean') {
            $optionsArray = [
                'choices' => ['نعم', 'لا'],
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        }

        CategoryFilter::create([
            'category_id' => $category->id,
            'name' => Str::slug($validated['label_ar']) ?: 'spec_' . time(),
            'label_ar' => $validated['label_ar'],
            'type' => $validated['type'],
            'options' => $optionsArray,
            'sort_order' => (int) $request->input('sort_order', 0),
        ]);

        return redirect()->back()->with('success', 'تم إضافة الخاصية للقسم بنجاح.');
    }

    public function updateFilter(Request $request, $filterId)
    {
        $filter = CategoryFilter::findOrFail($filterId);

        $validated = $request->validate([
            'label_ar' => 'required|string|max:255',
            'type' => 'required|in:select,multiselect,number,text,boolean',
            'raw_options' => 'nullable|string',
            'choices' => 'nullable|array',
            'choices.*' => 'nullable|string',
            'min' => 'nullable|numeric',
            'max' => 'nullable|numeric',
            'is_slider' => 'nullable|boolean',
            'placeholder' => 'nullable|string',
            'sort_order' => 'nullable|integer',
        ]);

        $optionsArray = null;
        $unit = $request->input('unit');
        $unitPosition = $request->input('unit_position', 'after');

        if (in_array($validated['type'], ['select', 'multiselect'])) {
            $choiceIds = $request->input('choice_id', []);
            $choiceLabels = $request->input('choice_label', []);
            $choiceOrders = $request->input('choice_order', []);

            $choices = [];
            $usedIds = [];

            // Fallback for legacy raw_options or choices array
            if (empty($choiceLabels)) {
                if (!empty($request->input('choices')) && is_array($request->input('choices'))) {
                    $choiceLabels = array_values(array_filter(array_map('trim', $request->input('choices'))));
                } elseif (!empty($validated['raw_options'])) {
                    $choiceLabels = array_values(array_filter(array_map('trim', explode(',', $validated['raw_options']))));
                }
            }

            foreach ($choiceLabels as $index => $label) {
                $trimmedLabel = trim($label);
                if (empty($trimmedLabel)) continue;

                if (in_array($trimmedLabel, $usedIds)) continue;
                $usedIds[] = $trimmedLabel;

                $sortOrder = isset($choiceOrders[$index]) ? (int)$choiceOrders[$index] : ($index + 1);

                $choices[] = [
                    'id' => $trimmedLabel,
                    'label' => $trimmedLabel,
                    'sort_order' => $sortOrder,
                ];
            }

            // ترتيب الخيارات تصاعدياً بحسب sort_order
            usort($choices, fn($a, $b) => $a['sort_order'] <=> $b['sort_order']);

            $optionsArray = [
                'choices' => $choices,
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        } elseif ($validated['type'] === 'number') {
            $optionsArray = [
                'min' => $request->filled('min') ? (float)$request->input('min') : null,
                'max' => $request->filled('max') ? (float)$request->input('max') : null,
                'is_slider' => $request->has('is_slider') || $request->input('is_slider') == '1',
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        } elseif ($validated['type'] === 'text') {
            $optionsArray = [
                'placeholder' => $request->input('placeholder'),
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        } elseif ($validated['type'] === 'boolean') {
            $optionsArray = [
                'choices' => ['نعم', 'لا'],
                'unit' => $unit,
                'unit_position' => $unitPosition,
            ];
        }

        $filter->update([
            'label_ar' => $validated['label_ar'],
            'type' => $validated['type'],
            'options' => $optionsArray,
            'sort_order' => (int) $request->input('sort_order', 0),
        ]);

        return redirect()->back()->with('success', 'تم تعديل الخاصية بنجاح.');
    }

    public function destroyFilter($filterId)
    {
        $filter = CategoryFilter::findOrFail($filterId);
        $filter->delete();

        return redirect()->back()->with('success', 'تم حذف الخاصية بنجاح.');
    }
}
