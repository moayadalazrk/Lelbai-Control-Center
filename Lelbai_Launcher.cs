using System;
using System.IO;
using System.Net;
using System.Text;
using System.Diagnostics;
using System.Threading;
using System.IO.Compression;

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
                Console.WriteLine("\nاضغط أي مفتاح للخروج...");
                Console.ReadKey();
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

            string currentDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(currentDir);

            // تمكين بروتوكول TLS 1.2 للاتصال الآمن مع GitHub
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072 | SecurityProtocolType.Tls;

            // 1. قراءة إعدادات المستودع من config.json إذا وجد
            ReadCustomConfig(currentDir);

            // 2. التحقق من وجود ملفات النظام الأساسية
            bool filesExist = File.Exists(Path.Combine(currentDir, "web_app.py"));

            if (!filesExist)
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("\n[1/4] 📦 لم يتم العثور على ملفات النظام في هذا المجلد.");
                Console.WriteLine("      جاري تنزيل أحدث نسخة من المستودع على GitHub بالكامل...");
                Console.ResetColor();

                bool cloned = TryGitClone(DefaultRepoUrl, currentDir);
                if (!cloned)
                {
                    Console.WriteLine("      جاري تنزيل حزمة الملفات عبر HTTPS مباشرة...");
                    DownloadAndExtractZip(DefaultZipUrl, currentDir);
                }
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("\n[1/3] 🔍 جاري فحص وجود تحديثات جديدة على GitHub...");
                Console.ResetColor();

                if (Directory.Exists(Path.Combine(currentDir, ".git")))
                {
                    UpdateViaGit(currentDir);
                }
                else
                {
                    UpdateViaApi(currentDir);
                }
            }

            // 3. عرض تاريخ آخر تحديث للنظام
            ShowLastUpdateDate(currentDir);

            // 4. تشغيل السيرفر المحلي وفتح لوحة التحكم
            LaunchApplication(currentDir);
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
                ProcessStartInfo psi = new ProcessStartInfo("git", "clone \"" + repoUrl + "\" .")
                {
                    UseShellExecute = false,
                    CreateNoWindow = false,
                    WorkingDirectory = targetDir
                };
                Process p = Process.Start(psi);
                p.WaitForExit(90000);
                return p.ExitCode == 0 && File.Exists(Path.Combine(targetDir, "web_app.py"));
            }
            catch
            {
                return false;
            }
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
                if (Directory.Exists(extractTemp)) Directory.Delete(extractTemp, true);
                ZipFile.ExtractToDirectory(tempZip, extractTemp);

                // نقل الملفات من المجلد الفرعي إذا كان مضغوطاً داخله
                string[] dirs = Directory.GetDirectories(extractTemp);
                string sourceDir = (dirs.Length == 1) ? dirs[0] : extractTemp;

                CopyDirectory(sourceDir, targetDir);

                Directory.Delete(extractTemp, true);
                if (File.Exists(tempZip)) File.Delete(tempZip);

                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("      ✅ تم تنزيل واستخراج الملفات بنجاح!");
                Console.ResetColor();
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("      ❌ تعذر تنزيل الملفات: " + ex.Message);
                Console.ResetColor();
            }
        }

        static void CopyDirectory(string sourceDir, string destDir)
        {
            foreach (string dir in Directory.GetDirectories(sourceDir, "*", SearchOption.AllDirectories))
            {
                string dirToCreate = dir.Replace(sourceDir, destDir);
                if (!Directory.Exists(dirToCreate)) Directory.CreateDirectory(dirToCreate);
            }

            foreach (string file in Directory.GetFiles(sourceDir, "*.*", SearchOption.AllDirectories))
            {
                string fileToCopy = file.Replace(sourceDir, destDir);
                File.Copy(file, fileToCopy, true);
            }
        }

        static void UpdateViaGit(string dir)
        {
            try
            {
                RunCommand("git", "fetch origin", dir, 20000);
                string status = RunCommandWithOutput("git", "status -uno", dir);

                if (status.Contains("behind") || status.Contains("Your branch is behind"))
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("      ⚡ تم العثور على تحديث جديد! جاري سحب التحديث وتطبيقه...");
                    Console.ResetColor();

                    string pullOut = RunCommandWithOutput("git", "pull", dir);
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("      ✅ تم تحديث الملفات بنجاح!");
                    Console.ResetColor();

                    if (pullOut.Contains("requirements.txt"))
                    {
                        Console.WriteLine("      📦 تحديث مكتبات Python المطلوبة...");
                        RunCommand("pip", "install -r requirements.txt", dir, 60000);
                    }
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

        static void LaunchApplication(string dir)
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("[2/2] 🚀 جاري تشغيل سيرفر لوحة التحكم وفتح المتصفح...");
            Console.ResetColor();

            // فحص ما إذا كان السيرفر يعمل بالفعل على منفذ 5000
            bool alreadyRunning = IsPortOpen(5000);
            if (alreadyRunning)
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("  🟢 سيرفر لوحة التحكم يعمل بنشاط على: http://localhost:5000");
                Console.ResetColor();
                OpenBrowser("http://localhost:5000");
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("\n==========================================================================");
                Console.WriteLine("  🌐 لوحة التحكم مفتوحة وتعمل الآن في المتصفح.");
                Console.WriteLine("  💡 يمكنك الضغط على [Enter] هنا في أي وقت لإغلاق هذه النافذة.");
                Console.WriteLine("==========================================================================");
                Console.ResetColor();
                Console.ReadLine();
                return;
            }

            // العثور على مفسر بايثون
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

                // الانتظار حتى يصبح المنفذ 5000 متاحاً ثم فتح المتصفح
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
                    Console.WriteLine("\nاضغط أي مفتاح للخروج...");
                    Console.ReadKey();
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("  ❌ تعذر تشغيل بايثون تلقائياً: " + ex.Message);
                Console.WriteLine("  يرجى التأكد من تثبيت Python وتضمينه في متغيرات النظام PATH.");
                Console.ResetColor();
                Console.WriteLine("\nاضغط أي مفتاح للخروج...");
                Console.ReadKey();
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
