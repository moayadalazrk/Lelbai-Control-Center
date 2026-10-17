<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;

class User extends Authenticatable
{
    use HasFactory;

    protected $fillable = [
        'name',
        'username',
        'email',
        'phone',
        'password',
        'avatar',
        'role',
        'is_banned',
        'phone_verified_at',
        'last_seen_at',
    ];

    protected $casts = [
        'is_banned' => 'boolean',
        'phone_verified_at' => 'datetime',
        'last_seen_at' => 'datetime',
    ];

    public static function generateUniqueUsername($name, $phone = null, $ignoreUserId = null)
    {
        $raw = trim($name ?? '');
        $slug = preg_replace('/[^\p{L}\p{N}_]+/u', '_', $raw);
        $slug = preg_replace('/_+/', '_', $slug);
        $slug = trim($slug, '_');

        if (empty($slug)) {
            $slug = 'مستخدم';
        }

        $candidate = mb_strtolower($slug);
        $query = static::where('username', $candidate);
        if ($ignoreUserId) {
            $query->where('id', '!=', $ignoreUserId);
        }

        if (!$query->exists()) {
            return $candidate;
        }

        $count = 1;
        while (true) {
            $candidate = mb_strtolower($slug . '_' . $count);
            $chk = static::where('username', $candidate);
            if ($ignoreUserId) {
                $chk->where('id', '!=', $ignoreUserId);
            }
            if (!$chk->exists()) {
                return $candidate;
            }
            $count++;
        }
    }

    public function listings()
    {
        return $this->hasMany(Listing::class);
    }
}
