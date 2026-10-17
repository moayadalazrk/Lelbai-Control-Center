<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Listing extends Model
{
    use HasFactory;

    protected $fillable = [
        'uuid',
        'user_id',
        'category_id',
        'city_id',
        'title',
        'slug',
        'description',
        'price',
        'old_price',
        'currency',
        'condition',
        'status',
        'rejection_reason',
        'previous_rejection_reason',
        'is_featured',
        'is_scraped',
        'source_type',
        'source_url',
        'contact_phone',
        'show_phone',
        'views_count',
        'impressions_count',
        'attributes',
        'ai_status',
        'ai_summary',
        'ai_flags',
        'ai_rejection_suggestion',
        'ai_reviewed_at',
        'published_at',
        'expires_at',
    ];

    protected $casts = [
        'is_featured' => 'boolean',
        'is_scraped' => 'boolean',
        'show_phone' => 'boolean',
        'price' => 'decimal:2',
        'old_price' => 'decimal:2',
        'views_count' => 'integer',
        'impressions_count' => 'integer',
        'attributes' => 'array',
        'ai_flags' => 'array',
        'ai_reviewed_at' => 'datetime',
        'published_at' => 'datetime',
        'expires_at' => 'datetime',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    public function city()
    {
        return $this->belongsTo(City::class);
    }

    public function primaryImage()
    {
        return $this->hasOne(ListingImage::class)->where('is_primary', true);
    }

    public function images()
    {
        return $this->hasMany(ListingImage::class)->orderBy('sort_order', 'asc');
    }
}
