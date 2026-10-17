<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Admin\DashboardController;
use App\Http\Controllers\Admin\CategoryController;
use App\Http\Controllers\Admin\ListingController;
use App\Http\Controllers\Admin\EnvironmentController;

Route::get('/', [DashboardController::class, 'index'])->name('admin.dashboard');
Route::get('/dashboard', [DashboardController::class, 'index']);

// التبديل بين بيئة التطوير المحلية وسيرفر الإنتاج الحقيقي
Route::get('switch-environment/{env}', [EnvironmentController::class, 'switch'])->name('admin.switchEnvironment');


// إدارة التصنيفات والخصائص المخصصة
Route::resource('categories', CategoryController::class);
Route::get('categories/{id}/filters-data', [CategoryController::class, 'getFilters'])->name('categories.getFilters');
Route::post('categories/{id}/filters', [CategoryController::class, 'storeFilter'])->name('categories.storeFilter');
Route::put('categories/filters/{filterId}', [CategoryController::class, 'updateFilter'])->name('categories.updateFilter');
Route::delete('categories/filters/{filterId}', [CategoryController::class, 'destroyFilter'])->name('categories.destroyFilter');

// إدارة وتدقيق الإعلانات
Route::get('listings', [ListingController::class, 'index'])->name('admin.listings.index');
Route::post('listings/{id}/status', [ListingController::class, 'updateStatus'])->name('admin.listings.updateStatus');
Route::post('listings/{id}/recheck-ai', [ListingController::class, 'recheckAiModeration'])->name('admin.listings.recheckAi');
Route::post('listings/toggle-ai-auto', [ListingController::class, 'toggleAiAutoModeration'])->name('admin.listings.toggleAiAuto');
Route::post('listings/bulk-action', [ListingController::class, 'bulkAction'])->name('admin.listings.bulkAction');
Route::delete('listings/{id}', [ListingController::class, 'destroy'])->name('admin.listings.destroy');

// إدارة وتوثيق الواتساب وبوابة الـ OTP
use App\Http\Controllers\Admin\WhatsAppController;
Route::get('whatsapp', [WhatsAppController::class, 'index'])->name('admin.whatsapp.index');
Route::get('whatsapp/status', [WhatsAppController::class, 'status'])->name('admin.whatsapp.status');
Route::get('whatsapp/sessions', [WhatsAppController::class, 'sessions'])->name('admin.whatsapp.sessions');
Route::post('whatsapp/sessions/create', [WhatsAppController::class, 'createSession'])->name('admin.whatsapp.createSession');
Route::post('whatsapp/sessions/{id}/activate', [WhatsAppController::class, 'activateSession'])->name('admin.whatsapp.activateSession');
Route::post('whatsapp/sessions/{id}/restart', [WhatsAppController::class, 'restartSession'])->name('admin.whatsapp.restartSession');
Route::post('whatsapp/sessions/{id}/pairing-code', [WhatsAppController::class, 'requestPairingCode'])->name('admin.whatsapp.requestPairingCode');
Route::delete('whatsapp/sessions/{id}', [WhatsAppController::class, 'deleteSession'])->name('admin.whatsapp.deleteSession');
Route::post('whatsapp/logout', [WhatsAppController::class, 'logout'])->name('admin.whatsapp.logout');
Route::post('whatsapp/check-number', [WhatsAppController::class, 'checkNumber'])->name('admin.whatsapp.checkNumber');
Route::post('whatsapp/verifications/{id}/manual-verify', [WhatsAppController::class, 'manualVerify'])->name('admin.whatsapp.manualVerify');
Route::delete('whatsapp/verifications/{id}', [WhatsAppController::class, 'destroyVerification'])->name('admin.whatsapp.destroyVerification');

