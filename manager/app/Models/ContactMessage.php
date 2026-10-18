<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ContactMessage extends Model
{
    use HasFactory;

    protected $table = 'contact_messages';

    protected $fillable = [
        'user_id',
        'name',
        'phone',
        'subject',
        'message',
        'status',
        'admin_notes',
        'ip_address',
        'user_agent',
    ];

    /**
     * Associated user if authenticated.
     */
    public function user()
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Helper for Arabic subject label.
     */
    public function getSubjectLabelAttribute(): string
    {
        return match ($this->subject) {
            'general' => 'استفسار عام',
            'technical' => 'مشكلة فنية بالموقع',
            'report' => 'بلاغ عن إعلان أو احتيال',
            'suggestion' => 'اقتراح لتطوير المنصة',
            'complaint' => 'شكوى رسمية',
            default => $this->subject ?: 'رسالة عامة',
        };
    }

    /**
     * Helper for status label and CSS classes.
     */
    public function getStatusMetaAttribute(): array
    {
        return match ($this->status) {
            'in_progress' => [
                'label' => 'قيد المعالجة',
                'badge' => 'bg-info-subtle text-info',
                'icon' => 'fa-solid fa-spinner',
            ],
            'resolved' => [
                'label' => 'تم الحل والرد',
                'badge' => 'bg-success-subtle text-success',
                'icon' => 'fa-solid fa-check-double',
            ],
            'closed' => [
                'label' => 'مغلق',
                'badge' => 'bg-secondary-subtle text-secondary',
                'icon' => 'fa-solid fa-folder-closed',
            ],
            default => [
                'label' => 'جديد (بانتظار المعالجة)',
                'badge' => 'bg-warning-subtle text-warning',
                'icon' => 'fa-solid fa-clock',
            ],
        };
    }
}
