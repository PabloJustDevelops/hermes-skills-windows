' Starts the local SearXNG without a console window.
' Keep it next to start-searxng.ps1; for autostart, drop a shortcut to this file
' in shell:startup (Win+R -> shell:startup).
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
ps1 = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "start-searxng.ps1")
sh.Run "powershell -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File """ & ps1 & """", 0, False
