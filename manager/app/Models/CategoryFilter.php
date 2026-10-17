<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class CategoryFilter extends Model
{
    protected $fillable = [
        'category_id',
        'name',
        'label_ar',
        'type',
        'options',
        'sort_order',
    ];

    protected $casts = [
        'options' => 'array',
    ];

    public function category()
    {
        return $this->belongsTo(Category::class);
    }
}
