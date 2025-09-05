# 服务路径
$servicePath = "D:\app_data\vscode\go\src\taskserver\bin\taskserver.exe"

# 检查服务是否已在运行
$serviceRunning = Get-Process | Where-Object { $_.Path -eq $servicePath }
if (-not $serviceRunning) {
    Write-Host "服务未运行，正在启动 taskserver.exe ..."
    Start-Process -FilePath $servicePath
    Start-Sleep -Seconds 2
} else {
    Write-Host "服务已经在运行。"}

# 提交任务
$inputValue = Read-Host "请输入要提交的数字"
$body = '{"input":' + $inputValue + '}'
$submitResponse = Invoke-RestMethod -Uri "http://localhost:8080/submit" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body $body
$jobId = $submitResponse.job_id
Write-Host "任务已提交，job_id =" $jobId

# 查询结果
$completed = $false
while (-not $completed) {
    Start-Sleep -Seconds 1
    try {
        $resultResponse = Invoke-RestMethod -Uri ("http://localhost:8080/result?id=" + $jobId) -Method GET
        if ($resultResponse.result) {
            Write-Host "任务完成，结果：" $resultResponse.result
            $completed = $true
        } elseif ($resultResponse.error) {
            Write-Host "任务失败，错误：" $resultResponse.error
            $completed = $true
        } else {
            Write-Host "任务还在处理，等待..."
        }
    } catch {
        Write-Host "查询失败，等待..."
    }
}
