<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\ContactMessage;
use App\Models\Report;
use App\Models\User;
use App\Models\Listing;
use App\Services\LiveBridgeService;
use Illuminate\Http\Request;
use Illuminate\Pagination\LengthAwarePaginator;

class ComplaintController extends Controller
{
    /**
     * Display complaints, inquiries, and customer reports.
     */
    public function index(Request $request)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $tab = $request->get('tab', 'messages'); // 'messages' or 'reports'
        $status = $request->get('status', 'all');
        $subject = $request->get('subject', 'all');
        $search = trim($request->get('search', ''));
        $page = max(1, (int)$request->get('page', 1));
        $perPage = 15;

        // KPI Counts
        $counts = [
            'total_messages' => 0,
            'pending_messages' => 0,
            'in_progress_messages' => 0,
            'resolved_messages' => 0,
            'total_reports' => 0,
            'pending_reports' => 0,
            'resolved_reports' => 0,
        ];

        $messages = new LengthAwarePaginator([], 0, $perPage, $page, ['path' => $request->url(), 'query' => $request->query()]);
        $reports = new LengthAwarePaginator([], 0, $perPage, $page, ['path' => $request->url(), 'query' => $request->query()]);

        if ($activeEnv === 'production') {
            try {
                // 1. KPI Counts via Bridge with Smart Caching (5 minutes)
                $kpiRows = \Illuminate\Support\Facades\Cache::remember('complaint_kpis', 300, function () {
                    return LiveBridgeService::query("
                        SELECT 
                            (SELECT COUNT(*) FROM contact_messages) as total_messages,
                            (SELECT COUNT(*) FROM contact_messages WHERE status = 'pending') as pending_messages,
                            (SELECT COUNT(*) FROM contact_messages WHERE status = 'in_progress') as in_progress_messages,
                            (SELECT COUNT(*) FROM contact_messages WHERE status = 'resolved') as resolved_messages,
                            (SELECT COUNT(*) FROM reports) as total_reports,
                            (SELECT COUNT(*) FROM reports WHERE status = 'pending') as pending_reports,
                            (SELECT COUNT(*) FROM reports WHERE status = 'resolved') as resolved_reports
                    ");
                });

                if (!empty($kpiRows[0])) {
                    $row = (array)$kpiRows[0];
                    foreach ($counts as $k => $v) {
                        $counts[$k] = (int)($row[$k] ?? 0);
                    }
                }

                // 2. Fetch Messages
                if ($tab === 'messages') {
                    $whereClauses = ["1=1"];
                    $bindings = [];

                    if ($status && $status !== 'all') {
                        $whereClauses[] = "c.status = ?";
                        $bindings[] = $status;
                    }
                    if ($subject && $subject !== 'all') {
                        $whereClauses[] = "c.subject = ?";
                        $bindings[] = $subject;
                    }
                    if (!empty($search)) {
                        $whereClauses[] = "(c.name LIKE ? OR c.phone LIKE ? OR c.message LIKE ? OR c.admin_notes LIKE ?)";
                        $like = "%{$search}%";
                        $bindings[] = $like;
                        $bindings[] = $like;
                        $bindings[] = $like;
                        $bindings[] = $like;
                    }

                    $whereSql = implode(' AND ', $whereClauses);

                    // Count total matching
                    $countRows = LiveBridgeService::query("SELECT COUNT(*) as total FROM contact_messages c WHERE {$whereSql}", $bindings);
                    $totalMessages = (int)($countRows[0]->total ?? $countRows[0]['total'] ?? 0);

                    // Fetch page
                    $offset = ($page - 1) * $perPage;
                    $querySql = "
                        SELECT c.*, u.name as user_name, u.phone as user_phone, u.username as user_username
                        FROM contact_messages c
                        LEFT JOIN users u ON c.user_id = u.id
                        WHERE {$whereSql}
                        ORDER BY c.created_at DESC, c.id DESC
                        LIMIT {$perPage} OFFSET {$offset}
                    ";
                    $rows = LiveBridgeService::query($querySql, $bindings);

                    $collection = collect($rows)->map(function ($r) {
                        $row = (array)$r;
                        $msg = new ContactMessage();
                        $msg->forceFill($row);
                        $msg->id = (int)$row['id'];
                        if (!empty($row['user_id'])) {
                            $user = new User(['name' => $row['user_name'] ?? '', 'phone' => $row['user_phone'] ?? '', 'username' => $row['user_username'] ?? '']);
                            $user->id = (int)$row['user_id'];
                            $msg->setRelation('user', $user);
                        }
                        return $msg;
                    });

                    $messages = new LengthAwarePaginator($collection, $totalMessages, $perPage, $page, [
                        'path' => $request->url(),
                        'query' => $request->query(),
                    ]);
                } else {
                    // Fetch Reports
                    $whereClauses = ["1=1"];
                    $bindings = [];

                    if ($status && $status !== 'all') {
                        $whereClauses[] = "r.status = ?";
                        $bindings[] = $status;
                    }
                    if (!empty($search)) {
                        $whereClauses[] = "(r.reason LIKE ? OR r.details LIKE ?)";
                        $like = "%{$search}%";
                        $bindings[] = $like;
                        $bindings[] = $like;
                    }

                    $whereSql = implode(' AND ', $whereClauses);

                    $countRows = LiveBridgeService::query("SELECT COUNT(*) as total FROM reports r WHERE {$whereSql}", $bindings);
                    $totalReports = (int)($countRows[0]->total ?? $countRows[0]['total'] ?? 0);

                    $offset = ($page - 1) * $perPage;
                    $querySql = "
                        SELECT r.*, 
                               u1.name as reporter_name, u1.phone as reporter_phone,
                               u2.name as reported_user_name, u2.phone as reported_user_phone,
                               l.title as listing_title, l.status as listing_status
                        FROM reports r
                        LEFT JOIN users u1 ON r.reporter_id = u1.id
                        LEFT JOIN users u2 ON r.reported_user_id = u2.id
                        LEFT JOIN listings l ON r.listing_id = l.id
                        WHERE {$whereSql}
                        ORDER BY r.created_at DESC, r.id DESC
                        LIMIT {$perPage} OFFSET {$offset}
                    ";
                    $rows = LiveBridgeService::query($querySql, $bindings);

                    $collection = collect($rows)->map(function ($r) {
                        $row = (array)$r;
                        $rep = new Report();
                        $rep->forceFill($row);
                        $rep->id = (int)$row['id'];
                        if (!empty($row['reporter_id'])) {
                            $u1 = new User(['name' => $row['reporter_name'] ?? '', 'phone' => $row['reporter_phone'] ?? '']);
                            $u1->id = (int)$row['reporter_id'];
                            $rep->setRelation('reporter', $u1);
                        }
                        if (!empty($row['reported_user_id'])) {
                            $u2 = new User(['name' => $row['reported_user_name'] ?? '', 'phone' => $row['reported_user_phone'] ?? '']);
                            $u2->id = (int)$row['reported_user_id'];
                            $rep->setRelation('reportedUser', $u2);
                        }
                        if (!empty($row['listing_id'])) {
                            $listing = new Listing(['title' => $row['listing_title'] ?? '', 'status' => $row['listing_status'] ?? '']);
                            $listing->id = (int)$row['listing_id'];
                            $rep->setRelation('listing', $listing);
                        }
                        return $rep;
                    });

                    $reports = new LengthAwarePaginator($collection, $totalReports, $perPage, $page, [
                        'path' => $request->url(),
                        'query' => $request->query(),
                    ]);
                }
            } catch (\Throwable $e) {
                // Keep default paginator if bridge query fails
            }
        } else {
            // Local Database direct queries
            try {
                $counts = [
                    'total_messages' => ContactMessage::count(),
                    'pending_messages' => ContactMessage::where('status', 'pending')->count(),
                    'in_progress_messages' => ContactMessage::where('status', 'in_progress')->count(),
                    'resolved_messages' => ContactMessage::where('status', 'resolved')->count(),
                    'total_reports' => Report::count(),
                    'pending_reports' => Report::where('status', 'pending')->count(),
                    'resolved_reports' => Report::where('status', 'resolved')->count(),
                ];

                if ($tab === 'messages') {
                    $q = ContactMessage::with('user')->orderBy('created_at', 'desc')->orderBy('id', 'desc');

                    if ($status && $status !== 'all') {
                        $q->where('status', $status);
                    }
                    if ($subject && $subject !== 'all') {
                        $q->where('subject', $subject);
                    }
                    if (!empty($search)) {
                        $q->where(function ($query) use ($search) {
                            $query->where('name', 'like', "%{$search}%")
                                ->orWhere('phone', 'like', "%{$search}%")
                                ->orWhere('message', 'like', "%{$search}%")
                                ->orWhere('admin_notes', 'like', "%{$search}%");
                        });
                    }

                    $messages = $q->paginate($perPage)->withQueryString();
                } else {
                    $rq = Report::with(['reporter', 'reportedUser', 'listing'])->orderBy('created_at', 'desc')->orderBy('id', 'desc');

                    if ($status && $status !== 'all') {
                        $rq->where('status', $status);
                    }
                    if (!empty($search)) {
                        $rq->where(function ($query) use ($search) {
                            $query->where('reason', 'like', "%{$search}%")
                                ->orWhere('details', 'like', "%{$search}%");
                        });
                    }

                    $reports = $rq->paginate($perPage)->withQueryString();
                }
            } catch (\Throwable $e) {}
        }

        return view('admin.complaints.index', compact('counts', 'messages', 'reports', 'tab', 'status', 'subject', 'search'));
    }

    /**
     * Update status and notes for a contact message / complaint.
     */
    public function updateStatus(Request $request, $id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $newStatus = $request->input('status');
        $adminNotes = $request->input('admin_notes');

        if (!in_array($newStatus, ['pending', 'in_progress', 'resolved', 'closed'])) {
            return redirect()->back()->with('error', 'الحالة المحددة غير صالحة.');
        }

        if ($activeEnv === 'production') {
            try {
                if ($adminNotes !== null) {
                    LiveBridgeService::statement(
                        "UPDATE contact_messages SET status = ?, admin_notes = ?, updated_at = NOW() WHERE id = ?",
                        [$newStatus, $adminNotes, $id]
                    );
                } else {
                    LiveBridgeService::statement(
                        "UPDATE contact_messages SET status = ?, updated_at = NOW() WHERE id = ?",
                        [$newStatus, $id]
                    );
                }
                session()->forget('pending_complaints_count');
                \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
                return redirect()->back()->with('success', 'تم تحديث حالة الشكوى/الرسالة بنجاح.');
            } catch (\Throwable $e) {
                return redirect()->back()->with('error', 'تعذر التحديث: ' . $e->getMessage());
            }
        }

        $message = ContactMessage::find($id);
        if (!$message) {
            return redirect()->back()->with('error', 'الرسالة غير موجودة.');
        }

        $message->status = $newStatus;
        if ($adminNotes !== null) {
            $message->admin_notes = $adminNotes;
        }
        $message->save();

        session()->forget('pending_complaints_count');
        return redirect()->back()->with('success', 'تم تحديث حالة الشكوى/الرسالة بنجاح.');
    }

    /**
     * Delete a contact message.
     */
    public function destroy($id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            try {
                LiveBridgeService::statement("DELETE FROM contact_messages WHERE id = ?", [$id]);
                session()->forget('pending_complaints_count');
                \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
                return redirect()->back()->with('success', 'تم حذف الرسالة بنجاح.');
            } catch (\Throwable $e) {
                return redirect()->back()->with('error', 'تعذر حذف الرسالة: ' . $e->getMessage());
            }
        }

        $message = ContactMessage::find($id);
        if ($message) {
            $message->delete();
        }

        session()->forget('pending_complaints_count');
        \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
        return redirect()->back()->with('success', 'تم حذف الرسالة بنجاح.');
    }

    /**
     * Update status of a report.
     */
    public function updateReportStatus(Request $request, $id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));
        $newStatus = $request->input('status', 'resolved');

        if (!in_array($newStatus, ['pending', 'reviewed', 'resolved'])) {
            return redirect()->back()->with('error', 'حالة البلاغ غير صالحة.');
        }

        if ($activeEnv === 'production') {
            try {
                LiveBridgeService::statement("UPDATE reports SET status = ?, updated_at = NOW() WHERE id = ?", [$newStatus, $id]);
                \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
                return redirect()->back()->with('success', 'تم تحديث حالة البلاغ بنجاح.');
            } catch (\Throwable $e) {
                return redirect()->back()->with('error', 'تعذر تحديث البلاغ: ' . $e->getMessage());
            }
        }

        $report = Report::find($id);
        if (!$report) {
            return redirect()->back()->with('error', 'البلاغ غير موجود.');
        }

        $report->status = $newStatus;
        $report->save();

        \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
        return redirect()->back()->with('success', 'تم تحديث حالة البلاغ بنجاح.');
    }

    /**
     * Delete a report.
     */
    public function destroyReport($id)
    {
        $activeEnv = session('active_db_env', env('DEFAULT_DB_ENV', 'local'));

        if ($activeEnv === 'production') {
            try {
                LiveBridgeService::statement("DELETE FROM reports WHERE id = ?", [$id]);
                \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
                return redirect()->back()->with('success', 'تم حذف البلاغ بنجاح.');
            } catch (\Throwable $e) {
                return redirect()->back()->with('error', 'تعذر حذف البلاغ: ' . $e->getMessage());
            }
        }

        $report = Report::find($id);
        if ($report) {
            $report->delete();
        }

        \Illuminate\Support\Facades\Cache::forget('complaint_kpis');
        return redirect()->back()->with('success', 'تم حذف البلاغ بنجاح.');
    }
}
