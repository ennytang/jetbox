$path = [Environment]::GetFolderPath('UserProfile') + '\.gemini\antigravity\conversations\*.pb'
Write-Host "Searching in $path"
$results = Select-String -Path $path -Pattern 'eksik|kategori|teknopark' -Context 1,1
if ($results) {
    $results | Select-Object -First 20 | Out-String | Write-Host
} else {
    Write-Host "No results found."
}
