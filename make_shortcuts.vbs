Set ws = CreateObject("WScript.Shell")
desktop = ws.SpecialFolders("Desktop")

' 1. Start Server
Set link1 = ws.CreateShortcut(desktop & "\Start_Server.lnk")
link1.TargetPath = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace\start_app.bat"
link1.WorkingDirectory = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace"
link1.IconLocation = "shell32.dll,14"
link1.Description = "Start Lelbai Server & Dashboard"
link1.Save

' 2. Facebook Login
Set link2 = ws.CreateShortcut(desktop & "\Facebook_Login.lnk")
link2.TargetPath = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace\login.bat"
link2.WorkingDirectory = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace"
link2.IconLocation = "shell32.dll,44"
link2.Description = "Facebook Login"
link2.Save

' 3. Arabic Named Shortcuts
name1 = ChrW(1578) & ChrW(1588) & ChrW(1594) & ChrW(1610) & ChrW(1604) & "_" & ChrW(1575) & ChrW(1604) & ChrW(1587) & ChrW(1610) & ChrW(1585) & ChrW(1601) & ChrW(1585) & ".lnk"
Set link3 = ws.CreateShortcut(desktop & "\" & name1)
link3.TargetPath = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace\start_app.bat"
link3.WorkingDirectory = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace"
link3.IconLocation = "shell32.dll,14"
link3.Save

name2 = ChrW(1578) & ChrW(1588) & ChrW(1594) & ChrW(1610) & ChrW(1604) & "_" & ChrW(1601) & ChrW(1610) & ChrW(1587) & ChrW(1576) & ChrW(1608) & ChrW(1603) & ".lnk"
Set link4 = ws.CreateShortcut(desktop & "\" & name2)
link4.TargetPath = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace\login.bat"
link4.WorkingDirectory = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace"
link4.IconLocation = "shell32.dll,44"
link4.Save

' 4. Direct Launcher Shortcut
name3 = ChrW(1605) & ChrW(1588) & ChrW(1594) & ChrW(1604) & "_" & ChrW(1608) & ChrW(1605) & ChrW(1581) & ChrW(1583) & ChrW(1579) & "_" & ChrW(1575) & ChrW(1604) & ChrW(1605) & ChrW(1606) & ChrW(1592) & ChrW(1608) & ChrW(1605) & ChrW(1577) & ".lnk"
Set link5 = ws.CreateShortcut(desktop & "\" & name3)
link5.TargetPath = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace\Lelbai_Launcher.exe"
link5.WorkingDirectory = "c:\Users\mwyda\Documents\antigravity\optimistic-lovelace"
link5.IconLocation = "shell32.dll,14"
link5.Description = "Lelbai Auto-Updater and Launcher"
link5.Save

WScript.Echo "All shortcuts created successfully"
