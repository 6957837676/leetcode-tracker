Set objShell = CreateObject("WScript.Shell")
Dim arg, title, content
arg = WScript.Arguments(0)

If arg = "morning" Then
    title = "LeetCode早间提醒"
    content = "早安！今日刷题目标：3题。请打开 http://localhost:8080 开始刷题"
ElseIf arg = "evening" Then
    title = "LeetCode晚间提醒"
    content = "晚上好！今天刷题了吗？请打开 http://localhost:8080 继续刷题"
Else
    title = "LeetCode刷题提醒"
    content = "该刷题了！请打开 http://localhost:8080 开始刷题"
End If

objShell.Run "powershell -WindowStyle Hidden -Command ""Invoke-RestMethod -Uri 'https://sctapi.ftqq.com/SCT331462TooDHBMsoiARnujWYAHtJKgxN.send' -Method Post -Body @{title='" & title & "'; desp='" & content & "'}""", 0, False
