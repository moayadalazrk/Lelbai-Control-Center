<?php

namespace App\Services;

use App\Models\Listing;
use App\Models\Notification;
use App\Models\Setting;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AiModerationService
{
    /**
     * Gemini API Key.
     */
    protected static function getApiKey(): string
    {
        $dbKey = Setting::get('gemini_api_key');
        if (!empty($dbKey)) {
            return trim($dbKey);
        }
        $envKey = env('GEMINI_API_KEY', '');
        return trim($envKey);
    }

    /**
     * Supported models with automatic fallback (ordered from Strongest to Lightest).
     */
    protected static $models = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b',
    ];

    /**
     * System & moderation rules prompt in Arabic.
     */
    protected static function getSystemRules(): string
    {
        return <<<PROMPT
أنت نظام رقابة وتدقيق آلي صارم ومحدد لمنصة إعلانات مبوبة في سوريا (للبيع - lelbai).
مهمتك تنحصر فقط في فحص محتوى الإعلان (النصوص والصور المرفقة) للتأكد من خلوه من المحظورات المنصوص عليها أدناه حصراً، واستخراج **جميع المخالفات المرصودة بلا استثناء**.

قواعد الرقابة والضوابط الإلزامية:
1. 📸 ضوابط الصور وخصوصية الأشخاص والوثائق:
   - 🚫 النساء (Women): تشديد قاطع وممنوع تماماً؛ يُحظر أي ظهور للنساء أو وجوههن أو أجسادهن أو عارضات الأزياء (مخالفة: woman_in_photos).
   - 🚫 الرجال (Men): تشديد خفيف؛ إذا كان شخص عابر أو بعيد أو غير مقصود في الخلفية (أثناء تصوير سيارة أو شارع أو عقار) يُقبل وعادي، أما إذا كانت صورة سيلفي مقصودة أو شخصية واضحة جداً لصاحب الإعلان فتُرفض (مخالفة: man_selfie_in_photos).
   - 🔒 الوثائق الرسمية وجوازات السفر والهويات: ممنوع منعاً باتاً نشر صور جوازات السفر أو البطاقات الشخصية أو الهويات أو المستندات الحساسة حفظاً للأمان والخصوصية (مخالفة: official_documents_or_passports).

2. 🚫 ضوابط السلع المحظورة وأحكام الشريعة الإسلامية:
   - 🚫 الأسلحة الحقيقية: ممنوعة تماماً وتشمل البنادق والمسدسات والذخائر الحية (ألعاب الأطفال ومجسمات البلاستيك مسموحة).
   - 🚫 المحرمات: الخنزير ولحومه ومشتقاته، المشروبات الكحولية والمسكرات (ممنوعة تماماً).
   - 🚫 الأدوات والآلات الموسيقية: ممنوعة تماماً (تشمل العود، الغيتار، البيانو، الكمان، الطبول، الدفوف، الميكروفونات الغنائية، إلخ).
   - 🚫 الألعاب الإلكترونية: أسطوانات وأكواد وحسابات الألعاب مثل حسابات ببجي وبلايستيشن ألعاب (ممنوعة).
   - 🚫 المحتوى الإجرامي والاتجار بالبشر: أي إعلان صريح لـ (عرض أشخاص، أطفال للتبني/البيع، مخدرات، روابط احتيالية، ألفاظ مخلة) = مخالفة صارمة (مخالفة: prohibited_goods_or_human_trafficking).

⛔ أشياء مسموحة تماماً ويُمنع رفض الإعلان بسببها (DO NOT REJECT FOR THESE):
- ✅ عدم تطابق الصور مع العنوان أو الوصف: مسموح ومقبول ولا يعتبر مخالفة إطلاقاً (مثلاً: إعلان عنوانه سيارة وتوجد فيه صور ملابس أو أجهزة أو ألعاب أخرى). لا ترفض الإعلان نهائياً بسبب عدم تطابق الصور مع العنوان أو القسم؛ مهمتك فقط فحص خلو الصور والنصوص من الممنوعات المحددة أعلاه.
- ✅ الأطفال: ظهور الأطفال في الصور مسموح وتمريره عادي.
- ✅ الأجهزة الإلكترونية: أجهزة البلايستيشن والإكسبوكس والكمبيوترات والهواتف والشاشات مسموحة ومقبولة 100%.
- ✅ ألعاب الأطفال العادية والدمى والمجسمات البلاستيكية: مسموحة تماماً.

⚠️ تنبيه وإلزام حاسم بخصوص تعدد المخالفات (Comprehensive Multi-Violation Rule):
إذا كان الإعلان يحتوي على أكثر من مخالفة حقيقية في نفس الوقت (مثلاً: صورة سيلفي + صور جوازات سفر + آلة موسيقية):
يجب حصر **كافة المخالفات المرصودة بلا استثناء** ووضعها كاملة في مصفوفة flags، وذكرها كاملة في summary، وصياغة suggested_rejection_reason على شكل **نقاط مرقمة ومفصلة (1) ... (2) ... (3) ...** تشمل كل المخالفات معاً بنص مهذب وشامل حتى يعلم المعلن بكل الأسباب التي تسببت برفض الإعلان.

المطلوب:
أرجع إجابتك حصراً بصيغة JSON صريحة بدون أي نصوص إضافية خارج الـ JSON:

إذا كان الإعلان سليماً:
{
  "is_safe": true,
  "status": "safe",
  "flags": [],
  "summary": "الإعلان سليم ومطابق للشروط بالكامل",
  "suggested_rejection_reason": null
}

إذا كان الإعلان مخالفاً:
{
  "is_safe": false,
  "status": "flagged",
  "flags": ["man_selfie_in_photos", "official_documents_or_passports", "prohibited_goods_or_human_trafficking"],
  "summary": "تم رصد المخالفات التالية: (1) وجود صور شخصية (سيلفي)، (2) نشر صور وثائق رسمية...",
  "suggested_rejection_reason": "عذراً تم رفض الإعلان للأسباب التالية: (1) وجود صور شخصية (سيلفي) للمعلن وهي مخالفة للسياسات، (2) مشاركة صور وثائق رسمية (جوازات سفر) مما يعد انتهاكاً لخصوصية البيانات، (3) ..."
}
PROMPT;
    }

    /**
     * Check if automatic AI moderation is enabled in system settings.
     */
    public static function isAutoModerationEnabled(): bool
    {
        $val = Setting::get('ai_auto_moderation_enabled', '1');
        return filter_var($val, FILTER_VALIDATE_BOOLEAN) || $val === '1';
    }

    /**
     * Moderate a newly created listing (review all text and all uploaded photos).
     */
    public static function moderateNewListing(Listing $listing, bool $force = false): array
    {
        if (!$force && !self::isAutoModerationEnabled()) {
            return ['is_safe' => true, 'status' => 'skipped', 'summary' => 'الفحص التلقائي معطل من الإدارة'];
        }

        try {
            $imagesData = [];
            $listing->loadMissing('images');

            foreach ($listing->images as $img) {
                $base64 = self::compressAndEncodeImage($img->image_path);
                if ($base64) {
                    $imagesData[] = $base64;
                }
            }

            $promptText = "إعلان جديد للمراجعة:\n";
            $promptText .= "العنوان: " . ($listing->title ?? 'بدون عنوان') . "\n";
            $promptText .= "الوصف: " . ($listing->description ?? 'بدون وصف') . "\n";
            $promptText .= "السعر: " . ($listing->price ?? 0) . " " . ($listing->currency ?? 'SYP') . "\n";
            $promptText .= "عدد الصور المرفقة المفحوصة: " . count($imagesData) . " صورة\n";

            $result = self::callGeminiApi($promptText, $imagesData);
            self::saveModerationResult($listing, $result);
            return $result;
        } catch (\Throwable $e) {
            Log::error('AI Moderation Error on Listing #' . $listing->id . ': ' . $e->getMessage());
            return ['is_safe' => true, 'status' => 'skipped', 'summary' => 'تعذر الفحص الآلي'];
        }
    }

    /**
     * Moderate only the modified parts of an existing listing (Diff-based economic check).
     */
    public static function moderateListingDiff(Listing $listing, array $changedFields, array $newImagePaths = [], bool $force = false): array
    {
        if (!$force && !self::isAutoModerationEnabled()) {
            return ['is_safe' => true, 'status' => 'skipped', 'summary' => 'الفحص التلقائي معطل من الإدارة'];
        }

        try {
            $hasTitleChanged = in_array('title', $changedFields);
            $hasDescChanged = in_array('description', $changedFields);
            $hasNewImages = !empty($newImagePaths);

            // If nothing moderated changed (e.g. only price or city changed), skip API call entirely!
            if (!$hasTitleChanged && !$hasDescChanged && !$hasNewImages) {
                return ['is_safe' => true, 'status' => $listing->ai_status ?? 'safe', 'summary' => 'لم يتم تعديل النصوص أو الصور'];
            }

            $imagesData = [];
            foreach ($newImagePaths as $imgPath) {
                $base64 = self::compressAndEncodeImage($imgPath);
                if ($base64) {
                    $imagesData[] = $base64;
                }
            }

            $promptText = "تعديل على إعلان قائم (يرجى فحص الأجزاء المعدلة فقط):\n";
            if ($hasTitleChanged) {
                $promptText .= "العنوان المعدل الجديد: " . $listing->title . "\n";
            }
            if ($hasDescChanged) {
                $promptText .= "الوصف المعدل الجديد: " . $listing->description . "\n";
            }
            if ($hasNewImages) {
                $promptText .= "الصور الجديدة المضافة حديثاً فقط: " . count($imagesData) . " صورة\n";
            }

            $result = self::callGeminiApi($promptText, $imagesData);
            self::saveModerationResult($listing, $result);
            return $result;
        } catch (\Throwable $e) {
            Log::error('AI Moderation Diff Error on Listing #' . $listing->id . ': ' . $e->getMessage());
            return ['is_safe' => true, 'status' => 'skipped', 'summary' => 'تعذر الفحص الآلي'];
        }
    }

    /**
     * Direct full scan on-demand (used by Admin Panel button).
     */
    public static function moderateListingDirect(Listing $listing): array
    {
        return self::moderateNewListing($listing, true);
    }

    /**
     * Save AI moderation results and automatically accept or reject the listing immediately!
     */
    protected static function saveModerationResult(Listing $listing, array $result): void
    {
        $status = $result['status'] ?? ($result['is_safe'] ? 'safe' : 'flagged');
        $summary = $result['summary'] ?? null;
        $flags = $result['flags'] ?? [];
        $rejectionSuggestion = $result['suggested_rejection_reason'] ?? null;

        $wasPreviouslyRejected = !empty($listing->previous_rejection_reason) || $listing->status === 'rejected';

        // 🤖 التفعيل الفوري للموافقة أو الرفض التلقائي بناءً على نتيجة الذكاء الاصطناعي
        $newListingStatus = $listing->status;
        $newRejectionReason = $listing->rejection_reason;
        $newPrevRejectionReason = $listing->previous_rejection_reason;
        $publishedAt = $listing->published_at;

        if ($status === 'flagged' && empty($result['is_safe'])) {
            // ❌ رفض الإعلان تلقائياً فوراً فقط في حال وجود مخالفة مؤكدة مرصودة
            $newListingStatus = 'rejected';
            $newRejectionReason = $rejectionSuggestion ?: ($summary ?: 'تم رفض الإعلان لمخالفته شروط وسياسة المنصة.');
            $newPrevRejectionReason = $newRejectionReason;
        } elseif ($status === 'safe' || $status === 'skipped' || !empty($result['is_safe'])) {
            // ✅ قبول ونشر الإعلان تلقائياً فوراً (أو الحفاظ عليه نشطاً إن تعذر الفحص الآلي)
            $newListingStatus = 'active';
            $newRejectionReason = null;
            if (empty($publishedAt)) {
                $publishedAt = now();
            }
        }

        $listing->timestamps = false;
        $listing->update([
            'status' => $newListingStatus,
            'rejection_reason' => $newRejectionReason,
            'previous_rejection_reason' => $newPrevRejectionReason,
            'published_at' => $publishedAt,
            'ai_status' => $status,
            'ai_summary' => $summary,
            'ai_flags' => $flags,
            'ai_rejection_suggestion' => $rejectionSuggestion,
            'ai_reviewed_at' => now(),
        ]);
        $listing->timestamps = true;

        // 🔔 إرسال الإشعارات الفورية للمعلن في حالتي الرفض التلقائي أو القبول بعد التعديل
        if ($listing->user_id) {
            try {
                $rawTitle = $listing->title ?: 'إعلانك';
                $cleanTitle = mb_strimwidth($rawTitle, 0, 45, '...');

                if ($newListingStatus === 'rejected') {
                    $reasonText = $newRejectionReason ? ": \"{$newRejectionReason}\"" : " لمخالفته شروط النشر.";
                    $notifTitle = $wasPreviouslyRejected ? 'تنبيه: تم رفض إعلانك بعد المراجعة ⚠️' : 'تنبيه بخصوص إعلانك ⚠️';
                    $notifBody = $wasPreviouslyRejected 
                        ? "تم رفض التعديلات على إعلانك ({$cleanTitle}){$reasonText}" 
                        : "تم رفض إعلانك ({$cleanTitle}){$reasonText}";

                    Notification::sendToUser(
                        $listing->user_id,
                        $notifTitle,
                        $notifBody,
                        '/listings/' . ($listing->uuid ?: $listing->id)
                    );
                } elseif ($newListingStatus === 'active' && $wasPreviouslyRejected) {
                    Notification::sendToUser(
                        $listing->user_id,
                        'تم قبول إعلانك بعد التعديل ✅',
                        "تهانينا! تمت مراجعة وقبول إعلانك ({$cleanTitle}) بعد تعديل الملاحظات وهو الآن معتمد ونشط.",
                        '/listings/' . ($listing->uuid ?: $listing->id)
                    );
                }
            } catch (\Throwable $e) {
                // Ignore notification errors
            }
        }
    }

    /**
     * Call Gemini API with automatic fallback between models and structured parsing.
     */
    protected static function callGeminiApi(string $promptText, array $imagesBase64 = []): array
    {
        $apiKey = self::getApiKey();
        if (empty($apiKey) || strlen($apiKey) < 20 || str_starts_with($apiKey, 'AQ.')) {
            return [
                'is_safe' => true,
                'status' => 'skipped',
                'flags' => [],
                'summary' => 'تم تجاوز الفحص الآلي لعدم ضبط مفتاح الذكاء الاصطناعي',
                'suggested_rejection_reason' => null
            ];
        }

        $parts = [];

        // 1. Add System Rules + User Prompt
        $parts[] = [
            'text' => self::getSystemRules() . "\n\n" . $promptText
        ];

        // 2. Add compressed images
        foreach ($imagesBase64 as $imgBase64) {
            $parts[] = [
                'inlineData' => [
                    'mimeType' => 'image/jpeg',
                    'data' => $imgBase64
                ]
            ];
        }

        $payload = [
            'contents' => [
                ['parts' => $parts]
            ],
            'generationConfig' => [
                'temperature' => 0.1,
                'maxOutputTokens' => 700,
                'responseMimeType' => 'application/json'
            ]
        ];

        foreach (self::$models as $modelName) {
            try {
                $url = "https://generativelanguage.googleapis.com/v1beta/models/{$modelName}:generateContent?key={$apiKey}";
                $response = Http::withOptions([
                    'curl' => [
                        CURLOPT_IPRESOLVE => CURL_IPRESOLVE_V4,
                        CURLOPT_SSL_VERIFYPEER => false,
                    ]
                ])->timeout(10)->post($url, $payload);

                if ($response->successful()) {
                    $json = $response->json();
                    $rawText = $json['candidates'][0]['content']['parts'][0]['text'] ?? '';
                    $parsed = json_decode(trim($rawText), true);

                    if (is_array($parsed) && isset($parsed['is_safe'])) {
                        return $parsed;
                    }
                }
            } catch (\Throwable $e) {
                // Try next model on failure/timeout
                continue;
            }
        }

        return [
            'is_safe' => true,
            'status' => 'skipped',
            'flags' => [],
            'summary' => 'تعذر الفحص الآلي وبانتظار المراجعة اليدوية',
            'suggested_rejection_reason' => null
        ];
    }

    /**
     * Find image on disk using multiple fallback paths.
     */
    protected static function resolveImageFullPath(string $path): ?string
    {
        $cleanPath = ltrim(str_replace(['storage/', 'public/'], '', $path), '/');
        
        $candidates = [
            storage_path('app/public/' . $cleanPath),
            storage_path('app/' . $cleanPath),
            public_path('storage/' . $cleanPath),
            public_path($path),
            base_path('../frontend/public/' . $cleanPath),
        ];

        foreach ($candidates as $cand) {
            if (file_exists($cand) && is_file($cand)) {
                return $cand;
            }
        }

        return null;
    }

    /**
     * Resize and compress an image file to a lightweight thumbnail (~25-35KB JPEG) in base64.
     */
    protected static function compressAndEncodeImage(?string $relativePath): ?string
    {
        if (empty($relativePath)) {
            return null;
        }

        $fullPath = self::resolveImageFullPath($relativePath);
        if (!$fullPath) {
            return null;
        }

        try {
            $imageInfo = @getimagesize($fullPath);
            if (!$imageInfo) {
                return null;
            }

            $mime = $imageInfo['mime'] ?? '';
            $origWidth = $imageInfo[0];
            $origHeight = $imageInfo[1];

            // Create source image based on type
            $srcImg = null;
            switch ($mime) {
                case 'image/jpeg':
                case 'image/jpg':
                    $srcImg = @imagecreatefromjpeg($fullPath);
                    break;
                case 'image/png':
                    $srcImg = @imagecreatefrompng($fullPath);
                    break;
                case 'image/webp':
                    $srcImg = @imagecreatefromwebp($fullPath);
                    break;
                default:
                    return null;
            }

            if (!$srcImg) {
                return null;
            }

            // Downscale to max 380px on the longest edge for ultra-economic token usage
            $maxDim = 380;
            $ratio = min($maxDim / max($origWidth, 1), $maxDim / max($origHeight, 1));
            $newWidth = (int)max(1, round($origWidth * min(1, $ratio)));
            $newHeight = (int)max(1, round($origHeight * min(1, $ratio)));

            $dstImg = imagecreatetruecolor($newWidth, $newHeight);
            
            // Handle white background for transparent PNG/WebP
            $white = imagecolorallocate($dstImg, 255, 255, 255);
            imagefilledrectangle($dstImg, 0, 0, $newWidth, $newHeight, $white);

            imagecopyresampled($dstImg, $srcImg, 0, 0, 0, 0, $newWidth, $newHeight, $origWidth, $origHeight);

            ob_start();
            imagejpeg($dstImg, null, 65); // 65% quality for ultra small size
            $compressedData = ob_get_clean();

            imagedestroy($srcImg);
            imagedestroy($dstImg);

            return base64_encode($compressedData);
        } catch (\Throwable $e) {
            return null;
        }
    }
}
