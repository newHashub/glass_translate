Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

' 优先使用项目目录下的虚拟环境
If fso.FileExists(scriptDir & "\venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & scriptDir & "\venv\Scripts\pythonw.exe"" main.py", 0, False
ElseIf fso.FileExists(scriptDir & "\.venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & scriptDir & "\.venv\Scripts\pythonw.exe"" main.py", 0, False
Else
    WshShell.Run "pythonw main.py", 0, False
End If
