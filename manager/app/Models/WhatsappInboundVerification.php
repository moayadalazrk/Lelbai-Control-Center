<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class WhatsappInboundVerification extends Model
{
    use HasFactory;

    protected $table = 'whatsapp_inbound_verifications';

    protected $fillable = [
        'session_token',
        'phone',
        'name',
        'password',
        'type',
        'verification_code',
        'verification_phrase',
        'is_verified',
        'verified_at',
        'expires_at',
    ];

    protected $casts = [
        'is_verified' => 'boolean',
        'verified_at' => 'datetime',
        'expires_at' => 'datetime',
    ];
}
