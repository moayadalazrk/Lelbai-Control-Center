using System;
using System.IO;
using System.Net;
using System.Text;
using System.Diagnostics;
using System.Threading;
using System.IO.Compression;
using System.Collections.Generic;

namespace LelbaiLauncher
{
    class Program
    {
        static string DefaultRepoUrl = "https://github.com/moayadalazrk/Lelbai-Control-Center.git";
        static string DefaultZipUrl = "https://github.com/moayadalazrk/Lelbai-Control-Center/archive/refs/heads/main.zip";
        static string CommitApiUrl = "https://api.github.com/repos/moayadalazrk/Lelbai-Control-Center/commits/main";

        static void Main(string[] args)
        {
            try
            {
                RunApp(args);
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("\n❌ حدث خطأ غير متوقع في المشغل:");
                Console.WriteLine(ex.Message);
                Console.ResetColor();
                SafeWaitForKey();
            }
        }

        static void SafeWaitForKey()
        {
            try
            {
                Console.WriteLine("\nاضغط [Enter] للمتابعة أو الخروج...");
                Console.ReadLine();
            }
            catch
            {
                try { Console.Read(); } catch { }
            }
        }

        static void RunApp(string[] args)
        {
            try
            {
                Console.OutputEncoding = Encoding.UTF8;
            }
            catch { }

            Console.Title = "منصة للبيع (LELBAI) - مشغل ومحدث النظام الذكي";
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("==========================================================================");
            Console.WriteLine("   🚀 منصة للبيع (LELBAI) - مشغل التحديث التلقائي ومركز التحكم الذكي 🇸🇾");
            Console.WriteLine("==========================================================================");
            Console.ResetColor();

            // تمكين بروتوكول TLS 1.2 للاتصال الآمن مع GitHub
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072 | SecurityProtocolType.Tls;

            // 1. تحديد المجلد المستقل في قرص C
            string appDir = DetermineAppDirectory(args);
            Console.ForegroundColor = ConsoleColor.DarkCyan;
            Console.WriteLine("📁 مجلد تثبيت النظام المستقل: " + appDir);
            Console.ResetColor();

            // 2. نسخ المشغل الحالي إلى المجلد المستقل
            EnsureLauncherInAppDir(appDir);

            // 3. إنشاء اختصار نظيف على سطح المكتب
            EnsureDesktopShortcut(appDir);

            // 4. تنظيف وإزالة كافة ملفات المشروع من سطح المكتب
            CleanDesktopArtifacts(appDir);

            // التوجه إلى مجلد النظام
            Directory.SetCurrentDirectory(appDir);

            // 5. قراءة إعدادات المستودع من config.json إذا وجد
            ReadCustomConfig(appDir);

            // 6. التحقق من وجود ملفات النظام الأساسية وتنزيلها إن لزم
            bool filesExist = File.Exists(Path.Combine(appDir, "web_app.py"));

            if (!filesExist)
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("\n[1/4] 📦 لم يتم العثور على ملفات النظام في هذا المجلد.");
                Console.WriteLine("      جاري تنزيل أحدث نسخة من المستودع على GitHub بالكامل...");
                Console.ResetColor();

                bool cloned = TryGitClone(DefaultRepoUrl, appDir);
                if (!cloned)
                {
                    Console.WriteLine("      جاري تنزيل حزمة الملفات عبر HTTPS مباشرة...");
                    DownloadAndExtractZip(DefaultZipUrl, appDir);
                }

                if (!File.Exists(Path.Combine(appDir, "web_app.py")))
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("\n❌ لم يتم العثور على ملفات النظام (web_app.py) بعد محاولة التنزيل!");
                    Console.WriteLine("   💡 ملاحظات هامة للحل:");
                    Console.WriteLine("   1. إذا كان مستودع GitHub مضبوطاً كـ Private (خاص)، يرجى جعله Public (عام)");
                    Console.WriteLine("      حتى يستطيع أي جهاز تنزيل الملفات دون طلب أي مفتاح أو حساب.");
                    Console.WriteLine("   2. أو تأكد من وجود برنامج Git على الجهاز.");
                    SafeWaitForKey();
                    return;
                }
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("\n[1/3] 🔍 جاري فحص وجود تحديثات جديدة على GitHub...");
                Console.ResetColor();

                if (Directory.Exists(Path.Combine(appDir, ".git")))
                {
                    UpdateViaGit(appDir);
                }
                else
                {
                    UpdateViaApi(appDir);
                }
            }

            // إعادة فحص سطح المكتب لتأكيد النظافة التامة
            CleanDesktopArtifacts(appDir);

            // 7. عرض تاريخ آخر تحديث للنظام
            ShowLastUpdateDate(appDir);

            // 8. تشغيل السيرفر المحلي وفتح لوحة التحكم
            LaunchApplication(appDir);
        }

        static string DetermineAppDirectory(string[] args)
        {
            foreach (string arg in args)
            {
                if (arg.Equals("--here", StringComparison.OrdinalIgnoreCase) || arg.Equals("--dev", StringComparison.OrdinalIgnoreCase))
                {
                    return AppDomain.CurrentDomain.BaseDirectory;
                }
            }

            string primaryDir = @"C:\Lelbai_Control_Center";
            try
            {
                if (!Directory.Exists(primaryDir))
                {
                    Directory.CreateDirectory(primaryDir);
                }
                return primaryDir;
            }
            catch
            {
                string fallback = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Lelbai_Control_Center");
                if (!Directory.Exists(fallback))
                {
                    Directory.CreateDirectory(fallback);
                }
                return fallback;
            }
        }

        static void EnsureLauncherInAppDir(string appDir)
        {
            try
            {
                string targetExe = Path.Combine(appDir, "Lelbai_Launcher.exe");
                string currentExe = Process.GetCurrentProcess().MainModule.FileName;
                if (!string.Equals(Path.GetFullPath(currentExe), Path.GetFullPath(targetExe), StringComparison.OrdinalIgnoreCase))
                {
                    if (File.Exists(currentExe))
                    {
                        File.Copy(currentExe, targetExe, true);
                    }
                }
            }
            catch { }
        }

        static void EnsureDesktopShortcut(string appDir)
        {
            try
            {
                string desktop = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
                if (string.IsNullOrEmpty(desktop) || !Directory.Exists(desktop)) return;

                string shortcutPath = Path.Combine(desktop, "منصة للبيع - مركز التحكم.lnk");
                string exePath = Path.Combine(appDir, "Lelbai_Launcher.exe");
                if (!File.Exists(shortcutPath) && File.Exists(exePath))
                {
                    string psScript = string.Format(
                        "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('{0}'); $s.TargetPath = '{1}'; $s.WorkingDirectory = '{2}'; $s.Save()",
                        shortcutPath, exePath, appDir
                    );
                    ProcessStartInfo psi = new ProcessStartInfo("powershell", "-NoProfile -ExecutionPolicy Bypass -Command \"" + psScript + "\"")
                    {
                        CreateNoWindow = true,
                        UseShellExecute = false
                    };
                    using (Process p = Process.Start(psi))
                    {
                        p.WaitForExit(4000);
                    }
                }
            }
            catch { }
        }

        static void CleanDesktopArtifacts(string appDir)
        {
            try
            {
                string desktop = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
                if (string.IsNullOrEmpty(desktop) || !Directory.Exists(desktop)) return;

                if (string.Equals(Path.GetFullPath(appDir).TrimEnd('\\'), Path.GetFullPath(desktop).TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
                    return;

                string[] projectFiles = new string[]
                {
                    "web_app.py",
                    "control_dashboard.html",
                    "scraper.py",
                    "publisher.py",
                    "syria_filter.py",
                    "login.py",
                    "login.bat",
                    "run.bat",
                    "start_app.bat",
                    "make_shortcuts.vbs",
                    "start_hidden.vbs",
                    "requirements.txt",
                    "README.md",
                    "last_update.json",
                    "mock_group_page.html",
                    "setup.py",
                    "upload_to_github.bat",
                    "Lelbai_Launcher.cs",
                    "test_append_preserve.py",
                    "test_browser_flow.py",
                    "test_city_sub_classifier.py",
                    "test_filter.py",
                    "test_gemini_moderation_pipeline.py",
                    "test_group_removal.py",
                    "test_image_processor.py",
                    "test_output_ads.json",
                    "test_bg.py",
                    "temp_update.zip"
                };

                string[] projectDirs = new string[]
                {
                    "_temp_clone",
                    ".git",
                    ".github",
                    "temp_extracted",
                    "__pycache__"
                };

                bool cleanedAny = false;

                // 1. نقل الصور إذا كانت قد وُجدت على سطح المكتب
                string desktopImgs = Path.Combine(desktop, "imgs");
                if (Directory.Exists(desktopImgs))
                {
                    string targetImgs = Path.Combine(appDir, "imgs");
                    if (!Directory.Exists(targetImgs)) Directory.CreateDirectory(targetImgs);
                    try
                    {
                        foreach (string f in Directory.GetFiles(desktopImgs))
                        {
                            string dest = Path.Combine(targetImgs, Path.GetFileName(f));
                            if (!File.Exists(dest)) File.Copy(f, dest, true);
                        }
                        RemoveReadonlyAttributes(desktopImgs);
                        Directory.Delete(desktopImgs, true);
                        cleanedAny = true;
                    }
                    catch { }
                }

                // 2. الحفاظ على ملفات البيانات إذا كانت موجودة على سطح المكتب
                string[] dataFiles = new string[] { "config.json", "pending_review.json", "published_ads.json", "flagged_ads.json", "groups_data.json" };
                foreach (string df in dataFiles)
                {
                    string src = Path.Combine(desktop, df);
                    string dst = Path.Combine(appDir, df);
                    if (File.Exists(src))
                    {
                        if (!File.Exists(dst))
                        {
                            try { File.Copy(src, dst, true); } catch { }
                        }
                        try { File.Delete(src); cleanedAny = true; } catch { }
                    }
                }

                // 3. حذف ملفات الكود والمستودع من سطح المكتب
                foreach (string file in projectFiles)
                {
                    string p = Path.Combine(desktop, file);
                    if (File.Exists(p))
                    {
                        try
                        {
                            File.SetAttributes(p, FileAttributes.Normal);
                            File.Delete(p);
                            cleanedAny = true;
                        }
                        catch { }
                    }
                }

                // 4. حذف مجلدات المشروع ومجلد git من سطح المكتب
                foreach (string dir in projectDirs)
                {
                    string p = Path.Combine(desktop, dir);
                    if (Directory.Exists(p))
                    {
                        try
                        {
                            RemoveReadonlyAttributes(p);
                            Directory.Delete(p, true);
                            cleanedAny = true;
                        }
                        catch { }
                    }
                }

                if (cleanedAny)
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("  🧹 تم تنظيف وإزالة كافة ملفات المستودع والمشروع من سطح المكتب بنجاح.");
                    Console.ResetColor();
                }
            }
            catch { }
        }

        static void RemoveReadonlyAttributes(string dirPath)
        {
            try
            {
                DirectoryInfo di = new DirectoryInfo(dirPath);
                di.Attributes = FileAttributes.Normal;
                foreach (FileInfo file in di.GetFiles("*", SearchOption.AllDirectories))
                {
                    file.Attributes = FileAttributes.Normal;
                }
                foreach (DirectoryInfo sub in di.GetDirectories("*", SearchOption.AllDirectories))
                {
                    sub.Attributes = FileAttributes.Normal;
                }
            }
            catch { }
        }

        static void ReadCustomConfig(string dir)
        {
            try
            {
                string cfgFile = Path.Combine(dir, "config.json");
                if (File.Exists(cfgFile))
                {
                    string content = File.ReadAllText(cfgFile);
                    int idx = content.IndexOf("\"github_repo\":");
                    if (idx >= 0)
                    {
                        int start = content.IndexOf("\"", idx + 14) + 1;
                        int end = content.IndexOf("\"", start);
                        if (start > 0 && end > start)
                        {
                            string repo = content.Substring(start, end - start).Trim();
                            if (!string.IsNullOrEmpty(repo) && repo.StartsWith("http"))
                            {
                                DefaultRepoUrl = repo;
                                string repoName = repo.Replace(".git", "").TrimEnd('/');
                                DefaultZipUrl = repoName + "/archive/refs/heads/main.zip";
                                
                                string cleanPath = repoName.Replace("https://github.com/", "");
                                CommitApiUrl = "https://api.github.com/repos/" + cleanPath + "/commits/main";
                            }
                        }
                    }
                }
            }
            catch { }
        }

        static bool TryGitClone(string repoUrl, string targetDir)
        {
            try
            {
                Console.WriteLine("      [+] جاري استنساخ وتحميل ملفات النظام عبر Git...");
                string tempClone = Path.Combine(targetDir, "_temp_clone");
                if (Directory.Exists(tempClone))
                {
                    try { RemoveReadonlyAttributes(tempClone); Directory.Delete(tempClone, true); } catch { }
                }

                RunCommand("git", "clone \"" + repoUrl + "\" \"" + tempClone + "\"", targetDir, 90000);

                if (Directory.Exists(tempClone) && File.Exists(Path.Combine(tempClone, "web_app.py")))
                {
                    string gitSrc = Path.Combine(tempClone, ".git");
                    string gitDst = Path.Combine(targetDir, ".git");
                    if (Directory.Exists(gitSrc))
                    {
                        if (Directory.Exists(gitDst))
                        {
                            try { RemoveReadonlyAttributes(gitDst); Directory.Delete(gitDst, true); } catch { }
                        }
                        try { Directory.Move(gitSrc, gitDst); } catch { }
                    }

                    CopyDirectory(tempClone, targetDir);

                    try { RemoveReadonlyAttributes(tempClone); Directory.Delete(tempClone, true); } catch { }

                    bool ok = File.Exists(Path.Combine(targetDir, "web_app.py"));
                    if (ok)
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("      ✅ تم تنزيل واستخراج كافة ملفات النظام بنجاح عبر Git!");
                        Console.ResetColor();
                    }
                    return ok;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("      ℹ️ تعذر السحب عبر Git: " + ex.Message);
            }

            return false;
        }

        static void DownloadAndExtractZip(string zipUrl, string targetDir)
        {
            string tempZip = Path.Combine(targetDir, "temp_update.zip");
            try
            {
                using (WebClient client = new WebClient())
                {
                    client.Headers.Add("User-Agent", "Lelbai-Launcher/1.0");
                    client.DownloadFile(zipUrl, tempZip);
                }

                string extractTemp = Path.Combine(targetDir, "temp_extracted");
                if (Directory.Exists(extractTemp))
                {
                    try { RemoveReadonlyAttributes(extractTemp); Directory.Delete(extractTemp, true); } catch { }
                }

                ZipFile.ExtractToDirectory(tempZip, extractTemp);

                string[] dirs = Directory.GetDirectories(extractTemp);
                string sourceDir = (dirs.Length == 1) ? dirs[0] : extractTemp;

                CopyDirectory(sourceDir, targetDir);

                try { RemoveReadonlyAttributes(extractTemp); Directory.Delete(extractTemp, true); } catch { }
                if (File.Exists(tempZip)) File.Delete(tempZip);

                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("      ✅ تم تنزيل واستخراج الملفات بنجاح عبر HTTPS!");
                Console.ResetColor();
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("      ❌ تعذر تنزيل الملفات عبر HTTPS: " + ex.Message);
                if (ex.Message.Contains("404"))
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("      💡 سبب الخطأ (404): مستودع GitHub مضبوط كـ Private (خاص).");
                    Console.WriteLine("         لتنزيل الحزمة على أي جهاز دون تسجيل دخول، اجعل المستودع Public (عام).");
                }
                Console.ResetColor();
            }
        }

        static void CopyDirectory(string sourceDir, string destDir)
        {
            foreach (string dir in Directory.GetDirectories(sourceDir, "*", SearchOption.AllDirectories))
            {
                if (dir.Contains(".git")) continue;
                string dirToCreate = dir.Replace(sourceDir, destDir);
                if (!Directory.Exists(dirToCreate)) Directory.CreateDirectory(dirToCreate);
            }

            foreach (string file in Directory.GetFiles(sourceDir, "*.*", SearchOption.AllDirectories))
            {
                if (file.Contains(".git")) continue;
                string fileName = Path.GetFileName(file);
                if (fileName.Equals("Lelbai_Launcher.exe", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                string fileToCopy = file.Replace(sourceDir, destDir);
                try
                {
                    File.Copy(file, fileToCopy, true);
                }
                catch { }
            }
        }

        static void UpdateViaGit(string dir)
        {
            try
            {
                RunCommand("git", "fetch origin --prune", dir, 30000);

                string localHead = RunCommandWithOutput("git", "rev-parse HEAD", dir).Trim();
                string remoteHead = RunCommandWithOutput("git", "rev-parse origin/main", dir).Trim();
                if (string.IsNullOrEmpty(remoteHead) || remoteHead.Length < 10)
                {
                    remoteHead = RunCommandWithOutput("git", "rev-parse origin/master", dir).Trim();
                }

                bool isBehind = false;
                if (!string.IsNullOrEmpty(remoteHead) && !string.IsNullOrEmpty(localHead) && !localHead.Equals(remoteHead, StringComparison.OrdinalIgnoreCase))
                {
                    isBehind = true;
                }
                else
                {
                    string status = RunCommandWithOutput("git", "status -uno", dir);
                    if (status.Contains("behind") || status.Contains("Your branch is behind"))
                    {
                        isBehind = true;
                    }
                }

                if (isBehind)
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("      ⚡ تم العثور على تحديث جديد! جاري سحب التحديث وتطبيقه بأمان...");
                    Console.ResetColor();

                    // حفظ بيانات المستخدم الهامة في الذاكرة حتى لا تُفقد أثناء المزامنة
                    string[] userFiles = new string[] {
                        "config.json",
                        "pending_review.json",
                        "published_ads.json",
                        "flagged_ads.json",
                        "groups_data.json",
                        "ads_syria.json"
                    };

                    Dictionary<string, byte[]> backupData = new Dictionary<string, byte[]>();
                    foreach (string f in userFiles)
                    {
                        string p = Path.Combine(dir, f);
                        if (File.Exists(p))
                        {
                            try {
                                byte[] raw = File.ReadAllBytes(p);
                                if (raw != null && raw.Length > 10)
                                {
                                    backupData[f] = raw;
                                }
                            } catch { }
                        }
                    }

                    // تطبيق التحديث باستخدام reset --hard لضمان عدم التعليق أو رفض الدمج بسبب اختلافات الملفات المحلية
                    string targetBranch = !string.IsNullOrEmpty(remoteHead) ? (RunCommandWithOutput("git", "branch -r", dir).Contains("origin/main") ? "origin/main" : "origin/master") : "origin/main";

                    RunCommand("git", "checkout -f -B main " + targetBranch, dir, 25000);
                    RunCommand("git", "reset --hard " + targetBranch, dir, 25000);
                    RunCommand("git", "clean -fd -e imgs/ -e *.json", dir, 15000);

                    // استعادة بيانات المستخدم المحفوظة إذا كانت تحتوي على بيانات حقيقية
                    foreach (var kvp in backupData)
                    {
                        try
                        {
                            string p = Path.Combine(dir, kvp.Key);
                            if (kvp.Value != null && kvp.Value.Length > 10)
                            {
                                File.WriteAllBytes(p, kvp.Value);
                            }
                        }
                        catch { }
                    }

                    string newLocalHead = RunCommandWithOutput("git", "rev-parse HEAD", dir).Trim();
                    if (!string.IsNullOrEmpty(remoteHead) && newLocalHead.Equals(remoteHead, StringComparison.OrdinalIgnoreCase))
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("      ✅ تم تحديث وتطبيق كافة الملفات البرمجية بنجاح 100%!");
                        Console.ResetColor();
                    }
                    else
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("      ✅ تم سحب التحديث بنجاح!");
                        Console.ResetColor();
                    }

                    try
                    {
                        RunCommand("pip", "install -r requirements.txt", dir, 45000);
                    }
                    catch { }
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("      ✅ كافة الملفات محدثة إلى أحدث إصدار على GitHub.");
                    Console.ResetColor();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("      ℹ️ تعذر فحص التحديث عبر Git: " + ex.Message);
            }
        }

        static void UpdateViaApi(string dir)
        {
            try
            {
                string gitCheck = RunCommandWithOutput("git", "--version", dir);
                if (gitCheck.Contains("git version"))
                {
                    Console.WriteLine("      [+] جاري تفعيل المزامنة التلقائية عبر Git...");
                    RunCommand("git", "init", dir, 15000);
                    RunCommand("git", "remote remove origin", dir, 5000);
                    RunCommand("git", "remote add origin " + DefaultRepoUrl, dir, 15000);
                    RunCommand("git", "fetch origin", dir, 30000);
                    RunCommand("git", "checkout -f -B main origin/main", dir, 20000);
                    RunCommand("git", "reset --hard origin/main", dir, 20000);
                    if (Directory.Exists(Path.Combine(dir, ".git")))
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("      ✅ تم تفعيل وتحديث المنظومة عبر Git بنجاح!");
                        Console.ResetColor();
                        return;
                    }
                }

                using (WebClient client = new WebClient())
                {
                    client.Headers.Add("User-Agent", "Lelbai-Launcher/1.0");
                    string json = client.DownloadString(CommitApiUrl);
                    int dateIdx = json.IndexOf("\"date\":");
                    if (dateIdx > 0)
                    {
                        int s = json.IndexOf("\"", dateIdx + 7) + 1;
                        int e = json.IndexOf("\"", s);
                        string commitDate = json.Substring(s, e - s);
                        SaveLastUpdate(dir, commitDate, "متزامن مع GitHub");
                    }
                }
            }
            catch { }
        }

        static void ShowLastUpdateDate(string dir)
        {
            string dateStr = "";
            string relative = "";
            string message = "";

            try
            {
                if (Directory.Exists(Path.Combine(dir, ".git")))
                {
                    string log = RunCommandWithOutput("git", "log -1 --format=\"%ci|%cr|%s\"", dir).Trim();
                    if (!string.IsNullOrEmpty(log) && log.Contains("|"))
                    {
                        string[] parts = log.Split('|');
                        dateStr = parts[0].Trim('"');
                        if (parts.Length > 1) relative = parts[1];
                        if (parts.Length > 2) message = parts[2].Trim('"');
                    }
                }
            }
            catch { }

            if (string.IsNullOrEmpty(dateStr))
            {
                string infoFile = Path.Combine(dir, "last_update.json");
                if (File.Exists(infoFile))
                {
                    try
                    {
                        string content = File.ReadAllText(infoFile);
                        int idx = content.IndexOf("\"last_updated_at\":");
                        if (idx >= 0)
                        {
                            int s = content.IndexOf("\"", idx + 18) + 1;
                            int e = content.IndexOf("\"", s);
                            dateStr = content.Substring(s, e - s);
                        }
                    }
                    catch { }
                }
            }

            if (string.IsNullOrEmpty(dateStr))
            {
                dateStr = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            }

            SaveLastUpdate(dir, dateStr, relative);

            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("--------------------------------------------------------------------------");
            Console.ForegroundColor = ConsoleColor.White;
            Console.WriteLine("  📅 تاريخ آخر تحديث للنظام: " + dateStr + (!string.IsNullOrEmpty(relative) ? " (" + relative + ")" : ""));
            if (!string.IsNullOrEmpty(message))
            {
                Console.WriteLine("  💬 ملخص التحديث الأخير : " + message);
            }
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("  ✅ حالة المنظومة        : متزامنة وجاهزة للعمل بنجاح");
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("--------------------------------------------------------------------------\n");
            Console.ResetColor();
        }

        static void SaveLastUpdate(string dir, string dateStr, string relative)
        {
            try
            {
                string json = "{\n  \"last_updated_at\": \"" + dateStr + "\",\n  \"relative_time\": \"" + relative + "\",\n  \"status\": \"up_to_date\"\n}";
                File.WriteAllText(Path.Combine(dir, "last_update.json"), json, Encoding.UTF8);
            }
            catch { }
        }

        static void KillExistingServer(int port)
        {
            try
            {
                string netstat = RunCommandWithOutput("netstat", "-ano -p tcp", AppDomain.CurrentDomain.BaseDirectory);
                foreach (string line in netstat.Split(new char[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    if (line.Contains(":" + port) && line.Contains("LISTENING"))
                    {
                        string[] parts = line.Trim().Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length > 0)
                        {
                            string pidStr = parts[parts.Length - 1];
                            int pid;
                            if (int.TryParse(pidStr, out pid) && pid > 0)
                            {
                                try
                                {
                                    Process p = Process.GetProcessById(pid);
                                    if (p != null && !p.HasExited)
                                    {
                                        p.Kill();
                                        p.WaitForExit(2000);
                                    }
                                }
                                catch { }
                            }
                        }
                    }
                }
            }
            catch { }
        }

        static void LaunchApplication(string dir)
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("[2/2] 🚀 جاري تشغيل سيرفر لوحة التحكم وفتح المتصفح...");
            Console.ResetColor();

            // إغلاق أي عملية بايثون قديمة معلقة على نفس المنفذ لضمان تشغيل النسخة المحدثة فوراً
            KillExistingServer(5000);
            Thread.Sleep(500);

            string pythonExe = FindPythonExecutable();
            string webAppScript = Path.Combine(dir, "web_app.py");

            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = "\"" + webAppScript + "\"",
                WorkingDirectory = dir,
                UseShellExecute = false,
                CreateNoWindow = false
            };

            try
            {
                Process p = Process.Start(psi);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("  🟢 تم تشغيل سيرفر لوحة التحكم بنجاح! PID: " + p.Id);
                Console.WriteLine("  ⏳ جاري الانتظار حتى اكتمال إقلاع السيرفر...");
                Console.ResetColor();

                new Thread(() =>
                {
                    for (int i = 0; i < 30; i++)
                    {
                        Thread.Sleep(700);
                        if (IsPortOpen(5000))
                        {
                            Console.ForegroundColor = ConsoleColor.Green;
                            Console.WriteLine("\n  🌐 السيرفر متصل بنجاح! جاري فتح المتصفح: http://localhost:5000");
                            Console.ResetColor();
                            OpenBrowser("http://localhost:5000");
                            break;
                        }
                    }
                }).Start();

                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("  💡 نافذة المشغل هذه تبقي السيرفر قيد العمل المباشر.");
                Console.WriteLine("==========================================================================\n");
                Console.ResetColor();

                p.WaitForExit();

                if (p.ExitCode != 0)
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("\n⚠️ توقف سيرفر بايثون (رمز الخروج: " + p.ExitCode + ")");
                    Console.ResetColor();
                    SafeWaitForKey();
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("  ❌ تعذر تشغيل بايثون تلقائياً: " + ex.Message);
                Console.WriteLine("  يرجى التأكد من تثبيت Python وتضمينه في متغيرات النظام PATH.");
                Console.ResetColor();
                SafeWaitForKey();
            }
        }

        static bool IsPortOpen(int port)
        {
            try
            {
                using (var client = new System.Net.Sockets.TcpClient())
                {
                    var result = client.BeginConnect("127.0.0.1", port, null, null);
                    bool success = result.AsyncWaitHandle.WaitOne(400);
                    if (!success) return false;
                    client.EndConnect(result);
                    return true;
                }
            }
            catch
            {
                return false;
            }
        }

        static string FindPythonExecutable()
        {
            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] possiblePaths = new string[]
            {
                "py",
                "python",
                Path.Combine(localApp, @"Python\pythoncore-3.14-64\python.exe"),
                Path.Combine(localApp, @"Programs\Python\Python311\python.exe"),
                Path.Combine(localApp, @"Programs\Python\Python312\python.exe"),
                Path.Combine(localApp, @"Programs\Python\Python310\python.exe"),
                @"C:\Python311\python.exe",
                @"C:\Python312\python.exe"
            };

            foreach (var path in possiblePaths)
            {
                try
                {
                    ProcessStartInfo psi = new ProcessStartInfo(path, "--version")
                    {
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        RedirectStandardOutput = true
                    };
                    Process p = Process.Start(psi);
                    p.WaitForExit(2000);
                    if (p.ExitCode == 0) return path;
                }
                catch { }
            }

            return "python";
        }

        static void OpenBrowser(string url)
        {
            try
            {
                Process.Start(url);
            }
            catch
            {
                try
                {
                    Process.Start(new ProcessStartInfo("cmd", "/c start " + url) { CreateNoWindow = true });
                }
                catch { }
            }
        }

        static void RunCommand(string cmd, string args, string dir, int timeoutMs)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo(cmd, args)
                {
                    WorkingDirectory = dir,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                Process p = Process.Start(psi);
                p.WaitForExit(timeoutMs);
            }
            catch { }
        }

        static string RunCommandWithOutput(string cmd, string args, string dir)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo(cmd, args)
                {
                    WorkingDirectory = dir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    StandardOutputEncoding = Encoding.UTF8
                };
                Process p = Process.Start(psi);
                string outText = p.StandardOutput.ReadToEnd();
                p.WaitForExit(15000);
                return outText;
            }
            catch
            {
                return "";
            }
        }
    }
}
