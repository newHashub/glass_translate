Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectDir = fso.GetParentFolderName(scriptDir)
WshShell.CurrentDirectory = projectDir

' 1. 如果已打包生成原生可执行程序，直接运行 EXE (零闪烁、纯原生应用体验)
If fso.FileExists(projectDir & "\dist\GlassTranslate\GlassTranslate.exe") Then
    WshShell.Run """" & projectDir & "\dist\GlassTranslate\GlassTranslate.exe""", 1, False
ElseIf fso.FileExists(projectDir & "\dist\GlassTranslate.exe") Then
    WshShell.Run """" & projectDir & "\dist\GlassTranslate.exe""", 1, False
' 2. 优先检查本地虚拟环境
ElseIf fso.FileExists(projectDir & "\venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & projectDir & "\venv\Scripts\pythonw.exe"" main.py", 0, False
ElseIf fso.FileExists(projectDir & "\.venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & projectDir & "\.venv\Scripts\pythonw.exe"" main.py", 0, False
' 3. 优先使用 Windows 官方 Python Launcher pyw.exe (精准指向系统完整环境)
Else
    Dim returnCode
    returnCode = WshShell.Run("pyw -3 main.py", 0, False)
End If
