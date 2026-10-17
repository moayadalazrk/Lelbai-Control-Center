<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;

class Category extends Model
{
    protected $fillable = [
        'name_ar',
        'slug',
        'icon',
        'sort_order',
        'is_active',
    ];

    protected $casts = [
        'is_active' => 'boolean',
        'sort_order' => 'integer',
    ];

    /**
     * Multiple Parent Categories (Many-to-Many via category_parent)
     */
    public function parents()
    {
        return $this->belongsToMany(Category::class, 'category_parent', 'category_id', 'parent_id');
    }

    /**
     * Multiple Child Categories (Many-to-Many via category_parent)
     */
    public function children()
    {
        return $this->belongsToMany(Category::class, 'category_parent', 'parent_id', 'category_id');
    }

    /**
     * Recursive Child Categories (Many-to-Many via category_parent)
     */
    public function childrenRecursive()
    {
        return $this->children()->with(['childrenRecursive', 'parents', 'filters', 'listings']);
    }

    /**
     * Direct Filters assigned to this category
     */
    public function filters()
    {
        return $this->hasMany(CategoryFilter::class);
    }

    /**
     * Listings in this category
     */
    public function listings()
    {
        return $this->hasMany(Listing::class);
    }

    /**
     * Recursively collect all descendant category IDs (children, grandchildren, etc.)
     */
    public function getAllChildrenIds(&$collected = [])
    {
        foreach ($this->children as $child) {
            if (!in_array($child->id, $collected)) {
                $collected[] = $child->id;
                $child->getAllChildrenIds($collected);
            }
        }

        return array_unique($collected);
    }

    /**
     * Recursively collect all inherited filters from all parent categories (without duplicates)
     */
    public function getAllInheritedFilters($visitedCategoryIds = [])
    {
        // Avoid infinite loops in circular references
        if (in_array($this->id, $visitedCategoryIds)) {
            return collect();
        }
        $visitedCategoryIds[] = $this->id;

        $inheritedFilters = collect();

        foreach ($this->parents as $parent) {
            // Get direct filters from parent
            foreach ($parent->filters as $filter) {
                $filter->inherited_from_category_name = $parent->name_ar;
                $inheritedFilters->push($filter);
            }

            // Get ancestor filters recursively
            $ancestorFilters = $parent->getAllInheritedFilters($visitedCategoryIds);
            foreach ($ancestorFilters as $ancestorFilter) {
                $inheritedFilters->push($ancestorFilter);
            }
        }

        // Key by filter ID or name to remove duplicate inherited filters
        return $inheritedFilters->unique('id')->values();
    }

    protected static function boot()
    {
        parent::boot();
        static::creating(function ($category) {
            if (empty($category->slug)) {
                $category->slug = Str::slug($category->name_ar) ?: 'cat-' . time();
            }
        });
    }
}
