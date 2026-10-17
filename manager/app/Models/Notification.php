<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Notification extends Model
{
    use HasFactory;

    protected $table = 'notifications';
    
    // Support string UUID / string primary keys used by Laravel notifications
    public $incrementing = false;
    protected $keyType = 'string';

    protected $fillable = [
        'id',
        'type',
        'notifiable_type',
        'notifiable_id',
        'user_id',
        'title',
        'body',
        'is_read',
        'data',
        'read_at',
    ];

    protected $casts = [
        'data' => 'array',
        'read_at' => 'datetime',
    ];

    /**
     * Helper to create a custom notification record safely.
     */
    public static function sendToUser(int|string $userId, string $title, string $body, ?string $link = null, string $type = 'App\\Notifications\\GenericNotification')
    {
        return static::create([
            'id' => (string) \Illuminate\Support\Str::uuid(),
            'type' => $type,
            'notifiable_type' => User::class,
            'notifiable_id' => $userId,
            'user_id' => $userId,
            'title' => $title,
            'body' => $body,
            'is_read' => 0,
            'data' => [
                'title' => $title,
                'body' => $body,
                'message' => $body,
                'link' => $link,
            ],
            'read_at' => null,
        ]);
    }
}
