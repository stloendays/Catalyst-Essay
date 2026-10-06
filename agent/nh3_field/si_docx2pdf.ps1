# Convert the Word SI files in si/ to PDF with WPS Writer COM (no Word/LibreOffice on this machine).
# Documents are opened read-only and closed without saving; existing PDFs are kept.
# Usage: pwsh -File si_docx2pdf.ps1
$si = Join-Path $PSScriptRoot "si"
$app = $null
try {
  $app = New-Object -ComObject "KWps.Application"
  $app.Visible = $false
  Get-ChildItem $si -Include *.docx, *.doc -File -Recurse | ForEach-Object {
    $pdf = [System.IO.Path]::ChangeExtension($_.FullName, ".pdf")
    if (Test-Path $pdf) { Write-Host "skip $($_.Name)"; return }
    $doc = $app.Documents.Open($_.FullName, $false, $true)   # ConfirmConversions=false, ReadOnly=true
    try {
      $doc.ExportAsFixedFormat($pdf, 17)                      # 17 = wdExportFormatPDF
      Write-Host ("OK {0} pages={1}" -f $_.Name, $doc.ComputeStatistics(2))
    } finally {
      $doc.Close($false)
    }
  }
} finally {
  if ($app) { $app.Quit() }
}
