<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class WhatsappMessageLog extends Model
{
    use HasFactory;

    protected $table = 'whatsapp_message_logs';

    protected $fillable = [
        'sender_phone',
        'message_body',
        'extracted_code',
        'matched_verification_id',
        'status',
        'details',
    ];

    public function verification()
    {
        return $this->belongsTo(WhatsappInboundVerification::class, 'matched_verification_id');
    }
}
