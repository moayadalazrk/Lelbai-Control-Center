<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Cache;

class Setting extends Model
{
    protected $fillable = ['key', 'value'];

    public static function get(string $key, $default = null)
    {
        return Cache::remember("sys_setting_{$key}", 3600, function () use ($key, $default) {
            $record = static::where('key', $key)->first();
            return $record ? $record->value : $default;
        });
    }

    public static function set(string $key, $value): void
    {
        static::updateOrCreate(['key' => $key], ['value' => (string)$value]);
        Cache::forget("sys_setting_{$key}");
    }
}
