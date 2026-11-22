$ErrorActionPreference = 'Stop'
$reserveDocPath = Join-Path $PSScriptRoot 'Circle_Reserve_Income_Report.docx'
$reservePdfPath = Join-Path $PSScriptRoot 'Circle_Reserve_Income_Report.pdf'
$reserveWordApp = $null
$reserveWordDoc = $null
try {
    $reserveWordApp = New-Object -ComObject Word.Application
    $reserveWordApp.Visible = $false
    $reserveWordApp.DisplayAlerts = 0
    $reserveWordApp.AutomationSecurity = 3
    $reserveWordDoc = $reserveWordApp.Documents.Open($reserveDocPath, $false, $true, $false)
    $reserveWordDoc.ExportAsFixedFormat($reservePdfPath, 17)
    Write-Output $reservePdfPath
} finally {
    if ($null -ne $reserveWordDoc) {
        $reserveWordDoc.Close($false)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($reserveWordDoc)
    }
    if ($null -ne $reserveWordApp) {
        $reserveWordApp.Quit($false)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($reserveWordApp)
    }
}
